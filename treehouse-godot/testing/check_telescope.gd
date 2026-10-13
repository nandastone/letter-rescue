extends SceneTree
var game
var checks: Array = []
var output: String
var touch: bool
var label: String

func _initialize() -> void:
	call_deferred("run")

func check(value: bool, name: String) -> void:
	checks.append({"name":label+": "+name,"passed":value})
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

func wait_for(condition: Callable) -> bool:
	for i in 10000:
		if condition.call():
			return true
		game.advance()
	return false

func settled() -> bool:
	return game.travel.is_empty() and not game.telescope.busy and not game.resident.busy

func run() -> void:
	output = OS.get_cmdline_user_args()[0]
	var fixture = JSON.parse_string(FileAccess.get_file_as_string(output+"/fixture.json"))
	for variant in 2:
		touch = bool(variant)
		label = "touch-girl" if touch else "mouse-boy"
		game = load("res://main.tscn").instantiate()
		game.boot_enabled = false
		game.persistence_enabled = false
		root.add_child(game)
		game.set_process(false)
		game.audio_output_enabled = false
		game.nature.storage_enabled = false
		click(Vector2i(145 if touch else 95,145))
		check(wait_for(func(): return game.scene=="inside" and not game.entering),"enter room")
		var seen: Array = []
		for visit in 4:
			click(Vector2i(199,122))
			check(not game.travel.is_empty() and game.travel.get("telescope",false),"approach starts")
			check(wait_for(func(): return game.scene=="telescope" and settled()),"view settles")
			var view = game.telescope.view
			check(not seen.has(view),"random visit does not repeat before four views")
			seen.append(view)
			var reference = fixture.views[view]
			game.pointer_visible = true
			game.move_pointer(Vector2i(reference.pointer[0],reference.pointer[1]))
			game.render()
			game.surface.image.save_png(output+"/"+label+"-view-%d.png"%view)
			var r = game.store.data.telescope.rectangles[view]
			var middle = int((r[0]+r[2])/2)
			click(Vector2i(r[1],middle))
			check(game.scene=="telescope" and game.telescope.actor.start_tick==game.tick,"inside left edge replays")
			if game.telescope.busy:
				click(Vector2i(r[1]-1,middle))
				check(game.scene=="telescope" and game.travel.is_empty(),"animation owns input while playing")
			check(wait_for(settled),"replay finishes")
			click(Vector2i(r[1]-1,middle))
			check(game.scene=="inside" and not game.travel.is_empty(),"outside left edge starts return")
			check(wait_for(settled) and game.resident.pose==1,"return finishes in original pose")
		check(seen.size()==4,"all four views reachable through room input")
		game.queue_free()
		await process_frame
	# Isolated populated-shelf fixture: native image, speech tail and view priority.
	label = "robot-shelf-fixture"
	game = load("res://main.tscn").instantiate()
	game.boot_enabled = false
	game.persistence_enabled = false
	root.add_child(game)
	game.set_process(false)
	game.audio_output_enabled = false
	game.nature.storage_enabled = false
	game.rewards.shelf = fixture.shelf.shelf
	game.rewards.visited = 7
	game.set_scene("telescope")
	check(game.telescope.view==3,"earned prize selects shelf on next visit")
	check(game.telescope.busy,"populated shelf runs robot speech")
	check(wait_for(settled),"robot speech finishes")
	game.move_pointer(Vector2i(fixture.shelf.pointer[0],fixture.shelf.pointer[1]))
	game.render()
	game.surface.image.save_png(output+"/robot-shelf.png")
	click(Vector2i(159,79))
	check(game.telescope.busy,"shelf replays through ordinary click")
	check(wait_for(func(): return game.telescope.actor.done),"robot display completes")
	if game.telescope.tail_wait:
		click(Vector2i(311,10))
		check(game.scene=="telescope" and not game.telescope.tail_wait,"click dismisses speech tail before leaving")
	game.queue_free()
	await process_frame
	var passed = checks.all(func(item): return item.passed)
	var file = FileAccess.open(output+"/controls.json",FileAccess.WRITE)
	file.store_string(JSON.stringify({"passed":passed,"checks":checks},"  "))
	file.close()
	print(JSON.stringify({"passed":passed,"checks":checks.size()}))
	quit(0 if passed else 1)
