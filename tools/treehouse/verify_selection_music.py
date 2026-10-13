"""Verify complete source-generated selection FM and its first native repeat."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import wave
import zipfile

from PIL import Image
from build_demo import ROOT, SOURCE_SHA
from executable import unpack
from fm_music import MelodicDriver
from midi import extract


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify(native, control, godot, output):
    output.mkdir(parents=True, exist_ok=False)
    checks = []
    def check(name, passed, **details):
        checks.append(dict(name=name, passed=bool(passed), **details))
    original = ROOT / 'testing/output/treehouse/source/The_Treehouse_1991.zip'
    check('pinned source', sha(original) == SOURCE_SHA)
    music = extract(original)
    with zipfile.ZipFile(original) as archive:
        image, _ = unpack(archive.read('TheTreeh/treehse.exe'))
    frequencies = list(struct.unpack_from('<14H', image, 0x31130))
    operators = list(image[0x31297:0x312a9])
    driver = MelodicDriver(music['bank'], frequencies, operators)
    for event in music['tracks']['midisnd:20200']['native']['events']:
        driver.event(event)
    initial_cursor = driver.cursor
    driver.irq = 0
    driver.writes = []
    driver.reset()
    for event in music['tracks']['midisnd:20000']['native']['events']:
        driver.event(event)
    generated = driver.writes[:]
    check('authored track returns allocation cursor to loop start', driver.cursor == initial_cursor)
    run = json.loads((native / 'run.json').read_text())
    other = json.loads((control / 'run.json').read_text())
    check('paired capture identity and completion', run['passed'] and other['passed'] and all(run[key] == other[key] for key in ('frames', 'core_sha256', 'content_sha256')))
    for name in ('frames.jsonl', 'state/audio.wav', 'state/selection.ram-0'):
        check('observer preserves ' + name, sha(native / name) == sha(control / name))
    events = run['events']
    resets = [i for i, event in enumerate(events) if event['label'] == 'fm.dispatch' and event['ax'] & 255 == 4]
    assert len(resets) >= 6, 'Capture does not include selection track completion and repeat'
    def observed(begin, end):
        irq, writes, channel = 0, [], []
        for event in events[begin:end]:
            if event['label'] == 'midi.irq':
                irq += 1
            elif event['label'] == 'fm.write':
                writes.append(dict(irq=irq, register=event['ax'] >> 8, value=event['ax'] & 255))
            elif event['label'] == 'midi.event' and event['ax'] & 255 < 0xf0:
                status = (event['ax'] & 255) | (event['ax'] >> 8)
                data = [event['dx'] & 255]
                if status >> 4 not in (12, 13):
                    data.append(event['dx'] >> 8)
                channel.append(dict(irq=irq, status=status, data=data))
        return writes, channel, irq
    actual, channel, last_irq = observed(resets[2], resets[3])
    track = music['tracks']['midisnd:20000']
    check('complete selection OPL values/order/timer ordinals', actual == generated, writes=len(actual))
    expected_channel = [dict(irq=e['irq'], status=e['status'], data=e['data']) for e in track['native']['events'] if e['kind'] == 'channel']
    check('complete selection MIDI values/order/timer ordinals', channel == expected_channel, events=len(channel), pitch_bends=sum(e['status'] >> 4 == 14 for e in channel))
    check('complete selection end-of-track interrupt', last_irq == track['native']['duration_irqs'], irq=last_irq)
    repeat, repeat_channel, _ = observed(resets[5], len(events))
    check('next loop starts with the same generated OPL sequence', len(repeat) > 100 and repeat == generated[:len(repeat)], writes=len(repeat))
    check('next loop starts with the same generated MIDI sequence', len(repeat_channel) > 10 and repeat_channel == expected_channel[:len(repeat_channel)])
    # Source-level bend boundaries and live retuning, beyond the authored song.
    offsets = {0:0xf400, 1:0xf5ff, 4096:0xfa00, 8191:0, 8192:0, 8193:0, 12288:0x0600, 16383:0x0bff}
    for bend, expected_offset in offsets.items():
        driver.pitch_bend(3, bend & 127, bend >> 7)
        offset, sign = driver.pitch[3]
        expected_sign = (bend > 8192) - (bend < 8192)
        check(f'bend {bend} exact source fixed-point representation', sign == expected_sign and offset == expected_offset)
    driver.pitch_bend(3, 0, 64)
    check('center bend restores zero offset', driver.pitch[3] == (0, 0))
    headless = json.loads((godot / 'godot.json').read_text())
    checks.extend(headless['checks'])
    for name in ('title', 'selection'):
        with wave.open(str(ROOT / f'treehouse-godot/data/{name}.wav'), 'rb') as audio:
            digest = hashlib.sha256(audio.readframes(audio.getnframes())).hexdigest()
        check(name + ' Godot import retains every original generated PCM byte', headless['pcm_sha256'][name] == digest)
    rgb = Image.open(godot / 'selection.png').convert('RGB').tobytes()
    digest = hashlib.sha256(rgb).hexdigest()
    timeline = [json.loads(line) for line in (native / 'frames.jsonl').read_text().splitlines()]
    match = next((row for row in timeline if row.get('rgb_sha256') == digest), None)
    check('initial Godot selection matches complete native frame', match is not None, pixels=64000, native_callback=match['callback'] if match else None)
    report = dict(passed=all(c['passed'] for c in checks), checks=checks,
                  evidence={str(p.relative_to(ROOT)):sha(p) for p in [native/'run.json', control/'run.json', godot/'godot.json']},
                  source_files={str(p.relative_to(ROOT)):sha(p) for p in [Path(__file__).resolve(), ROOT/'tools/treehouse/midi.py', ROOT/'tools/treehouse/fm_music.py', ROOT/'tools/treehouse/render_title_music.py', ROOT/'treehouse-godot/scripts/game.gd', ROOT/'treehouse-godot/scripts/preferences.gd']},
                  limits=['No native/Godot waveform or unshifted wall-clock timing equivalence claim.',
                          'PCM starts with source-derived post-title allocation and a fresh synthesizer; interrupted-logo chip state is not reconstructed.',
                          'PCM loop does not yet preserve live OPL oscillator/envelope state across the original restart calls.',
                          'Selection preview preparation is off-screen first-pose composition, already implemented; this is not an added animation.',
                          'Mute/unmute controls are functional tests, not native register/mixer equivalence.'])
    (output/'report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(dict(passed=report['passed'], checks=len(checks), failures=[c for c in checks if not c['passed']]), indent=2))
    return report['passed']


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('native', 'control', 'godot', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    raise SystemExit(0 if verify(args.native.resolve(), args.control.resolve(), args.godot.resolve(), args.output.resolve()) else 1)
