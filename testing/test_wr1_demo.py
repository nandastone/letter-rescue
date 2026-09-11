"""Native demo format semantics; no generated gameplay outcomes."""
import sys
import os
import json
import gzip
import hashlib
from pathlib import Path
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from decode_wr1_demo import decode
from run_wr1_parity import read, digest, run_engine, compare_demo_terminal
from compare_wr1_boundaries import compare
from prepare_wr1_demo import identify_music

ROOT = Path(__file__).resolve().parents[1]


class DemoFormatTests(unittest.TestCase):
    def test_compressed_evidence_is_lossless_and_hashes_stored_bytes(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp)/'evidence.json'
            value = {'updates':[{'x':-3,'y':12,'held':True}], 'text':'é'}
            packed = path.with_suffix('.json.gz')
            data = gzip.compress(json.dumps(value).encode(),mtime=0)
            packed.write_bytes(data)
            self.assertEqual(read(path), value)
            self.assertEqual(read(packed), value)
            self.assertEqual(digest(path), hashlib.sha256(data).hexdigest())
            path.write_text('{"uncompressed":true}')
            self.assertEqual(read(path), {'uncompressed':True})

    def test_checkpoint_music_bytes_identify_each_original_asset(self):
        candidates = sorted((ROOT/'assets/audio/original').glob('*.cmf'))
        self.assertEqual(len(candidates), 3)
        for path in candidates:
            data = path.read_bytes()
            initial = {'music_driver':{'prefix':list(data[:16])}, 'loaded_music_prefix':list(data[:64])}
            self.assertEqual(identify_music(initial, candidates), path)
            with self.assertRaises(ValueError):
                identify_music(initial, [p for p in candidates if p != path])
        # WR1.4 and WR1.5 share the short header: never silently pick one.
        short = {'music_driver':{'prefix':list(candidates[0].read_bytes()[:16])}}
        with self.assertRaises(ValueError):
            identify_music(short, candidates)

    def test_all_five_bits_and_idle(self):
        result = decode(bytes([0, 1, 2, 4, 8, 16, 31, 32]))
        self.assertEqual(result['updates'], 7)
        self.assertFalse(any(result['inputs'][0].values()))
        for row, key in zip(result['inputs'][1:6], ('up','down','right','left','slime_request')):
            self.assertTrue(row[key])
            self.assertEqual(sum(row.values()), 1)
        self.assertTrue(all(result['inputs'][6].values()))

    def test_first_stop_bit_ends_before_applying_other_bits(self):
        result = decode(bytes([4, 33, 9, 32]))
        self.assertEqual(result['updates'], 1)
        self.assertEqual(result['terminator_offset'], 1)
        self.assertEqual(result['trailing_bytes'], 2)

    def test_missing_stop_oversize_and_unknown_bits_fail(self):
        for data in (b'', bytes([1, 2]), bytes([0])*4000 + bytes([32]), bytes([64,32])):
            with self.assertRaises(ValueError):
                decode(data)

    def test_saved_demo_controls_reconstruct_the_original_file_hash(self):
        saved = read(ROOT / 'testing/fixtures/wr1_demo_level4_inputs.json')
        bits = {'up':1,'down':2,'right':4,'left':8,'slime_request':16}
        data = bytes(sum(bits[k] for k,v in row.items() if v) for row in saved['inputs']) + bytes([32])
        self.assertEqual(decode(data)['sha256'], saved['sha256'])
        inventory = read(ROOT / 'testing/fixtures/wr1_demo_inventory.json')
        self.assertEqual(len(inventory), 15)
        ninth = next(r for r in inventory if r['file'] == 'WR1.D8')
        self.assertEqual((ninth['updates'], ninth['trailing_bytes']), (1838, 71))


@unittest.skipUnless(os.environ.get('GODOT'), 'Set GODOT to exercise actual demo playback')
class DemoEngineTests(unittest.TestCase):
    def test_native_demo_states_and_terminal_rescue(self):
        replay_path = ROOT / 'testing/fixtures/wr1_demo_level4_replay.json'
        replay = read(replay_path)
        fixture = read(ROOT / 'testing/fixtures/wr1_demo_level4_boundaries.json')
        with tempfile.TemporaryDirectory(dir=ROOT / 'testing/output') as temp:
            directory = Path(temp)
            trace = directory / 'clone.jsonl'
            run_engine(os.environ['GODOT'], ['--headless','--','--original-rules','--replay',str(replay_path),
                       '--state-trace',str(trace)], directory, 'state', 180)
            clone = [json.loads(line) for line in trace.read_text().splitlines()]
            report = compare(fixture, clone, replay, digest(replay_path))
            self.assertEqual((report['completed_state_exact'],report['compared']), (1624,1624))
            self.assertEqual(report['missing_clone_updates'], [])
            self.assertFalse(any(m['inputs'] for m in report['mismatches']))
            self.assertEqual(report['validation_exact'], 1624)
            self.assertTrue(compare_demo_terminal(fixture, clone)['exact'])
            self.assertTrue(compare_demo_terminal(fixture, clone)['timing_exact'])
            self.assertFalse(compare_demo_terminal(fixture, clone[:-1])['exact'])
            clone[-1]['rng'] ^= 1
            failure = compare_demo_terminal(fixture, clone)
            self.assertFalse(failure['exact'])
            self.assertIn('rng', failure['state'])


if __name__ == '__main__':
    unittest.main()
