extends SceneTree
## Exercise the actual transition path through all fifteen maps, including EOF.
var failures := 0
var checks := 0

func check(ok: bool, message: String) -> void:
	checks += 1
	if not ok:
		failures += 1
		push_error(message)

func _initialize() -> void:
	run.call_deferred()

func run() -> void:
	var manager = root.get_node("GameManager")
	var replay = root.get_node("InputReplay")
	replay.mode = replay.Mode.REPLAYING # Test transitions must not write save data.
	replay.set_physics_process(false)
	replay.set_process(false)
	manager.current_level = 1
	change_scene_to_file("res://scenes/game.tscn")
	for i in range(30):
		await process_frame
		if current_scene != null and current_scene.replay_ready:
			break
	var game = current_scene
	check(game.replay_ready and game.player.original_rules_enabled, "Original game initialized")
	if not game.replay_ready or not game.player.original_rules_enabled:
		quit(1)
		return
	for level in range(1,16):
		game.player.set_physics_process(false)
		check(manager.current_level == level, "Transition level %d" % level)
		check(game.word_manager.words.size() == 7, "Seven playable words on level %d" % level)
		for word in game.word_manager.words:
			check(word.length() >= 1 and word.length() <= 7, "Valid word on level %d: %s" % [level,word])
		for layer in [game.bg_tilemap,game.fg_tilemap]:
			var atlas: TileSetAtlasSource = layer.tile_set.get_source(0)
			check(atlas.texture.resource_path == "res://assets/tiles/tileset_back%d.png" % int(game.level_data.tileset), "Correct tileset on level %d" % level)
		check(game.original_drips.snapshot().size() == game.level_data.drips.size(), "Drip count on level %d" % level)
		check(game.original_books != null and game.original_letters != null and game.original_gruzzles != null, "All interaction models present")
		var cursor: int = game.original_words.offset
		var words: Array = game.word_manager.words.duplicate()
		game.restart_original_level()
		check(game.original_words.offset == cursor and game.word_manager.words == words, "Death keeps the word cursor on level %d" % level)
		if level < 15:
			game.finish_original_exit({},-1)
		await process_frame
	game.player.set_physics_process(false)
	print("WR1 levels: %d checks, %d failures" % [checks, failures])
	quit(1 if failures else 0)
