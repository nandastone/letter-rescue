"""Native graphics measurements and recovered drawing-page selector."""
import gzip
import json
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from testing import test_wr1_hardware as hardware_tests
from wr1_graphics_work import GraphicsWork
from wr1_hardware_reference import Hardware,run_driver


class GraphicsTests(unittest.TestCase):
    assert_hardware=hardware_tests.HardwareTests.assert_hardware

    def test_native_fills(self):
        f=json.loads(gzip.decompress((ROOT/'testing/fixtures/wr1_fill_work.json.gz').read_bytes()))
        work=GraphicsWork(json.loads((ROOT/'assets/audio/original/driver_work.json').read_text()))
        names={int(k):v for k,v in f['event_names'].items()}
        for kind,count in [('fill_style',128),('fill_rect',58),('fill_raw',58)]:
            cases=[c for c in f['cases'] if c['kind']==kind]
            self.assertEqual(len(cases),count)
            for i,c in enumerate(cases):
                with self.subTest(kind=kind,case=i):
                    result=getattr(work,kind)(c)
                    model=Hardware(c['initial'],names)
                    run_driver(model,result[0])
                    self.assertEqual(round(model.observed_time()*27000),c['end_cycle'])
                    self.assert_hardware(model.snapshot(),c['expected'],str((kind,i)))
                    self.assertEqual(c['result_ax'],0)
                    self.assertEqual(c['fill_state'],c['expected_fill_state'])
                    if kind=='fill_raw':
                        self.assertEqual(result[1],c['expected_args'])
                        self.assertEqual(c['graphics_state'],c['expected_graphics_state'])
                    else:
                        self.assertEqual(result[1],c['expected_graphics_state'])
                        if kind=='fill_rect':self.assertEqual(result[2],c['expected_args'])
                    if kind!='fill_style':
                        self.assertEqual(c['clock_state'],c['expected_clock_state'])
                        self.assertEqual(c['music_driver'],c['expected_music_driver'])

    def test_native_drawing_page_selection(self):
        f=json.loads(gzip.decompress((ROOT/'testing/fixtures/wr1_graphics_profile.json.gz').read_bytes()))
        catalogue=json.loads((ROOT/'assets/audio/original/driver_work.json').read_text())
        work=GraphicsWork(catalogue)
        names={int(k):v for k,v in f['event_names'].items()}
        cases=[c for c in f['cases'] if c['kind']=='draw_page']
        self.assertEqual(len(cases),129)
        for i,c in enumerate(cases):
            with self.subTest(case=i):
                path,state=work.draw_page(c)
                model=Hardware(c['initial'],names)
                run_driver(model,path)
                self.assertEqual(round(model.observed_time()*27000),c['end_cycle'])
                self.assert_hardware(model.snapshot(),c['expected'],str(i))
                self.assertEqual(state,c['expected_graphics_state'])
                self.assertEqual(c['result_ax'],0)

    def test_native_aligned_ega_copies(self):
        f=json.loads(gzip.decompress((ROOT/'testing/fixtures/wr1_copy_bios.json.gz').read_bytes()))
        catalogue=json.loads((ROOT/'assets/audio/original/driver_work.json').read_text())
        work=GraphicsWork(catalogue)
        names={int(k):v for k,v in f['event_names'].items()}
        cases=[c for c in f['cases'] if c['kind']=='copy_rect']
        self.assertEqual(len(cases),1050)
        for i,c in enumerate(cases):
            with self.subTest(case=i):
                path,args=work.copy_rect(c)
                model=Hardware(c['initial'],names)
                run_driver(model,path)
                self.assertEqual(round(model.observed_time()*27000),c['end_cycle'])
                self.assert_hardware(model.snapshot(),c['expected'],str(i))
                self.assertEqual(args,c['expected_args'])
                self.assertEqual(c['result_ax'],0)
                self.assertEqual(c['graphics_state'],c['expected_graphics_state'])
                self.assertEqual(c['clock_state'],c['expected_clock_state'])
                self.assertEqual(c['music_driver'],c['expected_music_driver'])

    def test_native_masked_sprites(self):
        f=json.loads(gzip.decompress((ROOT/'testing/fixtures/wr1_masked_work.json.gz').read_bytes()))
        catalogue=json.loads((ROOT/'assets/audio/original/driver_work.json').read_text())
        work=GraphicsWork(catalogue)
        names={int(k):v for k,v in f['event_names'].items()}
        cases=[c for c in f['cases'] if c['kind']=='masked_sprite']
        self.assertEqual(len(cases),198)
        for i,c in enumerate(cases):
            with self.subTest(case=i):
                model=Hardware(c['initial'],names)
                run_driver(model,work.masked_sprite(c))
                self.assertEqual(round(model.observed_time()*27000),c['end_cycle'])
                self.assert_hardware(model.snapshot(),c['expected'],str(i))
                self.assertEqual(c['result_ax'],0)
                self.assertEqual(c['args'],c['expected_args'])
                self.assertEqual(c['image_header'],c['expected_image_header'])
                self.assertEqual(c['clock_state'],c['expected_clock_state'])
                self.assertEqual(c['music_driver'],c['expected_music_driver'])

    def test_native_display_page_selection(self):
        f=json.loads(gzip.decompress((ROOT/'testing/fixtures/wr1_display_work.json.gz').read_bytes()))
        catalogue=json.loads((ROOT/'assets/audio/original/driver_work.json').read_text())
        work=GraphicsWork(catalogue)
        names={int(k):v for k,v in f['event_names'].items()}
        cases=[c for c in f['cases'] if c['kind']=='display_page']
        self.assertEqual(len(cases),64)
        for i,c in enumerate(cases):
            with self.subTest(case=i):
                model=Hardware(c['initial'],names)
                path,state=work.display_page(c)
                run_driver(model,path)
                self.assertEqual(round(model.observed_time()*27000),c['end_cycle'])
                self.assert_hardware(model.snapshot(),c['expected'],str(i))
                self.assertEqual(state,c['expected_display_state'])
                self.assertEqual(c['result_ax'],0)
