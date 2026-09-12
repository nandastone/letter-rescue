extends SceneTree
## Focused smoke test for the default game's hidden mode.
##
##   godot --headless --fixed-fps 120 --path . \
##     --script tools/smoke_berserker_mode.gd -- \
##     --replay data/wr1/demos/level1.json

var waited := 0


func _initialize() -> void:
	change_scene_to_file.call_deferred("res://scenes/game.tscn")
	process_frame.connect(_check)


func _check() -> void:
	waited += 1
	var game := current_scene
	if game == null or not game.has_method("is_replay_ready") or not game.is_replay_ready():
		if waited > 2400:
			_fail("game never became ready")
		return
	process_frame.disconnect(_check)
	var mode: Node = game.berserker_mode
	if mode == null or mode.active:
		_fail("default game did not create an inactive berserker mode")
		return
	_type_code(mode, "IDKFA")
	if not mode.active or not mode.tint.visible or not mode.weapon.visible:
		_fail("IDKFA did not enable the visuals")
		return

	var p: RefCounted = game.player.original_state
	var direction := -1 if p.facing == 1 else 1
	var target_x: int = p.gx + direction * 2
	var timer_count: int = game.original_gruzzles.timers.size()
	game.original_gruzzles.actors.append({"gx": target_x, "gy": p.gy, "type": 0,
		"state": -1, "animation_index": 0, "jump_phase": -1})
	var manager := root.get_node("GameManager")
	var score_before: int = manager.score
	var sound_before: int = manager.original_sound
	manager.original_sound = 2 # Headless AudioServer retains a playing WAV at shutdown.
	game._try_use_slime()
	manager.original_sound = sound_before
	for actor in game.original_gruzzles.actors:
		if int(actor.gx) == target_x and int(actor.gy) == p.gy:
			_fail("shotgun left its guaranteed target alive")
			return
	if manager.score <= score_before:
		_fail("shotgun hit did not award points")
		return
	if game.original_gruzzles.timers.size() != timer_count:
		_fail("shotgun compacted the engine's fixed actor cadence slots")
		return
	var args := OS.get_cmdline_user_args()
	var screenshot_arg := args.find("--screenshot")
	if screenshot_arg >= 0 and screenshot_arg + 1 < args.size():
		var screenshot_path: String = args[screenshot_arg + 1]
		RenderingServer.frame_post_draw.connect(func() -> void:
			var image := root.get_texture().get_image()
			if image == null or image.save_png(screenshot_path) != OK:
				_fail("could not save the requested screenshot")
				return
			_finish(mode), CONNECT_ONE_SHOT)
		return
	_finish(mode)


func _finish(mode: Node) -> void:
	_type_code(mode, "IDKFA")
	if mode.active or mode.tint.visible or mode.weapon.visible:
		_fail("second IDKFA did not disable the mode")
		return
	print("berserker smoke: code, visuals, blast and toggle passed")
	mode.shot_player.stop()
	mode.shot_player.stream = null
	current_scene.queue_free()
	process_frame.connect(_quit_after_cleanup, CONNECT_ONE_SHOT)


func _quit_after_cleanup() -> void:
	process_frame.connect(func() -> void: quit(0), CONNECT_ONE_SHOT)


func _type_code(mode: Node, code: String) -> void:
	for letter in code:
		var event := InputEventKey.new()
		event.unicode = letter.unicode_at(0)
		event.pressed = true
		mode.handle_key(event)


func _fail(message: String) -> void:
	printerr("berserker smoke FAILED: " + message)
	quit(1)
