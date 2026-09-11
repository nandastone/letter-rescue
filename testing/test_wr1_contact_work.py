"""Native contact scans and word revelation generate their own graphics calls."""
import copy
import gzip
import json
from pathlib import Path
import sys
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from testing import test_wr1_hardware as hardware_tests
from wr1_contact_work import ContactWork
from wr1_hardware_reference import Hardware,run_driver
from prepare_wr1_graphics import DETAILS


class ContactWorkTests(unittest.TestCase):
    assert_hardware=hardware_tests.HardwareTests.assert_hardware

    def test_native_contacts(self):
        f=json.loads(gzip.decompress((ROOT/'testing/fixtures/wr1_contact_graphics.json.gz').read_bytes()))
        names={int(k):v for k,v in f['event_names'].items()}
        work=ContactWork(json.loads((ROOT/'assets/audio/original/driver_work.json').read_text()))
        cases=[c for c in f['cases'] if c['kind']=='contact']
        self.assertEqual(len(cases),64)
        for c in cases:
            with self.subTest(call=c['launch_call']):
                before=copy.deepcopy(c)
                graphics={k:c[k] for k in DETAILS+('graphics_flags','fill_state','text_state')}
                path,state,device,attributes,calls=work.body(c['contact'],c['contact_attributes'],graphics)
                self.assertEqual(state,c['expected_contact'])
                self.assertEqual(device,c['expected_graphics_state'])
                self.assertEqual(attributes,c['expected_contact_attributes'])
                h=Hardware(c['initial'],names)
                run_driver(h,path)
                self.assertEqual(round(h.observed_time()*27000),c['end_cycle'])
                self.assert_hardware(h.snapshot(),c['expected'],'contact return')
                children=sorted((x for x in f['cases'] if x['kind']!='contact' and c['start_cycle']<x['start_cycle'] and x['end_cycle']<c['end_cycle']),key=lambda x:x['start_cycle'])
                self.assertEqual([(x['kind'],x['args']) for x in calls],[(x['kind'],x['args']) for x in children])
                for child,expected in zip(calls,children):
                    for label,cycle,checkpoint in [('start','start_cycle','initial'),('return','end_cycle','expected')]:
                        h=Hardware(c['initial'],names)
                        run_driver(h,path[:child[label]])
                        self.assertEqual(round(h.observed_time()*27000),expected[cycle])
                        self.assert_hardware(h.snapshot(),expected[checkpoint],'contact child '+label)
                self.assertEqual(c,before,'Mutation of contact checkpoint/evidence')
