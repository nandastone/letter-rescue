"""Check that the art holds its shape between frames (see capture_web_frames.mjs).

Pixel art drawn at a fractional scale resamples differently every frame unless
positions are snapped, so a shape's drawn size flickers - the character and
background visibly shimmer as they move. A single screenshot cannot show it.

    python tools/check_drawn_stability.py out/frames

Measures the question block, which is a 24x24 square in the original art, in
each frame and reports its drawn size. Stable size = good. Also reports the
width/height ratio: 1.0 is square pixels, 0.83 the original 4:3 display shape.
After key release, the block must hold its screen position as well as its size.
"""
import sys
import json
from collections import Counter, deque
from pathlib import Path

from PIL import Image

GREEN = (85, 255, 85)  # The question block's frame; the grass is the same green.
MIN_PIXELS = 500
SQUARE = (0.7, 1.4)  # The block is square-ish in the art; grass strips are not.


def block_bounds(path: Path):
    image = Image.open(path).convert('RGB')
    width, height = image.size
    pixels = image.load()
    seen = [[False] * height for _ in range(width)]
    best = None
    for start_x in range(0, width, 2):
        for start_y in range(0, height, 2):
            if seen[start_x][start_y] or pixels[start_x, start_y] != GREEN:
                continue
            queue = deque([(start_x, start_y)])
            seen[start_x][start_y] = True
            found = []
            while queue:
                x, y = queue.popleft()
                found.append((x, y))
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < width and 0 <= ny < height and not seen[nx][ny] and pixels[nx, ny] == GREEN:
                        seen[nx][ny] = True
                        queue.append((nx, ny))
            if len(found) < MIN_PIXELS:
                continue
            xs = [p[0] for p in found]
            ys = [p[1] for p in found]
            box = (max(xs) - min(xs) + 1, max(ys) - min(ys) + 1)
            if not SQUARE[0] <= box[0] / box[1] <= SQUARE[1]:
                continue  # Grass, or a block merged with it.
            if best is None or len(found) > best[0]:
                best = (len(found), min(xs), min(ys)) + box
    return best[1:] if best else None


def main() -> int:
    directory = Path(sys.argv[1] if len(sys.argv) > 1 else 'out/frames')
    frames = sorted(directory.glob('frame_*.png'))
    if not frames:
        print(f'no frames in {directory}', file=sys.stderr)
        return 2
    moving_bounds = [bounds for bounds in (block_bounds(frame) for frame in frames) if bounds]
    sizes = [bounds[2:] for bounds in moving_bounds]
    if len(sizes) < 5:
        print(f'the question block was measurable in only {len(sizes)} frames', file=sys.stderr)
        return 2
    if len({bounds[:2] for bounds in moving_bounds}) < 2:
        print('camera did not scroll during capture; repeat with movement', file=sys.stderr)
        return 2
    usual = Counter(sizes).most_common(1)[0][0]
    # A shape that resamples differently each frame lands a pixel or two off.
    wobble = [size for size in sizes if size != usual]
    width, height = usual
    print(f'{len(sizes)} frames | usual drawn size {width}x{height} (aspect {width / height:.3f})'
          f' | frames differing: {len(wobble)} {sorted(set(wobble))}')
    if wobble:
        print('FAILED: the drawn size changes between frames, so the art shimmers as it moves',
              file=sys.stderr)
        return 1
    stopped_manifest = directory / 'stopped.json'
    if not stopped_manifest.exists():
        print('missing stopped.json; recapture with post-release frames', file=sys.stderr)
        return 2
    # Allow the last admitted move and its interpolation to finish. At default
    # speed this takes at most two ~83 ms updates, plus capture scheduling.
    stopped = json.loads(stopped_manifest.read_text())
    settled = [row for row in stopped if row['elapsed_ms'] >= 250]
    bounds = [block_bounds(directory / row['file']) for row in settled]
    if len(bounds) < 5 or any(box is None for box in bounds) or settled[-1]['elapsed_ms'] - settled[0]['elapsed_ms'] < 1000:
        print('insufficient measurable post-release frames over one second', file=sys.stderr)
        return 2
    if len(set(bounds)) != 1:
        print(f'FAILED: question block still moves or changes size after release: {sorted(set(bounds))}', file=sys.stderr)
        return 1
    print(f'{len(bounds)} post-release frames: question block remains at {bounds[0]}')
    print('stable across frames')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
