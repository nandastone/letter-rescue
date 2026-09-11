"""Record continuous original-game PCM through the read-only audio-probe core.

Never pauses the mixer. The BSV supplies all input. Closes only its own process.
Output starts with a uint32 sample rate, then stereo little-endian int16 PCM.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import socket
import subprocess
import time

from capture_wr1_replay import ROOT, replay_frame
from bsv_replay import read_replay
from wr1_trace import Reader


def capture(args):
    replay_data = args.replay.read_bytes()
    header, _ = read_replay(replay_data)
    if not 0 < args.end_frame < header['frame_count']:
        raise ValueError('Require 0 < end frame < replay length')
    exe_hash = hashlib.sha256((args.game_dir/'WR1.EXE').read_bytes()).hexdigest()
    if exe_hash != 'b8395fab1e0341e1398790b986c8cf8bf2393dcfdb5d492e7d7dd910d2589d0f':
        raise ValueError('Unsupported WR1 executable')
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as check:
        check.bind(('127.0.0.1', args.port))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(b'') # A missing probe must not reuse an older recording.
    config = args.output.with_suffix('.cfg')
    config.write_text(f'network_cmd_enable = "true"\nnetwork_cmd_port = "{args.port}"\n'
                      'config_save_on_exit = "false"\naudio_mute_enable = "true"\n'
                      'input_driver = "null"\ninput_joypad_driver = "null"\n'
                      'savestate_auto_save = "false"\nsavestate_auto_load = "false"\n')
    environment = dict(os.environ)
    environment.pop('DBP_WR1_TRACE_FILE', None)
    environment['DBP_WR1_AUDIO_FILE'] = str(args.output.resolve())
    startup = subprocess.STARTUPINFO()
    startup.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    startup.wShowWindow = 0
    result = dict(complete=False, source_sha256=hashlib.sha256(replay_data).hexdigest(),
                  core_sha256=hashlib.sha256(args.core.read_bytes()).hexdigest(),
                  exe_sha256=exe_hash, source_frame_count=header['frame_count'],
                  requested_end_frame=args.end_frame,
                  boundary='Continuous core output including startup; no frame stepping or memory edits')
    with args.output.with_suffix('.log').open('w') as log:
        process = subprocess.Popen([str(args.retroarch), '--verbose', '--appendconfig',
            str(ROOT/'tools/retroarch.cfg')+'|'+str(config.resolve()), '-L', str(args.core),
            '-P', str(args.replay.resolve()), str(args.game_dir)], stdout=log, stderr=subprocess.STDOUT,
            env=environment, startupinfo=startup)
        reader = Reader(args.port)
        try:
            deadline = time.monotonic() + args.timeout
            while time.monotonic() < deadline and process.poll() is None:
                try:
                    frame = replay_frame(reader)
                except (OSError, RuntimeError):
                    time.sleep(0.1)
                    continue
                if frame >= args.end_frame:
                    result['end_frame'] = frame
                    result['complete'] = True
                    break
                time.sleep(0.03)
            if not result['complete']:
                raise RuntimeError('Native PCM recording did not reach its requested endpoint')
        finally:
            reader.socket.close()
            if process.poll() is None:
                process.terminate()
                process.wait(timeout=10)
            if args.output.exists():
                data = args.output.read_bytes()
                result['sample_rate'] = int.from_bytes(data[:4], 'little')
                result['frames'] = (len(data)-4)//4
                result['pcm_sha256'] = hashlib.sha256(data).hexdigest()
                if len(data) <= 4 or (len(data)-4) % 4 or not 8000 <= result['sample_rate'] <= 192000:
                    result['complete'] = False
                    result['error'] = 'Missing or invalid stereo PCM output from the probe'
            args.output.with_suffix('.json').write_text(json.dumps(result, indent=2)+'\n')
    if not result['complete']:
        raise RuntimeError(result.get('error', 'Incomplete native PCM recording'))
    print(json.dumps(result))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--retroarch', type=Path, default=Path('C:/RetroArch-Win64/retroarch.exe'))
    parser.add_argument('--core', type=Path, default=Path('testing/output/dosbox-pure-trace/dosbox_pure_audio_probe.dll'))
    parser.add_argument('--game-dir', type=Path, required=True)
    parser.add_argument('--replay', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--end-frame', type=int, default=2200)
    parser.add_argument('--port', type=int, default=55453)
    parser.add_argument('--timeout', type=float, default=90)
    capture(parser.parse_args())
