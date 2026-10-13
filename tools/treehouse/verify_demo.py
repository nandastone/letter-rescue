"""Exercise the playable demo and report exact native-frame differences.

Uses Playwright with installed Edge. Behavioral checks and pixel comparisons
are reported separately; an unexplained pixel never becomes an allowed match.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageChops
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]


def verify(html: Path, output: Path, channel: str) -> dict:
    output.mkdir(parents=True, exist_ok=False)
    report = dict(demo_sha256=hashlib.sha256(html.read_bytes()).hexdigest(),
                  behavior_checks=[], pixel_comparisons={}, errors=[])
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(channel=channel, headless=True)
        context = browser.new_context(viewport={"width": 1360, "height": 960})
        page = context.new_page()
        page.on("pageerror", lambda error: report["errors"].append(str(error)))
        # Explicit stepping makes every inspection reproducible. A separate
        # live-rAF browser check below exercises the ordinary animation loop.
        page.add_init_script("window.requestAnimationFrame=()=>0;")
        page.goto(html.resolve().as_uri())
        page.wait_for_function("window.treehouseDemo !== undefined")
        # Native captured DOS clock/date are input fixtures, independent of
        # the browser's live clock used in ordinary play.
        page.evaluate('resident.ambientEnabled=false;resident.hungerDue=resident.fatigueDue=Infinity;room.now=()=>new Date(1992,0,1,12,39);room.date=room.now()')

        def check(condition: bool, label: str) -> None:
            report["behavior_checks"].append(dict(name=label, passed=bool(condition)))
            if not condition:
                raise AssertionError(label)

        def state() -> dict:
            return page.evaluate("treehouseDemo.state")

        def advance(ticks: int) -> None:
            page.evaluate("ticks=>{treehouseDemo.advance(ticks);treehouseDemo.render();}", ticks)

        def snapshot(scene: str, native: str, pointer: list[int]) -> None:
            page.evaluate("([scene,point])=>{treehouseDemo.setScene(scene);treehouseDemo.setPointer(...point);treehouseDemo.render();}", [scene, pointer])
            image = Image.frombytes("RGBA", (320, 200), bytes(page.evaluate("treehouseDemo.pixels()"))).convert("RGB")
            image.save(output / f"{scene}.png")
            original = Image.open(ROOT / "testing/output/treehouse" / native).convert("RGB")
            difference = ImageChops.difference(image, original)
            count = sum(a != b for a, b in zip(image.getdata(), original.getdata()))
            difference.save(output / f"{scene}-difference.png")
            report["pixel_comparisons"][scene] = dict(different_pixels=count,
                total_pixels=64000, exact=count == 0, bounding_box=difference.getbbox())
            page.screenshot(path=str(output / f"{scene}-browser.png"), full_page=True)
            if scene == "music":
                score = (88, 27, 300, 102)
                score_count = sum(a != b for a, b in zip(image.crop(score).getdata(), original.crop(score).getdata()))
                report["pixel_comparisons"]["music_score"] = dict(different_pixels=score_count,
                    total_pixels=212 * 75, exact=score_count == 0)

        page.evaluate("exterior.credit=2")  # Captured title is the third credit panel.
        snapshot("outside", "entry-verified-a/state/title.png", [160, 100])
        snapshot("inside", "entry-verified-a/state/after-click.png", [95, 145])
        snapshot("music", "demo-piano/state/piano.png", [49, 185])
        check(report["pixel_comparisons"]["inside"]["exact"], "Original interior matches every pixel")
        check(report["pixel_comparisons"]["outside"]["exact"], "Original title matches every pixel")
        check(report["pixel_comparisons"]["music_score"]["exact"], "Original initial music score matches every pixel")
        check(report["pixel_comparisons"]["music"]["exact"], "Original initial music room matches every pixel")

        for character in ("boy", "girl"):
            page.get_by_role("button", name="Home", exact=True).click()
            page.get_by_role("button", name=f"Choose the {character}", exact=True).click()
            check(state()["entering"], f"{character}: character entry begins")
            advance(2000)
            check(state()["scene"] == "inside" and state()["character"] == character,
                  f"{character}: original entry script reaches interior")
        page.get_by_role("button", name="Make some music", exact=True).click()
        advance(1500)
        check(state()["scene"] == "music", "Music room opens")
        page.locator("canvas").focus()
        keys = "zsxdcvgbhnjm,l.;/"
        for key in keys:
            page.keyboard.down(key)
            page.wait_for_function("treehouseDemo.state.held === 1")
            page.keyboard.up(key)
            check(state()["held"] == 0 and page.evaluate("audio.active.size===0"), f"Original key {key!r}: note releases")
        bounds = page.locator("canvas").bounding_box()
        page.mouse.move(bounds["x"] + bounds["width"] * 94 / 320,
                        bounds["y"] + bounds["height"] * 179 / 200)
        page.mouse.down()
        page.wait_for_function("treehouseDemo.state.held === 1")
        check(state()["held"] == 1, "Mouse presses the original canvas piano key")
        page.mouse.move(bounds["x"] - 40, bounds["y"] + 80)
        check(state()["held"] == 0, "Dragging outside the keyboard releases the note")
        page.mouse.up()
        advance(1)
        page.keyboard.down("z")
        page.wait_for_function("treehouseDemo.state.held === 1")
        page.evaluate("window.dispatchEvent(new Event('blur'))")
        check(state()["held"] == 0, "Window blur releases held keyboard notes")
        page.keyboard.up("z")
        for option in page.locator("#instrument option").all():
            value = option.get_attribute("value")
            page.locator("#instrument").select_option(value)
            page.get_by_role("button", name="Hear this instrument", exact=True).click()
            advance(500)
            advance(1)
            page.locator("canvas").focus()
            page.keyboard.down("z")
            page.wait_for_function("treehouseDemo.state.held === 1")
            page.keyboard.up("z")
        check(state()["stats"]["notesPlayed"] >= 52, "All 35 individual instrument samples play")
        for song in range(24):
            page.locator("#song").select_option(str(song))
            page.get_by_role("button", name="Play song", exact=True).click()
            check(state()["songPlaying"], f"Song {song}: playback starts")
            advance(10000)
            check(not state()["songPlaying"], f"Song {song}: playback completes")
        page.get_by_role("button", name="Record a tune", exact=True).click()
        page.locator("canvas").focus()
        for key in ("z", "x", "c"):
            page.keyboard.down(key)
            page.wait_for_function("treehouseDemo.state.held === 1")
            advance(15)
            page.keyboard.up(key)
            advance(5)
        page.get_by_role("button", name="Finish recording", exact=True).click()
        saved = page.evaluate("JSON.parse(localStorage.getItem('treehouse-demo-melody-v1'))")
        check(len(saved["notes"]) == 3, "Three-note melody saved locally")
        page.get_by_role("button", name="Play my tune", exact=True).click()
        check(state()["songPlaying"], "Saved melody playback starts")
        advance(1000)
        check(not state()["songPlaying"], "Saved melody playback completes")

        page.get_by_role("button", name="Back", exact=True).click()
        advance(1500)
        page.get_by_role("button", name="Look through the telescope", exact=True).click()
        advance(1500)
        for name in ("The planets", "A little alien", "The birdbath", "The robot’s shelf"):
            page.get_by_role("button", name=name, exact=True).click()
            advance(3000)
            check(state()["scene"] == "telescope", f"Telescope: {name} runs")
        page.keyboard.press("Escape")
        advance(1500)
        check(state()["scene"] == "inside", "Escape returns from telescope")
        page.set_viewport_size({"width": 390, "height": 844})
        page.get_by_role("button", name="Make some music", exact=True).click()
        advance(1500)
        advance(1)
        page.locator('#touch-keys button[data-pitch="0"]').scroll_into_view_if_needed()
        target = page.locator('#touch-keys button[data-pitch="0"]').bounding_box()
        page.mouse.move(target["x"] + target["width"] / 2, target["y"] + target["height"] - 10)
        page.mouse.down()
        page.wait_for_function("treehouseDemo.state.held === 1")
        page.mouse.up()
        check(state()["held"] == 0, "Large mobile piano key presses and releases")
        page.evaluate("window.scrollTo(0,0)")
        page.screenshot(path=str(output / "mobile-browser.png"), full_page=True)
        check(page.evaluate("document.documentElement.scrollWidth <= window.innerWidth"), "Mobile layout has no horizontal overflow")
        check(not report["errors"], "No browser exceptions during demo journey")
        report["final_state"] = state()
        live = context.new_page()
        live.on("pageerror", lambda error: report["errors"].append(str(error)))
        live.goto(html.resolve().as_uri())
        live.get_by_role("button", name="Choose the boy", exact=True).click()
        live.wait_for_function("treehouseDemo.state.scene === 'inside'", timeout=20000)
        check(live.evaluate("treehouseDemo.state.stats.errors.length===0"), "Real-time animation loop reaches the interior")
        browser.close()
    report["behavior_passed"] = all(item["passed"] for item in report["behavior_checks"]) and not report["errors"]
    report["full_clone_parity"] = False
    (output / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--html", type=Path, default=ROOT / "testing/output/treehouse/playable/index.html")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--browser", default="msedge")
    args = parser.parse_args()
    result = verify(args.html, args.output, args.browser)
    print(json.dumps({"behavior_passed": result["behavior_passed"], "checks": len(result["behavior_checks"]),
                      "pixels": result["pixel_comparisons"], "errors": result["errors"]}, indent=2))
