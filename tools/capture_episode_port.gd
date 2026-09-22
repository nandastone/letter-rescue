extends SceneTree
## Actual display captures for each registered episode.
const Profiles = preload("res://scripts/core/wr1_profiles.gd")
const Render = preload("res://scripts/core/wr1_frontend_render.gd")
var output := "res://testing/output/episode-port-visual"
var frames := 0

func _initialize() -> void:
	process_frame.connect(func():
		frames += 1
		if frames > 4000:
			printerr("Episode visual check timed out")
			quit(1))
	_run.call_deferred()

func capture(name: String) -> void:
	await process_frame
	RenderingServer.force_draw(false)
	assert(root.get_texture().get_image().save_png(output + "/" + name + ".png") == OK)

func _run() -> void:
	DirAccess.make_dir_recursive_absolute(output)
	Profiles.directory = output + "/profiles/"
	var manager = root.get_node("GameManager")
	var replay = root.get_node("InputReplay")
	root.size = Vector2i(960,600)
	for episode in [2, 3]:
		Episode.select(episode)
		for level in [1, 20]:
			manager.current_level = level
			manager.current_difficulty = 2
			manager.original_player_name = "Visual"
			replay.mode = replay.Mode.REPLAYING
			replay.original_start_seed = 20716
			var game = load("res://scenes/game.tscn").instantiate()
			root.add_child(game)
			current_scene = game
			while not game.is_replay_ready(): await process_frame
			game.process_mode = Node.PROCESS_MODE_DISABLED
			await capture("wr%d_level%d" % [episode,level])
			game.word_manager.original_model.touch(0)
			game.word_manager._refresh_original()
			await capture("wr%d_level%d_cards" % [episode,level])
			if level == 1:
				var frontend = load("res://scripts/core/wr1_frontend.gd").new()
				game.add_child(frontend)
				frontend.begin("menu", game)
				await capture("wr%d_menu" % episode)
				for kind in ["startup", "story", "ending"]:
					frontend.open(kind)
					frontend.set_process(false)
					for page in range(Render.metadata()[kind].screens.size()):
						frontend.index = page
						frontend.redraw()
						await capture("wr%d_%s%d" % [episode,kind,page])
			game.set_meta("frontend_replaced", true)
			game.queue_free()
			await process_frame
			current_scene = null
	print("Episode visuals passed: " + ProjectSettings.globalize_path(output))
	quit()
