extends SceneTree
var output: String

func _initialize() -> void:
	output = OS.get_cmdline_user_args()[0]
	call_deferred("run")

func run() -> void:
	var game = load("res://main.tscn").instantiate()
	game.boot_enabled = false
	game.persistence_enabled = false
	root.add_child(game)
	game.set_process(false)
	game.audio_output_enabled = false
	game.scene = "maze"
	var cases = JSON.parse_string(FileAccess.get_file_as_string(output.path_join("cases.json")))
	for entry in cases:
		game.maze.dispose()
		game.maze = game.MusicMaze.new(game)
		game.maze.cancel()
		game.character = entry.character
		for key in entry.state:
			game.maze.set(key.to_snake_case(),game.maze.integers(entry.state[key]))
		game.maze.draw(game.surface)
		game.surface.image.save_png(output.path_join(entry.name+".png"))
	game.queue_free()
	await process_frame
	quit()
