# Final bounded nature interaction audit

2026-09-27. Research only; no runtime edits. Reviewed `treehouse-demo/nature-quiz.js` after the reminder, RNG, reveal and cursor corrections. Parent may apply fixes concurrently, so this report records concrete findings at review time.

Primary sources: original overlay2 (`output/treehouse/research-resources/overlay2-disassembly.txt`), resident `all-disassembly.txt`, original DIGISND1006, and new ordinary-input captures under `output/treehouse/research-nature-input-final/`. Capture helper `nature-input-final-capture.py` restores existing ordinary-play states and supplies mouse movement/clicks only. Run files record input actions and source-state hashes. No guest RAM modification.

## 1. Definitions are reachable before the first roll

Current `inspectAttribute` updates the definition state in the ready phase, but `draw()` places all explanation drawing inside `phase!=="ready"`. Clicking the left icons therefore appears to do nothing.

Original dispatcher `3142..31FE` permits definition selection regardless of answered state. New native `ready-definition/state/definition.png` shows the LEGS definition before dealing the first visible hand. Route: restore `research-nature/quiz-roll-capture/state/quiz-ready.state`, click(14,54). Ready screen retains empty cards and normal die, while rectangle38 contains the definition and the legs tab is highlighted. DS57D8=4.

Action: allow explanation rendering in ready phase, without introducing cards or turn actor. Existing definition recipe remains correct.

## 2. Clicking the information panel dismisses temporary inspection

Current quiz `click()` handles icons, candidates and controls but not rectangle38. Clicking the definition or candidate information leaves it open.

Original switch routes rectangle38 to `3804`. If DS57D8!=0, `380E..3815` calls `3DC8(1,1)` to clear temporary information and restore learned answers. With no temporary panel, it invokes reminder `3C9F(1)` at381B..3821.

New ordinary captures click(79,50) immediately after the legs definition:

- `ready-definition/state/dismissed.png`: empty ready information panel restored.
- `question-definition/state/dismissed.png`: normal active-turn learned-answer panel restored; questions, actor, cards and guess button retain their existing state.

Both native RAM pairs change DS57D8 from4 to0. This is a direct panel click, not a second click on the same selected attribute icon (which is separately ignored by source314B..3154).

Action: handle `quiz_rectangles[38]` by clearing `selected`/`selectedAttribute`/`explanation` as appropriate and returning to learned answers, preserving the answer footer except the source-defined complete-reveal case. When nothing is open, use original invalid-input reminder feedback.

## 3. Help processing must skip previously eliminated candidates

Reviewed `question()` loops over all mismatching animals and yields18 even when their remaining bit was already clear. Original `3377..338B` tests the bit and skips those candidates before comparing attributes. The only18-tick wait is after a newly removed candidate (`3417..341F`).

This affects ordinary second/later robot questions and human Help-on play: every already-eliminated mismatch adds an unsupported18-tick wait in the reviewed implementation.

Action: require `(remaining[player] & (1<<i)) !== 0` before mismatch elimination, sound and wait. Keep ascending candidate order.

## 4. Candidate removal/restoration has a pitched blocking cue

Reviewed manual `crossOut`, automatic help elimination and help-enabled `wrongGuess` all change candidate state silently. Original all call `1EB9(index,0,1)` after changing the remaining bit:

- Help question:3414.
- Wrong guess with Help:36EE.
- Manual crossout/restore:37F8.

Within1EB9, `1FAE..1FC4` chooses DIGISND**1006** rate according to the **new** candidate state:

| New state | Requested playback rate | Approximate decoded duration |
|---|---:|---:|
| Eliminated | `0x204D` =8269Hz |13.47ticks; normal rounded wait≈14 |
| Available again | `0x4099` =16537Hz |6.73ticks; normal rounded wait≈7 |

The original digital sample has1856 decoded samples, nominal11000Hz. `1FD3` invokes resident733E to save and replace the sample's rate. `2051..2059` starts playback viaE4E0 then waits via577E; `2062..2077` restores the previous sample rate and releases the temporary handle. The requested rate should pass through the project's existing original-rate quantization rule.

The visual candidate/mark redraw happens before starting/waiting for this cue. Help's18-tick delay follows completion of the cue; do not replace18 with the cue duration. Native `research-nature-final-audit/robot-roll/frames.jsonl` shows successive automatic removal changes around ticks7052,7083,7114,7145,7176,7207, approximately31ticks apart, consistent with the pitched cue plus18tick wait.

The cue wait is interruptible: D51:577E is resident12C8E. While BAB2 reports the sound active, it calls callbackDS15F0 (`12C93`); a nonzero result takes `12C9B..12CA5`, calls13029 and returns1. It is not an unconditional full-duration sleep.

Action: centralize the state-change cue and wait so manual crossout, automatic elimination and help-assisted wrong guesses use the same behavior. No cue is requested for ordinary full candidate redraw or idle candidate flash (`1EB9` third argument0).

## 5. Definition selection also plays1008

Original `3157` calls resident5B9B immediately after checking that a different definition tab was selected. Resident5BA4/5BA8 plays nonblocking1008. The reviewed `inspectAttribute()` changes the panel without this cue. Do not replay it when reselecting the already-open tab; source returns early at3154.

The ordinary candidate inspection branch343C..3615 has no1008 call. In contrast, question-answer completion **3339** also calls5B9B after rendering the learned row/footer, before its36tick wait. That second1008 call was also omitted in the reviewed `question()`.

## 6. Invalid actions should trigger the existing reminder immediately

The reminder implementation now matches idle visual states, but reviewed rejected actions generally return silently after resetting the300tick timer. Original calls `3C9F(1)` for these direct ordinary actions:

- Guess control while answered/already guessing:3054..306E.
- Candidate card while ready, or crossed-out card while guessing:3618..363F.
- Manual crossout while ready, robot role, or Help enabled:3795..37CA.
- Empty information panel rectangle38:381B..3821.

In answered/ready state the flag adds1017 before the8tick lit-die feedback. In question/guess state it runs the corresponding question/card guidance recipe. This is source-backed reachable input feedback, not a new rule or an invented error dialog.

## 7. Starting a turn has a68-tick die lead-in

The reviewed `roll()` changesplayer and starts the entry animation immediately. Original normal die branch `2EE1..2EE7` first calls `3E27(1)`: sound1017, lit die8ticks, normal die. Then `2EEA..2EF2` waits60ticks, removes die, clears temporary information/footer, and only then switchesplayer at2F8F. Both waits are interruptible. This lead-in also precedes the winner's ribbon/reward chooser branch, before2F17 chooses normal roll versus award.

Native `research-nature-final-audit/robot-roll/run.json` supplies exact confirmation: input callback1815/tick6496, currentplayer changes0→1 atcallback1894/tick6564,68ticks later. This is separate from the later three30tick question reveals and robot60tick decision delay.

Read-only native model fields for all four definition/dismissal snapshots are available in `research-nature-input-final/fixtures.json`, including cards, secrets, player, role/help, masks, offered questions, selected attribute, source string reference, pointer and RNG seed.

## 8. Turn entry uses only SCR0's first display

Follow-up to the parent's ordered robot-turn comparison: overlay287E passes1 at28B6, forwarded by415F to419D's `bp+10`. Main4868 checks this flag;4871 tests DS5586==1 and487B jumps to playback cleanup48C0. The entry call therefore stops after the first displayed frame of `group+0`; it must not play that entire script. The script's first displayed pose can differ from simply drawing relativeSHAP1 at a hardcoded position.

Exact panel ordering:

1. Die lead-in8+60 completes.2EF9 removes die.
2.2F06 calls `3DC8(1,0)`: clear information panel **without restoring old learned answers**.2F12 clears footer.
3.2F8F changes logical currentplayer;2F9B clears answered flag.
4.2FA3 calls287E: present the new role's first SCR0 display over old candidate cards and blank information/footer panels.
5.2FA8 calls394A: draw the new player's learned answers.
6.2FB1 calls1E82(0): redraw new player's candidates/marks.
7.2FB4 onward clears/rebuilds three offered questions.

Native contact sheet `research-nature-final-audit/entry-first-display.png` contains callbacks1894..1901 of `robot-roll`.1895..1898 show blank information/footer and previous player's cards with the busy clock.1899 shows first robot pose while candidate redraw is in progress;1901 is settled with all new cards. Therefore do not preserve old learned text through the first entry display. This corrects the initial research message's overly broad wording about retained panels.

## Scope of this pass

The findings above are specific defects with reachable input paths or exact source predicates. The pass also read exploration selection/drag/erase code and earlier exploration render reports; it did not establish a new concrete exploration discrepancy within this bounded audit.
