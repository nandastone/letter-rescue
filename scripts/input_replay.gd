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
var recording_start: Dictionary = {}

# Replay state.
var replay_events: Array = []
var replay_index: int = 0  # Next event to process.
var replay_finished: bool = false
var replay_total_frames: int = 0  # Target duration; quit when we hit it.
var current_input_frame: int = -1
var source_start_frame: int = 0
var source_sha256: String = ""
var replay_sha256: String = ""
var original_start_background_frame: int = -1 # Optional measured replay-start phase.
var original_clock_phase_seconds: float = 0.0 # Sub-update phase of a measured replay slice.
var source_fps: float = 0.0 # Native frontend rate; 0 uses the Godot physics delta.
var source_clock_quantum_seconds: float = 0.0
var source_clock_phase_seconds: float = 0.0
var original_entity_start: Dictionary = {} # Measured initial actors/RNG; never future outcomes.
var original_picture_start: Dictionary = {}
var original_level_start: Dictionary = {} # One untouched post-load checkpoint, never later updates.
var original_start_seed: int = -1 # New live recordings save their one initial 16-bit seed.
var original_video_start: Dictionary = {} # Initial VGA phase, never a future frame schedule.
var original_music_clock: Dictionary = {} # Initial IRQ/CMF state; no future admission times.
var frontend_clock: RefCounted
var frontend_clock_frame: int = -1
var frontend_clock_seconds: float = 0.0
var video_capture_active: bool = false # Internal raster draws are not frontend frames.
var logical_inputs: Array = [] # Optional headless control-only diagnostic, indexed by update.
var logical_inputs_sha256: String = ""
var demo_inputs: Array = [] # Original .D file controls, not observed outcomes.
var demo_input_offset: int = 0
var demo_sha256: String = ""
var demo_mode: bool = false

# Auto-start: skip menu and jump straight into the game.
var auto_start_level: int = -1
var auto_start_difficulty: int = -1
var replay_character: String = "girl"

# Optional early-quit override (for tight iteration on frame-0 pixel-exact work).
# Set via `--max-frame N` on the CLI; quits at physics frame N regardless of
# whether the replay's total_frames has been reached.
var max_frame: int = -1


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	process_physics_priority = -100 # Supply this frame's inputs before Player runs.

	# Parse CLI args (everything after "--").
	var args := LaunchArgs.user_args()
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
	var seed_option := args.find("--original-seed")
	if seed_option >= 0:
		if mode == Mode.REPLAYING or seed_option + 1 >= args.size() or not args[seed_option + 1].is_valid_int():
			push_error("--original-seed requires an integer for live play; replays use their saved seed")
			get_tree().quit(1)
			return
		original_start_seed = int(args[seed_option + 1])
		if original_start_seed < 0 or original_start_seed > 65535:
			push_error("--original-seed must be between 0 and 65535")
			get_tree().quit(1)
			return
	var logical_arg := args.find("--logical-inputs")
	if logical_arg >= 0:
		assert(mode == Mode.REPLAYING and DisplayServer.get_name() == "headless")
		assert(logical_arg + 1 < args.size())
		var path: String = args[logical_arg + 1]
		var controls: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(path))
		assert(controls.source_sha256 == source_sha256 and controls.replay_sha256 == replay_sha256)
		logical_inputs = controls.inputs
		assert(not logical_inputs.is_empty())
		for entry in logical_inputs:
			assert(entry is Dictionary and entry.size() == 5)
			for key in ["up", "down", "left", "right", "slime_request"]:
				assert(entry.has(key) and entry[key] is bool)
		logical_inputs_sha256 = FileAccess.get_sha256(path)


func _start_recording() -> void:
	mode = Mode.RECORDING
	recorded_events.clear()
	recording_start.clear()
	physics_frame = 0
	for action in ACTIONS:
		action_state[action] = false
	print("[InputReplay] Recording to: ", replay_path)


func _start_replay(path: String = "") -> void:
	if not path.is_empty():
		replay_path = path
	frontend_clock_frame = -1
	frontend_clock_seconds = 0.0
	frontend_clock = null
	var file := FileAccess.open(replay_path, FileAccess.READ)
	if not file:
		push_error("[InputReplay] Cannot open replay file: %s" % replay_path)
		return

	var json := JSON.new()
	if json.parse(file.get_as_text()) != OK:
		push_error("[InputReplay] Invalid JSON in replay file.")
		return

	var data: Dictionary = json.data
	demo_inputs = data.get("original_demo_inputs", [])
	demo_mode = not demo_inputs.is_empty()
	demo_input_offset = int(data.get("demo_input_offset", 0))
	if demo_mode:
		demo_sha256 = data.demo_provenance.sha256
		for entry in demo_inputs:
			assert(entry is Dictionary and entry.size() == 5)
			for key in ["up", "down", "left", "right", "slime_request"]:
				assert(entry.has(key) and entry[key] is bool)
	original_entity_start = data.get("original_entity_start", {})
	original_picture_start = data.get("original_picture_start", {})
	original_level_start = data.get("original_level_start", {})
	var saved_seed = data.get("original_start_seed", -1)
	if data.has("original_start_seed") and (typeof(saved_seed) not in [TYPE_INT, TYPE_FLOAT]
			or not is_finite(float(saved_seed)) or float(saved_seed) != floor(float(saved_seed))
			or float(saved_seed) < 0 or float(saved_seed) > 65535):
		push_error("Replay original_start_seed must be an integer between 0 and 65535")
		get_tree().quit(1)
		return
	original_start_seed = int(saved_seed)
	if original_start_seed >= 0 and (demo_mode or not original_level_start.is_empty()
			or not original_entity_start.is_empty() or not original_picture_start.is_empty()
			or not data.get("original_music_clock", {}).is_empty()
			or not data.get("original_video_start", {}).is_empty()):
		push_error("Replay must use either a fresh-game seed or a measured native checkpoint")
		get_tree().quit(1)
		return
	original_music_clock = data.get("original_music_clock", {})
	if not original_music_clock.is_empty():
		frontend_clock = preload("res://scripts/wr1_frontend_clock.gd").new()
		frontend_clock.configure(original_music_clock)
	original_video_start = data.get("original_video_start", {})
	if not preload("res://scripts/wr1_video_clock.gd").valid_timing(original_video_start):
		push_error("[InputReplay] Invalid initial VGA timing.")
		get_tree().quit(1)
		return
	action_state.clear()
	for action in ACTIONS:
		action_state[action] = false
	replay_sha256 = FileAccess.get_sha256(replay_path)

	var replay_fps: int = int(data.get("fps", 70))
	if Engine.physics_ticks_per_second != replay_fps:
		push_error("[InputReplay] Physics tick rate mismatch: engine=%d Hz, replay=%d Hz. Set physics/common/physics_ticks_per_second=%d in project.godot." % [Engine.physics_ticks_per_second, replay_fps, replay_fps])
		get_tree().quit(1)
		return

	replay_events = data.get("events", [])
	replay_index = 0
	replay_finished = false
	replay_total_frames = int(data.get("total_frames", 0))
	source_start_frame = int(data.get("source_start_frame", 0))
	source_sha256 = str(data.get("source_sha256", ""))
	source_fps = float(data.get("source_fps", 0.0))
	source_clock_quantum_seconds = float(data.get("source_clock_quantum_seconds", 0.0))
	source_clock_phase_seconds = float(data.get("source_clock_phase_seconds", 0.0))
	if (not is_finite(source_clock_quantum_seconds) or not is_finite(source_clock_phase_seconds)
			or source_clock_quantum_seconds < 0.0 or source_clock_quantum_seconds > 0.1
			or source_clock_phase_seconds < 0.0
			or (source_clock_quantum_seconds == 0.0 and source_clock_phase_seconds != 0.0)
			or (source_clock_quantum_seconds > 0.0
				and (source_fps <= 0.0 or source_clock_phase_seconds >= source_clock_quantum_seconds))):
		push_error("[InputReplay] Invalid source clock quantum or phase.")
		get_tree().quit(1)
		return
	if not is_finite(source_fps) or source_fps < 0.0 or source_fps > 1000.0:
		push_error("[InputReplay] Source frame rate must be positive and at most 1000, or 0 for default.")
		get_tree().quit(1)
		return
	original_start_background_frame = int(data.get("original_start_background_frame", -1))
	original_clock_phase_seconds = float(data.get("original_clock_phase_seconds", 0.0))
	if not is_finite(original_clock_phase_seconds) or original_clock_phase_seconds < 0.0 or original_clock_phase_seconds >= 12428.0 * 8.0 / 1193182.0:
		push_error("[InputReplay] Original clock phase must be within one logical update.")
		get_tree().quit(1)
		return
	if original_start_background_frame < -1 or original_start_background_frame > 3:
		push_error("[InputReplay] Original background phase must be 0..3, or -1 for default.")
		get_tree().quit(1)
		return
	physics_frame = 0
	current_input_frame = -1
	mode = Mode.REPLAYING

	# Configure game state to match the recording.
	auto_start_level = data.get("level", 1)
	auto_start_difficulty = data.get("difficulty", 0)
	GameManager.original_speed_ticks = clampi(int(data.get("original_speed_ticks",8)),0,65535)
	GameManager.original_pending_profile = data.get("original_profile_start",{})
	replay_character = str(data.get("character", "girl"))

	print("[InputReplay] Replaying from: %s  (%d events, level %d, %d frames)" % [
		replay_path, replay_events.size(), auto_start_level, replay_total_frames
	])

	# Apply game settings and skip menu on next frame.
	_auto_start_game.call_deferred(replay_path,replay_sha256)


func _auto_start_game(expected_path: String = "", expected_hash: String = "") -> void:
	# An attract-menu key may cancel before this deferred scene launch runs.
	if not expected_path.is_empty() and (mode != Mode.REPLAYING or replay_path != expected_path or replay_sha256 != expected_hash):
		return
	GameManager.current_level = auto_start_level
	GameManager.current_difficulty = auto_start_difficulty
	GameManager.score = int(original_level_start.get("score", 0))
	if not GameManager.original_pending_profile.is_empty():
		GameManager.score = int(GameManager.original_pending_profile.score)
	if GameManager.original_demo_host != null:
		GameManager.original_demo_host.launch_demo_game()
		return
	get_tree().change_scene_to_file("res://scenes/game.tscn")

func finish_original_demo() -> void:
	if GameManager.original_demo_host != null:
		GameManager.original_demo_host.next_demo.call_deferred()
	else:
		get_tree().quit()


func original_frame_seconds(fallback: float) -> float:
	if current_input_frame < 0 or source_fps <= 0.0:
		return fallback
	if frontend_clock != null:
		if frontend_clock_frame != current_input_frame:
			assert(current_input_frame == frontend_clock_frame + 1, "Skipped native frontend interval")
			frontend_clock_seconds = frontend_clock.next_seconds()
			frontend_clock_frame = current_input_frame
		return frontend_clock_seconds
	if source_clock_quantum_seconds == 0.0:
		return 1.0 / source_fps
	# DOSBox Pure services its frame handoff on millisecond emulation ticks.
	# Preserve that quantization instead of accumulating an ideal video period.
	var before: float = source_clock_phase_seconds + current_input_frame / source_fps
	var after: float = source_clock_phase_seconds + (current_input_frame + 1) / source_fps
	return (ceil(after / source_clock_quantum_seconds) - ceil(before / source_clock_quantum_seconds)) * source_clock_quantum_seconds


func original_action_pressed(action: String) -> bool:
	# Focus changes can clear the OS/Input held state between recorded events.
	# Original-rule replays must keep using the recorded controls until release.
	if mode == Mode.REPLAYING or replay_finished:
		return bool(action_state.get(action, false))
	if GameManager.original_joystick:
		var devices := Input.get_connected_joypads()
		if not devices.is_empty():
			var device: int = devices[0]
			var stick := Vector2(Input.get_joy_axis(device,JOY_AXIS_LEFT_X),Input.get_joy_axis(device,JOY_AXIS_LEFT_Y)) - GameManager.original_joystick_center
			var joy := {"move_left":stick.x < -0.25 or Input.is_joy_button_pressed(device,JOY_BUTTON_DPAD_LEFT),
				"move_right":stick.x > 0.25 or Input.is_joy_button_pressed(device,JOY_BUTTON_DPAD_RIGHT),
				"jump":stick.y < -0.25 or Input.is_joy_button_pressed(device,JOY_BUTTON_DPAD_UP),
				"move_down":stick.y > 0.25 or Input.is_joy_button_pressed(device,JOY_BUTTON_DPAD_DOWN),
				"use_slime":Input.is_joy_button_pressed(device,JOY_BUTTON_A) or Input.is_joy_button_pressed(device,JOY_BUTTON_B)}
			if joy.get(action,false): return true
	return Input.is_action_pressed(action)

func record_setting(setting: String, value: int) -> void:
	if mode == Mode.RECORDING and not recording_start.is_empty():
		recorded_events.append({"frame":physics_frame,"setting":setting,"value":value})


func logical_controls(tick: int) -> Dictionary:
	assert(tick >= 1 and tick <= logical_inputs.size())
	return logical_inputs[tick - 1].duplicate()


func demo_controls(tick: int) -> Dictionary:
	assert(tick >= 1 and tick <= demo_inputs.size())
	return demo_inputs[tick - 1].duplicate()


func completed_logical_update(tick: int) -> void:
	if not logical_inputs.is_empty() and tick == logical_inputs.size():
		get_tree().quit()


func _physics_process(_delta: float) -> void:
	if mode == Mode.REPLAYING or mode == Mode.RECORDING:
		var scene := get_tree().current_scene
		if scene == null or not scene.has_method("is_replay_ready") or not scene.is_replay_ready():
			return # Loading time must not consume or lose frame-zero input.
	match mode:
		Mode.RECORDING:
			_record_frame()
		Mode.REPLAYING:
			_replay_frame()
	physics_frame += 1


func _record_frame() -> void:
	if recording_start.is_empty():
		# Save the starting level even if this recording later crosses an exit.
		recording_start = {"level": GameManager.current_level,
			"difficulty": GameManager.current_difficulty, "character": replay_character}
		var recorded_player := get_tree().current_scene.get_node_or_null("Player")
		if recorded_player != null:
			recording_start.character = recorded_player.original_character
		var scene := get_tree().current_scene
		recording_start.original_speed_ticks = GameManager.original_speed_ticks
		if scene.get("original_loaded_profile") != null and not scene.original_loaded_profile.is_empty():
			recording_start.original_profile_start = scene.original_loaded_profile.duplicate(true)
		if scene.original_start_seed >= 0:
			recording_start.original_start_seed = scene.original_start_seed
	for action in ACTIONS:
		var pressed := original_action_pressed(action)
		if pressed != action_state[action]:
			action_state[action] = pressed
			recorded_events.append({
				"frame": physics_frame,
				"action": action,
				"pressed": pressed,
			})


func _replay_frame() -> void:
	current_input_frame = physics_frame
	# Inject all events scheduled for the current frame (if any still pending).
	while replay_index < replay_events.size():
		var ev: Dictionary = replay_events[replay_index]
		var ev_frame: int = int(ev["frame"])
		if ev_frame > physics_frame:
			break  # Future event; wait.
		if ev.has("setting"):
			match ev.setting:
				"speed": GameManager.original_speed_ticks = clampi(int(ev.value),0,65535)
				"difficulty":
					GameManager.current_difficulty = clampi(int(ev.value),0,2)
					get_tree().current_scene.apply_original_difficulty(GameManager.current_difficulty)
				_: push_error("Unknown recorded original setting: " + str(ev.setting))
			replay_index += 1
			continue

		var ev_action: String = ev["action"]
		var ev_pressed: bool = ev["pressed"]
		action_state[ev_action] = ev_pressed

		var input_ev := InputEventAction.new()
		input_ev.action = ev_action
		input_ev.pressed = ev_pressed
		input_ev.strength = 1.0 if ev_pressed else 0.0
		Input.parse_input_event(input_ev)

		replay_index += 1
	# parse_input_event may buffer events until after this physics iteration.
	# Flush so held-state queries and _input handlers see this frame's changes.
	Input.flush_buffered_events()

	# Early-quit override for tight iteration (--max-frame N).
	if max_frame > 0 and physics_frame + 1 >= max_frame:
		print("[InputReplay] max-frame override (%d) reached. Quitting." % max_frame)
		get_tree().quit()
		return

	# Quit when we've run for the recording's full duration. This keeps the
	# clone alive for the same number of frames as the reference, even when
	# the event list is short (or empty) — so every reference frame has a
	# test-side counterpart to diff against.
	if not logical_inputs.is_empty() or demo_mode:
		# A divergent route must fail within a bounded duration, never hang.
		if physics_frame > replay_total_frames * 2 + 700:
			push_error("Update-input replay exceeded its duration budget")
			get_tree().quit(1)
		return
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
		"level": recording_start.get("level", GameManager.current_level),
		"difficulty": recording_start.get("difficulty", GameManager.current_difficulty),
		"character": recording_start.get("character", replay_character),
		"total_frames": physics_frame,
		"events": recorded_events,
	}
	if recording_start.has("original_start_seed"):
		data.original_start_seed = recording_start.original_start_seed
	for key in ["original_speed_ticks","original_profile_start"]:
		if recording_start.has(key): data[key] = recording_start[key]
	var file := FileAccess.open(replay_path, FileAccess.WRITE)
	if file:
		file.store_string(JSON.stringify(data, "\t"))
		print("[InputReplay] Saved %d events to %s" % [recorded_events.size(), replay_path])
	else:
		push_error("[InputReplay] Failed to write: %s" % replay_path)
