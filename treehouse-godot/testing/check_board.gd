extends SceneTree
var game
var output: String
var snapshots: Array = []
const FIELDS = ["mode","opponent","levels","options","played","phase","player","nodes","directions","balances","types","remaining","first","winner","loser","rewards","rewardCoins","path","message","rollFrames","rollIndex","rollResult","offerHint","nodeHint","offerStage","headerHidden","ending","carHidden","paymentHand","paymentCoinsVisible","paidChips","transfer","exchange","resolvedNodeIcons"]

func _initialize() -> void:
	output = OS.get_cmdline_user_args()[0]
	call_deferred("run")

func capture(name: String) -> void:
	var g = game.boardgame
	g.draw(game.surface)
	game.surface.image.save_png(output+"/"+name+".png")
	var state = {"seed":game.random.seed}
	for key in FIELDS:
		state[key] = g.get(key.to_snake_case())
	snapshots.append({"name":name,"state":state.duplicate(true),"sounds":game.sound_events.duplicate(true)})

func play_input() -> void:
	var g = game.boardgame
	if g.phase=="exchange" and g.exchange!=null and not g.motion.accepted:
		g.exchange_chips()
	elif not g.motion.busy and g.moving==null:
		if g.phase in ["ready","result"] and g.winner<0 and g.loser<0:
			g.roll()
		elif g.phase=="move" and g.role()!=2:
			g.move(g.neighbours()[0])
		elif g.phase=="reward":
			g.choose(0 if g.rewards[0]>=g.rewards[1] else 1)

func run() -> void:
	game = load("res://main.tscn").instantiate()
	game.boot_enabled = false
	game.persistence_enabled = false
	root.add_child(game)
	game.set_process(false)
	game.audio_output_enabled = false
	game.capture_sound_events = true
	game.scene = "boardgame"
	var cases = JSON.parse_string(FileAccess.get_file_as_string(output+"/cases.json"))
	for entry in cases:
		game.boardgame.dispose()
		game.boardgame = game.BoardGame.new(game,false)
		game.character = entry.get("character","boy")
		game.tick = 0
		game.random.reset(123456)
		game.sound_events.clear()
		var g = game.boardgame
		for key in entry.get("state",{}):
			g.set(key.to_snake_case(),game.MusicMaze.integers(entry.state[key]))
		var index = 0
		for action in entry.get("actions",[]):
			var method: String = action[0]
			var args: Array = game.MusicMaze.integers(action.slice(1))
			if method in ["advance","play"]:
				for i in args[0]:
					if method=="play":
						play_input()
					game.advance()
					if entry.get("continuous",false) and (i%24==23 or i==args[0]-1):
						capture(entry.name+"-%04d"%index)
						index += 1
			elif method=="motion":
				g.motion.start([g.motion.op(args[0],args.slice(1))])
			else:
				g.callv(method,args)
			if entry.get("continuous",false) and method not in ["advance","play"]:
				capture(entry.name+"-%04d"%index)
				index += 1
		if not entry.get("continuous",false):
			capture(entry.name)
	var file = FileAccess.open(output+"/godot.json",FileAccess.WRITE)
	file.store_string(JSON.stringify(snapshots))
	file.close()
	game.queue_free()
	await process_frame
	quit()
