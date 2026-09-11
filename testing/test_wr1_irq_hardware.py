"""Native timer bodies: speaker/game state, BIOS work and hardware completion."""
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
from wr1_opl_reference import Opl
from wr1_irq_work import IrqWork


class IrqHardwareTests(unittest.TestCase):
    assert_hardware = hardware_tests.HardwareTests.assert_hardware

    def test_native_short_timer_bodies(self):
        self.check_recording('wr1_irq_hardware',561)

    def test_native_full_song_timer_bodies_and_pending_interrupts(self):
        self.check_recording('wr1_irq_hardware_loop',9641)

    def check_recording(self,name,count):
        f=json.loads(gzip.decompress((ROOT/f'testing/fixtures/{name}.json.gz').read_bytes()))
        tables=json.loads((ROOT/'assets/audio/original/driver_tables.json').read_text())
        catalogue=json.loads((ROOT/'assets/audio/original/driver_work.json').read_text())
        cmf=(ROOT/f['music_file']).read_bytes()
        music=Music(cmf,f['initial_music'])
        opl=Opl(tables,cmf,f['initial_opl'])
        work=IrqWork(catalogue,len(tables['rhythm_registers']),f['dispatcher_use_dx'],f['external_timer'])
        names={int(k):v for k,v in f['event_names'].items()}
        self.assertEqual(len(f['cases']),count)
        for i,case in enumerate(f['cases']):
            path,writes,state=work.body(music,opl,case['initial_game'])
            model=Hardware(case['initial'],names)
            self.assertEqual(round(model.observed_time()*27000),case['start_cycle'],i)
            run_driver(model,path)
            self.assertEqual(round(model.observed_time()*27000),case['end_cycle'],i)
            self.assert_hardware(model.snapshot(),case['expected'],str(i))
            self.assertEqual(state,case['expected_game'],i)
            self.assertEqual(writes,case['writes'],i)
            self.assertEqual(music.state,case['music'],i)
            self.assertEqual(opl.state,case['opl'],i)
