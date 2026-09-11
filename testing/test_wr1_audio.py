"""Native speaker evidence, generated audio assets and actual Godot mixer output."""
import array
import gzip
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
import wave

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT/'assets/audio/original/playback'


class AudioAssetsTests(unittest.TestCase):
    def test_native_speaker_sequences_are_preserved(self):
        manifest = json.loads((ASSETS/'manifest.json').read_text())
        source = json.loads(gzip.decompress((ROOT/'testing/fixtures/wr1_irq_hardware_loop.json.gz').read_bytes()))
        expected = set()
        for case in source['cases']:
            state = case['initial_game']
            if state['speaker_index'] >= 0:
                expected.update((tuple(state['speaker_entry']), tuple(state['speaker_next'])))
        actual = {tuple(pair) for effect in manifest['effects'].values() for pair in effect['entries']}
        self.assertEqual(len(expected), 17)
        self.assertFalse(expected-actual, 'A native speaker pitch/duration is missing')
        self.assertEqual(manifest['source_exe_sha256'], source['exe_sha256'])

    def test_assets_have_valid_loops_and_audible_pcm(self):
        manifest = json.loads((ASSETS/'manifest.json').read_text())
        self.assertEqual(len(manifest['music']), 3)
        self.assertEqual(len(manifest['effects']), 10)
        for category in ('music', 'effects'):
            for name, item in manifest[category].items():
                with self.subTest(name=name):
                    path = ASSETS/item['file']
                    self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), item['wav_sha256'])
                    with wave.open(str(path)) as wav:
                        self.assertEqual((wav.getnchannels(), wav.getsampwidth(), wav.getframerate()), (1, 2, 48000))
                        frames = wav.getnframes()
                        samples = array.array('h', wav.readframes(min(frames, 48000)))
                    self.assertGreater(max(samples)-min(samples), 1000)
                    if category == 'music':
                        self.assertGreater(item['loop_begin'], 0)
                        self.assertEqual(item['loop_end'], frames)
                        self.assertLessEqual(abs(item['loop_end']-2*item['loop_begin']), 1)

    @unittest.skipUnless(os.environ.get('GODOT'), 'Set GODOT for real mixer checks')
    def test_original_scene_loop_and_mixer_output(self):
        with tempfile.TemporaryDirectory(dir=ROOT/'testing/output') as temporary:
            output = Path(temporary)/'mixer.wav'
            command = [os.environ['GODOT'], '--headless', '--path', str(ROOT), '--quit-after', '1500',
                       '--script', 'testing/test_wr1_audio.gd', '--', '--legacy',
                       '--original-seed', '20716', '--original-audio', '--audio-output', str(output)]
            result = subprocess.run(command, capture_output=True, text=True, timeout=40,
                                    creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
            self.assertEqual(result.returncode, 0, result.stdout+result.stderr)
            self.assertNotIn('ERROR:', result.stdout+result.stderr)
            self.assertIn('mixer recording PASS', result.stdout)
            with wave.open(str(output)) as wav:
                samples = array.array('h', wav.readframes(wav.getnframes()))
            mean = sum(samples)/len(samples)
            rms = math.sqrt(sum((value-mean)**2 for value in samples)/len(samples))
            self.assertGreater(rms, 100, 'Playback states succeeded but the mixer output is silent')
            self.assertLess(max(abs(value) for value in samples), 32767, 'Mixed output clipped')


if __name__ == '__main__':
    unittest.main()
