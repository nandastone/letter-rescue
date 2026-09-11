extends Node

# Preloaded sound effects.
var sounds := {}
var original: Node

func begin_original_level(level_number: int) -> void:
	var starting: bool = original == null
	if original == null:
		original = preload("res://scripts/wr1_audio.gd").new()
		add_child(original)
	original.level(level_number)
	original.set_music_enabled(GameManager.original_sound == 0)
	original.set_effects_enabled(GameManager.original_sound < 2)
	if starting:
		original.restore_music_checkpoint(InputReplay.original_music_clock)

func end_original_session() -> void:
	if original != null:
		original.music.stop()
		original.stop_effect()
		original.queue_free()
		original = null

func play_original(name: String, only_if_idle: bool = false) -> void:
	if original != null:
		original.play_effect(name, only_if_idle)

func _ready() -> void:
	var sfx_path := "res://assets/audio/sfx/"
	var sfx_names := [
		"jump", "correct", "wrong", "death", "slime",
		"collect", "level_complete", "reveal", "unlock",
	]
	for sfx_name in sfx_names:
		var path: String = sfx_path + sfx_name + ".wav"
		if ResourceLoader.exists(path):
			sounds[sfx_name] = load(path)

func play(sfx_name: String) -> void:
	if original != null:
		# Reveal/unlock UI has no matching speaker trigger in the original.
		if sfx_name in ["correct", "wrong"]:
			play_original(sfx_name)
		return
	if sfx_name not in sounds:
		return
	var player := AudioStreamPlayer.new()
	player.stream = sounds[sfx_name]
	player.bus = "Master"
	add_child(player)
	player.play()
	player.finished.connect(player.queue_free)
