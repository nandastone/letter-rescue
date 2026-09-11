"""Build an offline renderer from the pinned DOSBox Pure speaker kernel.

Only the mixer/clock adapters are substituted. The PIT and speaker slew code
execute unchanged; no emulator code is linked into the game.
"""
import argparse
import hashlib
import os
from pathlib import Path
import subprocess


def build(source, compiler, output):
    source = source / 'src/hardware/pcspeaker.cpp'
    text = source.read_text()
    if hashlib.sha256(source.read_bytes()).hexdigest() != '45bd8db3a4d25380417b687a11fa0c4b4d96c48be3edcfa40925335e0c362708':
        raise ValueError('Unsupported speaker kernel; verify a source update explicitly')
    kernel = text[text.index('#ifndef PI'):text.index('class PCSPEAKER:')]
    adapter = Path('tools/wr1_speaker_render.cpp').read_text()
    generated = output.with_suffix('.cpp')
    generated.parent.mkdir(parents=True, exist_ok=True)
    generated.write_text(adapter.replace('// ORIGINAL_SPEAKER_KERNEL', kernel))
    environment = dict(os.environ, PATH=str(compiler.resolve().parent)+os.pathsep+os.environ.get('PATH', ''))
    subprocess.run([str(compiler), '-std=c++11', '-O2', str(generated), '-o', str(output)],
                   check=True, env=environment)
    print('Speaker kernel SHA256:', hashlib.sha256(source.read_bytes()).hexdigest())


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=Path('testing/output/dosbox-pure-trace'))
    parser.add_argument('--compiler', type=Path, default=Path('testing/output/w64devkit/bin/g++.exe'))
    parser.add_argument('--output', type=Path, default=Path('testing/output/wr1_speaker_render.exe'))
    args = parser.parse_args()
    build(args.source, args.compiler, args.output)
