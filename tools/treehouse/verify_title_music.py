"""Compare generated title events/registers and Godot logo frames to DOS boot."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import zipfile

from PIL import Image
from build_demo import ROOT, SOURCE_SHA
from executable import unpack
from fm_music import render_registers
from midi import decode_sound, extract
from resources import parse_archive


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def vlq(value):
    result = [value & 127]
    while value >> 7:
        value >>= 7
        result.insert(0, 128 | (value & 127))
    return bytes(result)


def encode(track):
    data = b''
    previous = 0
    for event in track['events']:
        data += vlq(event['tick'] - previous)
        previous = event['tick']
        if event['explicit_status']:
            data += bytes([event['status']])
        if event['kind'] == 'meta':
            data += bytes([event['meta']])
        if event['kind'] != 'channel':
            data += vlq(len(event['data']))
        data += bytes(event['data'])
    return bytes([130 if track['loop'] else 2]) + b'MThd' + struct.pack('>I3H', 6, 0, 1, track['ppq']) + b'MTrk' + struct.pack('>I', len(data)) + data


def verify(output, native, control, godot):
    output.mkdir(parents=True, exist_ok=False)
    checks = []
    def check(name, passed, **details):
        checks.append(dict(name=name, passed=bool(passed), **details))
    source = ROOT / 'testing/output/treehouse/source/The_Treehouse_1991.zip'
    check('pinned original package', digest(source) == SOURCE_SHA)
    music = extract(source)
    with zipfile.ZipFile(source) as archive:
        image, _ = unpack(archive.read('TheTreeh/treehse.exe'))
        for name in ('th', 'midisnd'):
            data = archive.read(f'TheTreeh/{name}.dat')
            for record in parse_archive(data):
                key = f"{name}:{record['id']}"
                if record['tag'] != 'SND' or key not in music['tracks']:
                    continue
                original = data[record['payload_offset']:record['payload_offset'] + record['size']]
                check('lossless MIDI decode/re-encode ' + key, encode(music['tracks'][key]) == original,
                      events=len(music['tracks'][key]['events']))
    # Synthetic edge cases complement the eight real-resource round trips.
    header = b'\x02MThd' + struct.pack('>I3H', 6, 0, 1, 480) + b'MTrk'
    def song(data):
        return header + struct.pack('>I', len(data)) + data
    fixture = bytes.fromhex('00c00700903c4083603e0000ff510303d0908360803c0000ff2f00')
    parsed = decode_sound(song(fixture))
    check('running status retained and zero velocity preserved', parsed['events'][2]['data'] == [62, 0] and not parsed['events'][2]['explicit_status'])
    check('tempo change uses exact rational timeline', parsed['duration_us'] == [750000, 1])
    for name, bad in {
        'truncated header': header[:-1], 'running without status': song(bytes.fromhex('003c4000ff2f00')),
        'oversized delta': song(bytes.fromhex('8181818100903c4000ff2f00')),
        'status in data': song(bytes.fromhex('00903c9000ff2f00')),
        'missing end': song(bytes.fromhex('00903c40')),
        'zero tempo': song(bytes.fromhex('00ff510300000000ff2f00')),
        'data after end': song(bytes.fromhex('00ff2f0000')),
    }.items():
        try:
            decode_sound(bad)
            rejected = False
        except ValueError:
            rejected = True
        check('reject ' + name, rejected)
    run = json.loads((native / 'run.json').read_text())
    clean = json.loads((control / 'run.json').read_text())
    check('native and control captures succeeded', run['passed'] and clean['passed'])
    check('same original package and reference core', all(run[k] == clean[k] for k in ('core_sha256', 'content_sha256')))
    for name in ('frames.jsonl', 'state/audio.wav', 'state/selection.ram-0'):
        check('read-only observer preserves ' + name, digest(native / name) == digest(control / name))
    events = run['events']
    resets = [i for i, event in enumerate(events) if event['label'] == 'fm.dispatch' and event['ax'] & 255 == 4]
    irq, actual, cues, channel, tempos = 0, [], [], [], []
    for event in events[resets[0]:resets[1]]:
        label = event['label']
        if label == 'midi.irq':
            irq += 1
        elif label == 'fm.write':
            actual.append(dict(irq=irq, register=event['ax'] >> 8, value=event['ax'] & 255))
        elif label == 'midi.cue':
            cues.append(dict(irq=irq, value=event['ax'] & 255))
        elif label == 'midi.tempo':
            tempos.append(event['dx'] * 65536 + event['ax'])
        elif label == 'midi.event' and event['ax'] & 255 < 0xf0:
            status = (event['ax'] & 255) | (event['ax'] >> 8)
            data = [event['dx'] & 255]
            if status >> 4 not in (12, 13):
                data.append(event['dx'] >> 8)
            channel.append(dict(irq=irq, status=status, data=data))
    title = music['tracks']['midisnd:20200']
    expected = render_registers(title, music['bank'], list(struct.unpack_from('<12H', image, 0x31132)), list(image[0x31297:0x312a9]))
    check('all title OPL writes, order and timer ordinals', actual == expected, writes=len(expected))
    check('all title channel events and timer ordinals', channel == [dict(irq=e['irq'], status=e['status'], data=e['data']) for e in title['native']['events'] if e['kind'] == 'channel'], events=len(channel))
    check('all title cue bytes and timer ordinals', cues == [dict(irq=e['irq'], value=e['data'][0]) for e in title['native']['events'] if e['kind'] == 'meta' and e['meta'] == 7], cues=cues)
    check('original tempo conversion', tempos == [262144] + [t['step'] for t in title['native']['tempos']], steps=tempos)
    ram = (native / 'state/selection.ram-0').read_bytes()
    base = ram.index(b'Version 1.1') - image.index(b'Version 1.1')
    bank_event = next(e for e in events if e['label'] == 'fm.dispatch' and e['ax'] & 255 == 6)
    location = bank_event['es'] * 16 + bank_event['bx'] - (0x1a80 - base)
    bank = bytes(v for patch in music['bank']['patches'] for v in patch)
    check('source instrument bank matches active original driver bank', bank_event['ax'] >> 8 == len(music['bank']['patches']) and ram[location:location + len(bank)] == bank)
    headless = json.loads((godot / 'godot.json').read_text())
    checks.extend(headless['checks'])
    rows = [json.loads(line) for line in (native / 'frames.jsonl').read_text().splitlines()]
    previous = 0
    for frame in headless['frames']:
        rgb = Image.open(godot / frame['image']).convert('RGB').tobytes()
        sha = hashlib.sha256(rgb).hexdigest()
        match = next((i for i in range(previous, len(rows)) if rows[i].get('rgb_sha256') == sha), None)
        check('ordered complete native frame ' + frame['image'], match is not None,
              godot_tick=frame['tick'], native_callback=match, pixels=64000)
        if match is not None:
            previous = match
    report = dict(passed=all(c['passed'] for c in checks), checks=checks,
                  native_report_sha256=digest(native / 'run.json'), control_report_sha256=digest(control / 'run.json'),
                  godot_report_sha256=digest(godot / 'godot.json'),
                  source_files={str(p.relative_to(ROOT)):digest(p) for p in [Path(__file__).resolve(), ROOT/'tools/treehouse/midi.py', ROOT/'tools/treehouse/fm_music.py', ROOT/'treehouse-godot/scripts/startup.gd', ROOT/'treehouse-godot/scripts/game.gd']},
                  limits=['Image comparison proves ordered complete frames, not exact presentation times or all partial native redraws.',
                          'This register proof covers title track at default FM volume. Selection pitch bends have a separate proof; rhythm patches remain unsupported.',
                          'Synthesized PCM and Godot audio output are not proven equal to native mixer output.',
                          'Selection off-screen pose preparation is checked separately; full startup operation timing remains open.'])
    (output / 'report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(dict(passed=report['passed'], checks=len(checks), failures=[c for c in checks if not c['passed']]), indent=2))
    return report['passed']


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('output', 'native', 'control', 'godot'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    raise SystemExit(0 if verify(args.output, args.native, args.control, args.godot) else 1)
