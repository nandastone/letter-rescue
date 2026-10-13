extends SceneTree
var output: String
var snapshots: Array = []
var game

func _initialize() -> void:
	output = OS.get_cmdline_user_args()[0]
	call_deferred("run")

func capture(name: String) -> void:
	var n = game.nature
	var q = n.quiz
	n.draw(game.surface)
	game.surface.image.save_png(output.path_join(name+".png"))
	var state = {"nature":{},"quiz":{},"seed":game.random.seed}
	for key in ["time","attribute","values","category","selected","factIndex","factOpen","objects"]:
		state.nature[key] = n.get(key.to_snake_case())
	for key in ["cards","secret","remaining","asked","player","available","phase","guessing","winner","options","selected","selectedAttribute","answer","explanation","winStage"]:
		state.quiz[key] = q.get(key.to_snake_case())
	snapshots.append({"name":name,"state":state.duplicate(true),"sounds":game.sound_events.duplicate(true)})

func run() -> void:
	game = load("res://main.tscn").instantiate()
	game.boot_enabled = false
	game.persistence_enabled = false
	root.add_child(game)
	game.set_process(false)
	game.audio_output_enabled = false
	game.capture_sound_events = true
	game.scene = "nature"
	var cases = JSON.parse_string(FileAccess.get_file_as_string(output.path_join("cases.json")))
	for entry in cases:
		game.nature.dispose()
		game.nature = game.Nature.new(game,false)
		game.character = entry.get("character","boy")
		game.tick = 0
		game.random.reset(123456)
		game.sound_events.clear()
		var n = game.nature
		for key in entry.get("state",{}):
			n.set(key.to_snake_case(),game.MusicMaze.integers(entry.state[key]))
		for key in entry.get("quiz",{}):
			n.quiz.set(key.to_snake_case(),game.MusicMaze.integers(entry.quiz[key]))
		var index = 0
		for action in entry.get("actions",[]):
			var method: String = action[0]
			var args: Array = game.MusicMaze.integers(action.slice(1))
			if method=="advance":
				for i in args[0]:
					game.advance()
					if entry.get("continuous",false) and (i%12==11 or i==args[0]-1):
						capture(entry.name+"-%04d"%index)
						index += 1
			elif method=="smart_ask":
				n.quiz.ask(n.quiz.available[0])
			elif method=="smart_guess":
				n.quiz.guess((n.quiz.secret[n.quiz.player]+args[0])%8)
			elif method=="q_set":
				n.quiz.set(args[0].to_snake_case(),args[1])
			elif method.begins_with("q_"):
				n.quiz.callv(method.trim_prefix("q_"),args)
			elif method in ["click","begin_drag","move_drag"]:
				n.call(method,Vector2i(args[0],args[1]))
			else:
				n.callv(method,args)
			if entry.get("continuous",false) and method!="advance":
				capture(entry.name+"-%04d"%index)
				index += 1
		if not entry.get("continuous",false):
			capture(entry.name)
	var file = FileAccess.open(output.path_join("godot.json"),FileAccess.WRITE)
	file.store_string(JSON.stringify(snapshots))
	file.close()
	game.queue_free()
	await process_frame
	quit()
