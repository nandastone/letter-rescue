"""Long native routes exercise resets and terrain through the actual game."""
import copy
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from run_wr1_logical_route import input_stream, run
from run_wr1_parity import read, save, digest, run_engine
from compare_wr1_boundaries import compare


class LongRouteEvidenceTests(unittest.TestCase):
    def test_routes_cover_movement_and_repeated_rescues(self):
        for name, updates, rescues, positions in [('level3_long', 534, 6, 284), ('level4_long', 743, 4, 415)]:
            fixture = read(ROOT / f'testing/fixtures/wr1_{name}_boundaries.json')
            replay = read(ROOT / f'testing/fixtures/wr1_{name}_replay.json')
            states = [u['completed'] for u in fixture['updates']]
            self.assertEqual(len(states), updates)
            self.assertEqual(sum(bool(s['death']) for s in states), rescues)
            self.assertEqual(len({(s['gx'], s['gy']) for s in states}), positions)
            self.assertGreater(replay['total_frames'] / replay['source_fps'], 58)
            stream = input_stream(fixture, replay, 'test')
            self.assertTrue(all(set(row) == {'up', 'down', 'left', 'right', 'slime_request'} for row in stream['inputs']))
            self.assertTrue(all(type(v) is bool for row in stream['inputs'] for v in row.values()))
            broken = copy.deepcopy(fixture)
            broken['updates'].pop(20)
            with self.assertRaises(ValueError):
                input_stream(broken, replay, 'test')


@unittest.skipUnless(os.environ.get('GODOT'), 'Set GODOT for actual-game long-route checks')
class LongRouteEngineTests(unittest.TestCase):
    def test_all_gameplay_updates_and_reset_mistakes_match(self):
        with tempfile.TemporaryDirectory(dir=ROOT / 'testing/output') as temp:
            for name in ('level3_long', 'level4_long'):
                result = run(name, os.environ['GODOT'], Path(temp))
                self.assertTrue(result['exact'], result)

    def test_removing_one_recorded_jump_fails_actual_gameplay(self):
        replay_path = ROOT / 'testing/fixtures/wr1_level3_long_replay.json'
        replay = read(replay_path)
        fixture = read(ROOT / 'testing/fixtures/wr1_level3_long_boundaries.json')
        stream = input_stream(fixture, replay, digest(replay_path))
        self.assertTrue(stream['inputs'][254]['up'])
        stream['inputs'][254]['up'] = False
        with tempfile.TemporaryDirectory(dir=ROOT / 'testing/output') as temp:
            directory = Path(temp)
            controls, trace = directory / 'inputs.json', directory / 'clone.jsonl'
            save(controls, stream)
            run_engine(os.environ['GODOT'], ['--headless', '--', '--original-rules', '--replay', str(replay_path),
                       '--logical-inputs', str(controls), '--state-trace', str(trace)], directory, 'negative', 60)
            clone = [json.loads(line) for line in trace.read_text().splitlines()]
            report = compare(fixture, clone, replay, digest(replay_path))
            failure = next(m for m in report['mismatches'] if m['state'])
            self.assertEqual(failure['tick'], 255)
            self.assertIn('gy', failure['state'])
            self.assertIn('up', failure['inputs'])


if __name__ == '__main__':
    unittest.main()
