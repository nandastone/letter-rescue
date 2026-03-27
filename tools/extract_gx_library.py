#!/usr/bin/env python3
"""Extract files from a GX Library archive (used by Word Rescue).

Format documented at: https://moddingwiki.shikadi.net/wiki/GX_Library

Usage:
    python3 extract_gx_library.py <archive.1> <output_dir>
"""

import struct
import sys
import os
from pathlib import Path


def extract_gx_library(archive_path: str, output_dir: str) -> list[str]:
    """Extract all files from a GX Library archive."""
    data = open(archive_path, "rb").read()
    os.makedirs(output_dir, exist_ok=True)

    # Header: 146 bytes.
    if len(data) < 146:
        print("Error: file too small for GX Library header.")
        return []

    magic = struct.unpack_from("<H", data, 0x00)[0]
    if magic != 0xCA01:
        print(f"Warning: unexpected magic {magic:#06x} (expected 0xCA01).")

    copyright_str = data[0x02:0x34].split(b"\x00")[0].decode("ascii", errors="replace")
    version = struct.unpack_from("<H", data, 0x34)[0]
    label = data[0x36:0x5E].split(b"\x00")[0].decode("ascii", errors="replace")
    num_entries = struct.unpack_from("<H", data, 0x5E)[0]

    print(f"Archive: {archive_path}")
    print(f"  Copyright: {copyright_str}")
    print(f"  Version: {version}")
    print(f"  Label: {label}")
    print(f"  Entries: {num_entries}")
    print()

    # Directory starts at offset 0x80 (128 bytes header).
    dir_offset = 0x80

    extracted = []
    for i in range(num_entries):
        entry_offset = dir_offset + i * 26  # Each entry is 26 bytes.

        if entry_offset + 26 > len(data):
            print(f"  Entry {i}: truncated directory.")
            break

        pack_type = data[entry_offset]
        name_raw = data[entry_offset + 1:entry_offset + 14]
        name = name_raw.split(b"\x00")[0].decode("ascii", errors="replace").strip()
        file_offset = struct.unpack_from("<I", data, entry_offset + 14)[0]
        file_size = struct.unpack_from("<I", data, entry_offset + 18)[0]

        if file_offset + file_size > len(data):
            print(f"  {name}: offset {file_offset} + size {file_size} exceeds archive ({len(data)} bytes), skipping.")
            continue

        file_data = data[file_offset:file_offset + file_size]

        out_path = os.path.join(output_dir, name)
        with open(out_path, "wb") as f:
            f.write(file_data)

        print(f"  {name:16s} {file_size:8d} bytes  (pack={pack_type}, offset={file_offset:#08x})")
        extracted.append(name)

    return extracted


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python3 extract_gx_library.py <archive> <output_dir>")
        sys.exit(1)

    extract_gx_library(sys.argv[1], sys.argv[2])
