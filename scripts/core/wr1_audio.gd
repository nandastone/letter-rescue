extends Node
## Audible presentation only. Never changes the gameplay/IRQ timing models.
# Legacy reads the raw 48 kHz renders byte-for-byte (the parity suite depends on
# them). The default game plays the same audio encoded as Ogg: ~5 MB, not ~55 MB.
const DIRECTORY := "res://assets/audio/original/playback/"
const OGG_DIRECTORY := "res://assets/audio/original/ogg/"
var directory := DIRECTORY
const IRQ_SECONDS := 12428.0 / 1193182.0
var manifest: Dictionary
var music := AudioStreamPlayer.new()
var speaker := AudioStreamPlayer.new()
var tracks := {}
var effects := {}
var track: int = -1
var effect: String = ""
var enabled: bool = true
var music_enabled: bool = true
var effects_enabled: bool = true
var events: Array[Dictionary] = []

func _event(value: Dictionary) -> void:
	events.append(value)
	if events.size() > 64:
		events.pop_front()

func _ready() -> void:
	directory = DIRECTORY if LaunchArgs.legacy() else OGG_DIRECTORY
	manifest = JSON.parse_string(FileAccess.get_file_as_string(directory + "manifest.json"))
	add_child(music)
	add_child(speaker)
	# DOSBox adlib.cpp channel scale is 1.5; the speaker mixer uses unity.
	music.volume_db = linear_to_db(1.5)
	speaker.volume_db = 0.0
	speaker.finished.connect(func(): effect = "")
	# Accelerated state/image tests do not run an audible presentation clock.
	enabled = DisplayServer.get_name() != "headless" or "--original-audio" in LaunchArgs.user_args()
	if "--mute-original-audio" in LaunchArgs.user_args():
		enabled = false

func _stream(filename: String) -> AudioStream:
	if directory == DIRECTORY:
		return AudioStreamWAV.load_from_buffer(FileAccess.get_file_as_bytes(directory + filename))
	return load(directory + filename)

func level(level_number: int) -> void:
	var selected: int = (level_number - 1) % 3 + 4
	if selected == track:
		return # Cached death loads leave the current song playing.
	track = selected
	if not enabled:
		return
	if not tracks.has(track):
		var info: Dictionary = manifest.music[str(track)]
		var stream := _stream(info.file)
		if stream is AudioStreamWAV:
			stream.loop_mode = AudioStreamWAV.LOOP_FORWARD
			stream.loop_begin = int(info.loop_begin)
			stream.loop_end = int(info.loop_end)
		else:
			stream.loop = true
			stream.loop_offset = float(info.loop_offset)
		tracks[track] = stream
	music.stream = tracks[track]
	music.play()
	music.stream_paused = not music_enabled
	_event({"kind":"music", "track":track})

func play_effect(name: String, only_if_idle: bool = false) -> void:
	if not enabled or not effects_enabled:
		return
	if only_if_idle and speaker.playing and not effect.is_empty() and speaker.get_playback_position() * 48000.0 < float(manifest.effects[effect].logical_duration_samples):
		return
	assert(manifest.effects.has(name), "Unknown original sound: " + name)
	if not effects.has(name):
		effects[name] = _stream(manifest.effects[name].file)
	speaker.stream = effects[name]
	speaker.play() # A single PC speaker: new effects replace the previous one.
	effect = name
	_event({"kind":"effect", "name":name})

func restore_music_checkpoint(checkpoint: Dictionary) -> void:
	if not enabled or checkpoint.is_empty():
		return
	var source: Dictionary = checkpoint.initial.music_driver
	assert(manifest.music[str(track)].cmf_sha256 == checkpoint.music_sha256)
	# The recovered driver resets beats/counter at song restart. Verify the
	# decoded cursor/delay before using these counters as an audible seek.
	var sequencer = load("res://scripts/legacy/wr1_music.gd").new()
	sequencer.configure(FileAccess.get_file_as_bytes(checkpoint.music_file), source)
	# configure normalizes JSON numbers to integers, including nested tracks.
	var expected_tracks: Array = sequencer.state.tracks.duplicate(true)
	sequencer._restart()
	var ticks: int = int(source.beats) * int(source.division) + int(source.counter)
	for i in range(ticks):
		sequencer.tick()
	assert(sequencer.state.tracks == expected_tracks, "Music checkpoint is not reachable from song start")
	music.seek(ticks * IRQ_SECONDS)

func stop_effect(name: String = "") -> void:
	if name.is_empty() or effect == name:
		speaker.stop()
		effect = ""

func movement_before(p: RefCounted, up: bool) -> void:
	var supported: bool = p.attr(p.gx + 1, p.gy) in [0x73, 0x74]
	if supported:
		stop_effect("jump")
	if not up:
		stop_effect("jump")
		return
	var climbing: bool = (p.attr(p.gx + 1, p.gy) == 0x74 and p.attr(p.gx + 1, p.gy - 2) == 0x74) or (p.attr(p.gx + 1, p.gy - 1) == 0x74 and p.attr(p.gx + 1, p.gy - 3) == 0x74)
	if climbing:
		stop_effect()
	elif supported or p.phase == 0:
		play_effect("jump", true)

func movement_after(p: RefCounted) -> void:
	if p.frame in [3, 6, 13, 16]:
		play_effect("step", true)

func set_music_enabled(value: bool) -> void:
	music_enabled = value
	music.stream_paused = not value

func set_effects_enabled(value: bool) -> void:
	effects_enabled = value
	if not value:
		stop_effect()
