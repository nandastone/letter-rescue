"""Build the independent browser demo from the pinned original DOS package.

The output is one portable HTML file. No emulator, screenshots, or network
services are used by the demo. Original resources are decoded at build time.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
from pathlib import Path
import struct
import zipfile

from executable import disassemble_script, unpack
from images import decode_palette, decode_shape
from resources import parse_archive
from sound import decode_sound_with_info

ROOT = Path(__file__).resolve().parents[2]
SOURCE_SHA = "53ecb856cb6c49f28064ce22b9723eed9a8d19db139ae1bead9786f37a7eb78c"


def theater_tables(image: bytes) -> dict:
    """Original overlay-4 tables; offsets are pinned by the executable hash."""
    ds = 0x321d0

    def rows(offset: int, count: int, width: int) -> list:
        return [list(struct.unpack_from(f"<{width}h", image, offset + i * width * 2)) for i in range(count)]

    origins = rows(ds + 0x128e, 56, 2)
    times = rows(ds + 0x10da, 24, 2)
    return dict(room_entrance=rows(0x2e938 + 13*8, 1, 4)[0],
        ui_rects=rows(0x30c80, 29, 4), actor_bounds=rows(ds + 0x136e, 8, 4),
        actor_shape_offsets=rows(ds + 0x126e, 8, 2),
        actor_origins_by_place=[origins[i:i+8] for i in range(0, 56, 8)],
        time_background_variant=rows(ds + 0x1266, 1, 4)[0],
        time_shapes=rows(ds + 0x10ba, 4, 4),
        time_positions_by_place=[times[i:i+4] for i in range(0, 24, 4)],
        action_preview_shapes=rows(ds + 0x106a, 1, 8)[0],
        action_preview_offsets=rows(ds + 0x107a, 8, 2),
        action_icon_positions=rows(ds + 0x109a, 8, 2),
        prop_first=rows(ds + 0x101e, 1, 6)[0],prop_count=rows(ds + 0x102a, 1, 6)[0],
        prop_group=rows(ds + 0x1036, 1, 6)[0],
        curtain_positions=rows(0x30d68, 4, 4),curtain_shapes=rows(0x30d88, 4, 2))


def decode_assets(source: Path) -> dict:
    """Decode pinned resources for independent runtimes (Godot and JS reference)."""
    raw = source.read_bytes()
    if hashlib.sha256(raw).hexdigest() != SOURCE_SHA:
        raise ValueError("Demo requires the researched original DOS v1.1 ZIP")
    assets = dict(shapes={}, palettes={}, scripts={}, strings={}, songs={}, pcm={}, raw={}, font={})
    assets['platform'] = dict(cpu_cycles_per_millisecond=10000)
    with zipfile.ZipFile(source) as archive:
        original_books = archive.read('TheTreeh/songs.dat')
        assets['status'] = base64.b64encode(archive.read('TheTreeh/status.dat')).decode()
        image, _ = unpack(archive.read("TheTreeh/treehse.exe"))
        assets["cursor"] = list(image[0x310b0:0x310b0 + 68])
        assets["telescope"] = dict(rectangles=[list(struct.unpack_from('<4h', image, 0x321d0+0x358+8*i)) for i in range(4)])
        for name in ("th", "th64", "boy", "girl", "modules", "digisnd", "voices"):
            data = archive.read(f"TheTreeh/{name}.dat")
            for record in parse_archive(data):
                tag, rid = record["tag"], record["id"]
                key = f"{name}:{rid}"
                start = record["payload_offset"]
                payload = data[start:start + record["size"]]
                if tag == "SHAP":
                    width, height, pixels = decode_shape(payload)
                    assets["shapes"][key] = [width, height, base64.b64encode(pixels).decode()]
                elif tag == "SHPL":
                    first, count = struct.unpack_from("<HH", payload)
                    assets["palettes"][key] = dict(first=first, count=count, colors=decode_palette(payload))
                elif tag == "SCR":
                    script = disassemble_script(payload, image)
                    assets["scripts"][key] = dict(bounds=script["bounds_words"], code=[
                        [op["opcode"], list(bytes.fromhex(op["operand_hex"]))]
                        for op in script["instructions"]])
                elif tag == "STRL":
                    assets["strings"][key] = [s["cp437"] for s in record["strings"]]
                elif tag == "SONG":
                    assets["songs"][key] = list(payload)
                elif tag == "SND" and name in ("digisnd", "voices"):
                    info, pcm = decode_sound_with_info(payload)
                    assets["pcm"][key] = dict(rate=info.sample_rate, loop=info.loop,
                        loop_start=info.loop_start, loop_end=info.loop_end,
                        decode_cycles=info.decode_cycles,
                        pcm=base64.b64encode(pcm).decode())
                elif tag in ("FONT", "CURS"):
                    assets["raw"][f"{name}:{tag}:{rid}"] = base64.b64encode(payload).decode()
                    if tag == "FONT":
                        offsets = struct.unpack_from("<218H", payload, 10)
                        ends = sorted(set(offsets) | {len(payload)})
                        for char, offset in enumerate(offsets):
                            end = next(v for v in ends if v > offset)
                            height, width = struct.unpack_from("<HH", payload, offset)
                            if height and width:
                                width, height, pixels = decode_shape(payload[offset:end])
                                assets["font"][str(char)] = [width, height, base64.b64encode(pixels).decode()]
    assets["provenance"] = dict(source_sha256=SOURCE_SHA, version="DOS 1.1")
    source_dir = ROOT / "treehouse-demo"
    assets["music"] = json.loads((source_dir / "music-tables.json").read_text(encoding="utf-8"))
    assets["music"]["followup"] = json.loads((ROOT / "testing/treehouse/music-followup-tables.json").read_text(encoding="utf-8"))
    assets["music"]["maze"] = json.loads((ROOT / "testing/treehouse/music-maze-tables.json").read_text(encoding="utf-8"))
    assets["music"]["followup"]["fact_icon_groups"] = list(image[0x2ffe0+0x17e:0x2ffe0+0x17e+42])
    assets["music"]["followup"]["fact_icon_indices"] = list(image[0x2ffe0+0x1a8:0x2ffe0+0x1a8+42])
    assets["music"]["idle_frames"] = list(image[0x321d0+0xc76:0x321d0+0xc76+17])
    assets["music"]["tempo_thresholds"] = list(struct.unpack_from("<4h", image, 0x2f180+0x156))
    assets["music"]["idle_rect"] = list(struct.unpack_from("<4h",image,0x321d0+0xc88))
    assets["music"]["maze_cloud_positions"] = [list(struct.unpack_from("<2h",image,0x2f180+0x84b+4*i)) for i in range(8)]
    assets["music"]["note_letters"] = [image[0x2f180+0x486+17*i:0x2f180+0x486+17*(i+1)].decode('ascii') for i in range(2)]
    assets["music"]["drag_pitches"] = [list(image[0x2f180+0x3e7+37*i:0x2f180+0x3e7+37*(i+1)]) for i in range(2)]
    # Original overlay-1 loader uses 25 entries per score mode, independent
    # of the stock SONG headers. These preferences live for the DOS session.
    assets["music"]["listening_defaults"] = [list(image[0x2f180+off:0x2f180+off+50]) for off in (0x75f,0x791,0x7c3)]
    assets["music"]["cp437"] = bytes(range(256)).decode('cp437')
    assets["music"]["end_songs"] = [list(original_books[65*i:65*(i+1)]) for i in (42,85)]
    assets["music"]["song_icons"] = list(image[0x2f180 + 0x7f5:0x2f180 + 0x7f5 + 26])
    assets["theater"] = theater_tables(image)
    assets['rewards'] = json.loads((ROOT/'testing/output/treehouse/research-rewards/tables.json').read_text(encoding='utf-8'))
    ds = 0x321d0
    assets['room'] = dict(
        objects=[dict(type=i,palette=[870,900,930][struct.unpack_from('<H',image,ds+0x5f6+2*i)[0]],states=list(struct.unpack_from('<10H',image,ds+0x936+10*i)),
                      inside=list(struct.unpack_from('<4h',image,ds+0x7be+8*i)),outside=list(struct.unpack_from('<4h',image,ds+0x866+8*i))) for i in range(21)],
        poses=[list(struct.unpack_from('<4h',image,ds+0x1c4+8*i)) for i in range(5)],
        exempt=list(image[ds+0x1f6:ds+0x1f6+32]),
        surfaces=[[list(struct.unpack_from('<4h',image,ds+0x6f2+8*(11*scene+i))) for i in range(11)] for scene in range(2)])
    assets["boardgame"] = json.loads((source_dir / "boardgame-tables.json").read_text(encoding="utf-8"))
    animals = []
    for index in range(len(assets["strings"]["modules:5000"])):
        row = image[0x30218+12*index:0x30218+12*(index+1)]
        palette = 4900+100*row[9]
        animals.append(dict(id=index, attributes=list(row[:7]), active_time=row[7],
                            category=row[8], palette=palette, large=palette+row[10], small=palette+row[11]))
    assets["nature"] = dict(animals=animals,
        rectangles=[list(struct.unpack_from("<4h", image, 0x30668+8*i)) for i in range(27)],
        class_icons=[[5670+image[0x30898+2*i+t] for i in range(10)] for t in range(2)],
        quiz_rectangles=[list(struct.unpack_from("<4h",image,0x30740+8*i)) for i in range(39)],
        quiz_options=[list(struct.unpack_from("<4h",image,0x301c0+8*i)) for i in range(11)],
        question_shapes=list(struct.unpack_from("<8H",image,0x308ac)),
        question_positions=[list(struct.unpack_from("<2h",image,0x308bc+4*i)) for i in range(8)],
        reveal_rectangles=[list(struct.unpack_from("<4h",image,0x321d0+0xd9e+8*i)) for i in range(2)],
        guess_restore_rectangles=[list(struct.unpack_from("<4h",image,0x321d0+0xd76+8*i)) for i in range(4)])
    font = image[0x2eac0:0x2eac0 + 0x5f7]
    first, last = font[0], font[1]
    assets["heading_font"] = {}
    for char in range(first, last + 1):
        offset = struct.unpack_from("<H", font, 10 + (char-first)*2)[0]
        height, width, stride = struct.unpack_from("<HHH", font, offset)
        pixels = bytes((font[offset+6+y*stride+x//8] >> (7-x%8)) & 1
                       for y in range(height) for x in range(width))
        assets["heading_font"][str(char)] = [width, height, base64.b64encode(pixels).decode()]
    assets['help'] = json.loads((ROOT / 'testing/treehouse/help-layout.json').read_text(encoding='utf-8'))['layouts']
    return assets


def build(source: Path, output: Path) -> dict:
    assets = decode_assets(source)
    source_dir = ROOT / "treehouse-demo"
    html = (source_dir / "index.html").read_text(encoding="utf-8")
    html = html.replace("/* DEMO_STYLE */", (source_dir / "style.css").read_text(encoding="utf-8"))
    serialized = json.dumps(assets, separators=(",", ":"), ensure_ascii=True).replace("<", "\\u003c")
    html = html.replace("/* DEMO_ASSETS */", f"const ORIGINAL = {serialized};")
    html = html.replace("/* DEMO_ENGINE */", (source_dir / "engine.js").read_text(encoding="utf-8"))
    html = html.replace("/* DEMO_THEATER */", (source_dir / "theater.js").read_text(encoding="utf-8"))
    html = html.replace("/* DEMO_NATURE */", (source_dir / "nature.js").read_text(encoding="utf-8"))
    html = html.replace("/* DEMO_NATURE_QUIZ */", (source_dir / "nature-quiz.js").read_text(encoding="utf-8"))
    html = html.replace("/* DEMO_CHALKBOARD */", (source_dir / "chalkboard.js").read_text(encoding="utf-8"))
    html = html.replace("/* DEMO_BOARD_MOTION */", (source_dir / "board-motion.js").read_text(encoding="utf-8"))
    html = html.replace("/* DEMO_MUSIC_SELECTOR */", (source_dir / "music-selector.js").read_text(encoding="utf-8"))
    html = html.replace("/* DEMO_MUSIC_EDITOR */", (source_dir / "music-editor.js").read_text(encoding="utf-8"))
    html = html.replace("/* DEMO_MUSIC_MAZE */", (source_dir / "music-maze.js").read_text(encoding="utf-8"))
    html = html.replace("/* DEMO_ROOM */", (source_dir / "room.js").read_text(encoding="utf-8"))
    html = html.replace("/* DEMO_CHARACTER */", (source_dir / "room-character.js").read_text(encoding="utf-8"))
    html = html.replace("/* DEMO_ROOM_TRANSITION */", (source_dir / "room-transition.js").read_text(encoding="utf-8"))
    html = html.replace("/* DEMO_EXTERIOR */", (source_dir / "exterior.js").read_text(encoding="utf-8"))
    html = html.replace("/* DEMO_REWARDS */", (source_dir / "rewards.js").read_text(encoding="utf-8"))
    html = html.replace("/* DEMO_BOARDGAME */", (source_dir / "boardgame.js").read_text(encoding="utf-8"))
    html = html.replace("/* DEMO_SAVE */", (source_dir / "save.js").read_text(encoding="utf-8") + "\n" + (source_dir / "preferences.js").read_text(encoding="utf-8"))
    html = html.replace("/* DEMO_APP */", (source_dir / "audio-mixer.js").read_text(encoding="utf-8") + "\n" + (source_dir / "app.js").read_text(encoding="utf-8"))
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(html, encoding="utf-8")
    report = dict(output=str(output.resolve()), bytes=output.stat().st_size,
                  sha256=hashlib.sha256(output.read_bytes()).hexdigest(),
                  shapes=len(assets["shapes"]), scripts=len(assets["scripts"]),
                  source_sha256=SOURCE_SHA)
    output.with_suffix(".build.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=ROOT / "testing/output/treehouse/source/The_Treehouse_1991.zip")
    parser.add_argument("--output", type=Path, default=ROOT / "testing/output/treehouse/playable/index.html")
    args = parser.parse_args()
    print(json.dumps(build(args.source, args.output), indent=2))
