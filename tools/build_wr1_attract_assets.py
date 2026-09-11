"""Package decoded demo controls and one initial checkpoint for runtime playback.

No reference images, completed states, per-update timestamps or expected outcomes
are included. The maintained test fixtures remain immutable and independent.
"""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIELDS = {
    'fps', 'source_fps', 'level', 'difficulty', 'character', 'events',
    'source_sha256', 'source_start_frame', 'total_frames',
    'source_clock_quantum_seconds', 'source_clock_phase_seconds',
    'original_clock_phase_seconds', 'original_demo_inputs', 'demo_provenance',
    'demo_input_offset', 'original_level_start', 'original_entity_start',
    'original_picture_start', 'original_video_start', 'original_music_clock',
}

def build():
    destination = ROOT/'data/wr1/demos'
    destination.mkdir(parents=True, exist_ok=True)
    manifest = {'description': __doc__, 'demos': {}}
    for level in range(1, 16):
        source = ROOT/f'testing/fixtures/wr1_demo_level{level}_replay.json'
        original = json.loads(source.read_text())
        assert original.keys() >= FIELDS
        assert not original['events']
        data = {key: value for key, value in original.items() if key in FIELDS}
        target = destination/f'level{level}.json'
        target.write_text(json.dumps(data, separators=(',', ':'))+'\n', encoding='utf-8')
        manifest['demos'][str(level)] = {
            'source_fixture_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
            'runtime_sha256': hashlib.sha256(target.read_bytes()).hexdigest(),
            'demo_sha256': original['demo_provenance']['sha256'],
        }
    (destination/'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n', encoding='utf-8')

if __name__ == '__main__':
    build()
