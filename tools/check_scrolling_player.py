"""Check rendered player stability from smoke_scrolling_player.gd --capture-scroll."""
import sys
from pathlib import Path
from PIL import Image, ImageChops

folder = Path(sys.argv[1] if len(sys.argv) > 1 else 'testing/output/scroll-frames')
bounds = []
for path in sorted(folder.glob('*.png')):
    image = Image.open(path).convert('RGB')
    marker = Image.new('L', image.size, 255)
    for band, target in zip(image.split(), (123, 17, 231)):
        marker = ImageChops.multiply(marker, band.point([255 if value == target else 0 for value in range(256)]))
    bounds.append(marker.getbbox())
assert len(bounds) >= 20 and all(bounds), 'not enough visible player samples'
positions = sorted({box[0] for box in bounds})
widths = sorted({box[2] - box[0] for box in bounds})
print(f'Scrolling player: {len(bounds)} frames, left positions {positions}, widths {widths}')
assert len(positions) == 1, 'player shifts on screen while camera follows at the same speed'
assert len(widths) == 1, 'player width changes while scrolling'
