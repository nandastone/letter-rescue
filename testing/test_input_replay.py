"""Actual Godot replay scheduling. Set GODOT to the console executable to run."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
GODOT = os.environ.get('GODOT') or shutil.which('godot')


@unittest.skipUnless(GODOT, 'Set GODOT to run engine integration tests')
class InputReplayTests(unittest.TestCase):
    def test_live_recording_excludes_menu_and_title_then_replays(self):
        self.record_roundtrip(False)

    def test_saved_profile_speed_and_difficulty_changes_roundtrip(self):
        self.record_roundtrip(True)

    def record_roundtrip(self, profile_settings):
        folder = ROOT/'testing/output/replay_tests'/('profile_roundtrip' if profile_settings else 'roundtrip')
        folder.mkdir(parents=True, exist_ok=True)
        replay = folder/'recording.json'
        traces = []
        for mode in ('record', 'replay'):
            trace = folder/f'{mode}.jsonl'
            command = [GODOT, '--headless', '--fixed-fps', '70', '--quit-after', '1000',
                       '--path', str(ROOT)]
            if mode == 'record':
                command += ['--script', 'testing/record_wr1_roundtrip.gd']
            command += ['--', '--original-rules', '--'+mode, str(replay), '--state-trace', str(trace)]
            if mode == 'record':
                command += ['--character', 'boy']
                if profile_settings:
                    command += ['--profile-settings']
            result = subprocess.run(command, capture_output=True, text=True, timeout=30,
                                    creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertNotIn('ERROR:', result.stdout + result.stderr)
            if mode == 'record':
                self.assertIn('Record roundtrip PASS', result.stdout)
            rows = [json.loads(line) for line in trace.read_text().splitlines()]
            for row in rows:
                for key in ('physics_frame', 'replay_frame', 'source_frame', 'completed_source_frame',
                            'source_sha256', 'replay_sha256'):
                    row.pop(key, None)
            traces.append(rows)
        recording = json.loads(replay.read_text())
        self.assertEqual((recording['level'], recording['difficulty']), (5, 1) if profile_settings else (1, 0))
        self.assertEqual(recording['character'], 'boy')
        self.assertIn('original_start_seed', recording)
        self.assertGreaterEqual(recording['original_start_seed'], 0)
        self.assertLessEqual(recording['original_start_seed'], 65535)
        self.assertEqual(recording['total_frames'], 70)
        self.assertEqual([event['frame'] for event in recording['events']], [0, 10, 21, 30, 35, 56] if profile_settings else [0, 21, 35, 56])
        if profile_settings:
            self.assertEqual(recording['original_profile_start']['score'], 12345)
            self.assertEqual(recording['original_speed_ticks'], 6)
            self.assertEqual([e for e in recording['events'] if 'setting' in e],
                [{'frame':10,'setting':'speed','value':4},{'frame':30,'setting':'difficulty','value':2}])
        self.assertEqual(traces[0], traces[1])

    def run_replay(self, suffix, overrides=None):
        folder = ROOT/'testing/output/replay_tests'
        folder.mkdir(parents=True, exist_ok=True)
        replay = folder/'frame_zero.json'
        trace = folder/f'{suffix}.jsonl'
        data = {'fps': 70, 'level': 1, 'difficulty': 0, 'total_frames': 70,
            'source_start_frame': 350, 'events': [
                {'frame': 0, 'action': 'move_right', 'pressed': True},
                {'frame': 7, 'action': 'move_right', 'pressed': False},
                {'frame': 69, 'action': 'move_left', 'pressed': True}]}
        data.update(overrides or {})
        replay.write_text(json.dumps(data), encoding='utf-8')
        result = subprocess.run([GODOT, '--headless', '--fixed-fps', '70', '--path', str(ROOT), '--',
            '--original-rules', '--replay', str(replay), '--state-trace', str(trace)],
            capture_output=True, text=True, timeout=30,
            creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertNotIn('ERROR:', result.stdout + result.stderr)
        return [json.loads(line) for line in trace.read_text().splitlines()]

    def test_frame_zero_readiness_order_and_last_frame(self):
        rows = self.run_replay('first')
        self.assertEqual(len(rows), 13)  # Initialization +12 logical updates.
        self.assertEqual(rows[1]['replay_frame'], 5)
        self.assertEqual(rows[1]['source_frame'], 355)
        self.assertTrue(rows[1]['held']['right'])
        self.assertEqual(rows[1]['world_x'], 56)
        self.assertFalse(rows[2]['held']['right'])
        self.assertEqual(rows[-1]['replay_frame'], 69)
        self.assertTrue(rows[-1]['held']['left'])
        self.assertEqual(rows[-1]['world_x'], 48)

    def test_repeated_replay_has_identical_logical_trace(self):
        first, second = self.run_replay('repeat_a'), self.run_replay('repeat_b')
        for rows in (first, second):
            for row in rows:
                row.pop('physics_frame')  # Host scene-loading time is not replay time.
        self.assertEqual(first, second)

    def test_measured_rate_phase_and_background_are_applied(self):
        rows = self.run_replay('measured_clock', {'source_fps': 140.0,
            'original_clock_phase_seconds': 0.02, 'original_start_background_frame': 3})
        self.assertEqual(len(rows), 7)  # Half a native second plus the initial phase.
        self.assertEqual(rows[0]['background_frame'], 3)
        self.assertEqual(rows[1]['background_frame'], 0)
        self.assertEqual(rows[1]['replay_frame'], 8)
        self.assertFalse(rows[1]['held']['right'])  # Released before that first update.
        self.assertEqual(rows[-1]['world_x'], 48)
