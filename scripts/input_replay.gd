extends Node

## Autoload that records player input during play and replays it deterministically.
##
## CLI usage:
##   Record:  godot -- --record replay.json
##   Replay:  godot --fixed-fps 70 --write-movie frames/frame.png -- --replay replay.json
##
## During recording, press F9 to stop and save. The file is also saved on
## scene-tree quit (e.g. window close or --quit-after).

var ACTIONS: Array[String] = [
	"move_left", "move_right", "jump", "move_down", "use_slime",
]

enum Mode { DISABLED, RECORDING, REPLAYING }

var mode: Mode = Mode.DISABLED
var replay_path: String = ""
var physics_frame: int = 0

# Recording state.
var recorded_events: Array[Dictionary] = []
var action_state: Dictionary = {}  # action -> bool (current pressed state)

# Replay state.
var replay_events: Array = []
var replay_index: int = 0  # Next event to process.
var replay_finished: bool = false
var replay_total_frames: int = 0  # Target duration; quit when we hit it.

# Auto-start: skip menu and jump straight into the game.
var auto_start_level: int = -1
var auto_start_difficulty: int = -1

# Optional early-quit override (for tight iteration on frame-0 pixel-exact work).
# Set via `--max-frame N` on the CLI; quits at physics frame N regardless of
# whether the replay's total_frames has been reached.
var max_frame: int = -1


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS

	# Parse CLI args (everything after "--").
	var args := OS.get_cmdline_user_args()
	var i := 0
	while i < args.size():
		match args[i]:
			"--record":
				i += 1
				if i < args.size():
					replay_path = args[i]
					_start_recording()
			"--replay":
				i += 1
				if i < args.size():
					replay_path = args[i]
					_start_replay()
			"--max-frame":
				i += 1
				if i < args.size():
					max_frame = int(args[i])
		i += 1


func _start_recording() -> void:
	mode = Mode.RECORDING
	recorded_events.clear()
	for action in ACTIONS:
		action_state[action] = false
	print("[InputReplay] Recording to: ", replay_path)


func _start_replay() -> void:
	var file := FileAccess.open(replay_path, FileAccess.READ)
	if not file:
		push_error("[InputReplay] Cannot open replay file: %s" % replay_path)
		return

	var json := JSON.new()
	if json.parse(file.get_as_text()) != OK:
		push_error("[InputReplay] Invalid JSON in replay file.")
		return

	var data: Dictionary = json.data

	var replay_fps: int = int(data.get("fps", 70))
	if Engine.physics_ticks_per_second != replay_fps:
		push_error("[InputReplay] Physics tick rate mismatch: engine=%d Hz, replay=%d Hz. Set physics/common/physics_ticks_per_second=%d in project.godot." % [Engine.physics_ticks_per_second, replay_fps, replay_fps])
		get_tree().quit(1)
		return

	replay_events = data.get("events", [])
	replay_index = 0
	replay_finished = false
	replay_total_frames = int(data.get("total_frames", 0))
	mode = Mode.REPLAYING

	# Configure game state to match the recording.
	auto_start_level = data.get("level", 1)
	auto_start_difficulty = data.get("difficulty", 0)

	print("[InputReplay] Replaying from: %s  (%d events, level %d, %d frames)" % [
		replay_path, replay_events.size(), auto_start_level, replay_total_frames
	])

	# Apply game settings and skip menu on next frame.
	_auto_start_game.call_deferred()


func _auto_start_game() -> void:
	GameManager.current_level = auto_start_level
	GameManager.current_difficulty = auto_start_difficulty
	GameManager.score = 0
	get_tree().change_scene_to_file("res://scenes/game.tscn")


func _physics_process(_delta: float) -> void:
	match mode:
		Mode.RECORDING:
			_record_frame()
		Mode.REPLAYING:
			_replay_frame()
	physics_frame += 1


func _record_frame() -> void:
	for action in ACTIONS:
		var pressed := Input.is_action_pressed(action)
		if pressed != action_state[action]:
			action_state[action] = pressed
			recorded_events.append({
				"frame": physics_frame,
				"action": action,
				"pressed": pressed,
			})


func _replay_frame() -> void:
	# Inject all events scheduled for the current frame (if any still pending).
	while replay_index < replay_events.size():
		var ev: Dictionary = replay_events[replay_index]
		var ev_frame: int = int(ev["frame"])
		if ev_frame > physics_frame:
			break  # Future event; wait.

		var ev_action: String = ev["action"]
		var ev_pressed: bool = ev["pressed"]

		var input_ev := InputEventAction.new()
		input_ev.action = ev_action
		input_ev.pressed = ev_pressed
		input_ev.strength = 1.0 if ev_pressed else 0.0
		Input.parse_input_event(input_ev)

		replay_index += 1

	# Early-quit override for tight iteration (--max-frame N).
	if max_frame > 0 and physics_frame + 1 >= max_frame:
		print("[InputReplay] max-frame override (%d) reached. Quitting." % max_frame)
		get_tree().quit()
		return

	# Quit when we've run for the recording's full duration. This keeps the
	# clone alive for the same number of frames as the reference, even when
	# the event list is short (or empty) — so every reference frame has a
	# test-side counterpart to diff against.
	if replay_total_frames > 0 and physics_frame + 1 >= replay_total_frames:
		if not replay_finished:
			replay_finished = true
			mode = Mode.DISABLED
			print("[InputReplay] Replay duration reached (%d frames). Quitting." % replay_total_frames)
		get_tree().quit()


func _unhandled_input(event: InputEvent) -> void:
	# F9 stops recording and saves.
	if mode == Mode.RECORDING and event is InputEventKey:
		if event.keycode == KEY_F9 and event.pressed and not event.echo:
			save_recording()
			mode = Mode.DISABLED
			print("[InputReplay] Recording stopped. %d events saved." % recorded_events.size())


func _notification(what: int) -> void:
	if what == NOTIFICATION_WM_CLOSE_REQUEST and mode == Mode.RECORDING:
		save_recording()


func save_recording() -> void:
	var data := {
		"fps": Engine.physics_ticks_per_second,
		"level": GameManager.current_level,
		"difficulty": GameManager.current_difficulty,
		"total_frames": physics_frame,
		"events": recorded_events,
	}
	var file := FileAccess.open(replay_path, FileAccess.WRITE)
	if file:
		file.store_string(JSON.stringify(data, "\t"))
		print("[InputReplay] Saved %d events to %s" % [recorded_events.size(), replay_path])
	else:
		push_error("[InputReplay] Failed to write: %s" % replay_path)
