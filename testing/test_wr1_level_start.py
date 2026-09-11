"""Post-load parity: one starting state, then independently simulated inputs."""
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
sys.path.insert(0,str(ROOT/'tools'))
from compare_wr1_boundaries import compare, FIELDS
from compare_wr1_traces import differences
GODOT = os.environ.get('GODOT') or shutil.which('godot')


@unittest.skipUnless(GODOT,'Set GODOT to run post-load engine integration')
class LevelStartTests(unittest.TestCase):
    def test_focus_release_cannot_change_recorded_controls(self):
        path = ROOT/'testing/fixtures/wr1_level2_motion_replay.json'
        replay = json.loads(path.read_text())
        fixture = json.loads((ROOT/'testing/fixtures/wr1_level2_motion_boundaries.json').read_text())
        output = ROOT/'testing/output/replay_tests/level2_focus_release.jsonl'
        output.parent.mkdir(parents=True,exist_ok=True)
        run = subprocess.run([GODOT,'--headless','--fixed-fps','70','--path',str(ROOT),
            '--script','testing/release_wr1_replay_input.gd','--','--legacy',
            '--replay',str(path),'--state-trace',str(output)],
            capture_output=True,text=True,timeout=30,
            creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        self.assertEqual(run.returncode,0,run.stdout+run.stderr)
        self.assertNotIn('SCRIPT ERROR:',run.stderr)
        rows = [json.loads(line) for line in output.read_text().splitlines()]
        report = compare(fixture,rows,replay,hashlib.sha256(path.read_bytes()).hexdigest())
        self.assertTrue(report['all_validation_updates_exact'],report['mismatches'][:2])

    def test_initial_and_moving_pixels(self):
        manifest = json.loads((ROOT/'testing/fixtures/wr1_level2_motion_pixels.json').read_text())
        replay = json.loads((ROOT/'testing/fixtures/wr1_level2_motion_replay.json').read_text())
        self.assertEqual(manifest['source_sha256'],replay['source_sha256'])
        self.assertEqual(manifest['instruction_trace_sha256'],replay['instruction_trace_sha256'])
        directory = ROOT/'testing/output/replay_tests'/('level2_pixels_'+uuid.uuid4().hex)
        targets = ','.join(str(p['clone_source_frame']) for p in manifest['pairs'])
        run = subprocess.run([GODOT,'--path',str(ROOT),'--fixed-fps','70',
            '--script','testing/capture_wr1_replay_frames.gd','--','--legacy',
            '--replay','testing/fixtures/wr1_level2_motion_replay.json','--capture-initial',
            '--capture-source-frames',targets,'--capture-directory',str(directory)],
            capture_output=True,text=True,timeout=30,
            creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        self.assertEqual(run.returncode,0,run.stdout+run.stderr)
        self.assertNotIn('SCRIPT ERROR:',run.stderr)
        pairs = [(manifest['initial_file'],manifest['initial_sha256'],'initial.png')]
        pairs += [(p['native_file'],p['sha256'],f"source_{p['clone_source_frame']:06d}.png") for p in manifest['pairs']]
        for name,digest,clone in pairs:
            native = ROOT/'testing/fixtures'/name
            self.assertEqual(hashlib.sha256(native.read_bytes()).hexdigest(),digest)
            self.assertEqual(Image.open(native).convert('RGB').tobytes(),
                             Image.open(directory/clone).convert('RGB').tobytes(),name)

    def test_changed_jump_is_detected_after_synchronization(self):
        # A checkpoint must not turn the replay into recorded state playback.
        replay = json.loads((ROOT/'testing/fixtures/wr1_level2_motion_replay.json').read_text())
        fixture = json.loads((ROOT/'testing/fixtures/wr1_level2_motion_boundaries.json').read_text())
        replay['events'] = [e for e in replay['events'] if e['action'] != 'jump']
        directory = ROOT/'testing/output/replay_tests'
        directory.mkdir(parents=True,exist_ok=True)
        path, output = directory/'level2_no_jump.json',directory/'level2_no_jump.jsonl'
        path.write_text(json.dumps(replay)+'\n')
        run = subprocess.run([GODOT,'--headless','--fixed-fps','70','--path',str(ROOT),
            '--','--legacy','--replay',str(path),'--state-trace',str(output)],
            capture_output=True,text=True,timeout=30,
            creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        self.assertEqual(run.returncode,0,run.stdout+run.stderr)
        self.assertNotIn('SCRIPT ERROR:',run.stderr)
        rows = [json.loads(line) for line in output.read_text().splitlines()]
        report = compare(fixture,rows,replay,hashlib.sha256(path.read_bytes()).hexdigest())
        self.assertFalse(report['all_validation_updates_exact'])
        self.assertTrue(any(r['inputs'] and r['state'] for r in report['mismatches']))
        self.assertTrue(all(r['validation'] for r in report['mismatches']))

    def test_level_two_walk_jump_from_first_playable_frame(self):
        path = ROOT/'testing/fixtures/wr1_level2_motion_replay.json'
        replay = json.loads(path.read_text())
        fixture = json.loads((ROOT/'testing/fixtures/wr1_level2_motion_boundaries.json').read_text())
        output = ROOT/'testing/output/replay_tests/level2_motion.jsonl'
        output.parent.mkdir(parents=True,exist_ok=True)
        run = subprocess.run([GODOT,'--headless','--fixed-fps','70','--path',str(ROOT),
            '--','--legacy','--replay',str(path),'--state-trace',str(output)],
            capture_output=True,text=True,timeout=30,
            creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        self.assertEqual(run.returncode,0,run.stdout+run.stderr)
        self.assertNotIn('SCRIPT ERROR:',run.stderr)
        rows = [json.loads(line) for line in output.read_text().splitlines()]
        initial = rows[0]
        self.assertEqual(initial['tick'],0)
        self.assertNotIn('source_frame',initial)
        fields = FIELDS + ('words','word_cursor','level_index','door_state','recap_pending',
            'picture_timers','picture_frames','picture_animation_enabled','drips','slime_ever_used',
            'slime_used','miss_timer','miss_x','miss_y','mystery_prefix','mystery_pickups','slime_pickups','entrance_timer')
        self.assertEqual(differences(fixture['initial'],initial,fields),{})
        report = compare(fixture,rows,replay,hashlib.sha256(path.read_bytes()).hexdigest())
        (output.parent/'level2_motion_comparison.json').write_text(json.dumps(report,indent=2)+'\n')
        self.assertEqual(report['compared'],72)
        self.assertEqual(report['completed_state_exact'],72,report['mismatches'])
        self.assertTrue(all(not r['inputs'] for r in report['mismatches']),report['mismatches'])
        self.assertTrue(report['all_validation_updates_exact'],report['mismatches'])
        self.assertEqual(report['mismatches'],[])
        self.assertEqual(report['clone_updates_beyond_fixture'],0)


if __name__ == '__main__':
    unittest.main()
