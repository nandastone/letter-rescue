import copy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from compare_wr1_boundaries import compare


class BoundaryComparisonTests(unittest.TestCase):
    def setUp(self):
        self.fixture = json.loads((ROOT/'testing/fixtures/wr1_controlled_boundaries.json').read_text())
        self.replay = json.loads((ROOT/'testing/fixtures/wr1_controlled_quantized_replay.json').read_text())
        self.clone = []
        for update in self.fixture['updates']:
            row = dict(update['completed'])
            source = update['begin']['launch_call'] - 1
            row.update(tick=update['tick'],source_frame=source,
                       replay_frame=source-self.replay['source_start_frame'],
                       replay_sha256='test',source_sha256=self.replay['source_sha256'],
                       held={key: bool(update['begin'][key]) for key in ('up','down','left','right')})
            self.clone.append(row)

    def test_native_fixture_is_internally_consistent(self):
        report = compare(self.fixture,self.clone,self.replay,'test')
        self.assertEqual(report['completed_state_exact'],64)
        self.assertEqual(report['validation_exact'],50)

    def test_frame_input_and_completed_state_errors_each_fail(self):
        for field in ('frame','input','state'):
            rows = copy.deepcopy(self.clone)
            row = rows[18]  # Walking update 19, after calibration.
            if field == 'frame':
                row['source_frame'] -= 1
                row['replay_frame'] -= 1
            elif field == 'input':
                row['held']['right'] = False
            else:
                row['background_frame'] = (row['background_frame']+1)%4
            report = compare(self.fixture,rows,self.replay,'test')
            self.assertFalse(report['all_validation_updates_exact'],field)
            self.assertEqual(report['validation_exact'],49)

    def test_missing_updates_fail_without_discarding_earlier_differences(self):
        rows = copy.deepcopy(self.clone[:-1])
        rows[18]['rng'] ^= 1
        report = compare(self.fixture, rows, self.replay, 'test')
        self.assertFalse(report['all_validation_updates_exact'])
        self.assertEqual(report['missing_clone_updates'], [64])
        self.assertEqual(report['compared'], 63)
        self.assertEqual(report['expected_updates'], 64)
        self.assertEqual(report['completed_state_exact'], 62)
        self.assertEqual(report['validation_updates'], 50)
        self.assertIn('rng', report['mismatches'][0]['state'])

    def test_duplicate_and_stale_data_are_rejected(self):
        with self.assertRaises(ValueError):
            compare(self.fixture,self.clone+[self.clone[-1]],self.replay,'test')
        with self.assertRaises(ValueError):
            compare(self.fixture,self.clone,self.replay,'wrong digest')

    def test_actor_and_rng_corruption_fail_even_with_matching_player(self):
        for field in ('rng','gruzzles'):
            rows = copy.deepcopy(self.clone)
            if field == 'rng':
                rows[40]['rng'] ^= 1
            else:
                rows[40]['gruzzles'][0]['move_timer'] += 1
            report = compare(self.fixture,rows,self.replay,'test')
            self.assertFalse(report['all_validation_updates_exact'])
            self.assertIn(field,report['mismatches'][0]['state'])

    def test_observed_slime_request_corruption_is_an_input_failure(self):
        rows = copy.deepcopy(self.clone)
        fixture = copy.deepcopy(self.fixture)
        fixture['updates'][18]['begin']['slime_request'] = 0
        rows[18]['held']['slime_request'] = True
        report = compare(fixture, rows, self.replay, 'test')
        self.assertFalse(report['all_validation_updates_exact'])
        self.assertIn('slime_request', report['mismatches'][0]['inputs'])
        self.assertEqual(report['completed_state_exact'], 64)


if __name__ == '__main__':
    unittest.main()
