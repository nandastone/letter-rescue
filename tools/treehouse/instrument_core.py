"""Add deterministic capture boundaries to a pinned DOSBox Pure checkout.

Only changes frontend scheduling: complete the pending emulated frame before
polling input, and submit audio/video while the emulation worker is held.
Game binaries and emulated CPU/PIT/video implementations remain untouched.
"""
import argparse
import hashlib
from pathlib import Path
import subprocess

COMMIT = "db325ff427e3d0df2e6c38bc75b00b6771e03b38"


def instrument_frontend(code):
    old = "\t// start input update\n\tinput_poll_cb();"
    new = ("\t// Treehouse evidence: inputs belong to a completed frame boundary.\n"
           "\tif (dbp_state == DBPSTATE_RUNNING || dbp_state == DBPSTATE_FIRST_FRAME)\n"
           "\t\tDBP_ThreadControl(TCM_FINISH_FRAME);\n" + old)
    if code.count(old) != 1:
        raise ValueError("Input hook does not match pinned source")
    code = code.replace(old, new)
    skip = "bool skip_emulate = (fpsboost > 1 && (((fpsboost_count++)%fpsboost)!=0)) || DBP_NeedFrameSkip(false);"
    render_skip = "render.frameskip.max = DBP_NeedFrameSkip(true);"
    if code.count(skip) != 1 or code.count(render_skip) != 1:
        raise ValueError("Frame-skip hooks do not match pinned source")
    code = code.replace(skip, "bool skip_emulate = false; // Capture every emulated frame.")
    code = code.replace(render_skip, "render.frameskip.max = 0; // Never drop capture frames.")
    resume = "\tDBP_ThreadControl(skip_emulate ? TCM_RESUME_FRAME : TCM_NEXT_FRAME);"
    if code.count(resume) != 1:
        raise ValueError("Resume hook does not match pinned source")
    code = code.replace(resume, "\t// Worker remains held through the frontend callbacks.")
    end = "\n}\n\nstatic bool retro_serialize_all(DBPArchive& ar, bool unlock_thread)"
    replacement = ("\n" + resume + "\n}\n\n"
                   'extern "C" RETRO_API unsigned retro_treehouse_capture_version(void) { return 1; }\n'
                   "\nstatic bool retro_serialize_all(DBPArchive& ar, bool unlock_thread)")
    if code.count(end) != 1:
        raise ValueError("End-of-frame hook does not match pinned source")
    code = code.replace(end, replacement)
    return code


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("checkout", type=Path)
    args = parser.parse_args()
    revision = subprocess.check_output(["git", "-C", str(args.checkout), "rev-parse", "HEAD"], text=True).strip()
    if revision != COMMIT:
        raise ValueError("Unresearched DOSBox Pure revision")
    target = args.checkout / "dosbox_pure_libretro.cpp"
    original = subprocess.check_output(["git", "-C", str(args.checkout), "show", "HEAD:dosbox_pure_libretro.cpp"])
    if target.read_bytes().replace(b"\r\n", b"\n") != original.replace(b"\r\n", b"\n"):
        raise ValueError("Core source already modified; use a fresh checkout")
    code = original.decode()
    code = instrument_frontend(code)
    target.write_bytes(code.encode())
    makefile = args.checkout / "Makefile"
    make_source = makefile.read_text(encoding="utf-8")
    # GNU make on Windows passes the nested recipe's '@' through to sh.
    old_compile = "\t@$(CXX) $(CFLAGS) -MMD -MP -o $1 -c $2"
    if make_source.count(old_compile) != 1:
        raise ValueError("Compiler recipe does not match pinned source")
    makefile.write_text(make_source.replace(old_compile, old_compile.replace("@", "", 1)), encoding="utf-8")
    print("Pinned source", COMMIT, "instrumented SHA256", hashlib.sha256(code.encode()).hexdigest())


if __name__ == "__main__":
    main()
