extends SceneTree
var output: String
var game
var checks: Array = []
var frames: Array = []

func _initialize() -> void:
	output = OS.get_cmdline_user_args()[0]
	call_deferred("run")

func check(ok: bool, name: String) -> void:
	checks.append({"name":name,"passed":ok})
	if not ok:
		push_error(name)

func run() -> void:
	game = load("res://main.tscn").instantiate()
	game.persistence_enabled = false
	game.audio_output_enabled = false
	root.add_child(game)
	game.set_process(false)
	check(game.scene=="title","ordinary boot starts at logo")
	check(game.startup.player!=game.audio,"FM and digital voices are separate")
	check(game.startup.player.stream is AudioStreamWAV,"generated FM asset loads")
	var previous: PackedByteArray
	for tick in range(600):
		game.render()
		var pixels = game.surface.image.get_data()
		if game.scene=="title" and pixels!=previous:
			var name = "title-%03d.png"%tick
			game.surface.image.save_png(output.path_join(name))
			frames.append({"tick":tick,"image":name,"phase":game.startup.phase,"sparkle":game.startup.index})
		previous = pixels
		if game.scene!="title":
			break
		game.advance()
	check(game.scene=="outside" and not game.entering,"logo finishes at character selection")
	check(game.startup.player==null,"completed title releases its audio player")
	game.render()
	game.surface.image.save_png(output.path_join("selection.png"))
	var duration = game.tick
	for input_type in ["key","mouse","touch"]:
		game.scene = "title"
		game.startup = game.Startup.new(game)
		var event
		if input_type=="key":
			event = InputEventKey.new()
			event.keycode = KEY_SPACE
		elif input_type=="mouse":
			event = InputEventMouseButton.new()
			event.button_index = MOUSE_BUTTON_LEFT
		else:
			event = InputEventScreenTouch.new()
		event.pressed = true
		game._input(event)
		check(game.scene=="outside" and not game.entering and game.startup.player==null,"skip consumes "+input_type+" without selecting a child")
	game.enter("boy")
	for i in 2000:
		game.advance()
		if game.scene=="inside":
			break
	check(game.scene=="inside","character entrance remains playable after title")
	var passed = checks.all(func(c): return c.passed)
	var report = FileAccess.open(output.path_join("godot.json"),FileAccess.WRITE)
	report.store_string(JSON.stringify({"checks":checks,"frames":frames,"duration_ticks":duration,"passed":passed},"\t"))
	report.close()
	game.audio.stream = null
	game.audio_cache.clear()
	game.queue_free()
	await process_frame
	quit(0 if passed else 1)
