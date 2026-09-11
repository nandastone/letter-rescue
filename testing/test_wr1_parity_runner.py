"""Verify the integrated report cannot turn corrupted state or pixels green."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from PIL import Image
from testing import test_wr1_boundaries

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from compare_wr1_boundaries import compare
from run_wr1_parity import summarize_comparison, compare_pixels, ROOT, SCENARIOS, PIXELS, validate_demo_evidence, read, pixel_pairs, digest


class ReportTests(unittest.TestCase):
    def test_default_suite_is_all_fifteen_original_demos(self):
        self.assertEqual(SCENARIOS, tuple(f'demo_level{i}' for i in
                         (4,1,10,12,14,15,2,5,8,11,9,3,6,13,7)))
        self.assertEqual(set(PIXELS), set(SCENARIOS))

    def test_missing_demo_ending_is_an_evidence_error(self):
        replay = read(ROOT/'testing/fixtures/wr1_demo_level15_replay.json')
        fixture = read(ROOT/'testing/fixtures/wr1_demo_level15_boundaries.json')
        validate_demo_evidence('demo_level15', replay, fixture)
        del fixture['demo_terminal']
        with self.assertRaisesRegex(ValueError, 'terminal native evidence'):
            validate_demo_evidence('demo_level15', replay, fixture)

    def test_corrupt_state_input_and_timing_are_independent(self):
        source = test_wr1_boundaries.BoundaryComparisonTests()
        source.setUp()
        for category in ('state', 'inputs', 'timing'):
            rows = copy.deepcopy(source.clone)
            if category == 'state':
                rows[40]['rng'] ^= 1
            elif category == 'inputs':
                rows[40]['held']['right'] = not rows[40]['held']['right']
            else:
                rows[40]['source_frame'] += 1
                rows[40]['replay_frame'] += 1
            report = summarize_comparison(compare(source.fixture, rows, source.replay, 'test'))
            for dimension in ('state', 'inputs', 'timing'):
                self.assertEqual(report[dimension]['count'], int(dimension == category))
            self.assertEqual(report[category]['first']['tick'], rows[40]['tick'])

    def test_single_pixel_corruption_produces_artifacts(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            (directory / 'pixels').mkdir()
            native = Image.new('RGB', (320, 200))
            native.save(directory / 'native.png')
            native.save(directory / 'pixels/clone.png')
            pairs = [{'native_file': 'native.png', 'clone_file': 'clone.png'}]
            with patch('run_wr1_parity.FIXTURES', directory):
                self.assertTrue(compare_pixels(pairs, directory)[0]['exact'])
                native.putpixel((17, 23), (255, 0, 0))
                native.save(directory / 'pixels/clone.png')
                row = compare_pixels(pairs, directory)[0]
                self.assertFalse(row['exact'])
                self.assertEqual(row['different_pixels'], 1)
                self.assertEqual(row['bbox'], (17, 23, 18, 24))
                self.assertTrue((directory / 'pixels/comparison_clone.png').is_file())

    def test_missing_engine_fails_instead_of_skipping(self):
        result = subprocess.run([sys.executable, str(ROOT / 'tools/run_wr1_parity.py'),
                                 '--godot', 'missing-godot-executable'], capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)
        self.assertIn('cannot be skipped', result.stderr)

    def test_supplemental_images_require_complete_matching_capture(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            Image.new('RGB', (320,200)).save(directory/'native.png')
            manifest = {'pairs':[{'native_counter':10,'clone_source_frame':9,
                         'native_file':'native.png','sha256':digest(directory/'native.png'),
                         'capture_file':'capture.json'}]}
            capture = {'complete':True,'source_sha256':'movie',
                       'samples':[{'replay_frame':10,'screenshot':'counter_000010.png'}]}
            for change in ({}, {'complete':False}, {'source_sha256':'another-movie'}, {'samples':[]}):
                (directory/'capture.json').write_text(json.dumps(dict(capture,**change)))
                manifest['pairs'][0]['capture_sha256'] = digest(directory/'capture.json')
                (directory/'wr1_demo_level6_pixels.json').write_text(json.dumps(manifest))
                with patch('run_wr1_parity.FIXTURES', directory):
                    if change:
                        with self.assertRaisesRegex(ValueError, 'Supplemental pixel'):
                            pixel_pairs('demo_level6',{'source_sha256':'movie'},Path('replay.json'))
                    else:
                        self.assertEqual(len(pixel_pairs('demo_level6',{'source_sha256':'movie'},Path('replay.json'))),1)
                        (directory/'capture.json').write_text('{}')
                        with self.assertRaisesRegex(ValueError, 'capture hash mismatch'):
                            pixel_pairs('demo_level6',{'source_sha256':'movie'},Path('replay.json'))


if __name__ == '__main__':
    unittest.main()
