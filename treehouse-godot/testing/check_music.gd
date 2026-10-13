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
	game.scene = "music"
	var cases = JSON.parse_string(FileAccess.get_file_as_string(output.path_join("cases.json")))
	var result: Array = []
	for entry in cases:
		game.music.dispose()
		game.music = game.Music.new(game)
		var m = game.music
		game.tick = 0
		m.mode = int(entry.mode)
		m.song_id = int(entry.song)
		m.instrument = int(entry.get("instrument",m.song[3]))
		m.idle_frame = int(entry.get("idle",-1))
		m.contents = int(entry.get("contents",0))
		if entry.has("category"):
			m.selector.show(int(entry.category))
			m.selector.info = int(entry.get("info",0))
			m.instrument = int(entry.get("instrument",m.instrument))
		if entry.has("pitch"):
			m.note_down(int(entry.pitch),"mouse")
		m.draw(game.surface)
		if entry.has("pointer"):
			game.pointer = Vector2i(int(entry.pointer[0]),int(entry.pointer[1]))
			game.draw_pointer()
		game.surface.image.save_png(output.path_join(entry.name+".png"))
		m.capture_notes = true
		m.toggle_song()
		while m.playing and game.tick<30000:
			game.tick += 1
			m.advance_song()
		result.append({"name":entry.name,"sequence":m.sequence(),"notes":m.note_events,"tick":game.tick})
	var file = FileAccess.open(output.path_join("godot.json"),FileAccess.WRITE)
	file.store_string(JSON.stringify(result))
	file.close()
	game.queue_free()
	await process_frame
	quit()
