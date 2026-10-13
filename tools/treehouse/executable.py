"""Statically unpack the identified DOS v1.1 EXE and frame its SCR bytecode.

No original instructions execute. Only the measured build is accepted; loader
addresses and packer offsets must be researched afresh for another executable.
See testing/treehouse_executable_research.md for evidence and unknown semantics.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct
import zipfile

from resources import parse_archive

EXE_SHA256 = "16c5623174f0e97ee928790fd6d3e638d5724f3fb2a7794c7d3a48274f1d82d9"
IMAGE_SHA256 = "f2776b04a307996d1a7b4230d49b552b67ad787675b766a7b4c8577ad417973f"


def unpack(data: bytes) -> tuple[bytes, dict]:
    if hashlib.sha256(data).hexdigest() != EXE_SHA256:
        raise ValueError("Unresearched executable; expected original DOS v1.1 TREEHSE.EXE")
    mz = struct.unpack_from("<14H", data)
    start = mz[4] * 16
    packed_header = start + mz[11] * 16
    header = struct.unpack_from("<9H", data, packed_header)
    image = bytearray(header[6] * 16)
    source, dest, packets = packed_header - 1, len(image) - 1, 0
    while source >= start and data[source] == 255:
        source -= 1
    while True:
        if source - 2 < start:
            raise ValueError("Truncated EXEPACK packet")
        code = data[source]
        count = struct.unpack_from("<H", data, source - 2)[0]
        source -= 3
        packets += 1
        if not count or dest - count + 1 < 0:
            raise ValueError("EXEPACK output underflow")
        if code & 254 == 176:
            if source < start:
                raise ValueError("EXEPACK repeat outside source")
            image[dest - count + 1:dest + 1] = bytes([data[source]]) * count
            source -= 1
        elif code & 254 == 178:
            if source - count + 1 < start:
                raise ValueError("EXEPACK literal outside source")
            image[dest - count + 1:dest + 1] = data[source - count + 1:source + 1]
            source -= count
        else:
            raise ValueError(f"Unrecognized EXEPACK control: {code:02x}")
        dest -= count
        if code & 1:
            break
    if source - start != dest:
        raise ValueError("EXEPACK unchanged prefix lengths differ")
    image[:dest + 1] = data[start:source + 1]
    if hashlib.sha256(image).hexdigest() != IMAGE_SHA256:
        raise ValueError("Unpacked image differs from researched artifact")
    cursor = packed_header + 0x12d
    relocations = []
    for block in range(16):
        n = struct.unpack_from("<H", data, cursor)[0]
        cursor += 2
        for _ in range(n):
            offset = (block << 16) + struct.unpack_from("<H", data, cursor)[0]
            cursor += 2
            if offset + 2 > len(image):
                raise ValueError("Relocation outside image")
            relocations.append(offset)
    declared_end = (mz[2] - 1) * 512 + (mz[1] or 512)
    if cursor != declared_end:
        raise ValueError("Relocations do not end at declared EXE boundary")
    overlays = []
    offset = (declared_end + 511) & ~511
    while offset < len(data):
        fields = struct.unpack_from("<14H", data, offset)
        if fields[0] != 0x5a4d:
            raise ValueError("Expected aligned MZ overlay")
        size = (fields[2] - 1) * 512 + (fields[1] or 512)
        if offset + size > len(data) or fields[12] + fields[3] * 4 > fields[4] * 16:
            raise ValueError("Invalid overlay bounds")
        overlays.append(dict(file_offset=offset, id=fields[13], size=size,
                             header_bytes=fields[4] * 16, relocations=fields[3]))
        offset = (offset + size + 511) & ~511
    return bytes(image), dict(executable_sha256=EXE_SHA256, unpacked_sha256=IMAGE_SHA256,
                              expanded_bytes=len(image), packets=packets,
                              entry_cs=header[1], entry_ip=header[0],
                              relocation_offsets=relocations, overlays=overlays)


def disassemble_script(raw: bytes, image: bytes) -> dict:
    if len(raw) < 9:
        raise ValueError("Truncated SCR header or missing terminator")
    classes, sizes = image[0x32c8e:0x32c8e + 17], image[0x32ca0:0x32ca0 + 17]
    cursor, instructions = 8, []
    while cursor < len(raw):
        opcode = raw[cursor]
        matches = [i for i, tag in enumerate(classes)
                   if (opcode if i < 8 else opcode & 0xfc if i < 10 else opcode & 0xf0) == tag]
        if len(matches) != 1:
            raise ValueError(f"Unrecognized/ambiguous SCR opcode: {opcode:02x}")
        length = sizes[matches[0]]
        operand = raw[cursor + 1:cursor + 1 + length]
        if len(operand) != length:
            raise ValueError("Truncated SCR operand")
        instruction = dict(offset=cursor, opcode=opcode, operand_hex=operand.hex())
        if opcode & 0xf0 == 0xc0:
            instruction["shape_range"] = list(struct.unpack("<HH", operand))
        instructions.append(instruction)
        cursor += length + 1
        if opcode == 0:
            if cursor != len(raw):
                raise ValueError("Trailing bytes after SCR terminator")
            return dict(bounds_words=list(struct.unpack_from("<4h", raw)), instructions=instructions)
    raise ValueError("Missing SCR terminator")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path, help="New evidence directory")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    with zipfile.ZipFile(args.source) as archive:
        image, report = unpack(archive.read("TheTreeh/treehse.exe"))
        scripts, sounds = [], []
        for info in archive.infolist():
            data = archive.read(info)
            if len(data) < 6:
                continue
            start, size = struct.unpack_from("<IH", data)
            if start < 6 or start + size != len(data):
                continue
            for resource in parse_archive(data):
                offset = resource["payload_offset"]
                raw = data[offset:offset + resource["size"]]
                identity = dict(archive=info.filename, id=resource["id"], sha256=resource["sha256"])
                if resource["tag"] == "SCR":
                    scripts.append(dict(**identity, **disassemble_script(raw, image)))
                elif resource["tag"] == "PSL":
                    if len(raw) < 2:
                        raise ValueError("Truncated PSL")
                    count = struct.unpack_from("<H", raw)[0]
                    if len(raw) != 2 + count * 2:
                        raise ValueError("PSL length mismatch")
                    sounds.append(dict(**identity, sound_ids=list(struct.unpack_from(f"<{count}H", raw, 2))))
    (args.output / "unpacked.bin").write_bytes(image)
    for name, value in (("executable.json", report), ("scripts.json", scripts), ("sound-lists.json", sounds)):
        (args.output / name).write_text(json.dumps(value, indent=2), encoding="utf-8")
    print(f"Unpacked {len(image)} bytes; {len(scripts)} scripts and {len(sounds)} sound lists parsed exactly")


if __name__ == "__main__":
    main()
