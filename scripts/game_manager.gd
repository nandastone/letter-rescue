extends Node

# Difficulty settings.
enum Difficulty { EASY, MEDIUM, HARD }

const MAX_LEVELS := 15

var current_difficulty: Difficulty = Difficulty.EASY
var current_level: int = 1
var score: int = 0
var high_score: int = 0

# Difficulty-dependent values.
var gruzzle_counts := { Difficulty.EASY: 1, Difficulty.MEDIUM: 4, Difficulty.HARD: 9 }
var slime_refill := { Difficulty.EASY: 99, Difficulty.MEDIUM: 3, Difficulty.HARD: 2 }

# Save data.
var levels_completed := {}
var progress_path := "user://save.json"

# Original frontend profile/options are independent of the simplified game save.
var original_player_name := ""
var original_character := 1
var original_scancodes: Array = [77, 75, 72, 80, 57]
var original_custom_keys := false
var original_joystick := false
var original_sound := 0
var original_speed_ticks := 8
var original_joystick_center := Vector2.ZERO
var original_pending_profile: Dictionary = {}
var original_demo_host: Node

func get_gruzzle_count() -> int:
	return gruzzle_counts[current_difficulty]

func get_slime_refill() -> int:
	return slime_refill[current_difficulty]

func get_gruzzle_speed_multiplier() -> float:
	match current_difficulty:
		Difficulty.EASY: return 0.5
		Difficulty.MEDIUM: return 1.0
		Difficulty.HARD: return 1.5
	return 1.0

func add_score(points: int) -> void:
	score += points
	if score > high_score:
		high_score = score

func advance_level() -> void:
	levels_completed[current_level] = true
	current_level += 1

func restart_game() -> void:
	current_level = 1
	score = 0

func is_level_available(level: int) -> bool:
	if level == 1:
		return true
	return levels_completed.has(level - 1)

func save_progress() -> void:
	var save_data := {
		"high_score": high_score,
		"levels_completed": levels_completed,
	}
	var file := FileAccess.open(progress_path, FileAccess.WRITE)
	if file:
		file.store_string(JSON.stringify(save_data))

func load_progress() -> void:
	if not FileAccess.file_exists(progress_path):
		return
	var file := FileAccess.open(progress_path, FileAccess.READ)
	if file:
		var json := JSON.new()
		if json.parse(file.get_as_text()) == OK:
			var data: Dictionary = json.data
			high_score = data.get("high_score", 0)
			var saved_levels = data.get("levels_completed", {})
			for key in saved_levels:
				levels_completed[int(key)] = true

func _ready() -> void:
	load_progress()
