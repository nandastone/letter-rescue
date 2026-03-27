extends Node

# Preloaded sound effects.
var sounds := {}

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
	if sfx_name not in sounds:
		return
	var player := AudioStreamPlayer.new()
	player.stream = sounds[sfx_name]
	player.bus = "Master"
	add_child(player)
	player.play()
	player.finished.connect(player.queue_free)
