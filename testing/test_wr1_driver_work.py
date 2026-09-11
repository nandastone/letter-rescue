"""Source-derived edge cases for MIDI logic and original instruction paths."""
import gzip
import hashlib
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from wr1_driver_work import DriverWork
from wr1_opl_reference import Opl


class DriverWorkTests(unittest.TestCase):
    def test_constructed_source_paths_and_voice_state(self):
        fixture = json.loads(gzip.decompress((ROOT/'testing/fixtures/wr1_driver_work.json.gz').read_bytes()))
        tables = json.loads((ROOT/'assets/audio/original/driver_tables.json').read_text())
        work = DriverWork(json.loads((ROOT/'assets/audio/original/driver_work.json').read_text()),len(tables['rhythm_registers']))
        cmf = (ROOT/fixture['constructed_music_file']).read_bytes()
        self.assertEqual(len(fixture['constructed_cases']),42)
        for case in fixture['constructed_cases']:
            opl = Opl(tables,cmf,case['initial_opl'])
            path = work.event(case['midi'],opl.state)
            digest = hashlib.sha256(json.dumps(path,separators=(',',':')).encode()).hexdigest()
            self.assertEqual(digest,case['work_sha256'],case['label'])
            self.assertEqual(opl.event(case['midi']),case['writes'],case['label'])
            self.assertEqual(opl.state,case['expected_opl'],case['label'])


if __name__=='__main__':unittest.main()
