"""A single hardware checkpoint predicts every IRQ and the next idle gate."""
import copy
import gzip
import json
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from testing import test_wr1_hardware as hardware_tests
from wr1_idle_clock import IdleClock
from wr1_irq_work import STATE_FIELDS


class IdleClockTests(unittest.TestCase):
    assert_hardware=hardware_tests.HardwareTests.assert_hardware

    @classmethod
    def setUpClass(cls):
        cls.fixture=json.loads(gzip.decompress((ROOT/'testing/fixtures/wr1_idle_clock.json.gz').read_bytes()))
        cls.catalogue=json.loads((ROOT/'assets/audio/original/driver_work.json').read_text())
        cls.tables=json.loads((ROOT/'assets/audio/original/driver_tables.json').read_text())
        cls.cmf=(ROOT/cls.fixture['music_file']).read_bytes()
        cls.names={int(k):v for k,v in cls.fixture['event_names'].items()}

    def model(self,initial):
        return IdleClock(self.catalogue,self.tables,self.cmf,initial,self.names)

    def test_continuous_native_waits_without_future_input_changes(self):
        cases=[c for c in self.fixture['cases'] if not c['input_changes']]
        self.assertEqual(len(cases),54)
        self.assertEqual(cases[0]['start_call'],561)
        self.assertEqual(len(cases[0]['entries']),5)
        for c in cases:
            with self.subTest(start=c['start_call']):
                initial=copy.deepcopy(c['initial'])
                m=self.model(initial)
                self.assertEqual(round(m.hardware.observed_time()*27000),c['start_cycle'])
                self.assertEqual(m.until_admission(),c['end_cycle'])
                self.assert_hardware(m.hardware.snapshot(),c['expected'],'admission')
                self.assertEqual(len(m.entries),len(c['entries']))
                for actual,expected in zip(m.entries,c['entries']):
                    self.assert_hardware(actual['hardware'],expected['hardware'],'IRQ entry')
                    self.assertEqual({k:v for k,v in actual.items() if k!='hardware'},
                                     {k:v for k,v in expected.items() if k!='hardware'})
                self.assertEqual({k:m.game[k] for k in STATE_FIELDS},c['game'])
                self.assertEqual(m.music.state,c['music'])
                self.assertEqual(m.opl.state,c['opl'])
                self.assertEqual(initial,c['initial'],'Simulation mutated its checkpoint')

    def test_external_input_residuals_are_preserved_not_corrected(self):
        # Diagnostic coverage, deliberately separate from exact clock coverage.
        expected={669:-4,675:-10,681:-12,687:14,804:-14,809:12,815:-2,845:15,850:-9,903:13,909:-3}
        cases=[c for c in self.fixture['cases'] if c['input_changes']]
        self.assertEqual(len(cases),11)
        for c in cases:
            m=self.model(c['initial'])
            self.assertEqual(m.until_admission()-c['end_cycle'],expected[c['start_call']])

    def test_already_open_unsigned_timer_gate(self):
        initial=copy.deepcopy(self.fixture['cases'][0]['initial'])
        initial.update(cpu_ip=0x34ba-self.catalogue['main_file_base'],cpu_flags=512,pending_cycles=0)
        initial['clock_state'].update(timer=-1,threshold=0)
        m=self.model(initial)
        self.assertEqual(m.loop_cost,25)
        m.until_admission()
        self.assertEqual(m.entries,[])
        self.assertEqual(m.fast_loops,0)

    def test_continuous_native_waits_with_identical_timed_keys(self):
        f=json.loads(gzip.decompress((ROOT/'testing/fixtures/wr1_idle_keyboard_clock.json.gz').read_bytes()))
        names={int(k):v for k,v in f['event_names'].items()}
        self.assertEqual(len(f['cases']),65)
        self.assertEqual(sum(len(c['input_events']) for c in f['cases']),12)
        for c in f['cases']:
            with self.subTest(start=c['start_call']):
                m=IdleClock(self.catalogue,self.tables,self.cmf,c['initial'],names)
                self.assertEqual(m.until_admission(input_events=c['input_events']),c['end_cycle'])
                self.assert_hardware(m.hardware.snapshot(),c['expected'],'admission')
                for actual,expected in [(m.entries,c['entries']),(m.keyboard_entries,c['keyboard_entries'])]:
                    self.assertEqual(len(actual),len(expected))
                    for a,b in zip(actual,expected):
                        # Older IRQ0 hooks omit the keyboard controller; IRQ1
                        # and final admission independently check it in full.
                        self.assert_hardware({k:a['hardware'][k] for k in b['hardware']},b['hardware'],'entry')
                        self.assertEqual({k:v for k,v in a.items() if k!='hardware'},
                                         {k:v for k,v in b.items() if k!='hardware'})
                self.assertEqual({k:m.game[k] for k in STATE_FIELDS},c['game'])
                self.assertEqual(m.keyboard_game,c['keyboard_game'])
                self.assertEqual(m.music.state,c['music'])
                self.assertEqual(m.opl.state,c['opl'])
