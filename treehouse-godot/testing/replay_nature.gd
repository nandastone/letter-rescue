extends SceneTree
var game
var output: String
var expected: Image
var matched: int
var base_time: int = 0
var base_tick: int = 0

func _initialize() -> void:
	output = OS.get_cmdline_user_args()[0]
	call_deferred("run")

func observe() -> void:
	if base_time:
		game.date_override = Time.get_datetime_dict_from_unix_time(base_time+int((game.tick-base_tick)/game.TICK_HZ))
	game.render()
	if matched<0 and game.surface.image.get_data()==expected.get_data():
		matched = game.tick
		game.surface.image.save_png(output.path_join("matched.png"))

func step(count: int) -> void:
	for i in count:
		game.advance()
		observe()

func snapshot(kind: String) -> Dictionary:
	var n = game.nature
	var q = n.quiz
	var result = {"seed":game.random.seed}
	if kind=="edit":
		for key in ["time","attribute","category","values"]:
			result[key] = n.get(key)
		result.objects = []
		for list in n.objects:
			var items: Array = []
			for object in list:
				var shape = game.store.shape("modules",n.tables.animals[object.id].large)
				items.append({"id":object.id,"rect":[object.y,object.x,object.y+shape[1],object.x+shape[0]]})
			result.objects.append(items)
	else:
		for key in ["cards","secret","opponent","help","player","asked","remaining"]:
			result[key] = q.get(key)
		result.available = q.available.duplicate() if q.phase=="question" and q.winner<0 else []
		result.available.sort()
		result.answered = -1 if q.phase=="ready" else 1 if q.phase in ["answered","won"] else 0
		result.guessing = int(q.phase=="question" and q.guessing)
		result.win_phase = q.win_phase
		result.scene = 5 if game.scene=="inside" else 12 if game.scene=="telescope" else 13 if game.scene=="theater" else 9 if n.mode=="quiz" else 1
		result.shelf = game.rewards.shelf
		result.visited_mask = game.rewards.visited
		result.prize_choices = game.rewards.choices
		result.objects = game.resident.objects.map(func(o): return {"type":o.type,"state":o.state,"inside":o.inside,"rect":game.resident.bounds(o)})
		if q.win_phase:
			result.winner = q.winner
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
	game.nature.dispose()
	game.nature = game.Nature.new(game,false)
	game.scene = "nature"
	game.character = fixture.get("character","boy")
	var n = game.nature
	var q = n.quiz
	var initial = game.MusicMaze.integers(fixture.initial)
	game.tick = initial.tick
	n.tick = game.tick
	q.tick = game.tick
	n.interact()
	game.random.reset(initial.seed)
	game.pointer = Vector2i(initial.pointer[0],initial.pointer[1])
	if fixture.kind=="edit":
		for key in ["time","attribute","category","values"]:
			n.set(key,initial[key])
	else:
		n.mode = "quiz"
		for key in ["cards","secret","opponent","help","player","asked","remaining","available"]:
			q.set(key,initial[key])
		q.options = false
		q.visible_questions = []
		q.hint_due = game.tick+initial.idle_timer
		var room = game.MusicMaze.integers(fixture.room)
		base_tick = game.tick
		base_time = room.time
		game.animations.clear()
		game.resident.selected = true
		game.resident.tick = game.tick
		for key in ["pose","hunger","fatigue","ambient_due","long_due","hunger_due","fatigue_due"]:
			game.resident.set(key,room[key])
		game.resident.objects = initial.objects.duplicate(true)
		game.balloon.hidden = true
		for object in game.resident.objects:
			object.due = 2147483647
			if object.type==6:
				game.balloon.hidden = false
				game.balloon.state = object.state
				game.balloon.x = object.rect[1]
				game.balloon.y = object.rect[0]
		game.room.date = {"year":1992,"month":1,"day":1}
		game.room.tick = game.tick
		game.room.cloud = room.cloud
		game.room.cloud_x = room.cloud_x
	var held = false
	var previous: int = game.tick
	var results: Array = []
	for entry in fixture.checkpoints:
		var sound_start = game.sound_events.size()
		expected = Image.load_from_file(fixture.reference.path_join("state/"+entry.name+".png"))
		expected.convert(Image.FORMAT_RGBA8)
		matched = -1
		if fixture.kind=="edit":
			for action in entry.inputs:
				game.move_pointer(Vector2i(action.point[0],action.point[1]))
				if held!=action.left:
					held = action.left
					game.pointer_input("mouse",held,game.pointer)
				observe()
				step(int(action.to_tick-action.from_tick))
		elif entry.name!=fixture.checkpoints[0].name:
			game.move_pointer(Vector2i(entry.after.pointer[0],entry.after.pointer[1]))
			game.advance(int(entry.input_tick-previous))
			game.pointer_input("mouse",true,game.pointer)
			game.pointer_input("mouse",false,game.pointer)
			observe()
			step(int(entry.after.tick-entry.input_tick))
		observe()
		previous = int(entry.after.tick)
		if matched>=0:
			Image.load_from_file(output.path_join("matched.png")).save_png(output.path_join(entry.name+".png"))
		else:
			game.surface.image.save_png(output.path_join(entry.name+".png"))
		results.append({"name":entry.name,"matched_tick":matched,"actual":snapshot(fixture.kind),"sounds":game.sound_events.slice(sound_start)})
	var file = FileAccess.open(output.path_join("godot.json"),FileAccess.WRITE)
	file.store_string(JSON.stringify(results))
	file.close()
	game.queue_free()
	await process_frame
	quit()
