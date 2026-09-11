# Desktop input research

Researched 2026-09-07. Scope: making interactive desktop play reliable before changing the replay harness or gameplay. This note separates external research, locally measured probe results, and proposed game experiments.

## Main finding

**Resolved locally:** desktop walking and combined run/jump now work in both the
Godot clone and Word Rescue in the existing RetroArch/DOSBox Pure setup, without
native input replay. The working combination is PyDirectInput scan-code holds plus
RetroArch **Game Focus on**. No emulator replacement was needed. The original
accepted a player name, menu selections, a 600 ms right hold (collecting a book),
and a 250 ms right+up chord (jumping and collecting another book). The clone also
responded to a 600 ms right hold and a 250 ms right+up chord.

Use [tools/game_input.py](../tools/game_input.py) for future interactive play:

1. Use computer-use to list windows, select exactly one game, activate it, and
   inspect its current screenshot. Pass that returned window ID to the helper.
2. Install dependencies if necessary:
   `python -m pip install -r tools/requirements-desktop-input.txt`.
   This session installed them locally under `testing/output/python_packages`,
   which the helper also recognizes.
3. Send one bounded action, e.g.
   `python tools/game_input.py <window-id> right+up --hold-ms 250`.
   Refresh the game screenshot before choosing the next action. Window IDs change
   when applications restart; do not reuse the example IDs from the session log.
4. For RetroArch, send `scrolllock` if Game Focus is off, and verify its on-screen
   **Game Focus on** notification. Windows foreground focus alone is insufficient.

The helper checks the selected foreground game, bounds holds to 20–2,000 ms,
supports simultaneous keys, aborts on focus changes, and releases attempted keys
in cleanup. Computer-use remains useful for observation and window selection;
the user explicitly requested trying an alternative input tool for this task.

The reusable helper was rechecked against the probe: its 120 ms Right hold produced
the correct physical Right key across nine physics ticks. A deliberately invalid
foreground window ID was rejected without adding any events to the probe log.
The diagnostic probe was then closed; both gameplay sessions remain available.

There are credible reasons to investigate the input path further. A successful desktop-tool call does not establish that an emulator received a usable key hold. Duration, physical-key representation, and RetroArch's keyboard routing are distinct variables. A brief key can reach an event handler while never remaining pressed during a game update.

The current tool contract, as supplied to this research task, exposes `press_key(window, key)` without separate key-down/key-up or duration. The implementation has not been inspected here. The parent agent's local probe has now measured event timing and key identities, as recorded below.

## Local probe evidence

The parent agent ran an independent Godot probe; this research agent read its [event log](output/desktop_input_probe/events.jsonl). Two tool-injected keys produced these results:

| Requested key | Logical keycode | Physical keycode | Logged down/up duration | Physics ticks held |
| --- | ---: | ---: | ---: | ---: |
| Right | 4194321 (Right) | 4194313 (Pause) | 1,335 microseconds | 0 |
| A | 65 (A) | 4194313 (Pause) | 414 microseconds | 0 |
| Right via PyDirectInput, requested 120 ms hold | 4194321 (Right) | 4194321 (Right) | 125,109 microseconds | 9 |

These establish that events reached this probe, with correct logical identity but incorrect physical identity and no sustained physics-frame hold in these two trials. The durations are the probe's logged processing intervals, not hardware-level timing measurements. They do not alone establish the complete RetroArch failure path.

The physical value `4194313` is Godot's `KEY_PAUSE`. Godot's Windows implementation extracts physical scan code from bits 16–23 of the keyboard message's `lParam`; its map explicitly associates scan code `0x00` with Pause. **Inference:** a zero/missing scan-code field is a particularly good explanation for both unrelated requested keys appearing as physical Pause. This is stronger than a generic keyboard-layout hypothesis, but the input sender's internals or Windows message trace would be needed to prove where the field became zero. [Godot key enum documentation](https://docs.godotengine.org/en/4.1/classes/class_%40globalscope.html), [Godot Windows event processing](https://raw.githubusercontent.com/godotengine/godot/master/platform/windows/display_server_windows.cpp), [Godot Windows scan-code map](https://raw.githubusercontent.com/godotengine/godot/master/platform/windows/key_mapping_windows.cpp).

**The alternative sender passed the probe and subsequent actual-game tests.** The parent agent used PyDirectInput with separate down/up and a requested 120 ms hold. The probe reported the correct physical Right key and nine physics ticks held. Later interactive tests succeeded in both games as described above. The initial experiment used [hold_key.py](output/desktop_input_probe/hold_key.py); the reusable version is [game_input.py](../tools/game_input.py).

## Verified mechanisms

**Very short presses can disappear from state polling.** SDL's official `SDL_GetKeyboardState` documentation explicitly states that a press and release processed together will not appear as pressed in the state array. RetroArch's current DirectInput implementation reads the keyboard through `IDirectInputDevice8_GetDeviceState` in `dinput_poll`. That is relevant evidence for testing duration, though it does not establish which driver/version the local RetroArch is using or prove all core keyboard events take this path. [SDL documentation](https://wiki.libsdl.org/SDL2/SDL_GetKeyboardState), [RetroArch DirectInput source](https://raw.githubusercontent.com/libretro/RetroArch/master/input/drivers/dinput.c).

**Godot distinguishes edges from held state.** `is_action_just_pressed()` can remain true for a frame/tick even when a press has already been released; `is_action_pressed()` reports the current held state. Therefore a probe should log raw input events, physical keycodes, mapped actions, and physics-frame held states separately. A successful jump edge would not prove sustained walking input works. [Godot Input documentation](https://docs.godotengine.org/en/stable/classes/class_input.html).

**Text injection is not equivalent to physical keyboard input.** Windows `KEYEVENTF_UNICODE` produces `VK_PACKET`, which is translated into text messages. `KEYEVENTF_SCANCODE` instead specifies a physical scan code, with an extended-key flag where appropriate. An emulator that needs key identity should be tested with key events rather than bulk text insertion. This does not show which method the present tool uses. [Microsoft KEYBDINPUT documentation](https://learn.microsoft.com/en-us/windows/win32/api/winuser/ns-winuser-keybdinput).

**Privilege mismatch can block injection.** Windows permits `SendInput` into processes at the same or lower integrity level. Its return value counts inserted events, and UIPI blocking is not distinctly identified by the error result. Checking integrity levels is justified if no events arrive; elevating everything is not a useful first experiment. [Microsoft SendInput documentation](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-sendinput).

**RetroArch Game Focus is separate from Windows foreground focus.** DOSBox Pure recommends Game Focus (normally Scroll Lock) for real keyboard play. It disables hotkeys and keyboard-to-RetroPad translation, which can otherwise capture keys or generate multiple emulated presses. The local configuration should explicitly establish this state, instead of repeatedly toggling it without verification. [DOSBox Pure project documentation](https://github.com/schellingb/dosbox-pure#playing-with-keyboard-and-mouse), [Libretro input guide](https://docs.libretro.com/guides/input-and-controls/).

## Similar firsthand reports

- A 2017 report on the official Libretro forum describes RetroArch ignoring AutoHotkey input even after administrator and windowed-mode experiments. The thread resolves the user's menu requirement through RetroArch's own controller hotkey combinations; it does **not** demonstrate a fix for synthetic keyboard input. This supports that the symptom is not unique, not a particular cause. [Original report](https://forums.libretro.com/t/getting-ra-to-play-nice-with-autohotkey-or-button-combinations/11482).
- A 2024 RetroArch user reports physical-key remappings working while automatic AHK actions are ignored. A 2020 report describes a script typing into Notepad but not registering in RetroArch. These are firsthand symptom reports surfaced by search; full Reddit pages failed to load during research, so their comments and claimed fixes are not relied on. [2024 report](https://www.reddit.com/r/RetroArch/comments/1hlncqt), [2020 report](https://www.reddit.com/r/RetroArch/comments/gf7m8e).
- I did not find a well-matched Godot engine issue proving the same synthetic-input failure. The local event/physics probe is stronger evidence than attributing this to Godot generally.

## Ranked practical experiments

1. **Measure the existing tool first.** In a standalone Godot probe, log focus changes, key-down/up timestamps, keycode/physical-keycode, action edges, and held state on each physics tick. Try individual letter, arrow, Enter, and Space presses. This distinguishes no delivery, incorrect key representation, and a delivered but too-short hold without editing gameplay.
2. **Try explicit native key holds.** Use a small local scan-code `SendInput` helper or PyDirectInput's documented `keyDown`/`keyUp`, with 100–250 ms holds and guaranteed release cleanup. Test one key, then right plus jump. PyDirectInput is specifically intended for games where virtual-key based automation fails; it still uses Windows `SendInput`, not a virtual hardware driver. If holds work, this becomes a small interactive controller used alongside screenshots, independent of native replay. [PyDirectInput project](https://github.com/learncodebygaming/pydirectinput).
3. **AutoHotkey is another practical native sender.** Its official documentation says some games require a delay between down and up. Use `SendEvent` and an explicit press duration, or separate down/up calls with a sleep. `SetKeyDelay` does not affect the default `SendInput` mode, so merely adding that setting can misleadingly change nothing. Start with ordinary foreground activation and same integrity level. [Official AutoHotkey documentation source](https://raw.githubusercontent.com/AutoHotkey/AutoHotkeyDocs/v2/docs/lib/SetKeyDelay.htm).
4. **Isolate RetroArch routing and driver effects.** Establish Game Focus first. If native holds reach Godot but not RetroArch, compare temporary configurations using `dinput` and `raw`, restarting between runs and recording the actual selected driver. Libretro lists both Windows drivers and conditions on SDL video drivers. A driver change is an experiment, not a known synthetic-input cure. [Libretro driver documentation](https://docs.libretro.com/guides/input-controller-drivers/).
5. **Try standalone DOSBox-X with the same game files and sender.** This removes RetroArch's hotkey and RetroPad layers. DOSBox-X documents that SDL handles its input and that SDL1/SDL2 have different keyboard-layout handling. Prefer an SDL2 build for this comparison, but do not presume it cures press duration or scan-code issues. [DOSBox-X keyboard documentation](https://dosbox-x.com/wiki/Guide%3ARegional-settings-in-DOSBox%E2%80%90X).
6. **Browser-hosted js-dos is a real fallback.** Its documented Command Interface supplies `sendKeyEvent(keyCode, pressed)`, explicit screenshot, pause and resume functions; its player supports DOSBox and DOSBox-X backends. A local control page can expose a bounded hold action, making sustained input reviewable through browser controls. Verify the active browser tool's supported key-down/up or page-interaction APIs rather than assuming normal Playwright APIs are callable. Browser hosting changes the execution environment, so it suits exploratory play; timing equivalence to the current native setup would need separate validation. [js-dos Command Interface](https://js-dos.com/command-interface.html), [js-dos Player API](https://js-dos.com/player-api.html).

The fastest discriminating result is whether the existing sender delivers down and up to the probe but produces zero physics ticks with a held key. If so, explicit holds deserve priority over changing emulators. If no events arrive, focus, privilege, and event representation deserve priority instead.
