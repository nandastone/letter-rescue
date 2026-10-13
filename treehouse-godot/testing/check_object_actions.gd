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
	var cases = JSON.parse_string(FileAccess.get_file_as_string(output.path_join("cases.json")))
	var results: Array = []
	for entry in cases:
		game.tick = 0
		game.character = entry.who
		game.scene = entry.scene
		game.date_override = {"year":1992,"month":1,"day":1,"hour":10,"minute":0,"second":0}
		game.room = game.Room.new(game)
		game.exterior = game.Exterior.new(game)
		game.resident = game.Resident.new(game)
		var r = game.resident
		r.objects.clear()
		game.balloon.hidden = true
		r.hunger = int(entry.hunger)
		r.fatigue = int(entry.fatigue)
		r.hunger_due = 999999
		r.fatigue_due = 999999
		var object = r.create(int(entry.type),game.scene=="inside")
		object.state = int(entry.state)
		if entry.get("bird",false):
			r.create(15).rect = [95,218,115,243]
		game.random.reset(42)
		game.sound_events.clear()
		game.capture_sound_events = true
		if entry.op=="offer":
			r.offer(object)
		elif entry.op=="place":
			r.set_bounds(object,[40,100,40+int(object.rect[2]-object.rect[0]),100+int(object.rect[3]-object.rect[1])])
			r.tasks.start(r.tasks.place(object))
		else:
			r.click_object(object)
		var frames: Array = []
		for tick in range(1,4001):
			game.tick = tick
			game.room.update(tick,r.busy)
			r.update(tick)
			game.exterior.update(tick)
			var idle = not r.busy and not game.room.busy and game.room.speech.is_empty() and tick>=game.room.speech_due and not game.exterior.busy
			if tick%8==0 or idle:
				game.surface.image.fill(Color.BLACK)
				r.draw_nap(game.surface)
				r.draw_objects(game.surface,game.scene=="inside")
				if game.scene=="inside":
					r.draw(game.surface)
				r.draw_objects(game.surface,game.scene=="inside",true)
				if r.object_animation!=null:
					r.object_animation.draw(game.surface)
				r.tasks.draw(game.surface)
				var hashing = HashingContext.new()
				hashing.start(HashingContext.HASH_SHA256)
				hashing.update(game.surface.image.get_data())
				frames.append([tick,hashing.finish().hex_encode()])
			if idle:
				break
		var objects = r.objects.map(func(o): return {"type":o.type,"state":o.state,"inside":o.inside,"rect":r.bounds(o),"front":o.get("front",false)})
		results.append({"name":entry.name,"tick":game.tick,"pose":r.pose,"hunger":r.hunger,"fatigue":r.fatigue,"seed":game.random.seed,"objects":objects,"frames":frames,"sounds":game.sound_events.map(func(s): return [s.tick,s.key,s.duration])})
	var file = FileAccess.open(output.path_join("godot.json"),FileAccess.WRITE)
	file.store_string(JSON.stringify(results))
	file.close()
	game.queue_free()
	await process_frame
	quit()
