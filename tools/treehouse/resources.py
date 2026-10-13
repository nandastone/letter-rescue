"""Inspect/extract the DOS Treehouse resources without executing game code.

Container layout independently implemented from ScummVM DOSArchive_v2 and
checked against Treehouse v1.1. Checksums are verified for every resource.
Unknown flags and payloads remain opaque; extraction is not a game port.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import struct
import zipfile


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def parse_archive(data: bytes) -> list[dict]:
    if len(data) < 8:
        raise ValueError("Truncated archive header")
    directory, size = struct.unpack_from("<IH", data)
    if directory < 6 or size < 2 or directory + size != len(data):
        raise ValueError("Invalid directory bounds")
    count = struct.unpack_from("<H", data, directory)[0]
    tables_end = directory + 2 + count * 6
    if tables_end > len(data):
        raise ValueError("Truncated type table")
    resources, identities = [], set()
    for i in range(count):
        entry = directory + 2 + i * 6
        tag, relative = struct.unpack_from("<IH", data, entry)
        table = directory + relative
        if table < tables_end or table + 2 > len(data):
            raise ValueError("Resource table outside directory")
        n = struct.unpack_from("<H", data, table)[0]
        if table + 2 + n * 11 > len(data):
            raise ValueError("Truncated resource table")
        tag_bytes = tag.to_bytes(4, "big")
        tag_name = tag_bytes.strip(b"\0").decode("ascii", errors="backslashreplace")
        for j in range(n):
            pos = table + 2 + j * 11
            resource_id, start, length = struct.unpack_from("<HIH", data, pos)
            end = start + 1 + length
            if start < 6 or end > directory:
                raise ValueError(f"Payload outside data region: {tag_name}:{resource_id}")
            if (tag, resource_id) in identities:
                raise ValueError(f"Duplicate resource: {tag_name}:{resource_id}")
            identities.add((tag, resource_id))
            payload = data[start + 1:end]
            if sum(data[start:end]) & 0xff != 0xff:
                raise ValueError(f"Checksum mismatch: {tag_name}:{resource_id}")
            record = dict(tag=tag_name, tag_hex=f"{tag:08x}", id=resource_id,
                          directory_entry_offset=pos, checksum_offset=start,
                          payload_offset=start + 1, size=length,
                          checksum=data[start], flags_hex=data[pos + 8:pos + 11].hex(),
                          sha256=sha256(payload))
            if tag_name == "STRL" and payload:
                parts = payload[1:].split(b"\0")
                record["declared_string_count"] = payload[0]
                record["string_layout_matches_count"] = len(parts) == payload[0] + 1 and parts[-1] == b""
                record["strings"] = [dict(bytes_hex=p.hex(), cp437=p.decode("cp437"))
                                     for p in parts[:-1]]
                record["unterminated_tail_hex"] = parts[-1].hex()
            resources.append(record)
    return resources


def inspect_source(source: Path, output: Path, extract: bool) -> dict:
    # Refuse to mix new evidence with a previous run.
    output.mkdir(parents=True, exist_ok=False)
    if source.is_file() and zipfile.is_zipfile(source):
        with zipfile.ZipFile(source) as archive:
            members = [(i.filename, archive.read(i)) for i in archive.infolist() if not i.is_dir()]
        source_hash = sha256(source.read_bytes())
    elif source.is_dir():
        members = [(p.relative_to(source).as_posix(), p.read_bytes())
                   for p in sorted(source.rglob("*")) if p.is_file()]
        source_hash = None
    else:
        raise ValueError("Source must be a ZIP or installed directory")
    records, all_text = [], []
    for name, data in sorted(members):
        record = dict(path=name, size=len(data), sha256=sha256(data), header_hex=data[:32].hex())
        if len(data) >= 6:
            offset, size = struct.unpack_from("<IH", data)
            # Header match identifies candidates; malformed candidates fail loudly.
            if offset >= 6 and offset + size == len(data):
                resources = parse_archive(data)
                record.update(format="DOSArchive_v2", directory_offset=offset,
                              directory_size=size, resources=resources,
                              counts=dict(sorted(Counter(r["tag"] for r in resources).items())))
                for resource in resources:
                    if "strings" in resource:
                        all_text.append(dict(archive=name, **resource))
                    if extract:
                        # Names never come from archive paths or resource text.
                        folder = output / "resources" / f"{len(records):02d}"
                        folder.mkdir(parents=True, exist_ok=True)
                        target = folder / f"{resource['tag_hex']}-{resource['id']:05d}.bin"
                        start = resource["payload_offset"]
                        target.write_bytes(data[start:start + resource["size"]])
                        resource["extracted_file"] = target.relative_to(output).as_posix()
        records.append(record)
    manifest = dict(schema=1, source=str(source.resolve()), source_sha256=source_hash,
                    string_preview_encoding="CP437 (provisional; exact bytes retained)", files=records,
                    archive_count=sum("resources" in r for r in records),
                    resource_count=sum(len(r.get("resources", [])) for r in records))
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    (output / "strings.json").write_text(json.dumps(all_text, indent=2, ensure_ascii=False), encoding="utf-8")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path, help="New evidence directory (must not exist)")
    parser.add_argument("--extract", action="store_true")
    args = parser.parse_args()
    result = inspect_source(args.source, args.output, args.extract)
    print(f"{len(result['files'])} files; {result['archive_count']} archives; "
          f"{result['resource_count']} resources; all resource checksums verified")


if __name__ == "__main__":
    main()
