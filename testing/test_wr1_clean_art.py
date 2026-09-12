"""Pixel-level regressions for artwork underneath the modern frontend text."""
import os
from pathlib import Path
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless(os.environ.get('GODOT'), 'Set GODOT for clean artwork checks')
class CleanArtworkTests(unittest.TestCase):
    def test_text_free_backgrounds(self):
        result = subprocess.run([
            os.environ['GODOT'], '--headless', '--path', str(ROOT),
            '--script', 'testing/test_wr1_clean_art.gd', '--quit-after', '2',
        ], capture_output=True, text=True, timeout=20,
            creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertNotIn('ERROR:', result.stdout + result.stderr)
        self.assertIn('legacy source PASS', result.stdout)


if __name__ == '__main__':
    unittest.main()
