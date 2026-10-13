"""Export Godot and bind the immutable Web files to their source inventory."""
import argparse
import json
from pathlib import Path
import subprocess

from godot_completion import ROOT, fingerprint, sha, sources, web_files


def build(engine, output):
    output.mkdir(parents=True, exist_ok=False)
    web = output / 'web'
    web.mkdir()
    before = sources()
    command = [str(engine.resolve()), '--headless', '--path', str(ROOT/'treehouse-godot'),
               '--export-release', 'Web', str((web/'index.html').resolve())]
    process = subprocess.run(command, capture_output=True, text=True, encoding='utf-8', timeout=240)
    (output/'export.log').write_text(process.stdout+process.stderr, encoding='utf-8')
    after = sources()
    files = web_files(web)
    passed = process.returncode == 0 and 'ERROR' not in process.stdout+process.stderr and before == after
    passed = passed and {'index.html','index.pck','index.wasm','index.js'} <= files.keys()
    report = dict(schema=1, runtime='Godot', passed=passed, command=command, exit_code=process.returncode,
                  engine_sha256=sha(engine), web_directory=web.resolve().relative_to(ROOT).as_posix(),
                  web_files=files, build_sha256=fingerprint(files), source_files=before,
                  source_sha256=fingerprint(before), source_unchanged=before==after)
    (output/'build.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(dict(passed=passed,build_sha256=report['build_sha256'],pck_sha256=files.get('index.pck'))))
    return passed


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--godot',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    raise SystemExit(0 if build(args.godot,args.output.resolve()) else 1)
