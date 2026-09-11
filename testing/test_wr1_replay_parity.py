"""Actual replay regression: native snapshots and six instruction-boundary probes."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from compare_wr1_traces import compare as compare_frames
from compare_wr1_boundaries import compare as compare_boundaries
GODOT = os.environ.get('GODOT') or shutil.which('godot')


@unittest.skipUnless(GODOT, 'Set GODOT to run engine integration tests')
class NativeReplayParityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.path = ROOT/'testing/fixtures/wr1_controlled_quantized_replay.json'
        cls.replay = json.loads(cls.path.read_text())
        cls.digest = hashlib.sha256(cls.path.read_bytes()).hexdigest()
        cls.trace_path = ROOT/'testing/output/replay_tests/native_parity.jsonl'
        cls.trace_path.parent.mkdir(parents=True,exist_ok=True)
        result = subprocess.run([GODOT,'--headless','--fixed-fps','70','--path',str(ROOT),'--',
            '--original-rules','--mystery-word','cup','--replay',str(cls.path),
            '--state-trace',str(cls.trace_path)],capture_output=True,text=True,timeout=30,
            creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        if result.returncode or 'SCRIPT ERROR:' in result.stderr:
            raise AssertionError(result.stdout+result.stderr)
        errors = [line for line in result.stderr.splitlines() if line.startswith('ERROR:')]
        # Known accelerated audio shutdown warning, also present before this pass.
        if any(line != 'ERROR: 1 resources still in use at exit (run with --verbose for details).' for line in errors):
            raise AssertionError(result.stderr)
        cls.clone = [json.loads(line) for line in cls.trace_path.read_text().splitlines()]

    def test_same_frame_movement_and_interaction_match_native(self):
        native = json.loads((ROOT/'testing/fixtures/wr1_controlled_native.json').read_text())
        report = compare_frames(native,self.clone,self.replay,self.digest)
        self.assertEqual(report['compared'],62)
        for name in ('position','motion','interaction'):
            self.assertEqual(report['groups'][name]['mismatches'],[],name)

    def test_completed_update_state_and_entry_inputs_match(self):
        fixture = json.loads((ROOT/'testing/fixtures/wr1_controlled_boundaries.json').read_text())
        report = compare_boundaries(fixture,self.clone,self.replay,self.digest)
        self.assertEqual(report['completed_state_exact'],64)
        self.assertEqual(report['validation_updates'],50)
        self.assertTrue(report['all_validation_updates_exact'],report['mismatches'])
        # The first native update waits for startup Enter; it is explicitly outside
        # this ordinary-gameplay validation, not silently counted as a timing match.
        self.assertEqual([r['tick'] for r in report['mismatches']],[1])


if __name__ == '__main__':
    unittest.main()
