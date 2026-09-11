"""The generated native masks are independent evidence for extracted assets."""
import sys
import unittest
from pathlib import Path
from PIL import Image
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from json_evidence import read
from native_sprite_image import decode

ROOT=Path(__file__).resolve().parents[1]

class NativeSpriteTests(unittest.TestCase):
    def test_all_nine_slime_images_match_loaded_native_and_or_bytes(self):
        evidence=read(ROOT/'testing/fixtures/wr1_slime_assets.json')
        for index in range(9):
            expected=decode(evidence['images'][f'body_{index}'],evidence['images'][f'mask_{index}'])
            actual=Image.open(ROOT/f'assets/sprites/wr1_slime_{index}.png').convert('RGBA')
            self.assertEqual(actual.tobytes(),expected.tobytes(),f'Slime frame {index}')

if __name__=='__main__':
    unittest.main()
