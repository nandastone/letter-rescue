"""Actual-engine native parity for medium/hard hazards, rescue and cached reset."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import unittest
import uuid
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from compare_wr1_boundaries import compare, FIELDS
from compare_wr1_traces import differences
from prepare_wr1_boundaries import instruction_groups, STAGES, EXTENDED_STAGES
GODOT = os.environ.get('GODOT') or shutil.which('godot')


class RescueTraceTests(unittest.TestCase):
    def test_hard_impact_fixture_reaches_drip_and_cached_restart(self):
        fixture = json.loads((ROOT/'testing/fixtures/wr1_hard_drip_impact_boundaries.json').read_text())
        self.assertEqual(fixture['initial']['difficulty'], 2)
        deaths = [u for u in fixture['updates'] if u['completed']['death']]
        self.assertEqual(len(deaths), 1)
        death = deaths[0]
        self.assertEqual((death['completed']['gx'],death['completed']['gy']), (28,60))
        self.assertEqual(death['completed']['drips'][0]['frame'], 2)
        self.assertEqual(death['completed']['slime_used'], 1)
        after = next(u for u in fixture['updates'] if u['tick'] > death['tick'])['completed']
        self.assertEqual((after['reward_x'],after['reward_y']), (35,33))
        self.assertEqual(after['slime_used'], 1)  # Hard mode does not refill on death.

    def test_extended_observer_requires_all_intermediate_hooks(self):
        rows = [dict(event='instruction',ip=ip,pic_ms=i) for i,ip in enumerate(EXTENDED_STAGES)]
        self.assertEqual(len(list(instruction_groups(rows,rows))),1)
        for omitted in range(len(rows)):
            with self.assertRaises(ValueError):
                broken = rows[:omitted]+rows[omitted+1:]
                list(instruction_groups(broken,broken))

    def test_short_rescue_requires_entry_return_and_death(self):
        instructions = [dict(event='instruction',ip=ip,pic_ms=t,death=int(t==5))
                        for ip,t in zip((0x444,0x447,0xd72),(0,1,5))]
        life = [dict(event='lifecycle',ip=ip,pic_ms=t) for ip,t in ((0x8b1,2),(0x969,4))]
        self.assertEqual(len(list(instruction_groups(instructions,instructions+life))),1)
        for omitted in range(2):
            with self.assertRaises(ValueError):
                list(instruction_groups(instructions,instructions+life[:omitted]+life[omitted+1:]))
        instructions[-1]['death'] = 0
        with self.assertRaises(ValueError):
            list(instruction_groups(instructions,instructions+life))

    def test_missing_normal_render_hook_is_rejected(self):
        for omitted in range(len(STAGES)):
            rows = [dict(event='instruction',ip=ip,pic_ms=i) for i,ip in enumerate(STAGES) if i!=omitted]
            with self.assertRaises(ValueError):
                list(instruction_groups(rows,rows))


@unittest.skipUnless(GODOT,'Set GODOT for actual-engine comparisons')
class DifficultyTests(unittest.TestCase):
    def run_engine(self, args):
        run = subprocess.run([GODOT,'--path',str(ROOT),'--fixed-fps','70']+args,
            capture_output=True,text=True,timeout=45,
            creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        self.assertEqual(run.returncode,0,run.stdout+run.stderr)
        self.assertNotIn('SCRIPT ERROR:',run.stderr)

    def test_native_hazards_and_restarts(self):
        for stem,count,deaths in [('wr1_medium_drip',130,1),('wr1_hard_drip',113,2),('wr1_medium_pit',73,1),('wr1_boy_drip',130,1)]:
            with self.subTest(stem=stem):
                path = ROOT/'testing/fixtures'/(stem+'_replay.json')
                replay = json.loads(path.read_text())
                fixture = json.loads((path.parent/(stem+'_boundaries.json')).read_text())
                output = ROOT/'testing/output/replay_tests'/(stem+'.jsonl')
                output.parent.mkdir(parents=True,exist_ok=True)
                self.run_engine(['--headless','--','--legacy','--replay',str(path),'--state-trace',str(output)])
                rows = [json.loads(line) for line in output.read_text().splitlines()]
                self.assertEqual(differences(fixture['initial'],rows[0],FIELDS+('drips','gruzzle_move_timers','entrance_timer')), {})
                report = compare(fixture,rows,replay,hashlib.sha256(path.read_bytes()).hexdigest())
                self.assertEqual(report['completed_state_exact'],count,report['mismatches'][:2])
                self.assertEqual(report['compared'],count)
                self.assertEqual(report['clone_updates_beyond_fixture'],0)
                self.assertEqual(sum(u['completed']['death'] for u in fixture['updates']),deaths)
                if stem=='wr1_medium_drip':
                    self.assertTrue(any(u['completed']['death'] and u['completed']['drips'][0]['frame']==2 for u in fixture['updates']))
                # Freeze and expose the remaining timing issue. This is not an
                # exact frame-parity claim, nor a shifted comparison.
                known = json.loads((path.parent/(stem+'_timing_residuals.json')).read_text())['residuals']
                self.assertTrue(all(not m['state'] and not m['inputs'] for m in report['mismatches']))
                self.assertEqual([{k:m[k] for k in ('tick','native_entry_counter','clone_entry_counter')}
                                  for m in report['mismatches']],known)

    def test_initial_movement_impact_rescue_and_reset_pixels(self):
        for mode in ['medium','hard','boy']:
            with self.subTest(mode=mode):
                stem = 'wr1_'+mode+'_drip'
                path = ROOT/'testing/fixtures'/(stem+'_replay.json')
                replay = json.loads(path.read_text())
                manifest = json.loads((path.parent/(stem+'_pixels.json')).read_text())
                self.assertEqual(manifest['source_sha256'],replay['source_sha256'])
                self.assertEqual(manifest['instruction_trace_sha256'],replay['instruction_trace_sha256'])
                directory = ROOT/'testing/output/replay_tests'/(stem+'_pixels_'+uuid.uuid4().hex)
                targets = ','.join(str(p['clone_source_frame']) for p in manifest['pairs'])
                self.run_engine(['--script','testing/capture_wr1_replay_frames.gd','--','--legacy',
                    '--replay',str(path),'--capture-initial','--capture-source-frames',targets,'--capture-directory',str(directory)])
                pairs = [(manifest['initial_file'],manifest['initial_sha256'],'initial.png')]
                pairs += [(p['native_file'],p['sha256'],f"source_{p['clone_source_frame']:06d}.png") for p in manifest['pairs']]
                for name,digest,clone in pairs:
                    native = path.parent/name
                    self.assertEqual(hashlib.sha256(native.read_bytes()).hexdigest(),digest)
                    self.assertEqual(Image.open(native).convert('RGB').tobytes(),Image.open(directory/clone).convert('RGB').tobytes(),name)


if __name__ == '__main__':
    unittest.main()
