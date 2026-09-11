"""Build the offline audio tool against the existing DOSBox Pure source checkout."""
import argparse
import os
from pathlib import Path
import subprocess


if __name__=='__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,default=Path('testing/output/dosbox-pure-trace'))
    parser.add_argument('--compiler',type=Path,default=Path('testing/output/w64devkit/bin/g++.exe'))
    parser.add_argument('--output',type=Path,default=Path('testing/output/wr1_opl_render.exe'))
    args = parser.parse_args()
    environment = dict(os.environ,PATH=str(args.compiler.resolve().parent)+os.pathsep+os.environ.get('PATH',''))
    subprocess.run([str(args.compiler),'-std=c++11','-O2','-ffunction-sections','-fdata-sections',
                    '-Wl,--gc-sections','-D__LIBRETRO__','-I'+str(args.source/'include'),
                    '-I'+str(args.source/'src/hardware'),'tools/wr1_opl_render.cpp',
                    str(args.source/'src/hardware/dbopl.cpp'),'-o',str(args.output)],check=True,env=environment)
