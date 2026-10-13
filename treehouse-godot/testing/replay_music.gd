extends SceneTree
var output: String
var game
var matched_tick: int
var expected: Image
var held: bool = false
var keys: Array = []

func _initialize() -> void:
	output = OS.get_cmdline_user_args()[0]
	call_deferred("run")

func observe() -> void:
	game.music.draw(game.surface)
	game.draw_pointer()
	if matched_tick<0 and game.surface.image.get_data()==expected.get_data():
		matched_tick = game.tick
		game.surface.image.save_png(output.path_join("matched.png"))

func key_event(key: String, pressed: bool) -> void:
	var event = InputEventKey.new()
	event.pressed = pressed
	event.keycode = KEY_ENTER if key=="enter" else key.to_upper().unicode_at(0)
	event.unicode = 0 if key=="enter" else key.unicode_at(0)
	game._input(event)

func run() -> void:
	var fixture = JSON.parse_string(FileAccess.get_file_as_string(output.path_join("fixture.json")))
	game = load("res://main.tscn").instantiate()
	game.boot_enabled = false
	game.persistence_enabled = false
	root.add_child(game)
	game.set_process(false)
	game.audio_output_enabled = false
	game.scene = "music"
	game.music.editor = game.music.Editor.new(game,false)
	var m = game.music
	var e = m.editor
	var initial = fixture.initial
	game.tick = int(initial.tick)
	game.random.reset(int(initial.seed))
	m.mode = int(initial.advanced)
	e.mode = m.mode
	e.enabled = initial.composing
	e.index = initial.selection.slice(1,4,2).map(func(v): return int(v))
	e.books[m.mode][e.index[m.mode]] = initial.song.map(func(v): return int(v))
	e.titles[m.mode][e.index[m.mode]] = e.encode_title(initial.title)
	e.position = int(initial.marker)
	m.song_id = int(initial.selection[m.mode*2])
	m.instrument = int(initial.song[3])
	m.idle_due = game.tick+int(initial.idleCountdown)
	for mode in 2:
		for id in 25:
			for field in 3:
				m.books[mode][id][field+2] = int(initial.listeningPreferences[field][mode*25+id])
	game.pointer = Vector2i(int(initial.pointer[0]),int(initial.pointer[1]))
	var results: Array = []
	for checkpoint in fixture.checkpoints:
		expected = Image.load_from_file(fixture.reference.path_join("state/"+checkpoint.name+".png"))
		expected.convert(Image.FORMAT_RGBA8)
		matched_tick = -1
		for action in checkpoint.inputs:
			var point = Vector2i(int(action.point[0]),int(action.point[1]))
			game.move_pointer(point)
			if action.left!=held:
				held = action.left
				game.pointer_input("mouse",held,point)
			var next_keys = action.get("keys",[])
			for key in keys:
				if key not in next_keys:
					key_event(key,false)
			for key in next_keys:
				if key not in keys:
					key_event(key,true)
			keys = next_keys
			observe()
			for i in int(action.to_tick-action.from_tick):
				game.advance(1)
				observe()
		observe()
		if matched_tick>=0:
			Image.load_from_file(output.path_join("matched.png")).save_png(output.path_join(checkpoint.name+".png"))
		else:
			game.surface.image.save_png(output.path_join(checkpoint.name+".png"))
		results.append({"name":checkpoint.name,"matched_tick":matched_tick,"actual":{"tick":game.tick,"seed":game.random.seed,"song":m.song.duplicate(),"title":e.title_entry.value if not e.title_entry.is_empty() else m.title,"composing":e.enabled,"advanced":bool(m.mode),"marker":e.position,"selection":[m.song_id,e.index[0],m.song_id,e.index[1]],"instrument":m.instrument,"tempo":m.tempo}})
	var file = FileAccess.open(output.path_join("godot.json"),FileAccess.WRITE)
	file.store_string(JSON.stringify(results))
	file.close()
	game.queue_free()
	await process_frame
	quit()
