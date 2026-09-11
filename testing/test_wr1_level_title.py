"""Compare the recovered title renderer with an untouched native screenshot."""
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from run_wr1_parity import ROOT, run_engine


@unittest.skipUnless(os.environ.get('GODOT'), 'Set GODOT to run the title renderer')
class LevelTitleTests(unittest.TestCase):
    def test_native_pixels_and_live_lifecycle(self):
        fixture = ROOT / 'testing/fixtures/wr1_level_title.json'
        evidence = json.loads(fixture.read_text())
        native = fixture.parent / evidence['image']
        self.assertEqual(hashlib.sha256(native.read_bytes()).hexdigest(), evidence['image_sha256'])
        with tempfile.TemporaryDirectory(dir=ROOT / 'testing/output') as temporary:
            output = Path(temporary)
            run_engine(os.environ['GODOT'], ['--headless', '--quit-after', '700', '--script',
                       'testing/test_wr1_level_title.gd', '--', '--legacy', str(output)],
                       output, 'titles', 60)
            self.assertIn('lifecycle PASS', (output / 'titles.log').read_text())
            actual = Image.open(output / 'title-02.png').convert('RGB')
            expected = Image.open(native).convert('RGB')
            self.assertEqual(actual.size, expected.size)
            self.assertEqual(actual.tobytes(), expected.tobytes())
            self.assertEqual(len(list(output.glob('title-*.png'))), 15)


if __name__ == '__main__':
    unittest.main()
