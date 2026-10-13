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
	var results: Array = []
	for entry in cases:
		game.music.dispose()
		game.music = game.Music.new(game)
		var m = game.music
		m.editor = m.Editor.new(game,false)
		var e = m.editor
		game.tick = int(entry.get("tick",0))
		game.character = entry.get("character","boy")
		m.mode = int(entry.mode)
		e.mode = m.mode
		e.enabled = entry.get("enabled",true)
		m.song_id = int(entry.get("song_id",20))
		e.books[m.mode][0] = entry.raw.map(func(v): return int(v))
		e.titles[m.mode][0] = e.encode_title(entry.get("title",e.default_title(m.mode,0)))
		if not e.enabled:
			m.books[m.mode][m.song_id] = entry.raw.map(func(v): return int(v))
		m.instrument = int(entry.raw[3])
		e.duration[m.mode] = int(entry.get("duration",4))
		e.position = int(entry.get("position",0))
		e.eraser = entry.get("eraser",false)
		m.contents = int(entry.get("contents",0))
		if entry.has("drag"):
			e.drag = {"kind":"note","index":int(entry.drag)}
		if entry.has("title_entry"):
			e.title_entry = {"old":e.title,"value":entry.title_entry,"start":0}
		if entry.has("dialog"):
			m.dialog = {"message":entry.dialog,"start":0}
		if entry.get("print",false):
			e.draw_print(game.surface)
		else:
			m.draw(game.surface)
		if entry.has("pointer"):
			game.pointer = Vector2i(int(entry.pointer[0]),int(entry.pointer[1]))
			if entry.get("busy",false):
				var data = game.store.data.cursor
				game.store.data.cursor = Array(Marshalls.base64_to_raw(game.store.data.raw["th:CURS:1"]))
				game.draw_pointer()
				game.store.data.cursor = data
			else:
				game.draw_pointer()
		game.surface.image.save_png(output.path_join(entry.name+".png"))
		results.append({"name":entry.name,"sequence":m.sequence()})
	var file = FileAccess.open(output.path_join("godot.json"),FileAccess.WRITE)
	file.store_string(JSON.stringify(results))
	file.close()
	game.queue_free()
	await process_frame
	quit()
