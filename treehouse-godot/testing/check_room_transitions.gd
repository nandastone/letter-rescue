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
	game.scene = "inside"
	game.animations.clear()
	var fixtures = JSON.parse_string(FileAccess.get_file_as_string(output.path_join("fixtures.json")))
	var result: Dictionary = {}
	for fixture in fixtures:
		game.tick = 0
		game.character = "girl" if fixture.sex else "boy"
		game.date_override = {"year":1992,"month":1,"day":1,"hour":12,"minute":int(fixture.minute),"second":0}
		game.room.date = game.date_override
		game.room.cloud = int(fixture.cloud)
		game.room.cloud_x = int(fixture.cloudX)
		game.room.height = 28
		game.room.target = 28
		game.room.portrait_frame = 0
		game.resident.pose = int(fixture.pose)
		game.resident.objects = fixture.objects.duplicate(true)
		game.balloon.hidden = true
		for object in game.resident.objects:
			object.type = int(object.type)
			object.state = int(object.state)
			object.rect = object.rect.map(func(v): return int(v))
			if object.type==6:
				game.balloon.hidden = false
				game.balloon.state = object.state
				game.resident.set_bounds(object,object.rect)
		game.pointer = Vector2i(int(fixture.pointer[0]),int(fixture.pointer[1]))
		var effect = game.RoomTransition.new(game,int(fixture.variant),fixture.returning)
		var previous = ""
		var frames: Array = []
		for tick in 1400:
			game.tick = tick
			effect.draw(game.surface)
			if not effect.hide_pointer:
				game.draw_pointer()
			var rgb = game.surface.image.duplicate()
			rgb.convert(Image.FORMAT_RGB8)
			var hashing = HashingContext.new()
			hashing.start(HashingContext.HASH_SHA256)
			hashing.update(rgb.get_data())
			var digest = hashing.finish().hex_encode()
			if digest!=previous:
				var name = "%s-%d.png"%[fixture.name,frames.size()]
				rgb.save_png(output.path_join(name))
				frames.append({"tick":tick,"phase":effect.phase,"sha256":digest,"image":name})
				previous = digest
			game.tick = tick+1
			effect.update(game.tick)
			if effect.done:
				break
		result[fixture.name] = {"frames":frames,"finished":effect.done,"tick":game.tick}
		effect.dispose()
	var file = FileAccess.open(output.path_join("godot.json"),FileAccess.WRITE)
	file.store_string(JSON.stringify(result))
	file.close()
	game.queue_free()
	await process_frame
	quit()
