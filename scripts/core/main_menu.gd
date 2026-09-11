extends Control

# Entry scene. Hosts the original startup/menu frontend; native replays load
# the game scene directly from InputReplay instead.

func _ready() -> void:
	if InputReplay.mode == InputReplay.Mode.REPLAYING:
		return
	var frontend := preload("res://scripts/core/wr1_frontend.gd").new()
	add_child(frontend)
	frontend.begin()
