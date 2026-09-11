"""Native keyboard work, controller consumption, state and completion timing."""
import copy
import gzip
import json
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from testing import test_wr1_hardware as hardware_tests
from wr1_hardware_reference import Hardware,run_driver
from wr1_keyboard_work import KeyboardWork


class KeyboardTests(unittest.TestCase):
    assert_hardware=hardware_tests.HardwareTests.assert_hardware

    @classmethod
    def setUpClass(cls):
        cls.fixture=json.loads(gzip.decompress((ROOT/'testing/fixtures/wr1_keyboard_hardware.json.gz').read_bytes()))
        cls.catalogue=json.loads((ROOT/'assets/audio/original/driver_work.json').read_text())

    def test_native_keyboard_interrupts(self):
        f=self.fixture
        names={int(k):v for k,v in f['event_names'].items()}
        work=KeyboardWork(self.catalogue)
        self.assertEqual(len(f['cases']),24)
        for i,c in enumerate(f['cases']):
            with self.subTest(case=i):
                model=Hardware(c['initial'],names)
                path,state=work.body(c['initial_game'],c['initial']['keyboard']['port60'])
                self.assertEqual(round(model.observed_time()*27000),c['start_cycle'])
                run_driver(model,path)
                self.assertEqual(round(model.observed_time()*27000),c['end_cycle'])
                self.assert_hardware(model.snapshot(),c['expected'],str(i))
                self.assertEqual(state,c['game'])

    def test_custom_binding_precedence_and_latched_actions(self):
        # Source-derived cases beyond this native route's arrow-key coverage.
        work=KeyboardWork(self.catalogue)
        state=copy.deepcopy(self.fixture['cases'][0]['initial_game'])
        state.update(custom=1,bindings=[0x1e,0x30,0x2e,0x20,0x12])
        for scan in [0x1e,0x30,0x2e,0x20,0x12]:
            _,state=work.body(state,scan)
        self.assertTrue(all(state['flags'][k]==1 for k in ['0190','0192','0196','0194','019e']))
        for scan in [0x9e,0xb0,0xae,0xa0,0x92]:
            _,state=work.body(state,scan)
        self.assertTrue(all(state['flags'][k]==0 for k in ['0190','0192','0196','0194']))
        self.assertEqual(state['flags']['019e'],1,'Fire remains latched after release')
        state['bindings'][0]=0x20
        _,state=work.body(state,0x20)
        self.assertEqual(state['flags']['0190'],1)
        self.assertEqual(state['flags']['0194'],0,'First custom binding wins duplicates')
