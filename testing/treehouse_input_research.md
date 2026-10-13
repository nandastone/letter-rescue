# Treehouse DOS input: manual check and original setup evidence

Date: 2026-09-25. Target: pinned DOS v1.1 package. Read-only inspection; no input
settings changed or executable run by this research agent.

## The available PDF does not document startup controls

The linked [DOS manual PDF](https://d2.xp.myabandonware.com/f/lkbj/The-Treehouse_Manual_DOS_EN.pdf)
is 147,071 bytes, SHA-256
`e167b94a5c0565d38ae652fa6b99e0689fced3bf3756e0c468200709ebe804a7`.
It contains **one scanned page**, showing a musical-instrument identification
challenge and twelve groups of instruments. It has no text layer. The complete
page was rendered and visually inspected.

There are no instructions for starting from the title, choosing a player,
keyboard action keys, mouse controls, or SETUP input modes. The filename must
not be treated as evidence that a complete original manual has been obtained.

Local source copy:
`testing/output/treehouse/research-input/The-Treehouse_Manual_DOS_EN.pdf`.

## Original SETUP files confirm configurable input modes

Printable strings in the actual local files provide narrower primary evidence:

| Original file | File offset | Observed text |
| --- | ---: | --- |
| `SETUP.CFG` | `0x266` | `InputItemList=1,2,3` |
| `SETUP.EXE` | `0x6EB0` | `Select Input Device` |
| `SETUP.EXE` | `0x7DA8` | `Keyboard only` |
| `SETUP.EXE` | `0x7DB6` | `Mouse and Keyboard` |
| `SETUP.EXE` | `0x7DC9` | `Joystick and Keyboard` |
| `SETUP.EXE` | `0x7DDF` | `Alternate Keyboard` |

SETUP also contains a help string at `0x768D` describing choosing the installed
input device. These strings establish that input configuration matters. They do
**not** establish the numeric values written into CONFIG.DAT, which CONFIG.DAT
word stores the choice, or whether the fourth generic setup option is offered
by this game's three-item list.

A reliable next observation is to run this original SETUP, inspect its current
input selection, select the intended mode, and compare the resulting bytes with
the preserved CONFIG.DAT. Record that modified run separately from the source
archive. Startup action keys still require actual input-handler tracing or a
complete manual; Enter doing nothing does not identify the intended key.
