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
	# These accelerated cases compare sound-derived deadlines, not device output.
	game.audio_output_enabled = false
	game.audio.stop()
	game.scene = "inside"
	var cases = JSON.parse_string(FileAccess.get_file_as_string(output.path_join("cases.json")))
	var result: Array = []
	for entry in cases:
		game.character = entry.who
		game.tick = 0
		game.resident = game.Resident.new(game)
		var resident = game.resident
		resident.objects.clear()
		resident.pose = int(entry.pose)
		game.balloon.hidden = true
		game.random.reset(42)
		resident.action(int(entry.action))
		for tick in range(1,3001):
			game.tick = tick
			resident.update(tick)
			if not resident.busy:
				break
		game.surface.image.fill(Color.BLACK)
		resident.draw_objects(game.surface,true)
		resident.draw(game.surface)
		resident.draw_objects(game.surface,true,true)
		game.surface.image.save_png(output.path_join(entry.name+".png"))
		var objects = resident.objects.map(func(o): return {"type":o.type,"state":o.state,"inside":o.inside,"rect":o.rect,"front":o.get("front",false)})
		result.append({"name":entry.name,"pose":resident.pose,"objects":objects,"tick":game.tick,"busy":resident.busy,"seed":game.random.seed})
	var file = FileAccess.open(output.path_join("godot.json"),FileAccess.WRITE)
	file.store_string(JSON.stringify(result))
	file.close()
	game.queue_free()
	await process_frame
	quit()
