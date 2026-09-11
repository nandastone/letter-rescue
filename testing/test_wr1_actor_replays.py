"""Real engine regressions for wrong-match spawning and slime hit/miss replays."""
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import unittest
import uuid
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from compare_wr1_boundaries import compare
GODOT = os.environ.get('GODOT') or shutil.which('godot')


@unittest.skipUnless(GODOT,'Set GODOT to run engine integration tests')
class ActorReplayTests(unittest.TestCase):
    def test_second_level_pixels_at_fixed_input_frame(self):
        manifest = json.loads((ROOT/'testing/fixtures/wr1_level2_pixels.json').read_text())
        directory = ROOT/'testing/output/replay_tests'/('level2_pixels_'+uuid.uuid4().hex)
        frame = manifest['clone_source_frame']
        run = subprocess.run([GODOT,'--path',str(ROOT),'--fixed-fps','70',
            '--script','testing/capture_wr1_replay_frames.gd','--','--legacy','--mystery-word','cup',
            '--replay','testing/fixtures/wr1_exit_replay.json','--capture-source-frames',str(frame),
            '--capture-directory',str(directory)],capture_output=True,text=True,timeout=90,
            creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        self.assertEqual(run.returncode,0,run.stdout+run.stderr)
        self.assertNotIn('SCRIPT ERROR:',run.stderr)
        native = ROOT/'testing/fixtures'/manifest['native_file']
        self.assertEqual(hashlib.sha256(native.read_bytes()).hexdigest(),manifest['sha256'])
        self.assertEqual(Image.open(native).convert('RGB').tobytes(),
                         Image.open(directory/f'source_{frame:06d}.png').convert('RGB').tobytes())

    def test_recap_pixels_at_fixed_input_frames(self):
        manifest = json.loads((ROOT/'testing/fixtures/wr1_recap_pixels.json').read_text())
        directory = ROOT/'testing/output/replay_tests'/('recap_pixels_'+uuid.uuid4().hex)
        frames = ','.join(str(p['clone_source_frame']) for p in manifest['pairs'])
        run = subprocess.run([GODOT,'--path',str(ROOT),'--fixed-fps','70',
            '--script','testing/capture_wr1_replay_frames.gd','--','--legacy','--mystery-word','cup',
            '--replay','testing/fixtures/wr1_recap_replay.json','--capture-source-frames',frames,
            '--capture-directory',str(directory)],capture_output=True,text=True,timeout=60,
            creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        self.assertEqual(run.returncode,0,run.stdout+run.stderr)
        self.assertNotIn('SCRIPT ERROR:',run.stderr)
        self.assertNotIn('at: blit_rect',run.stderr)
        for pair in manifest['pairs']:
            native = ROOT/'testing/fixtures'/pair['native_file']
            self.assertEqual(hashlib.sha256(native.read_bytes()).hexdigest(),pair['sha256'])
            clone = directory/f'source_{pair["clone_source_frame"]:06d}.png'
            self.assertEqual(Image.open(native).convert('RGB').tobytes(),Image.open(clone).convert('RGB').tobytes(),pair)

    def check_replay(self, name, count, timing_residual):
        path = ROOT/f'testing/fixtures/wr1_{name}_replay.json'
        replay = json.loads(path.read_text())
        fixture = json.loads((ROOT/f'testing/fixtures/wr1_{name}_boundaries.json').read_text())
        output = ROOT/f'testing/output/replay_tests/{name}.jsonl'
        output.parent.mkdir(parents=True,exist_ok=True)
        run = subprocess.run([GODOT,'--verbose','--headless','--fixed-fps','70','--path',str(ROOT),
            '--','--legacy','--mystery-word','cup','--replay',str(path),
            '--state-trace',str(output)],capture_output=True,text=True,timeout=30,
            creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        self.assertEqual(run.returncode,0,run.stdout+run.stderr)
        self.assertNotIn('SCRIPT ERROR:',run.stderr)
        # Existing accelerated-audio shutdown issue: verify the leaked resources
        # are only known sound files, rather than accepting arbitrary errors.
        for line in run.stderr.splitlines():
            if line.startswith('ERROR:'):
                self.assertRegex(line,r'^ERROR: [1-9][0-9]* resources still in use at exit\.$')
        resources = re.findall(r'Resource still in use: (.+)',run.stdout)
        known_sounds = 'collect|wrong|reveal|correct|unlock' if name in ['all_words','recap'] else 'collect|wrong|reveal'
        self.assertTrue(all(re.fullmatch(r'res://assets/audio/sfx/('+known_sounds+r')\.wav \(AudioStreamWAV\)',r)
                            for r in resources),resources)
        clone = [json.loads(line) for line in output.read_text().splitlines()]
        report = compare(fixture,clone,replay,hashlib.sha256(path.read_bytes()).hexdigest())
        self.assertEqual(report['compared'],count)
        self.assertEqual(report['completed_state_exact'],count,report['mismatches'])
        residual = [r for r in report['mismatches'] if r['validation']]
        self.assertEqual([r['tick'] for r in residual],timing_residual)
        self.assertTrue(all(not r['state'] and not r['inputs'] for r in residual))
        (ROOT/f'testing/output/replay_tests/{name}_comparison.json').write_text(json.dumps(report,indent=2)+'\n')
        return fixture,clone

    def test_spawn_countdown_and_activation(self):
        fixture,clone = self.check_replay('spawn',83,[])
        rows = {r['tick']:r for r in clone}
        self.assertEqual(rows[49]['gruzzles'][1]['state'],63)
        self.assertEqual(rows[49]['gruzzles'][1]['move_timer'],2)
        self.assertEqual(rows[78]['gruzzles'][1]['state'],-1)

    def test_recap_return_keeps_completed_state_and_rng(self):
        # The drawing-work model removes the ten-frame recap gap. Remaining
        # one-frame main-loop drift is measured separately from exact state.
        residual = json.loads((ROOT/'testing/fixtures/wr1_recap_timing_residual.json').read_text())
        _, clone = self.check_replay('recap',369,residual['ticks'])
        rows = {r['tick']:r for r in clone}
        self.assertEqual(rows[762]['rng'],520533843)
        self.assertEqual(rows[762]['picture_animation_enabled'],0)
        self.assertEqual(rows[762]['source_frame'],5951)

    def test_original_exit_automatically_loads_second_level(self):
        path = ROOT/'testing/fixtures/wr1_exit_replay.json'
        output = ROOT/'testing/output/replay_tests/exit.jsonl'
        run = subprocess.run([GODOT,'--verbose','--headless','--fixed-fps','70','--path',str(ROOT),
            '--','--legacy','--mystery-word','cup','--replay',str(path),
            '--state-trace',str(output)],capture_output=True,text=True,timeout=30,
            creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        self.assertEqual(run.returncode,0,run.stdout+run.stderr)
        self.assertNotIn('SCRIPT ERROR:',run.stderr)
        for line in run.stderr.splitlines():
            if line.startswith('ERROR:'):
                self.assertRegex(line,r'^ERROR: [1-9][0-9]* resources still in use at exit\.$')
        resources = re.findall(r'Resource still in use: (.+)',run.stdout)
        self.assertTrue(all(re.fullmatch(r'res://assets/audio/sfx/(collect|wrong|reveal|correct|unlock)\.wav \(AudioStreamWAV\)',r)
                            for r in resources),resources)
        rows = [json.loads(line) for line in output.read_text().splitlines()]
        loaded = [r for r in rows if r['level_index']==1 and r['door_state']==0]
        self.assertTrue(loaded)
        first = loaded[0]
        self.assertEqual((first['gx'],first['gy'],first['word_offset'],first['picture_offset']), (73,48,5,6))
        self.assertEqual((first['score'],first['rng'],first['picture_animation_enabled']), (740,3921914530,1))
        self.assertEqual(first['words'],['hat','dog','arm','bat','ant','car','run'])
        self.assertEqual(first['word_cursor'],56)
        self.assertEqual(first['active_index'],4) # Inactive index survives reset.
        fixture = json.loads((ROOT/'testing/fixtures/wr1_exit_boundaries.json').read_text())
        report = compare(fixture,rows,json.loads(path.read_text()),hashlib.sha256(path.read_bytes()).hexdigest())
        self.assertEqual((report['compared'],report['completed_state_exact']),(77,77),report['mismatches'])
        self.assertTrue(all(not m['inputs'] and not m['state'] for m in report['mismatches']))
        self.assertEqual([m['tick'] for m in report['mismatches']],[778]+list(range(817,839)))

    def test_slime_hit_busy_gate_reward_and_removal(self):
        _,clone = self.check_replay('slime_hit',100,[94])
        rows = {r['tick']:r for r in clone}
        self.assertEqual(rows[49]['slime_used'],1)
        self.assertEqual(rows[72]['gruzzles'][0]['state'],24)
        self.assertEqual(rows[72]['score'],25)
        self.assertEqual(rows[73]['gruzzle_count'],0)

    def test_empty_slime_and_cooldown(self):
        _,clone = self.check_replay('slime_miss',100,[94])
        self.assertTrue(all(r['slime_used']==0 for r in clone))

    def test_bucket_refill_and_empty_effect(self):
        _,clone = self.check_replay('refill',100,[94])
        self.assertTrue(any(r['slime_used']==1 for r in clone))
        pickup = next(r for r in clone if r['slime_pickups'][1]['attribute']==32)
        self.assertEqual((pickup['slime_used'],pickup['score']),(0,20))
        self.assertTrue(any(r['miss_timer']==9 for r in clone))

    def test_mystery_letter_order_and_removal(self):
        _,clone = self.check_replay('letters',100,[94])
        wrong = next(r for r in clone if r['mystery_pickups'][2]['attribute']==32)
        self.assertEqual((wrong['mystery_prefix'],wrong['score']),(0,5))
        correct = next(r for r in clone if r['mystery_prefix']==1)
        self.assertEqual((correct['mystery_pickups'][0]['attribute'],correct['score']),(32,15))

    def test_full_mystery_word_and_slime_refill(self):
        _,clone = self.check_replay('letters_complete',319,[94,214,238,269,294])
        complete = next(r for r in clone if r['mystery_prefix']==3)
        self.assertEqual((complete['score'],complete['slime_used']),(215,0))
        previous = clone[clone.index(complete)-1]
        self.assertEqual((previous['score'],previous['slime_used']),(115,2))

    def test_all_seven_matches_and_perfect_bonus(self):
        _,clone = self.check_replay('all_words',761,[94,214,238,269,294,357,438,444,488,513,601,663,677,682,688,732,757])
        complete = next(r for r in clone if r['matched_count']==7)
        self.assertEqual((complete['score'],complete['mistakes'],complete['reward_bonus']),(740,0,3))
        sixth = next(r for r in clone if r['matched_count']==6)
        self.assertEqual((sixth['reward_x'],sixth['reward_timer']),(43,19))

    def test_death_and_respawn(self):
        # IRQ reset during native level loading changes the admission phase.
        # State parity is mandatory; timing discrepancies remain explicit.
        # This fixture records the observed residual counters, not engine inputs.
        residual = json.loads((ROOT/'testing/fixtures/wr1_death_timing_residual.json').read_text())
        _,clone = self.check_replay('death',200,residual['ticks'])
        rows = {r['tick']:r for r in clone}
        self.assertEqual(rows[58]['completed_source_frame']+1,818)
        self.assertEqual((rows[59]['rng'],rows[59]['word_offset'],rows[59]['picture_offset']),
                         (3482209081,3,4))


if __name__ == '__main__':
    unittest.main()
