"""Independently predicted OPL busy waits and final hardware state."""
import gzip
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from wr1_hardware_reference import Hardware, run_driver
from wr1_driver_work import DriverWork
from wr1_opl_reference import Opl


class HardwareTests(unittest.TestCase):
    def setUp(self):
        self.fixture = json.loads(gzip.decompress((ROOT/'testing/fixtures/wr1_opl_hardware.json.gz').read_bytes()))
        self.names = {int(k):v for k,v in self.fixture['event_names'].items()}

    def assert_hardware(self,actual,expected,path=''):
        if isinstance(actual,dict):
            self.assertEqual(actual.keys(),expected.keys(),path)
            for key in actual:
                self.assert_hardware(actual[key],expected[key],path+'.'+key)
        elif isinstance(actual,list):
            self.assertEqual(len(actual),len(expected),path)
            for i,(a,b) in enumerate(zip(actual,expected)):
                self.assert_hardware(a,b,f'{path}[{i}]')
        elif isinstance(actual,float):
            self.assertAlmostEqual(actual,expected,delta=1e-8,msg=path)
        else:
            self.assertEqual(actual,expected,path)

    def test_native_wait_cost_and_all_hardware_state(self):
        self.check_recording(self.fixture,205,0)

    def test_complete_song_waits_and_extra_timer_poll(self):
        fixture = json.loads(gzip.decompress((ROOT/'testing/fixtures/wr1_opl_hardware_loop.json.gz').read_bytes()))
        self.check_recording(fixture,6498,1)

    def test_whole_midi_call_cost_without_observed_wait_durations(self):
        fixture = json.loads(gzip.decompress((ROOT/'testing/fixtures/wr1_driver_hardware.json.gz').read_bytes()))
        names = {int(k):v for k,v in fixture['event_names'].items()}
        tables = json.loads((ROOT/'assets/audio/original/driver_tables.json').read_text())
        work = DriverWork(json.loads((ROOT/'assets/audio/original/driver_work.json').read_text()),len(tables['rhythm_registers']))
        opl = Opl(tables,(ROOT/fixture['music_file']).read_bytes(),fixture['initial_opl'])
        self.assertEqual(len(fixture['cases']),90)
        for index,case in enumerate(fixture['cases']):
            model = Hardware(case['initial'],names)
            path = work.event(case['midi'],opl.state)
            self.assertEqual([list(pair) for pair in path],case['work'],index)
            self.assertEqual(opl.event(case['midi']),case['writes'],index)
            waits = run_driver(model,path)
            self.assertEqual(len(waits),len(case['writes']))
            self.assertEqual(round(model.observed_time()*27000),case['end_cycle'],index)
            self.assert_hardware(model.snapshot(),case['expected'],str(index))

    def check_recording(self,fixture,count,polls):
        self.assertEqual(len(fixture['cases']),count)
        names = {int(k):v for k,v in fixture['event_names'].items()}
        extra = 0
        for index,case in enumerate(fixture['cases']):
            model = Hardware(case['initial'],names)
            self.assertEqual(model.opl(),case['cycles'],index)
            self.assert_hardware(model.snapshot(),case['expected'],str(index))
            extra += model.extra_polls
        self.assertEqual(extra,polls)

    def test_wrong_io_delay_does_not_match_native_timing(self):
        class WrongReadDelay(Hardware):
            def io_delay(self,cycles):
                super().io_delay(cycles+1 if cycles==26 else cycles)
        case = self.fixture['cases'][0]
        model = WrongReadDelay(case['initial'],self.names)
        self.assertNotEqual(model.opl(),case['cycles'])


if __name__=='__main__':
    unittest.main()
