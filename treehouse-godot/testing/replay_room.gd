extends SceneTree
## One initial native fixture, then room pointer events and advancing civil time.
var game
var output: String
var fixture: Dictionary
var base_time: int
var base_tick: int

func _initialize() -> void:
	output = OS.get_cmdline_user_args()[0]
	fixture = JSON.parse_string(FileAccess.get_file_as_string(output.path_join("fixture.json")))
	call_deferred("run")

func digest(image: Image) -> String:
	var hashing = HashingContext.new()
	hashing.start(HashingContext.HASH_SHA256)
	hashing.update(image.get_data())
	return hashing.finish().hex_encode()

func set_clock() -> void:
	game.date_override = Time.get_datetime_dict_from_unix_time(base_time+int((game.tick-base_tick)/game.TICK_HZ))

func equivalent(actual, expected) -> bool:
	if actual is Dictionary and expected is Dictionary:
		if actual.size()!=expected.size():
			return false
		for key in actual:
			if not expected.has(key) or not equivalent(actual[key],expected[key]):
				return false
		return true
	if actual is Array and expected is Array:
		if actual.size()!=expected.size():
			return false
		for i in actual.size():
			if not equivalent(actual[i],expected[i]):
				return false
		return true
	return actual==expected

func run() -> void:
	assert(equivalent([1992,1,1],[1992.0,1.0,1.0]))
	assert(not equivalent([1992,1,1],[1992.0,1.0,2.0]))
	game = load("res://main.tscn").instantiate()
	game.boot_enabled = false
	game.persistence_enabled = false
	root.add_child(game)
	game.set_process(false)
	game.capture_sound_events = true
	game.audio_output_enabled = false
	var initial = fixture.initial
	base_tick = int(initial.tick)
	base_time = int(fixture.time)
	game.tick = base_tick
	game.scene = {4:"outside",5:"inside",14:"hollow"}[int(initial.scene)]
	game.animations.clear()
	game.character = "girl" if initial.sex else "boy"
	game.resident.selected = bool(initial.selected)
	game.resident.tick = game.tick
	game.resident.pose = int(initial.pose)
	game.resident.hunger = int(initial.hunger)
	game.resident.fatigue = int(initial.fatigue)
	game.resident.hunger_due = int(initial.hungerDue)
	game.resident.fatigue_due = int(initial.fatigueDue)
	game.resident.ambient_due = int(initial.ambientDue)
	game.resident.long_due = int(initial.longDue)
	game.resident.objects = initial.objects.duplicate(true)
	for object in game.resident.objects:
		object.type = int(object.type)
		object.state = int(object.state)
		object.due = int(object.due)
		object.rect = object.rect.map(func(value): return int(value))
	game.exterior.outside_cycle = int(initial.outsideCycle)
	game.exterior.window_due = game.tick+int(initial.windowRemaining)
	game.random.reset(int(initial.seed))
	game.pointer = Vector2i(int(initial.pointer[0]),int(initial.pointer[1]))
	game.room.date = {"year":int(initial.date[0]),"month":int(initial.date[1]),"day":int(initial.date[2])}
	game.room.tick = game.tick
	game.room.cloud = int(initial.cloud)
	game.room.cloud_x = int(fixture.cloud_x)
	game.room.cloud_due = game.tick+int(initial.windowRemaining)
	game.room.height = 98 if initial.calendarOpen else 28
	game.room.target = game.room.height
	game.room.portrait_frame = int(fixture.portrait_frame)
	game.chalk.select(int(initial.chalkTool))
	game.balloon.hidden = true
	for object in initial.objects:
		if object.type==6:
			game.balloon.hidden = false
			game.balloon.state = int(object.state)
			game.balloon.x = int(object.rect[1])
			game.balloon.y = int(object.rect[0])
			game.balloon.due = int(object.due)
	set_clock()
	var results: Array = []
	var held = false
	for checkpoint in fixture.checkpoints:
		var target = Image.load_from_file(fixture.reference.path_join("state/"+checkpoint.name+".png"))
		target.convert(Image.FORMAT_RGBA8)
		var expected = digest(target)
		var matched = -1
		var chosen: Image
		for action in checkpoint.inputs:
			game.move_pointer(Vector2i(int(action.point[0]),int(action.point[1])))
			if bool(action.left)!=held:
				held = bool(action.left)
				game.pointer_input("mouse",held,game.pointer)
			var count = int(action.to_tick-action.from_tick)
			for i in count+1:
				game.render()
				if matched<0 and digest(game.surface.image)==expected:
					matched = game.tick
					chosen = game.surface.image.duplicate()
				if i<count:
					game.advance()
					set_clock()
		game.render()
		if checkpoint.inputs.is_empty() and digest(game.surface.image)==expected:
			matched = game.tick
		if chosen==null:
			chosen = game.surface.image
		chosen.save_png(output.path_join(checkpoint.name+".png"))
		var state = {"date":[game.room.date.year,game.room.date.month,game.room.date.day],"cloud":game.room.cloud,"calendarOpen":game.room.is_open,"chalkTool":game.chalk.tool,"scene":{"outside":4,"inside":5,"hollow":14}[game.scene],"selected":game.resident.selected,"sex":int(game.character=="girl"),"pose":game.resident.pose,"outsideCycle":game.exterior.outside_cycle,"hunger":game.resident.hunger,"fatigue":game.resident.fatigue}
		var differences: Dictionary = {}
		state.cloudX = game.room.cloud_x
		var object_order: Dictionary = {}
		if fixture.get("check_objects",false):
			state.seed = game.random.seed
			var expected_objects = checkpoint.after.objects.map(func(o): return {"type":o.type,"state":o.state,"inside":o.inside,"rect":o.rect})
			var actual_objects = game.resident.objects.map(func(o):
				var drag = game.resident.drag
				var r = drag.rect if not drag.is_empty() and drag.moved and drag.object==o else game.resident.bounds(o)
				return {"type":o.type,"state":o.state,"inside":o.inside,"rect":r})
			object_order = {"expected":expected_objects.map(func(o): return o.type),"actual":actual_objects.map(func(o): return o.type)}
			expected_objects.sort_custom(func(a,b): return a.type<b.type)
			actual_objects.sort_custom(func(a,b): return a.type<b.type)
			if not equivalent(actual_objects,expected_objects):
				differences.objects = {"expected":expected_objects,"actual":actual_objects}
		for field in state:
			if not checkpoint.after.has(field):
				continue
			if not equivalent(state[field],checkpoint.after[field]):
				differences[field] = {"expected":checkpoint.after[field],"actual":state[field]}
		var expected_balloon = null
		for object in checkpoint.after.objects:
			if object.type==6:
				expected_balloon = [object.state,object.rect]
		var actual_balloon = null if game.balloon.hidden else [game.balloon.state,[game.balloon.y,game.balloon.x,game.balloon.y+38,game.balloon.x+29]]
		if not equivalent(actual_balloon,expected_balloon):
			differences.balloon = {"expected":expected_balloon,"actual":actual_balloon}
		results.append({"name":checkpoint.name,"matched_tick":matched,"differences":differences,"passed":matched>=0 and differences.is_empty(),"object_order":object_order,"nuts":game.exterior.nuts.map(func(point): return [point.x,point.y])})
		print(checkpoint.name," matched=",matched," fields=",differences)
	var file = FileAccess.open(output.path_join("godot.json"),FileAccess.WRITE)
	file.store_string(JSON.stringify({"checkpoints":results,"sounds":game.sound_events},"\t"))
	file.close()
	game.queue_free()
	await process_frame
	quit()
