"""Movement paths derive from source and initial state, checked against DOSBox."""
import copy
import gzip
import json
from pathlib import Path
import sys
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from testing import test_wr1_hardware as hardware_tests
from wr1_movement_work import MovementWork
from wr1_hardware_reference import Hardware,run_driver


class MovementWorkTests(unittest.TestCase):
    assert_hardware=hardware_tests.HardwareTests.assert_hardware

    def test_native_movement(self):
        self.check_fixture('wr1_movement_work',65)

    def test_native_walk_jump(self):
        self.check_fixture('wr1_movement_walk_jump',71)

    def test_native_held_jump(self):
        self.check_fixture('wr1_movement_held_jump',41)

    def check_fixture(self,name,count):
        f=json.loads(gzip.decompress((ROOT/f'testing/fixtures/{name}.json.gz').read_bytes()))
        work=MovementWork(json.loads((ROOT/'assets/audio/original/driver_work.json').read_text()))
        names={int(k):v for k,v in f['event_names'].items()}
        self.assertEqual(len(f['cases']),count)
        for c in f['cases']:
            with self.subTest(call=c['launch_call']):
                before=copy.deepcopy(c['movement'])
                path,state=work.step(c['movement'],c['attributes'])
                self.assertEqual(state,c['expected_movement'])
                h=Hardware(c['initial'],names)
                run_driver(h,path)
                self.assertEqual(round(h.observed_time()*27000),c['end_cycle'])
                self.assert_hardware(h.snapshot(),c['expected'],'movement end')
                self.assertEqual(c['movement'],before,'Mutation of initial movement checkpoint')
