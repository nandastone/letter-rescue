extends SceneTree
## UI lifecycle integration, independent of the post-load demo clocks.
const Title = preload("res://scripts/core/wr1_level_title.gd")

func _initialize() -> void:
	_run.call_deferred()

func _run() -> void:
	var output := OS.get_cmdline_user_args()[-1]
	for level in range(1, 16):
		assert(Title.render(level).save_png(output.path_join("title-%02d.png" % level)) == OK)
	var manager = root.get_node("GameManager")
	manager.current_level = 1
	var game = load("res://scenes/game.tscn").instantiate()
	root.add_child(game)
	current_scene = game
	await process_frame
	await process_frame
	assert(game.original_level_title != null)
	assert(not game.is_replay_ready())
	assert(not game.player.is_physics_processing())
	# A release or keyboard autorepeat must not skip the opening card.
	var key := InputEventKey.new()
	key.keycode = KEY_SPACE
	Input.parse_input_event(key)
	key = key.duplicate()
	key.pressed = true
	key.echo = true
	Input.parse_input_event(key)
	await process_frame
	assert(game.original_level_title != null)
	key.echo = false
	Input.parse_input_event(key)
	key = InputEventKey.new()
	key.keycode = KEY_SPACE
	Input.parse_input_event(key)
	for i in range(4):
		await process_frame
	assert(game.is_replay_ready())
	assert(game.original_level_title == null)
	assert(game.player.is_physics_processing())
	# Native cached death resets rebuild directly, without a title or title delay.
	game.restart_original_level()
	assert(game.original_level_title == null)
	await process_frame
	await process_frame
	assert(game.is_replay_ready())
	# Exercise the fresh-map presentation seam without writing player save data.
	manager.current_level = 2
	game.level_data = LevelLoader.load_level(LevelLoader.get_level_path(2))
	await game._show_original_level_title(false)
	assert(game.original_level_title != null)
	assert(not game.is_replay_ready())
	assert(not game.player.is_physics_processing())
	assert(not game.original_level_title.waiting)
	game._build_level_from_data()
	await process_frame
	await process_frame
	assert(game.original_level_title == null)
	assert(game.is_replay_ready())
	# The opening timeout must also release the wait without keyboard input.
	var title = Title.new()
	title.configure(1)
	root.add_child(title)
	title.wait_for_start()
	await create_timer(3.25).timeout
	assert(not title.waiting)
	title.queue_free()
	print("Level titles: render, keyboard, timeout, cached restart and fresh-load lifecycle PASS")
	quit()
