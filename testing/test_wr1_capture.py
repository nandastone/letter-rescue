"""Real rendered capture must keep its images and state while minimized."""
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest

from PIL import Image

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from run_wr1_parity import ROOT, run_engine


@unittest.skipUnless(os.environ.get('GODOT'), 'Set GODOT for real viewport capture')
class CaptureWindowTests(unittest.TestCase):
    def test_minimized_window_preserves_requested_frames_and_state(self):
        with tempfile.TemporaryDirectory(dir=ROOT/'testing/output') as temporary:
            captures = []
            traces = []
            for mode in ('visible','minimized','start_minimized'):
                directory = Path(temporary)/mode
                directory.mkdir()
                args = ['--script','testing/capture_wr1_window_probe.gd']
                if mode == 'start_minimized':
                    args += ['--minimized']
                args += ['--','--original-rules','--replay','testing/fixtures/wr1_demo_level11_replay.json',
                         '--state-trace',str(directory/'state.jsonl'), '--capture-initial',
                         '--capture-through-replay-end','--capture-source-frames','639,999,1009',
                         '--capture-directory',str(directory/'pixels')]
                if mode == 'minimized':
                    args += ['--probe-minimize']
                run_engine(os.environ['GODOT'],args,directory,'game',60)
                expected = {'initial.png','source_000639.png','source_000999.png','source_001009.png'}
                self.assertEqual({p.name for p in (directory/'pixels').glob('*.png')},expected)
                captures.append({name:Image.open(directory/'pixels'/name).convert('RGB').tobytes() for name in expected})
                traces.append([json.loads(line) for line in (directory/'state.jsonl').read_text().splitlines()])
            for pictures, trace in zip(captures[1:],traces[1:]):
                self.assertEqual(pictures,captures[0])
                self.assertEqual(trace,traces[0])


if __name__ == '__main__':
    unittest.main()
