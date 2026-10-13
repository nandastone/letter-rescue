extends SceneTree
var game
var output: String

func _initialize() -> void:
	output = OS.get_cmdline_user_args()[0]
	call_deferred("run")

func snapshot() -> Dictionary:
	var m = game.maze
	var result = {"seed":game.random.seed,"phase":m.phase,"busy":m.busy}
	for field in ["hard","streak","excluded","supportedTypes","typeHistory","patternHistory","familyHistory","songs","history","secret","node","type","correct","choices","earned"]:
		result[field] = m.get(field.to_snake_case())
	result.history = result.history.duplicate()
	result.history.sort()
	return result.duplicate(true)

func load_fixture(fixture: Dictionary) -> void:
	game.maze.cancel()
	for key in fixture:
		if key=="seed":
			game.random.reset(int(fixture.seed))
		else:
			game.maze.set(key.to_snake_case(),game.maze.integers(fixture[key]))
	game.maze.started = true
	game.maze.introduced = true
	game.maze.round_replaced = false
	game.maze.reset_idle()

func run() -> void:
	var fixture = JSON.parse_string(FileAccess.get_file_as_string(output.path_join("fixture.json")))
	game = load("res://main.tscn").instantiate()
	game.boot_enabled = false
	game.persistence_enabled = false
	root.add_child(game)
	game.set_process(false)
	game.audio_output_enabled = false
	game.scene = "maze"
	var generation: Array = []
	for entry in fixture.generation:
		load_fixture(entry.initial)
		if entry.get("first",false):
			game.maze.setup_round()
		else:
			game.maze.streak += 1
			if game.maze.streak==2:
				game.maze.difficulty(true)
			game.maze.frog_voice()
			game.maze.challenge()
		generation.append({"name":entry.name,"actual":snapshot()})
	load_fixture(fixture.initial)
	var results: Array = []
	var highlight_match = false
	var highlight = Image.load_from_file(fixture.highlight)
	highlight.convert(Image.FORMAT_RGBA8)
	for entry in fixture.checkpoints:
		game.move_pointer(Vector2i(int(entry.pointer[0]),int(entry.pointer[1])))
		var elapsed = 0
		if entry.name!="settled":
			game.pointer_input("mouse",true,game.pointer)
			game.pointer_input("mouse",false,game.pointer)
			while game.maze.busy and elapsed<30000:
				game.advance()
				elapsed += 1
				if game.maze.phase=="arrival":
					game.maze.draw(game.surface)
					game.draw_pointer()
					if game.surface.image.get_data()==highlight.get_data():
						highlight_match = true
		game.maze.draw(game.surface)
		game.draw_pointer()
		game.surface.image.save_png(output.path_join(entry.name+".png"))
		results.append({"name":entry.name,"actual":snapshot(),"elapsed":elapsed})
	var file = FileAccess.open(output.path_join("godot.json"),FileAccess.WRITE)
	file.store_string(JSON.stringify({"generation":generation,"checkpoints":results,"highlight":highlight_match}))
	file.close()
	game.queue_free()
	await process_frame
	quit()
