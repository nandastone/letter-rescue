"""Native end-to-end CMF -> MIDI -> OPL verification from one initial state."""
import copy
import gzip
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from wr1_music_reference import Music
from wr1_opl_reference import Opl
from prepare_wr1_opl import prepare


class OplTests(unittest.TestCase):
    def setUp(self):
        self.fixture = json.loads((ROOT/'testing/fixtures/wr1_opl_ticks.json').read_text())
        self.data = (ROOT/self.fixture['music_file']).read_bytes()
        self.tables = json.loads((ROOT/'assets/audio/original/driver_tables.json').read_text())

    def test_native_registers_and_state_from_one_initial_checkpoint(self):
        self.check_sequence(self.fixture,self.data,(561,90,205))

    def test_native_startup_percussion_and_instrument_setup(self):
        f = json.loads((ROOT/'testing/fixtures/wr1_opl_startup_ticks.json').read_text())
        self.check_sequence(f,(ROOT/f['music_file']).read_bytes(),(363,69,200))

    def test_native_complete_song_and_loop(self):
        f = json.loads(gzip.decompress((ROOT/'testing/fixtures/wr1_opl_loop_ticks.json.gz').read_bytes()))
        self.check_sequence(f,(ROOT/f['music_file']).read_bytes(),(9641,2665,6498))

    def check_sequence(self,f,data,counts):
        self.assertEqual(hashlib.sha256(data).hexdigest(),f['music_sha256'])
        music,opl = Music(data,f['initial']),Opl(self.tables,data,f['initial_opl'])
        count = events_count = 0
        for tick in f['ticks']:
            events = music.tick()
            self.assertEqual(events,tick['events'],tick['tick'])
            writes = [write for event in events for write in opl.event(event)]
            if music.restarted:
                writes += opl.restart()
            self.assertEqual(writes,tick['writes'],tick['tick'])
            self.assertEqual(music.state,tick['state'],tick['tick'])
            self.assertEqual(opl.state,tick['opl_state'],tick['tick'])
            count += len(writes)
            events_count += len(events)
        self.assertEqual((len(f['ticks']),events_count,count),counts)

    def test_incorrect_tuning_is_detected_by_native_register_evidence(self):
        self.tables['frequencies'] = [n+1 for n in self.tables['frequencies']]
        f = self.fixture
        music,opl = Music(self.data,f['initial']),Opl(self.tables,self.data,f['initial_opl'])
        mismatches = 0
        for tick in f['ticks']:
            writes = [w for e in music.tick() for w in opl.event(e)]
            mismatches += writes!=tick['writes']
        self.assertGreater(mismatches,0)

    def test_missing_opl_return_is_rejected_by_fixture_preparation(self):
        f = self.fixture
        music = {**copy.deepcopy(f['initial']),'opl_state':f['initial_opl']}
        rows = [dict(event='frontend',call=561,pic_ms=1,music_driver=music),
                dict(event='irq',ip=0x2d8,launch_call=561,pic_ms=2,cycles_max=27000,cycles_auto=False,decoder='DynX86'),
                dict(event='driver_event',ip=0x58f1,ax=0x90,bx=0x4060,pic_ms=2.1),
                dict(event='opl',ip=0x579e,ax=0x1234,pic_ms=3),
                dict(event='driver_event',ip=0x599f)]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            capture,trace = root/'capture.json',root/'trace.jsonl'
            trace.write_text('\n'.join(json.dumps(r) for r in rows))
            capture.write_text(json.dumps({**{k:f[k] for k in ('source_sha256','exe_sha256','core_sha256')},
                                          'complete':True,'instruction_trace_sha256':hashlib.sha256(trace.read_bytes()).hexdigest()}))
            with self.assertRaisesRegex(ValueError,'Missing MIDI entry or OPL return'):
                prepare(capture,trace,ROOT/f['music_file'])


if __name__=='__main__':
    unittest.main()
