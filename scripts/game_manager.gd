extends Node

enum Difficulty { EASY, MEDIUM, HARD }

const MAX_LEVELS := 15

var current_difficulty: Difficulty = Difficulty.EASY
var current_level: int = 1
var score: int = 0

# Frontend profile/options, saved in the native .wr1 profile format.
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

func add_score(points: int) -> void:
	score += points

func advance_level() -> void:
	current_level += 1

func restart_game() -> void:
	current_level = 1
	score = 0
