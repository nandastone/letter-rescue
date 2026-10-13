extends SceneTree
var game
var checks: Array = []
var touch: bool
var label: String

func _initialize() -> void:
	call_deferred("run")

func check(value: bool, name: String) -> void:
	checks.append({"name":label+": "+name,"passed":value,"tick":game.tick})
	if not value:
		print(JSON.stringify(checks.back()))

func click(point: Vector2i) -> void:
	game.move_pointer(point)
	for down in [true,false]:
		if touch:
			var event = InputEventScreenTouch.new()
			event.position = point
			event.pressed = down
			game._input(event)
		else:
			game.pointer_input("mouse",down,point)

func rect_click(r: Array) -> void:
	click(Vector2i(int((r[1]+r[3])/2),int((r[0]+r[2])/2)))

func wait_for(condition: Callable, limit: int = 12000) -> bool:
	for i in limit:
		if condition.call():
			return true
		game.advance()
	return false

func run() -> void:
	for variant in 2:
		touch = bool(variant)
		label = "chips-touch-girl" if touch else "money-mouse-boy"
		game = load("res://main.tscn").instantiate()
		game.boot_enabled = false
		game.persistence_enabled = false
		root.add_child(game)
		game.set_process(false)
		game.audio_output_enabled = false
		game.boardgame.storage_enabled = false
		game.random.reset(123456)
		click(Vector2i(145 if touch else 95,145))
		check(wait_for(func(): return game.scene=="inside" and not game.entering),"character enters room")
		click(Vector2i(180,189))
		check(not game.travel.is_empty() and game.travel.variant==3,"board starts original transfer")
		check(wait_for(func(): return game.scene=="boardgame" and game.travel.is_empty()),"board opens from room")
		var g = game.boardgame
		check(g.options and not g.played,"first entry shows options over initialized board")
		rect_click(g.tables.options_rects[2 if touch else 1])
		check(g.mode==variant,"select game mode")
		rect_click(g.tables.options_rects[3])
		check(g.opponent==1,"select human opponent")
		rect_click(g.tables.options_rects[7])
		rect_click(g.tables.options_rects[9])
		check(g.levels==[2,1],"independent human goals")
		rect_click(g.tables.options_rects[4])
		rect_click(g.tables.options_rects[5])
		rect_click(g.tables.options_rects[17])
		check(not g.options and g.motion.busy and g.levels==[0,0],"start synchronizes robot goal and plays dashboard")
		check(wait_for(func(): return not g.motion.busy) and g.phase=="ready","dashboard finishes")
		var seen = {}
		var exchanges = 0
		var turns = 0
		for i in 250000:
			seen[g.phase] = true
			if g.phase=="exchange" and g.exchange!=null and not g.motion.accepted:
				var balance = g.balances.duplicate()
				rect_click(g.tables.chip_rects[0])
				check(not g.options and g.phase=="exchange" and g.balances==balance,"options cannot cancel a pending exchange")
				rect_click(g.tables.chip_rects[1+g.exchange.digit])
				exchanges += 1
			elif not g.motion.busy and g.moving==null:
				if g.winner>=0 or g.loser>=0:
					break
				if g.phase in ["ready","result"]:
					rect_click(g.tables.game_rects[2])
					turns += 1
				elif g.phase=="move" and g.role()!=2:
					var best = g.neighbours()[0]
					for node in g.neighbours():
						if g.types[node]<g.types[best]:
							best = node
					rect_click(g.tables.node_rects[best])
				elif g.phase=="reward":
					var choice = 0 if g.rewards[0]>=g.rewards[1] else 1
					rect_click((g.tables.chip_rects if touch else g.tables.money_rects)[8+choice])
			game.advance()
		check(g.phase=="result" and not g.motion.busy and (g.winner>=0 or g.loser>=0),"complete game reaches winning or losing ending")
		check(turns>1 and seen.has("rolling") and seen.has("move") and seen.has("reward"),"turns include rolling, movement and reward decisions")
		if touch:
			check(exchanges>0,"chip game carries or borrows through required input")
		rect_click(g.tables.game_rects[2])
		check(game.rewards.active and game.rewards.kind==("chips" if touch else "money"),"ending opens shared prize chooser")
		var robot = game.rewards.role==2
		var prize = game.rewards.choices[0]
		rect_click(game.rewards.rects[0])
		check(wait_for(func(): return not game.rewards.active),"prize delivery finishes")
		check(game.rewards.shelf[0] if robot else game.resident.find(prize)!=null,"prize belongs to winner")
		check(wait_for(func(): return not g.motion.busy) and g.phase=="ready","prize delivery starts a fresh game")
		click(Vector2i(311,10))
		check(wait_for(func(): return game.scene=="inside" and game.travel.is_empty()),"return to retained room")
		g.storage_enabled = true
		g.save_path = "user://board-control-check.json"
		g.save()
		var restored = game.BoardGame.new(game,false)
		restored.save_path = g.save_path
		restored.restore()
		check(restored.saved_state()==g.saved_state(),"mode, opponent and all six goal settings reload")
		var before = restored.saved_state()
		var invalid = FileAccess.open(g.save_path,FileAccess.WRITE)
		invalid.store_string('{"version":1,"mode":0,"opponent":1,"levels":[0,1,2,0,1,3]}')
		invalid.close()
		restored.restore()
		check(restored.saved_state()==before,"invalid goal file leaves preferences intact")
		restored.dispose()
		DirAccess.remove_absolute(ProjectSettings.globalize_path(g.save_path))
		g.storage_enabled = false
		game.queue_free()
		await process_frame
	var passed = checks.all(func(c): return c.passed)
	var file = FileAccess.open(OS.get_cmdline_user_args()[0],FileAccess.WRITE)
	file.store_string(JSON.stringify({"passed":passed,"checks":checks,"scope":"Fresh mouse/boy Money and touch/girl Chip sessions, through options, ordinary legal input, automatic robot movement, exchanges, game ending, prize delivery and room return. Shared RNG seeded once before character selection; no gameplay state or balances are injected."},"  "))
	file.close()
	print(JSON.stringify({"passed":passed,"checks":checks.size()}))
	quit(0 if passed else 1)
