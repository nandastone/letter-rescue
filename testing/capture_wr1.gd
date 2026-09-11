extends SceneTree
## Deterministic settled-start screenshot for legacy/original rendering checks.

func _initialize() -> void:
	if "--freeze-start" in OS.get_cmdline_user_args():
		paused = true
	run.call_deferred()

func run() -> void:
	var args := OS.get_cmdline_user_args()
	var settle := 20
	var settle_arg := args.find("--settle-frames")
	if settle_arg >= 0 and settle_arg + 1 < args.size():
		settle = int(args[settle_arg + 1])
	change_scene_to_file("res://scenes/game.tscn")
	for i in range(settle):
		await process_frame
	if "--interaction-preview" in args:
		var preview_player = current_scene.get_node("Player")
		preview_player.set_physics_process(false)
		current_scene.get_node("Entities").process_mode = Node.PROCESS_MODE_DISABLED
		preview_player.get_node("Hurtbox").monitoring = false
		Input.action_press("move_right")
		for i in range(7):
			preview_player._original_physics(preview_player.WR1Motion.STEP_SECONDS)
		Input.action_release("move_right")
		Input.action_press("jump")
		for i in range(8):
			preview_player._original_physics(preview_player.WR1Motion.STEP_SECONDS)
		Input.action_release("jump")
	await RenderingServer.frame_post_draw
	var index := args.find("--capture-output")
	if index < 0 or index + 1 >= args.size():
		push_error("Expected --capture-output <absolute path>")
		quit(1)
		return
	var output: String = args[index + 1]
	var error := root.get_texture().get_image().save_png(output)
	var player = current_scene.get_node("Player")
	if player.has_method("configure_original") and player.original_state != null:
		var file := FileAccess.open(output + ".json", FileAccess.WRITE)
		file.store_string(JSON.stringify(player.original_state.snapshot(), "  "))
	print("Captured ", output, " error=", error)
	quit(0 if error == OK else 1)
