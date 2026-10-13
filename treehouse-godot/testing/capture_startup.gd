extends SceneTree
## Headless deterministic rendering and real input-handler checks.
var output: String
var game
var checks: Array = []

func _initialize() -> void:
	output = OS.get_cmdline_user_args()[0]
	call_deferred("run")

func check(ok: bool, label: String) -> void:
	checks.append({"name":label,"passed":ok})
	if not ok:
		push_error(label)

func capture(name: String) -> void:
	game.render()
	check(game.surface.image.save_png(output.path_join(name+".png")) == OK,"save "+name)

func run() -> void:
	game = load("res://main.tscn").instantiate()
	game.boot_enabled = false
	game.persistence_enabled = false
	root.add_child(game)
	game.set_process(false)
	game.date_override = {"year":1992,"month":1,"day":1,"hour":12,"minute":39}
	game.room.date = game.date_override.duplicate()
	game.credit = 2
	capture("outside")
	for who in ["boy","girl"]:
		game.select_screen()
		var touch = InputEventScreenTouch.new()
		touch.pressed = true
		touch.position = Vector2(95,145) if who=="boy" else Vector2(145,145)
		game._input(touch)
		check(game.character==who and game.entering,"touch selects "+who)
		for i in 2000:
			game.advance()
			if game.scene=="inside":
				break
		check(game.scene=="inside" and not game.entering,who+" entrance reaches room")
		game.pointer = Vector2i(95,145)
		game.pointer_visible = true
		capture("inside-"+who)
		var escape = InputEventKey.new()
		escape.pressed = true
		escape.keycode = KEY_ESCAPE
		game._input(escape)
		check(game.scene=="outside" and game.resident.selected,"Escape returns to retained-character yard")
	var passed = checks.all(func(c): return c.passed)
	var report = FileAccess.open(output.path_join("godot.json"),FileAccess.WRITE)
	report.store_string(JSON.stringify({"checks":checks,"passed":passed},"\t"))
	report.close()
	game.queue_free()
	quit(0 if passed else 1)
