"""Native CMF sequencing evidence, independent of Godot and capture timing."""
import hashlib
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from wr1_music_reference import Music


class MusicTests(unittest.TestCase):
    def test_native_sequence_from_one_initial_state(self):
        fixture = json.loads((ROOT/'testing/fixtures/wr1_music_ticks.json').read_text())
        data = (ROOT/fixture['music_file']).read_bytes()
        self.assertEqual(hashlib.sha256(data).hexdigest(),fixture['music_sha256'])
        model = Music(data,fixture['initial'])
        events = []
        for tick in fixture['ticks']:
            events += model.tick()
            self.assertEqual(model.state,tick['state'],tick['tick'])
        self.assertEqual(len(fixture['ticks']),487)
        self.assertEqual(len(events),71)

    def test_another_original_song_does_not_match_the_recording(self):
        fixture = json.loads((ROOT/'testing/fixtures/wr1_music_ticks.json').read_text())
        for number in [4,6]:
            model = Music((ROOT/f'assets/audio/original/wr1_{number}.cmf').read_bytes(),fixture['initial'])
            differences = 0
            for tick in fixture['ticks']:
                model.tick()
                differences += model.state != tick['state']
            self.assertGreater(differences,0)


if __name__ == '__main__':
    unittest.main()
