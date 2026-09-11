"""Audit a native demo against its original bytes and prepare a post-load replay.

Native inputs are checked against the file, not copied from the observed game.
Only the single initial checkpoint and decoded controls enter the clone.
"""
import argparse
import gzip
import hashlib
import json
import math
from pathlib import Path

from decode_wr1_demo import decode
from prepare_wr1_boundaries import gameplay_instructions, instruction_groups, IRQ_SECONDS, STAGES, EXTENDED_STAGES
from prepare_wr1_level_start import MOTION, ACTORS, PICTURES, FRESH_ZERO, video_checkpoint
from wr1_hardware_reference import event_names


def identify_music(initial, candidates):
    """Identify the loaded CMF from bytes captured at the initial checkpoint."""
    prefix = bytes(initial.get('loaded_music_prefix', initial['music_driver']['prefix']))
    if prefix[:16] != bytes(initial['music_driver']['prefix']):
        raise ValueError('Paused CMF bytes disagree with the initial trace header')
    matches = [path for path in candidates if path.read_bytes().startswith(prefix)]
    if len(prefix) < 16 or not prefix.startswith(b'CTMF') or len(matches) != 1:
        raise ValueError('Initial CMF header must uniquely identify the supplied music asset')
    return matches[0]


def prepare(capture, trace, demo, source_hash, start=500, level=4, launch_after=450):
    if not capture['complete'] or capture['source_sha256'] != source_hash:
        raise ValueError('Require a complete capture of the supplied frontend replay')
    frames = {r['call']: r for r in trace if r['event'] == 'frontend'}
    samples = 0
    for row in capture['samples']:
        frame = frames.get(row['replay_frame'] + 1)
        if frame is None:
            continue
        for key in ('x','y','gx','gy','sprite','phase','background_frame','entity_timer','timer','score'):
            if frame[key] != row[key]:
                raise ValueError(f'Capture/frontend disagreement at {row["replay_frame"]}: {key}')
        samples += 1
    if not samples or not any(r['replay_frame'] == start and r.get('demo_mode') == 1 for r in capture['samples']):
        raise ValueError('Checkpoint must be independently observed in native demo mode')
    first = next(r for r in trace if r['event'] == 'instruction' and r['ip'] == 0x444
                 and r['level_index'] == level - 1 and r['main_iteration'] == 0
                 and r['launch_call'] > launch_after)
    # The attract loop can start another demo after this one. Preserve all data
    # but restrict the comparison to this first invocation on the selected map.
    stop = next((r['pic_ms'] for r in trace if r['event'] == 'instruction' and r['ip'] == 0x444
                 and r['pic_ms'] > first['pic_ms'] and (r['level_index'] != level - 1 or r['main_iteration'] == 0)), math.inf)
    segment = [r for r in trace if first['pic_ms'] <= r.get('pic_ms', -1) < stop]
    if any(r.get('keyboard_any',0) for r in segment if r['event'] in ('instruction','frontend')):
        raise ValueError('Live keyboard activity interrupted the native demo; recapture with host input isolated')
    instructions, interruptions = gameplay_instructions(segment)
    final_complete = max(i for i, row in enumerate(instructions) if row['ip'] == 0xd72) + 1
    tail = instructions[final_complete:]
    terminal = None
    if tail and tail[-1].get('door_state') == 2:
        if tuple(r['ip'] for r in tail) != EXTENDED_STAGES[:7]:
            raise ValueError('Unrecognized terminal demo exit sequence')
        ending = [r for r in segment if r['event'] == 'lifecycle' and r['pic_ms'] > tail[-1]['pic_ms']
                  and r['ip'] in (0xa56, 0xa61, 0xaef, 0xc2e)]
        if not ending or [r['ip'] for r in ending[:2]] != [0xa56, 0xa61] or ending[-1]['ip'] != 0xc2e:
            raise ValueError('Demo exit lacks its completed door animation')
        terminal = {'kind':'demo_exit', 'begin':tail[0], 'completed':ending[-1],
                    'boundary':'0096:0C2E before demo return at file 3F94; level is not advanced'}
        instructions = instructions[:final_complete]
    elif tail:
        # 40C8..40CD: demo death returns from main without incrementing BP-2.
        # Require its actual rescue entry AND return; never forgive a trace gap.
        if tuple(r['ip'] for r in tail) not in (STAGES[:2], STAGES[:-1], EXTENDED_STAGES[:-1]):
            raise ValueError('Unrecognized terminal demo instruction sequence')
        rescue = [r for r in segment if r['event'] == 'lifecycle' and r['ip'] in (0x8b1, 0x969)
                  and r['pic_ms'] > tail[-1]['pic_ms']]
        if [r['ip'] for r in rescue] != [0x8b1, 0x969]:
            raise ValueError('Terminal demo admission lacks a complete rescue')
        walk = [r for r in segment if r['event'] == 'lifecycle' and r['ip'] == 0xa0c
                and r['pic_ms'] > rescue[1]['pic_ms']]
        if not walk or walk[-1]['x'] != first['x']:
            raise ValueError('Demo rescue did not finish walking to the saved spawn X')
        terminal = {'kind':'demo_death', 'begin':tail[0], 'rescue_begin':rescue[0],
                    'walk_begin':rescue[1], 'completed':walk[-1],
                    'boundary':'0096 main returns without D72; final rescue walk wait at 01A3:0A0C, before screen erase/return'}
        instructions = instructions[:final_complete]
    groups = list(instruction_groups(instructions, segment))
    for index, group in enumerate(groups):
        begin, end = group[0], group[-1]
        if begin['main_iteration'] != index or end['main_iteration'] != index + 1:
            raise ValueError('Native demo skipped or repeated a completed input index')
        if index >= len(demo['inputs']):
            raise ValueError('Native demo played beyond the stop marker')
        for key, expected in demo['inputs'][index].items():
            if bool(begin[key]) != expected:
                raise ValueError(f'Demo byte {index} disagrees with native {key}')
    if terminal:
        index = terminal['begin']['main_iteration']
        if index != len(groups) or any(bool(terminal['begin'][key]) != expected for key, expected in demo['inputs'][index].items()):
            raise ValueError('Terminal native controls disagree with the demo file')
    elif len(groups) != demo['updates']:
        raise ValueError('Capture ends before the full demo input stream without an observed terminal ending')
    initial = frames[start + 1].copy()
    if initial['cpu_cs'] != first['cs'] or not initial['cpu_flags'] & 512:
        raise ValueError('Checkpoint is inside a helper or interrupt; choose a stable main-loop handoff')
    sample = next(row for row in capture['samples'] if row['replay_frame'] == start)
    if 'loaded_music_prefix' in sample:
        initial['loaded_music_prefix'] = sample['loaded_music_prefix']
    previous = [g[-1] for g in groups if g[-1]['pic_ms'] < initial['pic_ms']][-1]
    for key in ('idle_ticks','left_index','right_index'):
        initial[key] = previous[key]
    remaining = [g for g in groups if g[0]['pic_ms'] > initial['pic_ms']]
    begin = remaining[0][0]
    offset = begin['main_iteration']
    for key in MOTION + ACTORS + PICTURES + ('entrance_timer','drips','gruzzle_move_timers'):
        if initial[key] != begin[key]:
            raise ValueError(f'Unstable initial checkpoint: {key}')
    if any(initial[k] for k in FRESH_ZERO) or initial['entrance_timer'] <= 10:
        raise ValueError('Require an untouched post-load checkpoint')
    if any(a['state'] != -1 for a in initial['gruzzles']):
        raise ValueError('Initial actor effects are unsupported')
    period = 1000 / 70.086304
    lower, upper = -math.inf, math.inf
    irq_lower, irq_upper = 0., IRQ_SECONDS * 8
    calibration_start = first['launch_call']
    for counter in range(calibration_start, start):
        row = frames[counter + 1]
        if any(row[k] for k in ('up','down','left','right')) or row['threshold'] != 8:
            raise ValueError('Demo clock calibration must use idle controls')
        ms = row['pic_ms']
        if abs(ms - round(ms)) > .001:
            raise ValueError('Frontend handoff must be on a millisecond boundary')
        lower, upper = max(lower, ms - 1 - (counter + 1) * period), min(upper, ms - (counter + 1) * period)
        updates = row['entity_timer'] - initial['entity_timer']
        interrupts = updates * 8 + row['timer']
        elapsed = (ms - initial['pic_ms']) / 1000
        irq_lower, irq_upper = max(irq_lower, interrupts * IRQ_SECONDS - elapsed), min(irq_upper, (interrupts + 1) * IRQ_SECONDS - elapsed)
    phase = initial['timer'] * IRQ_SECONDS + initial['pit0_elapsed_ms'] / 1000
    if lower >= upper or not irq_lower - 1e-6 <= phase <= irq_upper + 1e-6:
        raise ValueError('Initial hardware phase contradicts idle observations')
    end_counter = min(capture['end_frame'], (terminal['completed'] if terminal else remaining[-1][-1])['launch_call'] + 2)
    updates = [{'tick': i + 1, 'demo_index': g[0]['main_iteration'], 'begin': g[0], 'completed': g[-1]}
               for i, g in enumerate(remaining)]
    replay = {'fps':70, 'source_fps':70.086304, 'level':level, 'difficulty':initial['difficulty'],
              'character':'girl' if initial['character'] else 'boy', 'events':[],
              'source_sha256':source_hash, 'source_start_frame':start, 'source_end_frame':end_counter,
              'total_frames':end_counter - start, 'source_clock_quantum_seconds':.001,
              'source_clock_phase_seconds':(((lower+upper)/2+(start+1)*period)%1)/1000,
              'original_clock_phase_seconds':phase,
              'original_demo_inputs':demo['inputs'][offset:],
              'demo_provenance':{k:demo[k] for k in ('sha256','size','updates','terminator_offset','trailing_bytes')},
              'demo_input_offset':offset,
              'original_level_start':{k:initial[k] for k in MOTION + ('score','words','word_cursor','mystery_index','active_index','word_offset','picture_offset','entrance_timer','drips')},
              'original_entity_start':{k:initial[k] for k in ACTORS + ('gruzzle_move_timers',)},
              'original_picture_start':{k:initial[k] for k in PICTURES},
              'original_video_start':video_checkpoint(initial)}
    fixture = {k:capture[k] for k in ('complete','source_sha256','exe_sha256','core_sha256')}
    fixture.update(demo_sha256=demo['sha256'], boundary='before WR1 instruction 0096:0d72 / file 0x40d2',
                   initial=initial, initial_counter=start, validation_input_start_frame=start,
                   updates=updates, interrupted_admissions=interruptions, demo_terminal=terminal,
                   demo_audit={'decoded_updates':demo['updates'],'native_completed_updates':len(groups),
                               'verified_input_bits':(len(groups)+int(terminal is not None))*5,'checkpoint_input_offset':offset,
                               'terminal_input_index':terminal['begin']['main_iteration'] if terminal else None,
                               'native_consumed_inputs':len(groups)+int(terminal is not None),
                               'observed_entire_input_stream':len(groups)+int(terminal is not None)==demo['updates']},
                   clock_bounds_ms=[lower,upper],irq_phase_bounds_seconds=[irq_lower,irq_upper])
    return replay, fixture


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('capture','trace','demo','replay'):
        p.add_argument('--'+name, type=Path, required=True)
    p.add_argument('--name', default='demo_level4')
    p.add_argument('--level', type=int, default=4)
    p.add_argument('--start', type=int, default=500)
    p.add_argument('--launch-after', type=int, default=450)
    p.add_argument('--checkpoint-capture', type=Path, help='Additional checkpoint screenshot from the identical frontend replay')
    p.add_argument('--music', type=Path, help='CMF asset; otherwise identify it from the initial native header')
    p.add_argument('--link-map', type=Path, default=Path('testing/output/dosbox-pure-trace/wr1_trace.map'))
    p.add_argument('--directory', type=Path, default=Path('testing/fixtures'))
    a = p.parse_args()
    capture = json.loads(a.capture.read_text())
    if a.checkpoint_capture:
        extra = json.loads(a.checkpoint_capture.read_text())
        if not extra['complete'] or any(extra[k] != capture[k] for k in ('source_sha256','exe_sha256','core_sha256')):
            raise ValueError('Additional checkpoint must use the same complete native experiment')
        with a.checkpoint_capture.with_suffix('.jsonl').open('rb') as stream:
            if hashlib.file_digest(stream, 'sha256').hexdigest() != extra['instruction_trace_sha256']:
                raise ValueError('Additional checkpoint trace hash disagrees with capture')
        checkpoint = next(r for r in extra['samples'] if r['replay_frame'] == a.start and 'screenshot' in r)
        capture['samples'] = [r for r in capture['samples'] if r['replay_frame'] != a.start] + [checkpoint]
    trace, h = [], hashlib.sha256()
    with a.trace.open('rb') as stream:
        for line in stream:
            h.update(line)
            # Avoid retaining the much larger CPU/driver trace in memory.
            if not any(b'"event":"' + kind + b'"' in line[:40] for kind in (b'frontend', b'instruction', b'lifecycle')):
                continue
            row = json.loads(line)
            if row['event'] in ('frontend','instruction','lifecycle'):
                trace.append(row)
    if h.hexdigest() != capture['instruction_trace_sha256']:
        raise ValueError('Full instruction trace hash disagrees with capture')
    replay, fixture = prepare(capture, trace, decode(a.demo.read_bytes()), hashlib.sha256(a.replay.read_bytes()).hexdigest(),
                              a.start, a.level, a.launch_after)
    keys = ('pic_ms','pic_ticks','cycle_left','cycles_remaining','pit','pic_interrupts','pic_queue','vga_timing',
            'keyboard','cpu_cs','cpu_ip','cpu_ax','cpu_flags','music_driver','clock_state','keyboard_game')
    music = identify_music(fixture['initial'], [a.music] if a.music else sorted(Path('assets/audio/original').glob('*.cmf')))
    replay['original_music_clock'] = {
        'initial':{k:fixture['initial'][k] for k in keys}, 'event_names':event_names(a.link_map.read_text()),
        'music_file':'res://'+music.as_posix(), 'music_sha256':hashlib.sha256(music.read_bytes()).hexdigest(),
        'link_map_sha256':hashlib.sha256(a.link_map.read_bytes()).hexdigest()}
    replay['instruction_trace_sha256'] = fixture['instruction_trace_sha256'] = h.hexdigest()
    if a.checkpoint_capture:
        provenance = {'capture_sha256':hashlib.sha256(a.checkpoint_capture.read_bytes()).hexdigest(),
                      'instruction_trace_sha256':extra['instruction_trace_sha256'], 'counter':a.start}
        replay['checkpoint_capture'] = fixture['checkpoint_capture'] = provenance
    manifest = {'source_sha256':replay['source_sha256'], 'instruction_trace_sha256':h.hexdigest(), 'pairs':[]}
    files = {}
    for row in capture['samples']:
        counter = row['replay_frame']
        if 'screenshot' not in row or not replay['source_start_frame'] <= counter < replay['source_end_frame']:
            continue
        source = Path(row['screenshot'])
        name = f'wr1_{a.name}_counter_{counter:06d}.png'
        data = source.read_bytes()
        files[a.directory/name] = data
        sha = hashlib.sha256(data).hexdigest()
        if counter == replay['source_start_frame']:
            manifest.update(initial_file=name,initial_sha256=sha)
        else:
            manifest['pairs'].append({'native_counter':counter,'clone_source_frame':counter-1,'native_file':name,'sha256':sha})
    if 'initial_file' not in manifest:
        raise ValueError('Missing native checkpoint image')
    for kind, data in [('replay',replay),('boundaries',fixture),('pixels',manifest)]:
        path = a.directory/f'wr1_{a.name}_{kind}.json'
        if kind == 'boundaries':
            files[path.with_suffix('.json.gz')] = gzip.compress(json.dumps(data,separators=(',',':')).encode(),mtime=0)
        else:
            files[path] = (json.dumps(data,indent=2)+'\n').encode()
    if any(path.exists() or (path.suffix == '.gz' and path.with_suffix('').exists()) for path in files):
        raise ValueError('Refusing to overwrite existing demo evidence')
    a.directory.mkdir(parents=True,exist_ok=True)
    for path, data in files.items():
        path.write_bytes(data)
    print(json.dumps(fixture['demo_audit']))


if __name__ == '__main__':
    main()
