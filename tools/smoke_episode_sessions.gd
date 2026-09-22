extends SceneTree
## Check live level changes, demos and return to the same suspended game.
var frames := 0
func _initialize() -> void:
	process_frame.connect(func():
		frames += 1
		if frames > 10000:
			printerr("Episode session check timed out")
			quit(1))
	_run.call_deferred()

func _run() -> void:
	var manager = root.get_node("GameManager")
	var replay = root.get_node("InputReplay")
	for episode in [2, 3]:
		Episode.select(episode)
		manager.current_level = 1
		manager.current_difficulty = 0
		manager.original_player_name = ""
		manager.original_pending_profile = {}
		replay.original_start_seed = 20716
		replay.mode = replay.Mode.REPLAYING
		var game = load("res://scenes/game.tscn").instantiate()
		root.add_child(game)
		current_scene = game
		while not game.is_replay_ready(): await process_frame
		replay.mode = replay.Mode.DISABLED
		manager.apply_default_tick_rate()
		# Use real warp and cached-level rebuild, including the new upper bound.
		game.warp_to_original_level(20)
		while not game.is_replay_ready(): await process_frame
		assert(manager.current_level == 20 and game.word_manager.blocks.size() == 7)
		game.player.set_physics_process(false)
		game.finish_original_exit({},0)
		var ending = game.get_child(game.get_child_count()-1)
		assert(ending.state == "ending")
		ending.queue_free()
		await process_frame
		# Re-open a regular playable map for the suspended-session check.
		manager.current_level = 19
		game.replay_ready = true
		game.warp_to_original_level(1)
		while not game.is_replay_ready(): await process_frame
		game.open_original_frontend("menu")
		var menu = game.get_child(game.get_child_count()-1)
		var before: Dictionary = game.original_interaction_snapshot()
		var words: Array = game.original_words.words.duplicate()
		menu.begin_demos()
		for index in range(6):
			while current_scene == game or current_scene == null or not current_scene.is_replay_ready() or current_scene.player.original_state.ticks < 3:
				await process_frame
			assert(replay.content_demo and replay.demo_mode and Episode.current == episode)
			assert(current_scene.original_words.words == words, "Demo replaced the current word set")
			assert(current_scene.player.original_character == "boy")
			if index < 5:
				var previous: Node = current_scene
				menu.next_demo(false)
				while current_scene == previous: await process_frame
		menu.finish_demos()
		while current_scene != game: await process_frame
		assert(not replay.demo_mode and not replay.content_demo)
		assert(Engine.physics_ticks_per_second == manager.DEFAULT_TICKS_PER_SECOND)
		assert(game.original_interaction_snapshot() == before)
		assert(game.original_words.words == words)
		assert(manager.current_level == 1 and menu.state == "menu")
		menu.press(KEY_ESCAPE)
		await process_frame
		# Test cancellation before a deferred demo scene is launched.
		game.open_original_frontend("menu")
		menu = game.get_child(game.get_child_count()-1)
		menu.begin_demos()
		menu.press(KEY_ESCAPE)
		for frame in range(4): await process_frame
		assert(current_scene == game and not replay.demo_mode)
		game.queue_free()
		await process_frame
		current_scene = null
		print("Episode %d: warp20, six demo starts, cancellation and live-session restoration passed" % episode)
	quit()
