"""Optional original-binary instruction accounting against independent traces."""
import json
import gzip
import os
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))


@unittest.skipUnless(os.environ.get('WR1_EXE'),'Set WR1_EXE to the supported original executable')
class DriverCpuTests(unittest.TestCase):
    def test_static_catalogue_and_work_digests_are_reproducible(self):
        from extract_wr1_driver_work import extract
        from prepare_wr1_driver_work import prepare
        executable = Path(os.environ['WR1_EXE'])
        self.assertEqual(extract(executable),json.loads((ROOT/'assets/audio/original/driver_work.json').read_text()))
        expected = json.loads(gzip.decompress((ROOT/'testing/fixtures/wr1_driver_work.json.gz').read_bytes()))
        self.assertEqual(prepare(executable.read_bytes()),expected)

    def test_combined_fixture_work_is_derived_from_executable(self):
        from wr1_driver_cpu import DriverCPU
        f = json.loads(gzip.decompress((ROOT/'testing/fixtures/wr1_driver_hardware.json.gz').read_bytes()))
        cpu = DriverCPU(Path(os.environ['WR1_EXE']).read_bytes(),(ROOT/f['music_file']).read_bytes(),f['initial_opl'])
        self.assertEqual(len(f['cases']),90)
        for case in f['cases']:
            writes,cost = cpu.event(case['midi'])
            self.assertEqual(writes,case['writes'])
            self.assertEqual(cost,case['instructions'])
            self.assertEqual([list(pair) for pair in cpu.timeline],case['work'])

    def test_recovered_paths_match_registers_and_explain_instruction_cost(self):
        from wr1_driver_cpu import DriverCPU, account_blocks
        from wr1_driver_work import DriverWork
        from wr1_opl_reference import Opl
        tables = json.loads((ROOT/'assets/audio/original/driver_tables.json').read_text())
        planner = DriverWork(json.loads((ROOT/'assets/audio/original/driver_work.json').read_text()),len(tables['rhythm_registers']))
        executable = Path(os.environ['WR1_EXE']).read_bytes()
        for name,expected_events,residual_count,last_tick in [
            ('wr1_opl_ticks.json',90,1,561),
            ('wr1_opl_startup_ticks.json',69,0,363),
            ('wr1_opl_loop_ticks.json.gz',2588,10,9281)]:
            raw = (ROOT/f'testing/fixtures/{name}').read_bytes()
            f = json.loads(gzip.decompress(raw) if name.endswith('.gz') else raw)
            cpu = DriverCPU(executable,(ROOT/f['music_file']).read_bytes(),f['initial_opl'])
            opl = Opl(tables,(ROOT/f['music_file']).read_bytes(),f['initial_opl'])
            residuals,events = [],0
            for tick in f['ticks']:
                if tick['tick']>last_tick:
                    break
                writes = []
                self.assertEqual(len(tick['events']),len(tick['event_cycles']))
                for index,(midi,observed_cycles) in enumerate(zip(tick['events'],tick['event_cycles'])):
                    actual,cost = cpu.event(midi)
                    self.assertEqual(planner.event(midi,opl.state),cpu.timeline,(name,tick['tick'],index))
                    self.assertEqual(opl.event(midi),actual)
                    intervals = tick['write_cycles'][len(writes):len(writes)+len(actual)]
                    end,loss = account_blocks(tick['event_begin_cycles'][index],cpu.timeline,intervals)
                    self.assertEqual(end,tick['event_end_cycles'][index],(name,tick['tick'],index))
                    self.assertEqual(cost-loss,observed_cycles,(name,tick['tick'],index))
                    writes += actual
                    events += 1
                    if cost!=observed_cycles:
                        residuals.append((tick['tick'],midi['status'],cost,observed_cycles))
                self.assertEqual(writes,tick['writes'],(name,tick['tick']))
            self.assertEqual(events,expected_events)
            # Every formerly unexplained difference must follow the block / ms
            # accounting above, without event-specific correction constants.
            self.assertEqual(len(residuals),residual_count)


if __name__=='__main__':
    unittest.main()
