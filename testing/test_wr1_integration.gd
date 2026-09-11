extends SceneTree

var failures: int = 0

func _initialize() -> void:
	run.call_deferred()

func run() -> void:
	change_scene_to_file("res://scenes/game.tscn")
	for i in range(20):
		await process_frame
		if current_scene != null and current_scene.get_node("Player").original_state != null:
			break
	var player = current_scene.get_node("Player")
	if player.original_state == null:
		push_error("Run this integration check with -- --original-rules")
		quit(1)
		return
	player.set_physics_process(false)
	if player.original_sprite.texture == null:
		push_error("Original sprite atlas failed to load")
		quit(1)
		return
	# This fixture tests movement/projection; legacy interaction rules are separate.
	player.collision_layer = 0
	player.get_node("Hurtbox").monitoring = false
	for fixture in ["wr1_left_walk", "wr1_full_jump"]:
		var trace: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://testing/fixtures/%s.json" % fixture))
		for key in trace.initial:
			if key not in ["world_x", "world_y"]:
				player.original_state.set("frame" if key == "sprite" else key, int(trace.initial[key]))
		player.original_elapsed = 0.0
		player.original_state.left_index = -1
		player.original_state.right_index = -1
		player._present_original()
		if fixture == "wr1_left_walk":
			Input.action_press("move_left")
		for update in trace.updates:
			var expected: Dictionary = update.get("state", update)
			if update.get("up", false):
				Input.action_press("jump")
			else:
				Input.action_release("jump")
			player._original_physics(player.WR1Motion.STEP_SECONDS)
			var state: Dictionary = player.original_state.snapshot()
			for key in expected:
				if state[key] != int(expected[key]):
					failures += 1
					push_error("Integrated native trace mismatch: %s %s" % [fixture, key])
			var screen_feet: Vector2 = player.get_canvas_transform() * player.global_position
			if screen_feet != Vector2(expected.x + 12, expected.y):
				failures += 1
				push_error("Projection mismatch: %s" % screen_feet)
			if player.original_sprite.frame != int(expected.sprite):
				failures += 1
		Input.action_release("move_left")
		Input.action_release("jump")
	var before: int = player.original_state.ticks
	player.original_elapsed = 0.0
	for i in range(70):
		player._original_physics(1.0 / 70.0)
	if player.original_state.ticks - before != 12:
		failures += 1
		push_error("Nominal clock must produce 12 updates in 70 physics ticks")
	before = player.original_state.ticks
	player._original_physics(1.0)
	if player.original_state.ticks - before != 1:
		failures += 1
		push_error("A stalled frame must not replay a backlog of movement")
	print("WR1 integration: 26 native updates, projection, sprite and clock checks, %d failures" % failures)
	quit(1 if failures else 0)
