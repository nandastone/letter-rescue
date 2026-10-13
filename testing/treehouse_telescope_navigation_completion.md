# Telescope navigation: exact pre-click native references

Primary-source capture follow-up,2026-09-27. No runtime changes or DOS RAM mutation.

Evidence folder: `testing/output/treehouse/research-telescope-navigation/`. Capture driver: `research-telescope-navigation-capture.py`. It restores the ordinary room entry state, moves the pointer for30callbacks, saves PNG/RAM/emulator state **after the movement**, then presses left5callbacks and releases650callbacks. The sequence enters and returns twice, without restoring between visits. Initial state SHA256 `9eea3d004a365f901fc653e633fd497b9024256fd646b93d4c649839e4e4d391`.

|Saved state stem in state/|Native run|Original tick|Pose|Action immediately following|
|---|---:|---:|---:|---|
|visit-0-before-click|1829|2588|0|Click telescope(199,122), source action19 selects20519|
|visit-0-view|2484|3150|3|First chosen view is robot prize shelf|
|visit-0-before-return|2514|3174|3|Click exit(313,12), redraw room then20528|
|visit-0-returned|3169|3736|1|Room idle after completed return|
|visit-1-before-click|3199|3761|1|Click telescope(199,122), source action19 selects20719|
|visit-1-view|3854|4322|3|Second view is planets|
|visit-1-before-return|3884|4347|3|Click exit(313,12), redraw room then20528|
|visit-1-returned|4539|4908|1|Room idle after completed return|

Each stem has `.png`, `.state`, `.ram-0` and the companion low-memory `.ram-100000`. `driver.json` contains every sampled callback’s pose, all original object records, pointer, frame counter, telescope mask and audio-active status. `frames.jsonl` links all runs to native image files and PITticks. No pre-click frame needs to be inferred from a much earlier room state.

## Balloon scheduling

The initial restored balloon was `(43,96,81,125)`. During the first30-callback pointer movement it advances to `(44,98,82,127)`, next due2634. **This is already the rectangle in visit-0-before-click.** It does not move during20519, the following60-tick pause, or the telescope view. This explains comparisons seeded from the earlier entry state failing outside the character region.

On room rebuild, the object’s position is preserved and its next deadline is reset. At native run2553/tick3208 the return action begins and pose becomes1; balloon still `(44,98,82,127)`,due3253. Its first actual movement is run2704/tick3337, after the10-display return finishes, to `(43,100,81,129)`,due3385. Normal idle movement then repeats roughly49ticks apart under strict `now>due` checks.

Second approach uses `(35,116,73,145)`,due3777 throughout20719 and the planet view. Return begins run3926/tick4383, position unchanged,due4428; first movement after return is run4078/tick4513 to `(34,118,72,147)`,due4561.

Source ownership: ordinary idle loopD8E calls8742; its in-room branch8773 calls89BD. The telescope handler141D invokes action19 synchronously, waits60, leaves the room and opens2534; return redraw1F24 then action28 remains synchronous. No8742/89BD idle servicing is performed in those character scripts. Generic419D invokes only its animation-specific4E9E callback hook while pumping the SCR; it does not call room idle. Room rebuildB95C resets object deadlines throughB8A3, which sets balloon due=now+48. Source and capture therefore agree that ordinary cursor-follow motion is paused during approach/return and only resumes at room idle.

Separate behavior: wrapper43AC/8CF4 can deliberately move a balloon away from an intersecting animation rectangle before the SCR starts (up by2pixels per2ticks for these character groups). Neither captured telescope precondition intersects its approach rectangle, so that clearance does not occur here. Do not conflate this source-backed collision-clearance precondition with idle cursor-follow movement.

Primary code references: `testing/output/treehouse/research-resources/main-disassembly.txt`,141D..1456,43AC..43DA,8742..8773,89BD..8B3C,B8A3,B95C. The existing telescope script mapping and timings are in `treehouse_room_completion_research.md` §5.
