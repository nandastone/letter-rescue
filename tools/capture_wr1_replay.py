"""Capture bounded read-only native snapshots from a task-owned replay process.
	
Samples are paused frontend-frame states, not guaranteed completed DOS updates.
Leaves normal game sessions alone and closes only the process this command starts.
"""
import argparse
import hashlib
import json
import os
import socket
import subprocess
import time
from pathlib import Path
from bsv_replay import read_replay
from wr1_trace import Reader

ROOT = Path(__file__).resolve().parents[1]


def replay_frame(reader):
    result = reader.command('GET_CONFIG_PARAM active_replay').split()
    if len(result) != 5 or result[:2] != ['GET_CONFIG_PARAM', 'active_replay']:
        raise RuntimeError('No active native replay: ' + ' '.join(result))
    return int(result[4])


def advance(reader):
    before = replay_frame(reader)
    reader.command('FRAMEADVANCE', False)
    deadline = time.monotonic() + 2
    while True:
        time.sleep(.02)
        after = replay_frame(reader)
        if after != before or time.monotonic() >= deadline:
            break
    if after != before + 1:
        raise RuntimeError(f'Native replay advanced {before} -> {after}, expected one frame')
    return after


def advance_to(reader, target):
    """Run a sparse gap normally, then frame-step to the exact requested counter."""
    frame = replay_frame(reader)
    if target-frame > 40:
        reader.require_paused()
        reader.command('PAUSE_TOGGLE', False)
        deadline = time.monotonic()+max(10,(target-frame)/40)
        while frame < target-20:
            if time.monotonic()>deadline:
                raise RuntimeError('Native replay stalled between sparse samples')
            time.sleep(.02)
            frame = replay_frame(reader)
        reader.command('FRAMEADVANCE', False)
        time.sleep(.15)
        reader.require_paused()
        frame = replay_frame(reader)
        if frame>target:
            raise RuntimeError(f'Sparse capture overshot {target}: {frame}')
    while frame<target:
        frame = advance(reader)
    return frame


def capture(args):
    replay_data = args.replay.read_bytes()
    header, _ = read_replay(replay_data)
    if not 32 <= args.start_frame < args.end_frame < header['frame_count']:
        raise ValueError('Require32 <= start < end < replay length (end inclusive)')
    exe = (args.game_dir/'WR1.EXE').read_bytes()
    if hashlib.sha256(exe).hexdigest() != 'b8395fab1e0341e1398790b986c8cf8bf2393dcfdb5d492e7d7dd910d2589d0f':
        raise ValueError('Unsupported WR1 executable')
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as check:
        check.bind(('127.0.0.1', args.port))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    screenshot_frames = set(args.screenshot_frames or [])
    sample_frames = set(args.sample_frames or []) | screenshot_frames | {args.start_frame,args.end_frame}
    run_between_samples = getattr(args,'run_between_samples',False)
    if run_between_samples and args.sample_frames is None:
        raise ValueError('Running gaps requires an explicit --sample-frames selection')
    if any(f < args.start_frame or f > args.end_frame for f in screenshot_frames):
        raise ValueError('Screenshot frames must be inside the capture range')
    screenshot_dir = args.output.with_suffix('').resolve().with_name(args.output.stem + '_frames')
    if screenshot_frames:
        screenshot_dir.mkdir(parents=True, exist_ok=True)
    overlay = args.output.with_suffix('.cfg').resolve()
    overlay.write_text(f'network_cmd_enable = "true"\nnetwork_cmd_port = "{args.port}"\n'
        'config_save_on_exit = "false"\naudio_mute_enable = "true"\n'
        # Replay controls still reach the core through BSV. Host focus/modifier
        # releases must not inject live keyboard callbacks into the experiment.
        'input_driver = "null"\ninput_joypad_driver = "null"\n'
        'savestate_auto_save = "false"\nsavestate_auto_load = "false"\n', encoding='utf-8')
    if args.generic_keyboard_port is not None:
        with overlay.open('a', encoding='utf-8') as config:
            config.write(f'input_max_users = "{args.generic_keyboard_port + 1}"\n')
            config.write(f'input_libretro_device_p{args.generic_keyboard_port + 1} = "257"\n')
    if getattr(args, 'core_options', None):
        with overlay.open('a', encoding='utf-8') as config:
            config.write('game_specific_options = "false"\nglobal_core_options = "true"\n')
            config.write(f'core_options_path = "{args.core_options.resolve().as_posix()}"\n')
    if args.game_focus:
        # BSV keyboard callbacks still pass through RetroArch's hotkey filter.
        # Match physical-key recordings made with Game Focus enabled.
        with overlay.open('a', encoding='utf-8') as config:
            config.write('input_auto_game_focus = "1"\n')
    if screenshot_frames:
        with overlay.open('a', encoding='utf-8') as config:
            config.write(f'screenshot_directory = "{screenshot_dir.as_posix()}"\nvideo_gpu_screenshot = "false"\n')
    startup = None
    if hasattr(subprocess, 'STARTUPINFO'):
        startup = subprocess.STARTUPINFO()
        startup.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startup.wShowWindow = 0
    rows, process, reader = [], None, None
    result = {'source_sha256': hashlib.sha256(replay_data).hexdigest(),
              'host_input_driver':'null',
              'exe_sha256': hashlib.sha256(exe).hexdigest(),
              'core_sha256': hashlib.sha256(args.core.read_bytes()).hexdigest(),
              'source_frame_count': header['frame_count'], 'start_frame': args.start_frame,
              'end_frame': args.end_frame, 'complete': False,
              'boundary': 'paused frontend snapshots; render/display parity is diagnostic only', 'samples': rows}
    if args.game_focus:
        result['game_focus'] = True
    if run_between_samples:
        result['run_between_samples'] = True
    if args.generic_keyboard_port is not None:
        result['generic_keyboard_port'] = args.generic_keyboard_port
    try:
        with args.output.with_suffix('.log').open('w', encoding='utf-8') as log:
            environment = os.environ.copy()
            environment.pop('DBP_WR1_TRACE_FILE', None)
            environment.pop('DBP_WR1_AUDIO_FILE', None)
            if args.instruction_trace:
                args.instruction_trace.parent.mkdir(parents=True, exist_ok=True)
                args.instruction_trace.write_bytes(b'') # A stock core must not reuse a stale trace.
                environment['DBP_WR1_TRACE_FILE'] = str(args.instruction_trace.resolve())
            process = subprocess.Popen([str(args.retroarch), '--verbose', '--appendconfig',
                str(ROOT/'tools/retroarch.cfg')+'|'+str(overlay), '-L', str(args.core),
                '-P', str(args.replay.resolve()), str(args.game_dir)],
                stdout=log, stderr=subprocess.STDOUT, startupinfo=startup, env=environment)
            reader = Reader(args.port)
            # Long instruction traces can briefly stall the core's command loop.
            reader.socket.settimeout(10.0)
            deadline = time.monotonic() + args.startup_timeout
            while True:
                if time.monotonic() > deadline or process.poll() is not None:
                    raise RuntimeError('Native replay failed to reach capture range')
                try:
                    frame = replay_frame(reader)
                    if frame >= args.start_frame - 20:
                        reader.command('FRAMEADVANCE', False)
                        time.sleep(.15)
                        break
                except (OSError, RuntimeError):
                    pass
                time.sleep(.02)
            reader.require_paused()
            frame = replay_frame(reader)
            if frame > args.start_frame:
                raise RuntimeError(f'Pause overshot requested start: {frame}')
            while frame < args.start_frame:
                frame = advance(reader)
            base = reader.find_ds(exe)
            result.update({'mapped_ds_base': base, 'retroarch': reader.command('VERSION')})
            while frame <= args.end_frame:
                if args.sample_frames is not None and frame not in sample_frames:
                    frame = advance_to(reader,min(f for f in sample_frames if f>frame)) if run_between_samples else advance(reader)
                    continue
                row = reader.snapshot(base)
                music_prefix = reader.music_prefix(base)
                if music_prefix is not None:
                    row['loaded_music_prefix'] = music_prefix
                if row.get('replay_frame') != frame:
                    raise RuntimeError('Native sample frame changed while reading')
                rows.append(row)
                if frame in screenshot_frames:
                    before = set(screenshot_dir.glob('*.png'))
                    reader.command('SCREENSHOT', False)
                    deadline = time.monotonic() + 3
                    while not (created := set(screenshot_dir.glob('*.png')) - before):
                        if time.monotonic() > deadline:
                            raise RuntimeError('Native screenshot was not produced')
                        time.sleep(.02)
                    if len(created) != 1:
                        raise RuntimeError('Ambiguous native screenshot output')
                    image = created.pop()
                    # Screenshot is the returned video frame, independent of the
                    # ahead-of-video paused memory snapshot documented above.
                    destination = screenshot_dir / f'counter_{frame:06d}.png'
                    while True:
                        try:
                            image.replace(destination)
                            break
                        except PermissionError:
                            if time.monotonic() > deadline:
                                raise
                            time.sleep(.02) # RetroArch can still be flushing the PNG.
                    row['screenshot'] = str(destination)
                if len(rows) % 50 == 0:
                    print(f'Captured {len(rows)} native frames through {frame}', flush=True)
                if frame == args.end_frame:
                    break
                frame = advance(reader)
            if args.instruction_trace and (not args.instruction_trace.is_file() or args.instruction_trace.stat().st_size == 0):
                raise RuntimeError('Core did not produce the requested instruction trace')
            result['complete'] = True
    except Exception as error:
        result['error'] = str(error)
        raise
    finally:
        if reader:
            reader.socket.close()
        if process and process.poll() is None:
            process.terminate()
            process.wait(timeout=10)
        if args.instruction_trace and args.instruction_trace.is_file():
            with args.instruction_trace.open('rb') as stream:
                result['instruction_trace_sha256'] = hashlib.file_digest(stream, 'sha256').hexdigest()
        args.output.write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
    print(f'Saved {len(rows)} native snapshots: {args.output}')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--retroarch', type=Path, required=True)
    parser.add_argument('--core', type=Path, required=True)
    parser.add_argument('--game-dir', type=Path, required=True)
    parser.add_argument('--replay', type=Path, required=True)
    parser.add_argument('--start-frame', type=int, required=True)
    parser.add_argument('--end-frame', type=int, required=True)
    parser.add_argument('--port', type=int, default=55445)
    parser.add_argument('--startup-timeout', type=float, default=40,
                        help='Seconds allowed to play through to the capture range')
    parser.add_argument('--generic-keyboard-port', type=int, choices=range(4),
                        help='Enable DOSBox Pure Generic Keyboard on this zero-based controller port')
    parser.add_argument('--core-options', type=Path, help='Isolated per-run core options; never modifies user settings')
    parser.add_argument('--game-focus', action='store_true',
                        help='Enable Game Focus for physical-key BSV recordings; prevents hotkey filtering')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--instruction-trace', type=Path, help='Requires the separate WR1 tracing core')
    parser.add_argument('--screenshot-frames', type=int, nargs='*', help='Paused counters whose returned video frame to save')
    parser.add_argument('--sample-frames', type=int, nargs='*', help='Only read RAM at these counters, screenshots and endpoints; instruction tracing stays continuous')
    parser.add_argument('--run-between-samples', action='store_true', help='Run sparse gaps normally; still pause at exact requested sample counters')
    args = parser.parse_args()
    capture(args)


if __name__ == '__main__':
    main()
