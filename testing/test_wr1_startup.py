"""Original-code seed cases and actual fresh-scene / recording contracts."""
import json
import os
import subprocess
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from run_wr1_parity import ROOT, run_engine


@unittest.skipUnless(os.environ.get('GODOT'), 'Set GODOT for startup checks')
class StartupTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(dir=ROOT / 'testing/output')
        self.addCleanup(self.temporary.cleanup)
        self.output = Path(self.temporary.name)

    def start(self, seed, mode=0):
        name = f'start-{seed}-{mode}'
        output = self.output / f'{name}.json'
        run_engine(os.environ['GODOT'], ['--headless', '--quit-after', '500', '--script',
                   'testing/probe_wr1_start.gd', '--', '--original-rules', '--original-seed',
                   str(seed), '--probe-difficulty', str(mode), '--probe-output', str(output)],
                   self.output, name, 30)
        return json.loads(output.read_text())

    def test_time_conversion_against_original_machine_code(self):
        run_engine(os.environ['GODOT'], ['--headless', '--quit-after', '2', '--script',
                   'testing/test_wr1_startup.gd'], self.output, 'clock', 30)
        self.assertIn('seed cases PASS: 1552', (self.output / 'clock.log').read_text())

    def test_live_scene_matches_native_fresh_start(self):
        fixture = json.loads((ROOT / 'testing/fixtures/wr1_fresh_start.json').read_text())
        for case in fixture['cases']:
            with self.subTest(difficulty=case['difficulty']):
                actual = self.start(case['seed'], case['difficulty'])
                expected = case['expected'].copy()
                mystery_index = expected.pop('mystery_index')
                expected['mystery_word'] = expected['words'][mystery_index].upper()
                self.assertEqual({k: actual[k] for k in expected}, expected)

    def test_different_seeds_change_starts_for_every_difficulty(self):
        for difficulty in range(3):
            rows = [self.start(seed, difficulty) for seed in (0, 1, 65535)]
            self.assertEqual(len({r['rng'] for r in rows}), 3)
            for row in rows:
                self.assertNotEqual(row['word_offset'], row['picture_offset'])
                self.assertIn(row['mystery_word'].lower(), row['words'])
                self.assertIn(row['gruzzle_count'], ((1,), (2, 3), (4,))[difficulty])
        self.assertEqual(self.start(20716), self.start(20716))

    def test_replay_rejects_invalid_or_mixed_seed_state(self):
        cases = [{'original_start_seed': value} for value in (-1, 65536, 1.5, '123', True)]
        cases += [{'original_start_seed': 20716, field: {'rng': 1}} for field in
                  ('original_entity_start', 'original_level_start', 'original_picture_start',
                   'original_music_clock', 'original_video_start')]
        for index, data in enumerate(cases):
            with self.subTest(data=data):
                replay = self.output / f'invalid-{index}.json'
                replay.write_text(json.dumps(dict(fps=70, level=1, difficulty=0, total_frames=1,
                                                  events=[], **data)))
                process = subprocess.run([os.environ['GODOT'], '--headless', '--quit-after', '10',
                    '--path', str(ROOT), '--', '--original-rules', '--replay', str(replay)],
                    capture_output=True, text=True, timeout=30,
                    creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
                self.assertEqual(process.returncode, 1, process.stdout + process.stderr)
                self.assertNotIn('SCRIPT ERROR:', process.stderr)


if __name__ == '__main__':
    unittest.main()
