"""Small independent fixtures for strict parsing, compression, and evidence failure."""
import json
from pathlib import Path
import struct
import tempfile
import unittest

from compare import load_capture
from executable import disassemble_script, unpack
from images import decode_palette, decode_shape
from resources import parse_archive


def archive(payload=b"hello"):
    prefix = b"\0" * 6 + bytes([(255 - sum(payload)) & 255]) + payload
    directory = struct.pack("<HIHHHIH3s", 1, int.from_bytes(b"SHAP", "big"), 8, 1, 42, 6, len(payload), b"\0\0\0")
    return struct.pack("<IH", len(prefix), len(directory)) + prefix[6:] + directory


def shape(width, height, mode, data):
    return struct.pack("<HHH", height, width, 0xf000 | (mode << 8)) + data


class Formats(unittest.TestCase):
    def test_archive_exact_offsets_and_checksum(self):
        data = archive()
        row, = parse_archive(data)
        self.assertEqual((row["tag"], row["id"], row["payload_offset"], row["size"]), ("SHAP", 42, 7, 5))
        self.assertEqual(data[row["payload_offset"]:row["payload_offset"] + row["size"]], b"hello")

    def test_archive_rejects_corruption_and_truncation(self):
        data = bytearray(archive())
        data[7] ^= 1
        with self.assertRaisesRegex(ValueError, "Checksum"):
            parse_archive(data)
        with self.assertRaisesRegex(ValueError, "bounds"):
            parse_archive(archive()[:-1])

    def test_all_compression_modes_and_column_order(self):
        rows = bytes(range(1, 9))
        columns = bytes([1, 5, 2, 6, 3, 7, 4, 8])
        encoded = [rows, b"\x07" + rows, b"\x07" + columns,
                   b"\xff" + rows, b"\xff" + columns]
        for method, stream in enumerate(encoded):
            with self.subTest(method=method):
                self.assertEqual(decode_shape(shape(4, 2, method, stream)), (4, 2, rows))

    def test_rle_repeat_and_lz_overlap(self):
        self.assertEqual(decode_shape(shape(6, 1, 1, b"\xfaA"))[2], b"AAAAAA")
        token = ((5 - 3) << 10) | 958
        self.assertEqual(decode_shape(shape(6, 1, 3, b"\x01A" + token.to_bytes(2, "big")))[2], b"AAAAAA")

    def test_packed_pixels_and_padding(self):
        data = struct.pack("<HHH", 1, 3, 0xb000) + b"\x12\x3f"
        self.assertEqual(decode_shape(data), (3, 1, b"\x01\x02\x03"))

    def test_image_rejects_missing_extra_and_overflow_bytes(self):
        for data in (shape(1, 1, 0, b""), shape(1, 1, 0, b"12"), shape(1, 1, 1, b"\xfeA")):
            with self.subTest(data=data), self.assertRaises(ValueError):
                decode_shape(data)

    def test_palette_uses_bit_replication(self):
        palette = b"\0" * 6 + b"\x01\x10\x20\x3f"
        self.assertEqual(decode_palette(palette), [(65, 130, 255)])
        with self.assertRaises(ValueError):
            decode_palette(palette[:-1] + b"\x40")

    def test_scr_boundaries_and_unknown_opcode(self):
        image = bytearray(226208)
        image[0x32c8e:0x32c8e + 17] = bytes([0, 1, 2, 3, 4, 5, 6, 7, 0x10, 0x14, 0x90, 0xa0, 0xb0, 0xc0, 0xd0, 0xe0, 0xf0])
        image[0x32ca0:0x32ca0 + 17] = bytes([0, 4, 2, 2, 2, 2, 1, 0, 2, 4, 4, 4, 4, 4, 8, 8, 1])
        script = b"\0" * 8 + b"\xc0\x01\0\x03\0\0"
        result = disassemble_script(script, image)
        self.assertEqual(result["instructions"][0]["shape_range"], [1, 3])
        for broken in (script[:-1], script + b"\0", b"\0" * 8 + b"\x80\0"):
            with self.subTest(broken=broken), self.assertRaises(ValueError):
                disassemble_script(broken, image)

    def test_unpack_rejects_unresearched_build(self):
        with self.assertRaisesRegex(ValueError, "Unresearched"):
            unpack(b"MZ")

    def test_comparison_rejects_incomplete_run(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            (path / "run.json").write_text(json.dumps({"complete": False}))
            with self.assertRaisesRegex(ValueError, "Incomplete"):
                load_capture(path)


if __name__ == "__main__":
    unittest.main()
