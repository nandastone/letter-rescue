extends Node
class_name LevelLoader

# Loads level data from JSON and spawns entities.

static func load_level(path: String) -> Dictionary:
	var file := FileAccess.open(path, FileAccess.READ)
	if file == null:
		push_error("Failed to open level file: %s" % path)
		return {}
	var json := JSON.new()
	var err := json.parse(file.get_as_text())
	if err != OK:
		push_error("Failed to parse level JSON: %s" % json.get_error_message())
		return {}
	return json.data

static func get_level_path(level_number: int) -> String:
	return "res://data/levels/level_%02d.json" % level_number
