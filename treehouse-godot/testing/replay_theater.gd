extends SceneTree
var output: String
var game
var expected: Image
var matched_tick: int
var base_time: int = 0
var base_tick: int = 0

func _initialize() -> void:
	output = OS.get_cmdline_user_args()[0]
	call_deferred("run")

func observe() -> void:
	if base_time:
		game.date_override = Time.get_datetime_dict_from_unix_time(base_time+int((game.tick-base_tick)/game.TICK_HZ))
	game.render()
	if matched_tick<0 and game.surface.image.get_data()==expected.get_data():
		matched_tick = game.tick
		game.surface.image.save_png(output.path_join("matched.png"))

func run() -> void:
	var fixture = JSON.parse_string(FileAccess.get_file_as_string(output.path_join("fixture.json")))
	game = load("res://main.tscn").instantiate()
	game.boot_enabled = false
	game.persistence_enabled = false
	root.add_child(game)
	game.set_process(false)
	game.audio_output_enabled = false
	game.capture_sound_events = true
	game.theater.dispose()
	game.theater = game.Theater.new(game,false)
	game.scene = "theater"
	game.resident.selected = true
	var initial = fixture.initial
	game.tick = int(initial.tick)
	game.theater.tick = game.tick
	game.random.reset(int(initial.seed))
	for key in ["selection","order","mixUp","propsEnabled","actor_drag","props"]:
		game.theater.set(key.to_snake_case(),game.MusicMaze.integers(initial[key]))
	game.theater.options = initial.scene!=2
	game.theater.previous_validation = int(initial.validation)
	game.pointer = Vector2i(initial.pointer[0],initial.pointer[1])
	if fixture.has("room"):
		var room = game.MusicMaze.integers(fixture.room)
		base_tick = game.tick
		base_time = room.time
		game.scene = "inside"
		game.animations.clear()
		game.resident.tick = game.tick
		for key in ["pose","hunger","fatigue","ambient_due","long_due","hunger_due","fatigue_due","objects"]:
			game.resident.set(key,room[key])
		game.room.date = {"year":1992,"month":1,"day":1}
		game.room.tick = game.tick
		game.room.cloud = room.cloud
		game.room.cloud_x = room.cloud_x
		game.room.cloud_due = game.tick+room.cloud_due
		game.balloon.hidden = true
		for object in game.resident.objects:
			if object.type==6:
				game.balloon.hidden = false
				game.balloon.state = object.state
				game.balloon.x = object.rect[1]
				game.balloon.y = object.rect[0]
				game.balloon.due = object.due
	var held = false
	var results: Array = []
	for entry in fixture.checkpoints:
		var sound_start = game.sound_events.size()
		expected = Image.load_from_file(fixture.reference.path_join("state/"+entry.name+".png"))
		expected.convert(Image.FORMAT_RGBA8)
		matched_tick = -1
		for action in entry.inputs:
			game.move_pointer(Vector2i(action.point[0],action.point[1]))
			if held!=action.left:
				held = action.left
				game.pointer_input("mouse",held,game.pointer)
			observe()
			for i in int(action.to_tick-action.from_tick):
				game.advance()
				observe()
		observe()
		if matched_tick>=0:
			Image.load_from_file(output.path_join("matched.png")).save_png(output.path_join(entry.name+".png"))
		else:
			game.surface.image.save_png(output.path_join(entry.name+".png"))
		var a = game.theater
		results.append({"name":entry.name,"matched_tick":matched_tick,"actual":{"scene":5 if game.scene=="inside" else 13 if a.options else 2,"seed":game.random.seed,"selection":a.selection.duplicate(),"order":a.order.duplicate(),"mixUp":a.mix_up,"propsEnabled":a.props_enabled,"validation":a.previous_validation,"prop_counts":a.props.map(func(list): return list.size()),"actor_drag":a.actor_drag.duplicate(true),"props":a.props.duplicate(true)},"sounds":game.sound_events.slice(sound_start)})
	var file = FileAccess.open(output.path_join("godot.json"),FileAccess.WRITE)
	file.store_string(JSON.stringify(results))
	file.close()
	game.queue_free()
	await process_frame
	quit()
