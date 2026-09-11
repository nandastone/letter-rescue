"""Exercise original frontend and compare recovered pages to immutable DOSBox PNGs."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from PIL import Image, ImageChops

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT/'testing/fixtures/wr1_frontend'

class FrontendTests(unittest.TestCase):
    @unittest.skipUnless(os.environ.get('GODOT'), 'Set GODOT for real frontend tests')
    def test_original_frontend(self):
        self.run_frontend(False)

    @unittest.skipUnless(os.environ.get('GODOT'), 'Set GODOT for real frontend tests')
    def test_visible_frontend_compositing(self):
        self.run_frontend(True)

    def run_frontend(self, presented):
        with tempfile.TemporaryDirectory(dir=ROOT/'testing/output') as temporary:
            result = subprocess.run([os.environ['GODOT']]+([] if presented else ['--headless'])+['--path',str(ROOT),
				'--quit-after','1800',
                '--script','testing/test_wr1_frontend.gd','--','--original-rules',
                '--original-seed','20716','--skip-intro','--frontend-output',temporary]+(['--frontend-presented','--mute-original-audio'] if presented else []),
                capture_output=True,text=True,timeout=45,
                creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
            self.assertNotIn('ERROR:',result.stdout+result.stderr)
            self.assertIn('ending PASS',result.stdout)
            metadata=json.loads((FIXTURES/'manifest.json').read_text())
            self.assertTrue(metadata['capture_complete'])
            for case in metadata['cases']:
                with self.subTest(page=case['name']):
                    native=FIXTURES/(case['name']+'.png')
                    self.assertEqual(hashlib.sha256(native.read_bytes()).hexdigest(),case['sha256'])
                    reference=Image.open(native).convert('RGB')
                    clone=Image.open(Path(temporary)/native.name).convert('RGB')
                    if 'crop' in case:
                        reference=reference.crop(case['crop'])
                        clone=clone.crop(case['crop'])
                    difference=ImageChops.difference(reference,clone)
                    self.assertIsNone(difference.getbbox(),case['name']+' differs from native rendering')
            if presented:
                difference=ImageChops.difference(Image.open(FIXTURES/'menu.png').convert('RGB'),Image.open(Path(temporary)/'menu_presented.png').convert('RGB'))
                self.assertIsNone(difference.getbbox(),'Actual viewport failed to present the original menu')

if __name__=='__main__': unittest.main()
