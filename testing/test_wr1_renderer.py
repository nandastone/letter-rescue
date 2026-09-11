"""Compare generated renderer opening work against independent native probes."""
import gzip
import json
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from testing import test_wr1_hardware as hardware_tests
from wr1_renderer_work import RendererWork
from wr1_hardware_reference import Hardware,run_driver


class RendererTests(unittest.TestCase):
    assert_hardware=hardware_tests.HardwareTests.assert_hardware

    def test_native_backgrounds(self):
        self.check_extended('background')

    def test_native_tiles(self):
        self.check_extended('tiles')

    def test_native_doors(self):
        self.check_extended('doors')

    def test_native_matching(self):
        self.check_extended('matching')

    def test_native_player(self):
        self.check_extended('player')

    def test_native_actors(self):
        self.check_extended('actors')

    def test_native_complete(self):
        self.check_extended('complete')

    def test_native_visible_rewards(self):
        self.check_extended('complete','rewards',85)

    def check_extended(self,kind,fixture_name=None,count=75):
        f=json.loads(gzip.decompress((ROOT/f'testing/fixtures/wr1_renderer_{fixture_name or kind}.json.gz').read_bytes()))
        work=RendererWork(json.loads((ROOT/'assets/audio/original/driver_work.json').read_text()))
        names={int(k):v for k,v in f['event_names'].items()}
        self.assertEqual(len(f['cases']),count)
        for i,c in enumerate(f['cases']):
            with self.subTest(case=i):
                if kind=='background':
                    path,state,graphics,calls,_=work.background(c['initial_prefix'],c['graphics'],c['background'])
                elif kind=='tiles':
                    path,state,graphics,calls,_,tiles=work.tiles(c['initial_prefix'],c['graphics'],c['background'],c['tiles'])
                    self.assertEqual(tiles,c['expected_tiles'])
                elif kind=='doors':
                    path,state,graphics,calls,_,tiles,doors=work.doors(c['initial_prefix'],c['graphics'],c['background'],c['tiles'],c['doors'])
                    self.assertEqual(tiles,c['expected_tiles'])
                    self.assertEqual(doors,c['expected_doors'])
                else:
                    args=[c['initial_prefix'],c['graphics'],c['background'],c['tiles'],c['doors'],c['matching']]
                    if kind in ('player','actors','complete'):args.append(c['player'])
                    if kind in ('actors','complete'):args.extend([c['actors'],c['actor_images']])
                    if kind=='complete':args.append(c['tail'])
                    result=getattr(work,kind)(*args)
                    path,state,graphics,calls,_,tiles,doors=result[:7]
                    if kind in ('actors','complete'):self.assertEqual(result[7],c['expected_actors'])
                    if kind=='complete':self.assertEqual(result[8],c['expected_tail'])
                    self.assertEqual(tiles,c['expected_tiles'])
                    self.assertEqual(doors,c['expected_doors'])
                    self.assertEqual(c['matching'],c['expected_matching'])
                    self.assertEqual(c['player'],c['expected_player'])
                model=Hardware(c['initial'],names)
                run_driver(model,path)
                self.assertEqual(round(model.observed_time()*27000),c['end_cycle'])
                self.assert_hardware(model.snapshot(),c['expected'],str(i))
                self.assertEqual(state,c['prefix'])
                self.assertEqual(graphics,c['expected_graphics_state'])
                self.assertEqual([(x['kind'],x['args']) for x in calls],[(x['kind'],x['args']) for x in c['calls']])
                for call,expected in zip(calls,c['calls']):
                    for index,cycle,checkpoint in [('start','entry_cycle','initial'),('return','return_cycle','expected')]:
                        boundary=Hardware(c['initial'],names)
                        run_driver(boundary,path[:call[index]])
                        self.assertEqual(round(boundary.observed_time()*27000),expected[cycle])
                        self.assert_hardware(boundary.snapshot(),expected[checkpoint],str((i,index)))

    def test_native_openings(self):
        f=json.loads(gzip.decompress((ROOT/'testing/fixtures/wr1_renderer_prefix.json.gz').read_bytes()))
        catalogue=json.loads((ROOT/'assets/audio/original/driver_work.json').read_text())
        work=RendererWork(catalogue)
        names={int(k):v for k,v in f['event_names'].items()}
        self.assertEqual(len(f['cases']),75)
        for i,c in enumerate(f['cases']):
            with self.subTest(case=i):
                path,state,graphics,calls,_=work.prefix(c['initial_prefix'],c['graphics'])
                model=Hardware(c['initial'],names)
                run_driver(model,path)
                self.assertEqual(round(model.observed_time()*27000),c['end_cycle'])
                self.assert_hardware(model.snapshot(),c['expected'],str(i))
                self.assertEqual(state,c['prefix'])
                self.assertEqual(graphics,c['expected_graphics_state'])
                self.assertEqual(len(calls),len(c['calls']))
                for call,expected in zip(calls,c['calls']):
                    self.assertEqual(call['kind'],expected['kind'])
                    self.assertEqual(call['args'],expected['args'])
                    for index,cycle,checkpoint in [('start','entry_cycle','initial'),('return','return_cycle','expected')]:
                        boundary=Hardware(c['initial'],names)
                        run_driver(boundary,path[:call[index]])
                        self.assertEqual(round(boundary.observed_time()*27000),expected[cycle])
                        self.assert_hardware(boundary.snapshot(),expected[checkpoint],str((i,index)))
