"""Decode original DOS Treehouse SHAP images and SHPL palettes.

Format references and independent native comparison: see
testing/treehouse_graphics_research.md and treehouse_resource_research.md.
All compressed input must be consumed; truncation and output overflow fail.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct

from PIL import Image


def decode_shape(data: bytes) -> tuple[int, int, bytes]:
    if len(data) < 6:
        raise ValueError("Truncated SHAP header")
    height, width, flags = struct.unpack_from("<HHH", data)
    depth = ((flags >> 12) & 7) + 1
    method = (flags >> 8) & 15
    if not width or not height or depth not in (1, 2, 4, 8) or flags & 0xff:
        raise ValueError(f"Unsupported SHAP header: {width}x{height}, {flags:04x}")
    stride = (width * depth + 7) // 8
    expected = height * stride
    if expected > 16 * 1024 * 1024:
        raise ValueError("SHAP dimensions exceed decoder limit")
    cursor = 6
    unpacked = bytearray()

    def take(n: int) -> bytes:
        nonlocal cursor
        if cursor + n > len(data):
            raise ValueError("Truncated SHAP compressed stream")
        result = data[cursor:cursor + n]
        cursor += n
        return result

    if method == 0:
        unpacked.extend(take(expected))
    elif method in (1, 2):
        while len(unpacked) < expected:
            code = take(1)[0]
            run = take(code + 1) if code < 128 else take(1) * (256 - code)
            unpacked.extend(run)
    elif method in (3, 4):
        history = bytearray(1024)
        write = 958
        while len(unpacked) < expected:
            control = take(1)[0]
            for bit in range(8):
                if len(unpacked) >= expected:
                    break
                if control & (1 << bit):
                    value = take(1)[0]
                    unpacked.append(value)
                    history[write] = value
                    write = (write + 1) & 1023
                else:
                    token = int.from_bytes(take(2), "big")
                    start, length = token & 1023, (token >> 10) + 3
                    for _ in range(length):
                        value = history[start]
                        start = (start + 1) & 1023
                        unpacked.append(value)
                        history[write] = value
                        write = (write + 1) & 1023
    else:
        raise ValueError(f"Unsupported SHAP compression: {method}")
    if len(unpacked) != expected or cursor != len(data):
        raise ValueError(f"SHAP size mismatch: decoded {len(unpacked)}/{expected}, read {cursor}/{len(data)}")
    if method in (2, 4):
        unpacked = bytearray(unpacked[x * height + y] for y in range(height) for x in range(stride))
    mask = (1 << depth) - 1
    pixels = bytes((unpacked[y * stride + x * depth // 8] >> (8 - depth - x * depth % 8)) & mask
                   for y in range(height) for x in range(width))
    return width, height, pixels


def decode_palette(data: bytes) -> list[tuple[int, int, int]]:
    if len(data) < 7:
        raise ValueError("Truncated SHPL header")
    count = data[6]
    raw = data[7:7 + count * 3]
    if not count or len(raw) != count * 3 or any(v > 63 for v in raw):
        raise ValueError("Invalid 6-bit SHPL palette")
    rgb = [(v << 2) | (v >> 4) for v in raw]
    return [tuple(rgb[i:i + 3]) for i in range(0, len(rgb), 3)]


def render(shape: bytes, palette: bytes) -> Image.Image:
    width, height, pixels = decode_shape(shape)
    colors = decode_palette(palette)
    if max(pixels) >= len(colors):
        raise ValueError("Selected palette does not cover image indices")
    rgb = bytes(channel for pixel in pixels for channel in colors[pixel])
    return Image.frombytes("RGB", (width, height), rgb)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("output", type=Path, help="New directory for decoded index images")
    parser.add_argument("--archive", help="Only this original archive basename")
    parser.add_argument("--shape", type=int, help="Only this resource ID")
    parser.add_argument("--palette", type=int, help="Explicit SHPL ID in selected archive; no guessed mapping")
    args = parser.parse_args()
    if args.palette is not None and not args.archive:
        parser.error("--palette requires --archive")
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    args.output.mkdir(parents=True, exist_ok=False)
    report = []
    for file in manifest["files"]:
        if args.archive and Path(file["path"]).name.lower() != args.archive.lower():
            continue
        resources = file.get("resources", [])

        def payload(entry: dict) -> bytes:
            data = (args.manifest.parent / entry["extracted_file"]).read_bytes()
            if hashlib.sha256(data).hexdigest() != entry["sha256"]:
                raise ValueError("Extracted resource hash mismatch")
            return data

        palette = next((payload(r) for r in resources if r["tag"] == "SHPL" and r["id"] == args.palette), None)
        if args.palette is not None and palette is None:
            raise ValueError("Requested palette is missing")
        for resource in resources:
            if resource["tag"] != "SHAP" or (args.shape is not None and resource["id"] != args.shape):
                continue
            data = payload(resource)
            width, height, pixels = decode_shape(data)
            name = f"{len(report):04d}-{resource['id']:05d}.png"
            image = render(data, palette) if palette is not None else Image.frombytes("L", (width, height), pixels)
            image.save(args.output / name)
            report.append(dict(archive=file["path"], id=resource["id"], width=width, height=height,
                               indices_sha256=hashlib.sha256(pixels).hexdigest(), file=name,
                               palette_id=args.palette, presentation="RGB" if palette is not None else "raw indices"))
    if not report:
        raise ValueError("No matching SHAP resources")
    (args.output / "images.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Decoded {len(report)} original SHAP resources with exact input/output lengths")


if __name__ == "__main__":
    main()
