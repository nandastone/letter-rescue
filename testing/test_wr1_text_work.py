"""Native text primitives, including DOSBox's normal-core SCAS fallback."""
import gzip
import json
from pathlib import Path
import sys
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from testing import test_wr1_hardware as hardware_tests
from wr1_text_work import TextWork
from wr1_hardware_reference import Hardware,run_driver


class TextWorkTests(unittest.TestCase):
    assert_hardware=hardware_tests.HardwareTests.assert_hardware

    def test_native_text_primitives(self):
        self.check_fixture('wr1_contact_graphics',7)

    def test_native_reward_and_word_text(self):
        self.check_fixture('wr1_text_matching_graphics',151)

    def test_native_font_selection_and_reward_text(self):
        self.check_fixture('wr1_reward_graphics',237)

    def check_fixture(self,name,count):
        f=json.loads(gzip.decompress((ROOT/f'testing/fixtures/{name}.json.gz').read_bytes()))
        names={int(k):v for k,v in f['event_names'].items()}
        work=TextWork(json.loads((ROOT/'assets/audio/original/driver_work.json').read_text()))
        cases=[c for c in f['cases'] if c['kind'].startswith('text_') or c['kind']=='string_length']
        self.assertEqual(len(cases),count)
        for c in cases:
            with self.subTest(kind=c['kind']):
                kind=c['kind']
                if kind in ('text_color','text_background'):path,state=work.style(kind,c)
                elif kind=='text_cursor':path,state=work.cursor(c)
                elif kind=='string_length':
                    path,value=work.length(c);state=c['graphics_state']
                    self.assertEqual(value,c['result_ax'])
                elif kind=='text_font':
                    path,state,font=work.font(c)
                    self.assertEqual(font,c['expected_text_state'])
                else:path,state=work.string(c)
                h=Hardware(c['initial'],names)
                run_driver(h,path)
                self.assertEqual(round(h.observed_time()*27000),c['end_cycle'])
                self.assert_hardware(h.snapshot(),c['expected'],'text return')
                self.assertEqual(state,c['expected_graphics_state'])
