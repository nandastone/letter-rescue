"""Same-input recap must return on the native frontend frame."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
GODOT = os.environ.get('GODOT') or shutil.which('godot')


@unittest.skipUnless(GODOT, 'Set GODOT to run timing integration')
class RecapTimingTests(unittest.TestCase):
    def test_first_resumed_update_enters_on_native_frame(self):
        # Keep the complete causal input prefix, stop just after native return.
        replay = json.loads((ROOT/'testing/fixtures/wr1_recap_replay.json').read_text())
        directory = ROOT/'testing/output/recap_timing'
        directory.mkdir(parents=True, exist_ok=True)
        replay['total_frames'] = 5970 - replay['source_start_frame']
        replay['events'] = [e for e in replay['events'] if e['frame'] < replay['total_frames']]
        path, output = directory/'input.json', directory/'clone.jsonl'
        path.write_text(json.dumps(replay)+'\n')
        run = subprocess.run([GODOT,'--headless','--fixed-fps','70','--path',str(ROOT),
            '--','--legacy','--mystery-word','cup','--replay',str(path),
            '--state-trace',str(output)],capture_output=True,text=True,timeout=30,
            creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        self.assertEqual(run.returncode,0,run.stdout+run.stderr)
        self.assertNotIn('SCRIPT ERROR:',run.stderr)
        rows = [json.loads(line) for line in output.read_text().splitlines()]
        resumed = next(row for row in rows if row['tick'] == 762)
        self.assertEqual(resumed['rng'],520533843)
        self.assertEqual(resumed['source_frame'],5951)
