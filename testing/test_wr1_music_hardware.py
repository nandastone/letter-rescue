"""Complete music service from live CMF/voice state and initial hardware phase."""
import gzip
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from testing import test_wr1_hardware as hardware_tests
from wr1_hardware_reference import Hardware, run_driver
from wr1_music_reference import Music
from wr1_music_work import MusicWork
from wr1_opl_reference import Opl


class MusicHardwareTests(unittest.TestCase):
    assert_hardware = hardware_tests.HardwareTests.assert_hardware

    def test_complete_interrupt_with_continuous_music_and_voice_state(self):
        self.check_recording('wr1_music_hardware',561,561)

    def test_full_song_before_repeat_including_iret_millisecond_boundary(self):
        self.check_recording('wr1_music_hardware_loop',9641,9281)

    def test_full_song_through_repeat_and_following_notes(self):
        self.check_recording('wr1_music_hardware_repeat',9641,9641)

    def test_native_repeat_memory_intermediate_hardware_state(self):
        f = json.loads(gzip.decompress((ROOT/'testing/fixtures/wr1_music_hardware_repeat.json.gz').read_bytes()))
        self.assertEqual(len(f['repeat_memory_cases']),12)
        names = {int(k):v for k,v in f['event_names'].items()}
        for case in f['repeat_memory_cases']:
            hardware = Hardware(case['initial'],names)
            run_driver(hardware,[(f"rep:{case['count']}",case['ip'])])
            self.assertEqual(round(hardware.observed_time()*27000),case['end_cycle'])
            self.assert_hardware(hardware.snapshot(),case['expected'])

    def check_recording(self,name,total,count):
        f = json.loads(gzip.decompress((ROOT/f'testing/fixtures/{name}.json.gz').read_bytes()))
        tables = json.loads((ROOT/'assets/audio/original/driver_tables.json').read_text())
        catalogue = json.loads((ROOT/'assets/audio/original/driver_work.json').read_text())
        cmf = (ROOT/f['music_file']).read_bytes()
        music = Music(cmf,f['initial_music'])
        opl = Opl(tables,cmf,f['initial_opl'])
        work = MusicWork(catalogue,len(tables['rhythm_registers']),f['dispatcher_use_dx'],f.get('external_timer'))
        names = {int(k):v for k,v in f['event_names'].items()}
        self.assertEqual(len(f['cases']),total)
        for i,case in enumerate(f['cases'][:count]):
            path,writes = work.tick(music,opl)
            hardware = Hardware(case['initial'],names)
            self.assertEqual(round(hardware.observed_time()*27000),case['start_cycle'],i)
            run_driver(hardware,path)
            self.assertEqual(round(hardware.observed_time()*27000),case['end_cycle'],i)
            self.assert_hardware(hardware.snapshot(),case['expected'],str(i))
            self.assertEqual(writes,case['writes'],i)
            self.assertEqual(music.state,case['music'],i)
            self.assertEqual(opl.state,case['opl'],i)
