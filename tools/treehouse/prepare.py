"""Create a reproducible DOSBox Pure launch ZIP while preserving original bytes."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import zipfile

CONFIG = """[cpu]
core=normal
cycles=fixed 10000
[autoexec]
@echo off
c:
cd TheTreeh
date 01-01-1992
time 12:00:00
treehse.exe
"""


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="Unmodified DOS v1.1 preservation ZIP")
    parser.add_argument("output", type=Path, help="New derived ZIP")
    parser.add_argument("--program", choices=("treehse.exe", "setup.exe"), default="treehse.exe")
    args = parser.parse_args()
    if args.output.exists() or args.output.with_suffix(".json").exists():
        parser.error("Output evidence already exists")
    with zipfile.ZipFile(args.source) as source:
        names = [i.filename for i in source.infolist()]
        if len(names) != len(set(names)):
            raise ValueError("Duplicate ZIP members")
        if "TheTreeh/treehse.exe" not in names:
            raise ValueError("Expected TheTreeh/treehse.exe; inspect another layout before adapting")
        if any(n.lower().endswith("dosbox.conf") for n in names):
            raise ValueError("Source already contains DOSBox configuration")
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(args.output, "x", zipfile.ZIP_DEFLATED) as target:
            for entry in source.infolist():
                target.writestr(entry, source.read(entry))
            # Fixed ZIP metadata ensures identical launch archives across runs.
            entry = zipfile.ZipInfo("dosbox.conf", date_time=(1992, 1, 1, 0, 0, 0))
            entry.compress_type = zipfile.ZIP_DEFLATED
            config = CONFIG.replace("treehse.exe\n", args.program + "\n")
            target.writestr(entry, config)
    report = dict(source_sha256=hashlib.sha256(args.source.read_bytes()).hexdigest(),
                  output_sha256=hashlib.sha256(args.output.read_bytes()).hexdigest(),
                  added_file="dosbox.conf", config=config, original_members_unchanged=True)
    args.output.with_suffix(".json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(args.output)


if __name__ == "__main__":
    main()
