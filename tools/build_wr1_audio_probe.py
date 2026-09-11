"""Build an observation-only PCM tap without replacing the reference core.

Temporarily adds a host-output observer, builds a separately named DLL, then
restores the source byte-for-byte. No guest memory/instructions are changed.
"""
import argparse
import hashlib
import os
from pathlib import Path
import subprocess

TAP = '''
        // Read-only tap of the exact stereo int16 buffer submitted to RetroArch.
        static FILE* wr1_audio_output = []() -> FILE* {
            const char* path = std::getenv("DBP_WR1_AUDIO_FILE");
            return path ? std::fopen(path, "wb") : NULL;
        }();
        if (wr1_audio_output) {
            static bool header_written = false;
            if (!header_written) {
                uint32_t rate = (uint32_t)av_info.timing.sample_rate;
                std::fwrite(&rate, 4, 1, wr1_audio_output);
                header_written = true;
            }
            std::fwrite(dbp_audio[dbp_audio_active].audio, 4, mixSamples, wr1_audio_output);
            std::fflush(wr1_audio_output);
        }
'''

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=Path('testing/output/dosbox-pure-trace'))
    parser.add_argument('--toolchain', type=Path, default=Path('testing/output/w64devkit/bin'))
    args = parser.parse_args()
    cpp = args.source/'dosbox_pure_libretro.cpp'
    original = cpp.read_bytes()
    reference = args.source/'dosbox_pure_libretro.dll'
    before = hashlib.sha256(reference.read_bytes()).hexdigest()
    text = original.decode().replace('\r\n', '\n')
    old = '\tif (mixSamples)\n\t\taudio_batch_cb(dbp_audio[dbp_audio_active].audio, mixSamples);'
    if text.count(old) != 1:
        raise ValueError('Unknown native audio submission code')
    text = text.replace(old, '\tif (mixSamples) {\n'+TAP+
                        '\t\taudio_batch_cb(dbp_audio[dbp_audio_active].audio, mixSamples);\n\t}')
    environment = dict(os.environ, PATH=str(args.toolchain.resolve())+os.pathsep+os.environ.get('PATH', ''))
    try:
        cpp.write_text(text)
        subprocess.run([str((args.toolchain/'make.exe').resolve()), '-j4',
                        'SHELL=cmd.exe', 'CXX=g++', 'STRIP=strip',
                        'OUTNAME=dosbox_pure_audio_probe.dll'], cwd=args.source,
                       env=environment, check=True)
    finally:
        cpp.write_bytes(original)
    assert hashlib.sha256(reference.read_bytes()).hexdigest() == before
    print('Reference core unchanged:', before)
