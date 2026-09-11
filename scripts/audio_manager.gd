extends Node

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
