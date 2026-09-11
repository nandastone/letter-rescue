"""Original attract controls/checkpoint packaging and real scene transitions."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import unittest
from tools.build_wr1_attract_assets import FIELDS

ROOT = Path(__file__).resolve().parents[1]

class AttractTests(unittest.TestCase):
    def test_runtime_demos_contain_only_controls_and_initial_state(self):
        manifest = json.loads((ROOT/'data/wr1/demos/manifest.json').read_text())
        for level in range(1, 16):
            with self.subTest(level=level):
                source = ROOT/f'testing/fixtures/wr1_demo_level{level}_replay.json'
                target = ROOT/f'data/wr1/demos/level{level}.json'
                data = json.loads(target.read_text())
                original = json.loads(source.read_text())
                self.assertEqual(set(data), FIELDS)
                self.assertEqual(data, {k:v for k,v in original.items() if k in FIELDS})
                self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(),manifest['demos'][str(level)]['source_fixture_sha256'])
                self.assertEqual(hashlib.sha256(target.read_bytes()).hexdigest(),manifest['demos'][str(level)]['runtime_sha256'])

    @unittest.skipUnless(os.environ.get('GODOT'), 'Set GODOT for actual attract playback')
    def test_natural_end_all_starts_and_session_restoration(self):
        self.run_attract(False)

    @unittest.skipUnless(os.environ.get('GODOT'), 'Set GODOT for actual attract playback')
    def test_clear_text_session_restoration(self):
        self.run_attract(True)

    def run_attract(self, clear_text):
        result = subprocess.run([os.environ['GODOT'],'--path',str(ROOT),
            '--fixed-fps','70','--quit-after','15000','--script','testing/test_wr1_attract.gd',
            '--','--original-rules','--original-seed','20716','--attract-presented','--mute-original-audio'] + (['--clear-text'] if clear_text else []),
            capture_output=True,text=True,timeout=240,
            creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        self.assertNotIn('ERROR:',result.stdout+result.stderr)
        self.assertIn('live-session restoration PASS',result.stdout)

if __name__ == '__main__': unittest.main()
