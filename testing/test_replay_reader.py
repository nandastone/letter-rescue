import struct
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from bsv_replay import read_replay
from replay_to_json import frame_action_states, frames_to_godot_json


def checkpoint(payload=b'abc'):
    return struct.pack('<BBIII', 1, 0, 200, 200, len(payload)) + payload


def record(keys=(), inputs=(), token=b'f', payload=b''):
    return (struct.pack('<IB', 0, len(keys)) + b''.join(struct.pack('<BBHII', *k) for k in keys)
            + struct.pack('<H', len(inputs)) + b''.join(struct.pack('<BBBBHh', *v) for v in inputs)
            + token + payload)


def replay(*records):
    initial = checkpoint()
    return struct.pack('<IIIIQIIII', 0x42535632, 2, 123, len(initial), 456, len(records), 64, 128, 0) + initial + b''.join(records)


def frame(number, keys=(), inputs=()):
    return {'frame': number, 'key_events': [{'code': key, 'down': down} for key, down in keys],
            'input_events': [{'port': 0, 'device': device, 'idx': 0, 'id': button, 'value': value}
                             for device, button, value in inputs]}


class ReplayReaderTests(unittest.TestCase):
    def test_unicode_keyboard_and_both_checkpoint_layouts(self):
        data = replay(record(keys=[(1, 0, 0x1234, 273, 0x1f642)], token=b'C', payload=checkpoint(b'12345')),
                      record(inputs=[(0, 1, 0, 0, 7, 1)], token=b'c', payload=struct.pack('<Q', 2)+b'XY'), record())
        header, frames = read_replay(data)
        self.assertEqual(header['checkpoint_config'], 0)
        self.assertEqual(frames[0]['key_events'][0], {'down': True, 'mod': 0x1234, 'code': 273, 'character': 0x1f642})
        self.assertEqual(frames[1]['input_events'][0]['id'], 7)
        self.assertEqual(frames[-1]['end'], len(data))

    def test_truncations_and_trailing_garbage_fail(self):
        data = replay(record(keys=[(1, 0, 0, 273, 0)]), record(token=b'C', payload=checkpoint(b'12345')))
        for length in [0, 39, 40, 53, 56, 61, 68, len(data)-1]:
            with self.subTest(length=length), self.assertRaises(ValueError):
                read_replay(data[:length])
        with self.assertRaises(ValueError):
            read_replay(data+b'bad')

    def test_invalid_format_token_and_counts_fail(self):
        for offset, value in [(0, 0), (4, 3), (12, 999), (24, 2)]:
            data = bytearray(replay(record()))
            struct.pack_into('<I', data, offset, value)
            with self.subTest(offset=offset), self.assertRaises(ValueError):
                read_replay(data)
        with self.assertRaisesRegex(ValueError, 'Invalid frame token'):
            read_replay(replay(record(token=b'?')))

    def test_native_smoke_recording_has_exact_frame_count_and_eof(self):
        data = (ROOT/'testing/replays/smoke.replay').read_bytes()
        header, frames = read_replay(data)
        self.assertEqual(header['frame_count'], 1309)
        self.assertEqual(len(frames), 1309)
        self.assertEqual(frames[-1]['end'], len(data))
        self.assertEqual(frames[719]['key_events'][0]['code'], 32)
        self.assertTrue(frames[719]['key_events'][0]['down'])

    def test_idle_joypad_cannot_release_held_keyboard(self):
        frames = [frame(0, [(276, True)], [(1, 6, 0)]), frame(1, inputs=[(1, 6, 1)]),
                  frame(2, [(276, False)], [(1, 6, 1)]), frame(3, inputs=[(1, 6, 0)])]
        self.assertEqual(frames_to_godot_json(frames)['events'], [
            {'frame': 0, 'action': 'move_left', 'pressed': True},
            {'frame': 3, 'action': 'move_left', 'pressed': False}])

    def test_alias_release_keeps_other_key_held(self):
        frames = [frame(0, [(32, True), (13, True)]), frame(1, [(13, False)]), frame(2, [(32, False)])]
        self.assertEqual([s['held'] for s in frame_action_states(frames)], [{'use_slime'}, {'use_slime'}, set()])

    def test_mask_polled_keyboard_and_simultaneous_directions(self):
        frames = [frame(0, inputs=[(1, 256, (1 << 4) | (1 << 6)), (3, 275, 1)]), frame(1)]
        self.assertEqual([s['held'] for s in frame_action_states(frames)], [{'jump', 'move_left', 'move_right'}, set()])

    def test_slice_carries_held_keys_and_rebases_releases(self):
        frames = [frame(0, [(273, True)]), frame(1), frame(2, [(273, False)]), frame(3)]
        result = frames_to_godot_json(frames, start_frame=1, end_frame=3)
        self.assertEqual(result['total_frames'], 2)
        self.assertEqual(result['source_start_frame'], 1)
        self.assertEqual(result['events'], [{'frame': 0, 'action': 'jump', 'pressed': True},
                                           {'frame': 1, 'action': 'jump', 'pressed': False}])

    def test_conflicting_subframe_samples_are_not_silently_flattened(self):
        with self.assertRaisesRegex(ValueError, 'Conflicting'):
            list(frame_action_states([frame(0, inputs=[(1, 4, 1), (1, 4, 0)])]))


if __name__ == '__main__':
    unittest.main()
