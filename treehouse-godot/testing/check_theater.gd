extends SceneTree
var output: String
var snapshots: Array = []

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
	game.capture_sound_events = true
	game.scene = "theater"
	var cases = JSON.parse_string(FileAccess.get_file_as_string(output.path_join("cases.json")))
	for entry in cases:
		game.theater.dispose()
		game.theater = game.Theater.new(game,false)
		game.tick = 0
		game.sound_events.clear()
		game.random.reset(123456)
		game.pointer_visible = false
		for key in entry.get("state",{}):
			game.theater.set(key.to_snake_case(),game.MusicMaze.integers(entry.state[key]))
		var index = 0
		for action in entry.get("actions",[]):
			var method: String = action[0]
			var args: Array = game.MusicMaze.integers(action.slice(1))
			if method=="advance":
				for i in args[0]:
					game.advance()
					if entry.get("continuous",false) and (i%8==7 or i==args[0]-1):
						capture(game,entry.name+"-%04d"%index,entry.get("pointer",[]))
						index += 1
			elif method=="set":
				game.theater.set(args[0].to_snake_case(),args[1])
			elif method in ["click","begin_drag","move_drag"]:
				game.theater.call(method,Vector2i(args[0],args[1]))
			else:
				game.theater.callv(method,args)
			if entry.get("continuous",false) and method!="advance":
				capture(game,entry.name+"-%04d"%index,entry.get("pointer",[]))
				index += 1
		if not entry.get("continuous",false):
			capture(game,entry.name,entry.get("pointer",[]))
	var file = FileAccess.open(output.path_join("godot.json"),FileAccess.WRITE)
	file.store_string(JSON.stringify(snapshots))
	file.close()
	game.queue_free()
	await process_frame
	quit()

func capture(game, name: String, pointer: Array) -> void:
	var a = game.theater
	a.draw(game.surface)
	if not pointer.is_empty():
		game.pointer = Vector2i(pointer[0],pointer[1])
		game.draw_pointer()
	game.surface.image.save_png(output.path_join(name+".png"))
	snapshots.append({"name":name,"state":{"selection":a.selection.duplicate(),"order":a.order.duplicate(),"category":a.category,"tick":a.tick,"playing":a.playing,"presenting":a.presenting,"phase":a.phase,"curtain":a.curtain,"curtainMoving":a.curtain_moving,"director":a.director,"feedback":a.feedback,"previousValidation":a.previous_validation,"performances":a.performances,"actorDrag":a.actor_drag.duplicate(true),"props":a.props.duplicate(true),"tokenSprite":a.token_sprite.duplicate() if a.token_sprite!=null else null,"random":game.random.seed},"sounds":game.sound_events.duplicate(true)})
