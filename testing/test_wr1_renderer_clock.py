"""One renderer checkpoint predicts the next original gameplay admission."""
import copy
import gzip
import json
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from testing import test_wr1_hardware as hardware_tests
from wr1_renderer_clock import RendererClock
from wr1_irq_work import STATE_FIELDS


class RendererClockTests(unittest.TestCase):
    assert_hardware=hardware_tests.HardwareTests.assert_hardware

    @classmethod
    def setUpClass(cls):
        cls.fixture=json.loads(gzip.decompress((ROOT/'testing/fixtures/wr1_renderer_clock.json.gz').read_bytes()))
        cls.catalogue=json.loads((ROOT/'assets/audio/original/driver_work.json').read_text())
        cls.tables=json.loads((ROOT/'assets/audio/original/driver_tables.json').read_text())
        cls.cmf=(ROOT/cls.fixture['music_file']).read_bytes()
        cls.names={int(k):v for k,v in cls.fixture['event_names'].items()}

    def model(self,c):
        return RendererClock(self.catalogue,self.tables,self.cmf,c['initial'],self.names)

    def test_native_renderer_to_admission(self):
        self.assertEqual(len(self.fixture['cases']),64)
        self.assertEqual(len(self.fixture['excluded']),11)
        for c in self.fixture['cases']:
            with self.subTest(start=c['start_call']):
                before=copy.deepcopy(c)
                m=self.model(c)
                m.finish_render(c['renderer'],c['post'],c['display_state'],c['return_cs'])
                renderer=c['renderer']
                expected={'renderer_return':{'hardware':renderer['expected'],'cycle':renderer['end_cycle']},
                          **{k:c[k] for k in ('display_entry','display_return','update_done')}}
                for name,e in expected.items():
                    actual=m.checkpoints[name]
                    self.assertEqual(actual['cycle'],e['cycle'],name)
                    self.assert_hardware({k:actual['hardware'][k] for k in e['hardware']},e['hardware'],name)
                self.assertEqual(m.display_state,c['display_return']['state'])
                self.assertEqual(m.result[1],renderer['prefix'])
                self.assertEqual(m.result[2],renderer['expected_graphics_state'])
                self.assertEqual(m.result[5],renderer['expected_tiles'])
                self.assertEqual(m.result[6],renderer['expected_doors'])
                self.assertEqual(m.result[7],renderer['expected_actors'])
                self.assertEqual(m.result[8],renderer['expected_tail'])
                wait=c['wait']
                self.assertEqual(m.until_admission(wait['input_events']),c['end_cycle'])
                self.assert_hardware(m.idle.hardware.snapshot(),wait['expected'],'admission')
                for actual,expected in [(m.idle.entries,wait['entries']),(m.idle.keyboard_entries,wait['keyboard_entries'])]:
                    self.assertEqual(len(actual),len(expected))
                    for a,b in zip(actual,expected):
                        self.assert_hardware({k:a['hardware'][k] for k in b['hardware']},b['hardware'],'IRQ entry')
                        self.assertEqual({k:v for k,v in a.items() if k!='hardware'},
                                         {k:v for k,v in b.items() if k!='hardware'})
                self.assertEqual({k:m.idle.game[k] for k in STATE_FIELDS},wait['game'])
                self.assertEqual(m.idle.keyboard_game,wait['keyboard_game'])
                self.assertEqual(m.idle.music.state,wait['music'])
                self.assertEqual(m.idle.opl.state,wait['opl'])
                self.assertEqual(c,before,'Simulation mutated its checkpoint/evidence')

    def test_renderer_preemption_remains_explicit(self):
        c=copy.deepcopy(self.fixture['cases'][0])
        c['initial']['pic_interrupts']['irq_check']=1
        m=self.model(c)
        with self.assertRaisesRegex(NotImplementedError,'IRQ preemption'):
            m.finish_render(c['renderer'],c['post'],c['display_state'],c['return_cs'])
