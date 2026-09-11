"""Actual-window Clear Text checks; no display pixels are compared to DOSBox."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

from PIL import Image, ImageChops

ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless(os.environ.get('GODOT'), 'Set GODOT for graphical Clear Text checks')
class ClearTextTests(unittest.TestCase):
    def test_readable_display_preserves_original_raster(self):
        with tempfile.TemporaryDirectory(dir=ROOT/'testing/output') as temporary:
            output = Path(temporary)
            for mode in ('original', 'clear'):
                directory = output/mode
                directory.mkdir()
                result = subprocess.run([
                    os.environ['GODOT'], '--path', str(ROOT), '--quit-after', '900',
                    '--script', 'testing/test_wr1_clear_text.gd', '--',
                    '--original-rules', '--original-seed', '20716', '--mute-original-audio',
                    '--clear-output', str(directory),
                ] + (['--clear-text'] if mode == 'clear' else []),
                    capture_output=True, text=True, timeout=45,
                    creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
                self.assertEqual(result.returncode, 0, result.stdout+result.stderr)
                self.assertNotIn('ERROR:', result.stdout+result.stderr)
                self.assertIn('word list PASS', result.stdout)
            original = Image.open(output/'original/reference.png').convert('RGB')
            reference = Image.open(output/'clear/reference.png').convert('RGB')
            self.assertEqual(reference.size, (320, 200))
            self.assertIsNone(ImageChops.difference(original, reference).getbbox())
            for name in ('cards', 'bonus', 'recap'):
                self.assertIsNone(ImageChops.difference(
                    Image.open(output/f'original/{name}_reference.png').convert('RGB'),
                    Image.open(output/f'clear/{name}_reference.png').convert('RGB')).getbbox(),
                    name+' changed original reference pixels')
            display = Image.open(output/'clear/reading.png').convert('RGB')
            self.assertGreater(display.width, 320)
            # Re-enlarging its downsampled text must lose detail: this detects
            # accidentally drawing a smooth font into the old 320x200 buffer.
            enlarged = display.resize((320, 200), Image.Resampling.NEAREST).resize(display.size, Image.Resampling.NEAREST)
            region = tuple(int(v*display.width/320) for v in (60, 1, 127, 17))
            self.assertIsNotNone(ImageChops.difference(display, enlarged).crop(region).getbbox())
            with Image.open(output/'clear/words_resized.png') as resized:
                self.assertEqual(resized.size, (960, 600))
            with Image.open(output/'clear/descenders.png') as source:
                descenders = source.convert('RGB')
            scale = descenders.width/320
            def ink(rect, color):
                crop = descenders.crop(tuple(round(value*scale) for value in rect))
                return sum(pixel == color for pixel in crop.getdata())
            reference_ink = ink((59, 40, 128, 80), (255, 255, 255))
            self.assertGreater(reference_ink, 0)
            self.assertEqual(ink((60, 4, 127, 15), (255, 255, 255)), reference_ink,
                             'HUD bevel clips descenders compared with an unconstrained Label')
            bonus_reference_ink = ink((128, 40, 192, 80), (255, 255, 255))
            self.assertEqual(ink((128, 185, 192, 199), (255, 255, 85)), bonus_reference_ink,
                             'Bonus word loses descenders')


if __name__ == '__main__':
    unittest.main()
