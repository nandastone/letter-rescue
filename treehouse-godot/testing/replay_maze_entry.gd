extends SceneTree
var output: String
var game
var expected: Image
var matched_tick: int
var previous_hash: String = ""
var frames: Array = []

func _initialize() -> void:
	output = OS.get_cmdline_user_args()[0]
	call_deferred("run")

func observe(name: String) -> void:
	game.render()
	if matched_tick<0 and game.surface.image.get_data()==expected.get_data():
		matched_tick = game.tick
		game.surface.image.save_png(output.path_join("matched.png"))
	if game.travel.get("maze",false):
		var rgb = game.surface.image.duplicate()
		rgb.convert(Image.FORMAT_RGB8)
		var hash = HashingContext.new()
		hash.start(HashingContext.HASH_SHA256)
		hash.update(rgb.get_data())
		var digest = hash.finish().hex_encode()
		if digest!=previous_hash:
			frames.append({"tick":game.tick,"hash":digest,"checkpoint":name})
			previous_hash = digest

func snapshot() -> Dictionary:
	var result = {"seed":game.random.seed,"scene":game.scene,"busy":game.maze.busy}
	for key in ["songs","history","hard","secret","node","type","correct","choices","typeHistory","patternHistory","familyHistory"]:
		result[key] = game.maze.get(key.to_snake_case())
	result.history = result.history.duplicate()
	result.history.sort()
	return result.duplicate(true)

func run() -> void:
	var fixture = JSON.parse_string(FileAccess.get_file_as_string(output.path_join("fixture.json")))
	game = load("res://main.tscn").instantiate()
	game.boot_enabled = false
	game.persistence_enabled = false
	root.add_child(game)
	game.set_process(false)
	game.audio_output_enabled = false
	game.capture_sound_events = true
	game.scene = "music"
	var initial = fixture.initial
	game.tick = int(initial.tick)
	game.random.reset(int(initial.maze.seed))
	for key in ["songs","history","hard","typeHistory","patternHistory","familyHistory"]:
		game.maze.set(key.to_snake_case(),game.maze.integers(initial.maze[key]))
	game.maze.initial_advanced = initial.maze.hard
	game.maze.introduced = not bool(initial.first_intro)
	game.music.mode = int(initial.advanced)
	game.music.editor.mode = game.music.mode
	game.music.song_id = int(initial.selection[2*game.music.mode])
	game.music.books[game.music.mode][game.music.song_id] = initial.song.map(func(v): return int(v))
	game.music.instrument = int(initial.song[3])
	game.music.idle_due = game.tick+int(initial.idleCountdown)
	game.pointer = Vector2i(int(initial.pointer[0]),int(initial.pointer[1]))
	var held = false
	var results: Array = []
	for entry in fixture.checkpoints:
		var sound_start = game.sound_events.size()
		expected = Image.load_from_file(fixture.reference.path_join("state/"+entry.name+".png"))
		expected.convert(Image.FORMAT_RGBA8)
		matched_tick = -1
		for action in entry.inputs:
			game.move_pointer(Vector2i(int(action.point[0]),int(action.point[1])))
			if held!=action.left:
				held = action.left
				game.pointer_input("mouse",held,game.pointer)
			observe(entry.name)
			for i in int(action.to_tick-action.from_tick):
				game.advance()
				observe(entry.name)
		observe(entry.name)
		if matched_tick>=0:
			Image.load_from_file(output.path_join("matched.png")).save_png(output.path_join(entry.name+".png"))
		else:
			game.surface.image.save_png(output.path_join(entry.name+".png"))
		results.append({"name":entry.name,"matched_tick":matched_tick,"actual":snapshot(),"sounds":game.sound_events.slice(sound_start)})
	var file = FileAccess.open(output.path_join("godot.json"),FileAccess.WRITE)
	file.store_string(JSON.stringify({"checkpoints":results,"frames":frames}))
	file.close()
	game.queue_free()
	await process_frame
	quit()
