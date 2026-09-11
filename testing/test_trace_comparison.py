import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from compare_wr1_traces import GROUPS, compare


class TraceComparisonTests(unittest.TestCase):
    def setUp(self):
        fields = {key: 0 for group in GROUPS.values() for key in group}
        self.replay = {'source_sha256': 'fixture', 'source_start_frame': 10, 'total_frames': 5}
        self.native = {'source_sha256': 'fixture', 'complete': True, 'start_frame': 10, 'end_frame': 12,
                       'samples': [dict(fields, replay_frame=i) for i in range(10, 13)]}
        self.clone = [dict(fields, source_sha256='fixture', replay_sha256='configuration', source_frame=10, replay_frame=0, tick=1)]

    def test_completed_counter_is_input_frame_plus_one(self):
        self.native['samples'][0]['world_x'] = 999
        report = compare(self.native, self.clone, self.replay, 'configuration')
        self.assertTrue(report['all_compared_samples_exact'])
        self.assertEqual(report['exact'], 1)

    def test_adjacent_match_never_counts_as_exact(self):
        self.native['samples'][1]['world_x'] = 8
        report = compare(self.native, self.clone, self.replay, 'configuration')
        self.assertFalse(report['all_compared_samples_exact'])
        mismatch = report['groups']['position']['mismatches'][0]
        self.assertEqual(mismatch['native_completed_frames'], 11)
        self.assertEqual(mismatch['adjacent_match_offsets'], [-1, 1])

    def test_reject_incomplete_missing_duplicate_or_wrong_source(self):
        for mutate in (
            lambda n: n.update(complete=False),
            lambda n: n['samples'].pop(),
            lambda n: n['samples'].append(n['samples'][0]),
            lambda n: n.update(source_sha256='wrong'),
        ):
            native = copy.deepcopy(self.native)
            mutate(native)
            with self.assertRaises(ValueError):
                compare(native, self.clone, self.replay, 'configuration')
        self.clone[0]['source_sha256'] = 'wrong'
        with self.assertRaises(ValueError):
            compare(self.native, self.clone, self.replay, 'configuration')

    def test_missing_field_is_not_an_agreement(self):
        self.native['samples'][1].pop('world_x')
        report = compare(self.native, self.clone, self.replay, 'configuration')
        self.assertEqual(report['exact'], 0)

    def test_stale_trace_after_replay_edit_is_rejected(self):
        with self.assertRaises(ValueError):
            compare(self.native, self.clone, self.replay, 'changed configuration')


if __name__ == '__main__':
    unittest.main()

