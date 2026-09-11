extends SceneTree
## A real recording with menu/title time and gameplay controls.
func _initialize() -> void:
	_run.call_deferred()

func _run() -> void:
	var input = root.get_node("InputReplay")
	# Stand in the actual main menu before starting, as --record normally does.
	change_scene_to_file("res://scenes/main_menu.tscn")
	for i in range(12):
		await process_frame
	assert(input.physics_frame == 0)
	if "--profile-settings" in OS.get_cmdline_user_args():
		var gm := root.get_node("GameManager")
		var words := preload("res://scripts/wr1_words.gd").new()
		words.next_words()
		words.next_words()
		gm.current_level = 5
		gm.current_difficulty = 1
		gm.score = 12345
		gm.original_speed_ticks = 6
		gm.original_pending_profile = {"level":5,"character":0,"word_cursor":words.offset,
			"score":12345,"words":words.words,"difficulty":1,"custom_keys":false,
			"scancodes":[77,75,72,80,57],"joystick":false}
	change_scene_to_file("res://scenes/game.tscn")
	for i in range(12):
		await process_frame
	assert(input.physics_frame == 0)
	assert(current_scene.original_level_title != null)
	physics_frame.connect(_controls)
	# Let the title expire naturally. All input is then indexed after readiness.
	while not current_scene.is_replay_ready():
		await process_frame
	while input.physics_frame < 70:
		await process_frame
	# A later level/difficulty must not overwrite the session's starting settings.
	root.get_node("GameManager").current_level = 2
	root.get_node("GameManager").current_difficulty = 2
	input.save_recording()
	print("Record roundtrip PASS")
	quit()

func _controls() -> void:
	if not current_scene.is_replay_ready():
		return
	if "--profile-settings" in OS.get_cmdline_user_args():
		var replay := root.get_node("InputReplay")
		var gm := root.get_node("GameManager")
		if replay.physics_frame == 10:
			gm.original_speed_ticks = 4
			replay.record_setting("speed",4)
		if replay.physics_frame == 30:
			gm.current_difficulty = 2
			current_scene.apply_original_difficulty(2)
			replay.record_setting("difficulty",2)
	match root.get_node("InputReplay").physics_frame:
		0: Input.action_press("move_right")
		21: Input.action_release("move_right")
		35: Input.action_press("jump")
		56: Input.action_release("jump")
