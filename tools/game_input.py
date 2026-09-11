"""Send a bounded physical-key hold to an already selected, foreground game.

Usage: python tools/game_input.py <observed-window-id> right+up --hold-ms 250
Select/activate the window with computer-use first; this script never picks one.
Dependency: PyDirectInput==1.0.4 (see requirements-desktop-input.txt).
"""

import argparse
import ctypes
from pathlib import Path
import sys
import time


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("hwnd", type=int, help="Current window id returned by computer-use")
    parser.add_argument("keys", help="One key, or simultaneous keys joined with +")
    parser.add_argument("--hold-ms", type=int, default=120)
    args = parser.parse_args()
    if sys.platform != "win32":
        parser.error("This input sender requires Windows")
    if not 20 <= args.hold_ms <= 2000:
        parser.error("Hold duration must be between 20 and 2000 ms")

    # Optional project-local installation used by the desktop research session.
    local_packages = Path(__file__).resolve().parents[1] / "testing/output/python_packages"
    if local_packages.is_dir():
        sys.path.insert(0, str(local_packages))
    try:
        import pydirectinput
    except ImportError:
        parser.error("Install dependencies with: python -m pip install -r tools/requirements-desktop-input.txt")

    keys = args.keys.lower().split("+")
    if len(keys) > 3 or len(set(keys)) != len(keys):
        parser.error("Use one to three distinct keys")
    if any(key not in pydirectinput.KEYBOARD_MAPPING for key in keys):
        parser.error("Unrecognized key; examples: right, up, space, enter, scrolllock")

    user32 = ctypes.windll.user32
    user32.GetForegroundWindow.restype = ctypes.c_void_p
    user32.GetWindowTextW.argtypes = [ctypes.c_void_p, ctypes.c_wchar_p, ctypes.c_int]
    if user32.GetForegroundWindow() != args.hwnd:
        parser.error("Target is not the foreground window; no keys sent")
    title = ctypes.create_unicode_buffer(512)
    user32.GetWindowTextW(args.hwnd, title, len(title))
    if not title.value.startswith(("Desktop Input Probe", "Letter Rescue", "RetroArch")):
        parser.error("Target is not a supported game/probe window; no keys sent")

    pydirectinput.PAUSE = 0
    attempted = []
    try:
        for key in keys:
            if user32.GetForegroundWindow() != args.hwnd:
                raise RuntimeError("Focus changed; aborting input")
            attempted.append(key)
            if not pydirectinput.keyDown(key):
                raise RuntimeError("Key-down injection failed")
        deadline = time.monotonic() + args.hold_ms / 1000
        while time.monotonic() < deadline:
            if user32.GetForegroundWindow() != args.hwnd:
                raise RuntimeError("Focus changed during hold; releasing keys")
            time.sleep(min(0.02, max(0, deadline - time.monotonic())))
    finally:
        # Cleanup must release even if the pointer moved to the failsafe corner.
        previous_failsafe = pydirectinput.FAILSAFE
        pydirectinput.FAILSAFE = False
        try:
            for key in reversed(attempted):
                pydirectinput.keyUp(key)
        finally:
            pydirectinput.FAILSAFE = previous_failsafe
    print(f"{title.value}: held {args.keys} for {args.hold_ms} ms; released")


if __name__ == "__main__":
    main()
