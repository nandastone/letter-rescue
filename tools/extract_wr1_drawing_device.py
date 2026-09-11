"""Preserve graphics-library descriptors; no frames, durations or future state."""
import gzip
import hashlib
import json
from pathlib import Path

source = Path('testing/fixtures/wr1_renderer_player.json.gz')
fixture = json.loads(gzip.decompress(source.read_bytes()))
case = fixture['cases'][0]
data = {'exe_sha256':fixture['exe_sha256'], 'source_fixture_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
        'scope':'Graphics-library device descriptors and 24x32 player image headers for mandatory drawing work.',
        'graphics':case['graphics'], 'player_images':case['player']['images']}
text_source = Path('testing/fixtures/wr1_renderer_rewards.json.gz')
text_fixture = json.loads(gzip.decompress(text_source.read_bytes()))
assert text_fixture['exe_sha256'] == data['exe_sha256']
data['text_source_fixture_sha256'] = hashlib.sha256(text_source.read_bytes()).hexdigest()
data['graphics'] = text_fixture['cases'][0]['graphics']
Path('data/wr1/drawing_device.json').write_text(json.dumps(data,indent=2)+'\n')
