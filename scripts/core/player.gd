extends Node2D

var is_dead: bool = false

const WR1Motion = preload("res://scripts/core/wr1_motion.gd")
var original_state
var original_sprite: Sprite2D
var original_elapsed: float = 0.0
var original_music_clock: RefCounted
var original_trace: FileAccess
var original_rescue: RefCounted
var original_recap: RefCounted
var original_recap_skip_requested: bool = false
var original_exit: RefCounted
var original_exit_held: Dictionary
var original_exit_source_frame: int = -1
var original_spawn: Vector2i
var original_death_held: Dictionary
var original_death_source_frame: int = -1
var original_rescue_layer: CanvasLayer
var original_rescue_backdrop: ColorRect
var original_rescue_sprite: Sprite2D
var original_character: String = "girl"
signal original_presented(state: RefCounted)
signal original_moved(state: RefCounted)

func configure_original(data: Dictionary, restarting: bool = false, advancing: bool = false) -> void:
	z_index = 3 # Original draws the player over word cards, below foreground tiles.
	var previous_background: int = original_state.background_frame if original_state != null else 0
	var first_configuration: bool = original_state == null
	if original_state == null and InputReplay.original_start_background_frame >= 0:
		# configure renders once; arrange for that draw to reproduce the sampled phase.
		previous_background = (InputReplay.original_start_background_frame + 3) % 4
	if restarting:
		# Cached-level reset retains motion phase and main-loop local counters.
		var spawn_state = WR1Motion.new()
		spawn_state.configure(data)
		if advancing:
			original_spawn = Vector2i(spawn_state.x, spawn_state.y - 8)
		original_state.attributes = data.attributes
		original_state.width = spawn_state.width
		original_state.height = spawn_state.height
		original_state.camera_x = spawn_state.camera_x
		original_state.camera_y = spawn_state.camera_y
		original_state.x = spawn_state.x if advancing else original_spawn.x
		original_state.y = spawn_state.y if advancing else original_spawn.y
		original_state.gx = int(float(original_state.x - 16) / 8.0) + original_state.camera_x - 1
		original_state.gy = int(float(original_state.y - 31) / 8.0) + original_state.camera_y
		original_state.frame = 0
		original_state.facing = 0
	else:
		original_state = WR1Motion.new()
		original_state.configure(data)
		original_spawn = Vector2i(original_state.x, original_state.y - 8)
		original_state.background_frame = previous_background
		if InputReplay.original_level_start.is_empty():
			original_state.render_step()
		else:
			# The checkpoint is already rendered. An extra render would scroll the
			# camera and advance animation before the first measured input.
			var initial: Dictionary = InputReplay.original_level_start
			for key in ["x", "y", "gx", "gy", "camera_x", "camera_y", "phase",
					"facing", "background_frame", "idle_ticks", "left_index", "right_index"]:
				original_state.set(key, int(initial[key]))
			original_state.frame = int(initial.sprite)
		original_elapsed = 0.0
	if first_configuration:
		original_elapsed = InputReplay.original_clock_phase_seconds
		if LaunchArgs.legacy() and not InputReplay.original_music_clock.is_empty():
			original_music_clock = load("res://scripts/legacy/wr1_music_clock.gd").new()
			original_music_clock.configure(InputReplay.original_music_clock)
	if original_sprite == null:
		original_sprite = Sprite2D.new()
		var user_args := LaunchArgs.user_args()
		var character_arg := user_args.find("--character")
		var character := InputReplay.replay_character
		if character_arg >= 0 and character_arg + 1 < user_args.size() and user_args[character_arg + 1] in ["boy", "girl"]:
			character = user_args[character_arg + 1]
		original_character = character
		original_sprite.texture = load("res://assets/sprites/wr1_%s.png" % character)
		original_sprite.hframes = 26
		original_sprite.position = Vector2(0, -16)
		add_child(original_sprite)
	_present_original()
	var args := LaunchArgs.user_args()
	var trace_arg := args.find("--state-trace")
	if original_trace == null and trace_arg >= 0 and trace_arg + 1 < args.size():
		original_trace = FileAccess.open(args[trace_arg + 1], FileAccess.WRITE)
		if original_trace == null:
			push_error("Cannot open original-rule state trace: " + args[trace_arg + 1])

func _present_original(queue_video: bool = true) -> void:
	# Godot's player anchor is bottom-center; WR1 uses sprite left/bottom.
	global_position = Vector2(original_state.world_position()) + Vector2(-4, -32)
	original_sprite.frame = original_state.frame
	get_node("../Camera").apply_original(original_state)
	original_presented.emit(original_state)
	if queue_video and get_parent().has_method("queue_original_video"):
		# Recap pauses the main timer. Its scene and overlay writes must share
		# the active recap clock or the video queue can reverse their order.
		var elapsed: float = original_recap.elapsed if original_recap != null else original_elapsed
		get_parent().queue_original_video(elapsed, original_state.ticks > 0
			and original_recap == null and original_rescue == null and original_exit == null)

func _record_original(held: Dictionary, entry_source_frame: int = -1) -> void:
	if original_trace == null:
		return
	var row: Dictionary = original_state.snapshot()
	if get_parent().has_method("original_interaction_snapshot"):
		row.merge(get_parent().original_interaction_snapshot())
	row["physics_frame"] = Engine.get_physics_frames()
	if InputReplay.current_input_frame >= 0:
		row["replay_frame"] = InputReplay.current_input_frame
		row["source_frame"] = InputReplay.source_start_frame + InputReplay.current_input_frame
		row["completed_source_frame"] = row["source_frame"]
		if entry_source_frame >= 0:
			row["source_frame"] = entry_source_frame
			row["replay_frame"] = entry_source_frame - InputReplay.source_start_frame
		row["source_sha256"] = InputReplay.source_sha256
		row["replay_sha256"] = InputReplay.replay_sha256
	row["held"] = held
	if InputReplay.demo_mode:
		row["input_clock"] = "native_demo"
		row["demo_sha256"] = InputReplay.demo_sha256
		if original_state.ticks > 0:
			row["demo_input_index"] = InputReplay.demo_input_offset + original_state.ticks - 1
	if not InputReplay.logical_inputs.is_empty():
		row["input_clock"] = "logical_update"
		row["logical_inputs_sha256"] = InputReplay.logical_inputs_sha256
	original_trace.store_line(JSON.stringify(row))
	original_trace.flush()
	InputReplay.completed_logical_update(original_state.ticks)

func _original_physics(delta: float) -> void:
	if original_state == null:
		return
	var music_admissions: Array = []
	if original_music_clock != null:
		music_admissions = original_music_clock.advance(InputReplay.original_frame_seconds(delta),
			original_recap == null and original_rescue == null and original_exit == null)
	if original_exit != null:
		if original_exit.advance(InputReplay.original_frame_seconds(delta), _present_original_exit):
			original_elapsed = original_exit.elapsed
			original_exit = null
			get_parent().finish_original_exit(original_exit_held, original_exit_source_frame)
		return
	if original_rescue != null:
		if original_rescue.advance(InputReplay.original_frame_seconds(delta), original_state, _present_rescue):
			original_elapsed = original_rescue.elapsed
			original_rescue = null
			_record_original(original_death_held, original_death_source_frame)
			if InputReplay.demo_mode:
				# 40C8..40CD returns from demo main after the rescue, without reset.
				get_parent().replay_ready = false
				InputReplay.finish_original_demo()
				return
			original_rescue_layer.hide()
			original_sprite.show()
			get_parent().restart_original_level()
		return
	if is_dead:
		return
	var frame_seconds: float = InputReplay.original_frame_seconds(delta)
	var step_seconds: float = maxi(1,GameManager.original_speed_ticks) * 12428.0 / 1193182.0
	if original_recap != null:
		if original_recap_skip_requested:
			if Input.is_action_pressed("ui_cancel"):
				original_recap.elapsed += frame_seconds
				return
			original_recap.skip()
			original_recap_skip_requested = false
		if not original_recap.advance(frame_seconds, original_state, get_parent().original_gruzzles.random_word,
				_present_original, get_parent().present_original_recap):
			return
		# The last helper leaves the main gate's timer at eight IRQs. The next
		# admission can run immediately; the recap itself does not count a tick.
		original_elapsed = original_recap.elapsed + (0.0 if original_recap.skipped else WR1Motion.STEP_SECONDS)
		if original_music_clock != null:
			music_admissions = [original_music_clock.resume_main(original_recap.elapsed)]
		original_recap = null
		get_parent().finish_original_recap()
		frame_seconds = 0.0
	# A replay physics iteration represents one native video frame. Its duration
	# can differ from Godot's integer physics rate (WR1 VGA is about 70.086 Hz).
	original_elapsed += frame_seconds
	if original_music_clock != null:
		assert(music_admissions.size() <= 1, "Multiple gameplay admissions in one frontend frame")
		if music_admissions.is_empty():
			return
		original_elapsed = (original_music_clock.now_ms - original_music_clock.origin_ms) / 1000.0 - music_admissions[0].at
	elif original_elapsed < step_seconds:
		return
	# One update only after a stall: WR1 resets its gate rather than catching up.
	# Keep sub-tick remainder during normal 70 Hz scheduling to avoid quantization.
	original_elapsed = fmod(original_elapsed, step_seconds)
	if get_parent().begin_original_recap():
		return
	if InputReplay.demo_mode and original_state.ticks >= InputReplay.demo_inputs.size():
		# The .D terminator is tested before movement at 373C.
		InputReplay.finish_original_demo()
		get_parent().replay_ready = false
		return
	var held := {"up": InputReplay.original_action_pressed("jump"), "down": InputReplay.original_action_pressed("move_down"),
		"left": InputReplay.original_action_pressed("move_left"), "right": InputReplay.original_action_pressed("move_right")}
	if not InputReplay.logical_inputs.is_empty():
		held = InputReplay.logical_controls(original_state.ticks + 1)
		get_parent().original_gruzzles.slime_request = held.slime_request
	elif InputReplay.demo_mode:
		held = InputReplay.demo_controls(original_state.ticks + 1)
		get_parent().original_gruzzles.slime_request = held.slime_request
	held["slime_request"] = get_parent().original_gruzzles.slime_request
	if AudioManager.original != null:
		AudioManager.original.movement_before(original_state, held.up)
	original_state.step(held.up, held.down, held.left, held.right)
	if AudioManager.original != null:
		AudioManager.original.movement_after(original_state)
	original_moved.emit(original_state)
	if original_state.gy >= original_state.height:
		# 40ac rolls the screen anchor back one cell; raw gy stays at the rim.
		original_state.y -= 8
		_begin_original_rescue(held)
		return
	if get_parent().original_presentation != null:
		get_parent().original_presentation.prepare_world()
	original_state.render_step()
	_present_original()
	if get_parent().original_door_state == 2:
		original_exit_held = held
		original_exit_source_frame = InputReplay.source_start_frame + InputReplay.current_input_frame if InputReplay.current_input_frame >= 0 else -1
		original_exit = preload("res://scripts/core/wr1_exit.gd").new()
		original_exit.begin(original_elapsed, not get_parent().original_gruzzles.slime_ever_used)
		get_parent().original_gruzzles.actors.clear()
		original_state.render_step()
		_present_original()
		return
	if get_parent().original_player_dead():
		_begin_original_rescue(held)
	else:
		_record_original(held)

func _begin_original_rescue(held: Dictionary) -> void:
	original_death_held = held
	original_death_source_frame = InputReplay.source_start_frame + InputReplay.current_input_frame if InputReplay.current_input_frame >= 0 else -1
	die()

func _present_original_exit(frame: int, bonus: bool, flash: int) -> void:
	get_parent().exit_door.present_original_frame(frame, bonus, flash)
	get_parent().queue_original_video(original_exit.elapsed)

func _present_rescue(kind: String, at: Vector2i) -> void:
	if kind in ["descend", "ascend"]:
		_present_original(false)
		original_sprite.visible = kind == "descend"
		original_rescue_backdrop.hide()
		original_rescue_sprite.hframes = 1
		original_rescue_sprite.texture = load("res://assets/sprites/wr1_rescue_%s.png" % ("down" if kind == "descend" else original_character))
		original_rescue_sprite.position = at
	else:
		original_sprite.hide()
		original_rescue_backdrop.show()
		original_rescue_sprite.texture = original_sprite.texture
		original_rescue_sprite.hframes = 26
		original_rescue_sprite.frame = original_state.frame
		original_rescue_sprite.position = Vector2(original_state.x, original_state.y - 31)
	original_rescue_sprite.show()
	get_parent().queue_original_video(original_rescue.elapsed)

func _physics_process(delta: float) -> void:
	_original_physics(delta)

func die() -> void:
	if is_dead:
		return
	is_dead = true
	original_rescue = preload("res://scripts/core/wr1_rescue.gd").new()
	AudioManager.play_original("death")
	original_rescue.begin(original_state, original_spawn, original_elapsed, original_music_clock)
	if original_rescue_layer == null:
		original_rescue_layer = CanvasLayer.new()
		original_rescue_layer.layer = 20
		add_child(original_rescue_layer)
		original_rescue_backdrop = ColorRect.new()
		original_rescue_backdrop.color = Color.BLACK
		original_rescue_backdrop.size = Vector2(320, 200)
		original_rescue_backdrop.mouse_filter = Control.MOUSE_FILTER_IGNORE
		original_rescue_layer.add_child(original_rescue_backdrop)
		original_rescue_sprite = Sprite2D.new()
		original_rescue_sprite.centered = false
		original_rescue_layer.add_child(original_rescue_sprite)
	original_rescue_layer.show()
	original_rescue_backdrop.hide()
	original_rescue_sprite.hide()
