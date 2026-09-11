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

# Updates are admitted on physics ticks, so a 70 Hz tick makes each 12 Hz step
# last 5 or 6 ticks and walking speed wobble by ~9%. At 240 Hz a step is 19.998
# ticks, so every step lasts the same time and draws evenly.
const DEFAULT_TICKS_PER_SECOND := 240

func apply_default_tick_rate() -> void:
	if not LaunchArgs.legacy():
		Engine.physics_ticks_per_second = DEFAULT_TICKS_PER_SECOND

func _ready() -> void:
	apply_default_tick_rate()

func add_score(points: int) -> void:
	score += points

func advance_level() -> void:
	current_level += 1

func restart_game() -> void:
	current_level = 1
	score = 0
