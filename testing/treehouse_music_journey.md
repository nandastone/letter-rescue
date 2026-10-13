# Complete music editing and interchange journeys

## Ordinary browser session

`verify_music_journey.py` starts with normal character selection and uses visible
controls and actual keyboard notes throughout. It authors and names both books,
replaces and erases notes, enters a rest and a second-staff note, plays both
compositions at all five speeds, exercises repeat/stop and contents, declines
erase, and copies an original song into each book's first free page.

It then downloads SONGS.DAT, reloads the browser, erases a song, restores the
download through the file chooser, rejects an invalid import without changing
the books, and downloads again. Both 8,688-byte exports are identical. The test
observes actual pitch dispatch while retaining its normal audio implementation;
it does not install gameplay state. `music-journey-h` passes all 30 assertions.

Early runs `music-journey-a` through `-g` exposed a driver ambiguity, not an app
defect: this installed Python Playwright adapter converts `value=` into
`valueOrLabel`. Requesting value "1" matched the first option's one-based label
"1", rather than the second slot's zero-based value. The helper now passes the
exact option element. Requested and returned selections remain in the report.
No application code changed in response to those failures.

## Paired original journey

`capture_music_journey.py` restores a blank personal short book once and drives
ordinary clicks, held drags and typing. It writes two notes, moves the marker,
replaces a pitch, drags another pitch, names the song, plays it, creates and plays
a long-book phrase with a rest, revisits both books, declines erase, switches to
listening, copies the original song, and returns to both authored compositions.

The original processes Enter as pointer activation after title acceptance. With
the pointer still over the title, the ten-frame press reopens a blank title
field. The early `music-native-journey-a/b` captures stop at this failed title
assertion. The final route moves the pointer to blank canvas before pressing
Enter, using normal input; it then completes title acceptance. The additional
`music-keyboard-probe-a` confirms that letter input itself is working. No game
RAM or emulation code is patched.

`music-native-journey-c` and `-d` repeat all 22 checkpoint states and PNGs, the
complete callback timeline and recorded audio exactly. The result is preserved
in `music-native-journey-repeat.json`.

## Browser comparison and fixture corrections

`verify_music_native_journey.py` installs one initial music snapshot and replays
the original inputs. `music-native-check-b` matches all 22 full-RGB checkpoints
and checked active song/title/marker/random state. There are no later resets.

The earlier `music-native-check-a` used an unrelated countdown for idle eyes and
derived the listening instrument from a stock resource header. It also compared
the stale personal-title buffer while listening. These produced false mismatches.
The corrected fixture uses the original initial idle deadline at DS:56C4 and
the stored short-book instrument at geometry+0791+songIndex. This initialization
comes entirely from the starting snapshot.

Original loader 3258 restores per-song tempo, instrument and notation from
geometry+075F, +0791 and +07C3, with 25 entries per score mode. While listening,
the comparison uses the effective tempo/instrument rather than ignored stock
header values, and does not treat the inactive personal-title buffer as a
displayed title. It compares the active record length, header and notes; unused
other-mode lengths and empty-slot duration bytes are not musical content.

## Scope and remaining work

Both verifiers are registered regression suites. All results above identify
playable SHA `e9af2b698fce8aec436c97f7052384f3aeb0f8d8ab8bf7059de2b8364f2d812c`;
this pass has not changed the game runtime.

These results establish the covered authoring, playback completion, ordinary
interchange and original checkpoint journeys. They do not establish complete
audio waveforms, every original playback timestamp, or every song/instrument.
The original's per-song/per-score-mode listening preferences need a dedicated
song-switch journey: the current browser keeps a single `listeningInstrument`
and resets tempo from the stock song on scene refresh. Record that as an open
behavior audit rather than assuming this passing composition route covers it.
