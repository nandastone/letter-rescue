"""Run a verifier and bind its result to unchanged Godot source and export files.

Component scope remains component evidence even when it shares build inputs.
Native journey, timing and waveform scope requires the verifier to identify the
actual Web export it exercised; it cannot be inferred from a headless test.
"""
import argparse
import json
from pathlib import Path
import subprocess
import time

from godot_completion import ROOT, fingerprint, reference, sha, sources, successful, web_files


def run(build_path, output, result_path, scope, verifiers, claims, command):
    if result_path.exists():
        raise ValueError('Result already exists; choose a fresh evidence destination')
    if not verifiers:
        raise ValueError('Specify the verifier and its test scripts')
    output.mkdir(parents=True,exist_ok=False)
    build=json.loads(build_path.read_text(encoding='utf-8'))
    before=sources()
    files=web_files(ROOT/build['web_directory'])
    assert successful(build) and before==build['source_files'] and files==build['web_files']
    tool_files={p.resolve().relative_to(ROOT).as_posix():sha(p) for p in verifiers}
    start=time.monotonic()
    process=subprocess.run(command,capture_output=True,text=True,encoding='utf-8',timeout=900)
    log=process.stdout+process.stderr
    (output/'run.log').write_text(log,encoding='utf-8')
    after=sources()
    result=json.loads(result_path.read_text(encoding='utf-8')) if result_path.exists() else {}
    same_tools=all(sha(ROOT/name)==digest for name,digest in tool_files.items())
    same_build=before==after and files==web_files(ROOT/build['web_directory'])
    passed=process.returncode==0 and 'SCRIPT ERROR' not in log and successful(result) and same_tools and same_build
    if scope in ('web','native_journey','strict_timing','native_audio'):
        passed=passed and result.get('web_files',result.get('files'))==files
    envelope=dict(schema=1,passed=passed,scope=scope,claims=claims,
                  result=reference(result_path) if result_path.exists() else None,
                  build_sha256=fingerprint(files),source_sha256=fingerprint(before),
                  verifier_files=tool_files,source_unchanged=before==after,
                  execution=dict(command=command,exit_code=process.returncode,seconds=time.monotonic()-start))
    (output/'evidence.json').write_text(json.dumps(envelope,indent=2),encoding='utf-8')
    print(json.dumps(dict(passed=passed,result=str(result_path),scope=scope)))
    return passed


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('build','output','result'):
        parser.add_argument('--'+name,type=Path,required=True)
    parser.add_argument('--scope',choices=['component','web','native_journey','strict_timing','native_audio','desktop'],required=True)
    parser.add_argument('--verifier',type=Path,action='append',required=True)
    parser.add_argument('--claim',action='append',default=[])
    parser.add_argument('command',nargs=argparse.REMAINDER)
    args=parser.parse_args();command=args.command[1:] if args.command[:1]==['--'] else args.command
    if not command:parser.error('Provide a verifier command after --')
    raise SystemExit(0 if run(args.build,args.output,args.result,args.scope,args.verifier,args.claim,command) else 1)
