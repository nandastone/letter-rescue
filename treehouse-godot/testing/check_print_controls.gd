extends SceneTree
var game
var checks: Array = []
var output: String

func _initialize() -> void:
	call_deferred("run")

func check(value: bool, name: String) -> void:
	checks.append({"name":name,"passed":value})
	if not value: print(JSON.stringify(checks.back()))

func click(x: int, y: int) -> void:
	game.move_pointer(Vector2i(x,y))
	game.pointer_input("mouse",true,game.pointer)
	game.pointer_input("mouse",false,game.pointer)

func key(code: int) -> void:
	var event = InputEventKey.new()
	event.keycode = code
	event.pressed = true
	game._input(event)
	event.pressed = false
	game._input(event)

func wait_for(condition: Callable) -> bool:
	for i in 10000:
		if condition.call(): return true
		game.advance()
	return false

func print_controls(label: String, source: Image) -> void:
	var f = game.file_exchange
	var pixels = source.get_data()
	key(KEY_F9)
	check(f.active and f.print_image!=null,label+": F9 opens print controls")
	check(f.buttons["save-picture"].visible and not f.buttons["load-status"].visible,label+": picture controls replace save-file actions")
	var png = f.export_data("save-picture")
	var decoded = Image.new()
	check(decoded.load_png_from_buffer(png)==OK and decoded.get_size()==Vector2i(320,200) and decoded.get_data()==pixels,label+": complete PNG equals preview pixels")
	var file = FileAccess.open(output+"/"+label+".png",FileAccess.WRITE)
	file.store_buffer(png)
	file.close()
	file = FileAccess.open(output+"/"+label+".html",FileAccess.WRITE)
	file.store_string(f.print_document(png))
	file.close()
	var tick = game.tick
	game._process(1.0)
	check(game.tick==tick,label+": output controls pause simulation")
	key(KEY_Z)
	check(game.music.notes.is_empty() and source.get_data()==pixels,label+": key input cannot change print source")
	key(KEY_ESCAPE)
	check(not f.active and f.print_image==null and f.preview()==source,label+": Escape returns to unchanged preview")
	key(KEY_F9)
	check(f.export_data("save-picture")==png,label+": reopening preserves identical PNG")
	key(KEY_F9)
	check(not f.active and f.preview()==source,label+": F9 closes utility without dismissing preview")
	key(KEY_ESCAPE)
	check(f.preview()==null,label+": second Escape dismisses original preview")

func run() -> void:
	output = OS.get_cmdline_user_args()[0]
	game = load("res://main.tscn").instantiate()
	game.boot_enabled = false
	game.persistence_enabled = false
	root.add_child(game)
	game.set_process(false)
	game.audio_output_enabled = false
	click(95,145)
	check(wait_for(func(): return game.scene=="inside"),"room entry")
	click(60,185)
	check(wait_for(func(): return game.scene=="music" and game.travel.is_empty()),"music entry")
	click(274,169)
	key(KEY_Z)
	key(KEY_C)
	for mode in 2:
		if mode: click(275,149)
		click(298,125)
		check(game.music.dialog.get("message","")=="print","score confirmation "+str(mode))
		click(23,70)
		print_controls("score-"+str(mode),game.music.print_view)
	game.preferences.settings.printing = false
	click(298,125)
	check(game.music.dialog.is_empty() and game.music.print_view==null,"printing preference disables score prompt")
	game.preferences.settings.printing = true
	key(KEY_ESCAPE)
	check(wait_for(func(): return game.scene=="inside" and game.travel.is_empty() and not game.resident.busy),"music room return")
	click(134,109)
	check(wait_for(func(): return game.scene=="nature" and game.travel.is_empty()),"nature entry")
	var n = game.nature
	game.move_pointer(Vector2i(14,112))
	game.pointer_input("mouse",true,game.pointer)
	game.move_pointer(Vector2i(210,110))
	game.pointer_input("mouse",false,game.pointer)
	check(n.objects[0].size()==1,"animal placed through drag input")
	for mode in 2:
		if mode:
			var r = n.tables.rectangles[13]
			click(int((r[1]+r[3])/2),int((r[0]+r[2])/2))
		click(30,185)
		check(n.dialog.get("print",false),"nature confirmation "+str(mode))
		click(30,145)
		print_controls("nature-"+str(mode),n.print_view)
	key(KEY_F9)
	check(game.file_exchange.active and game.file_exchange.print_image==null and game.file_exchange.buttons["load-status"].visible and not game.file_exchange.buttons["save-picture"].visible,"F9 returns to save-file controls outside preview")
	key(KEY_ESCAPE)
	var passed = checks.all(func(c): return c.passed)
	var report = FileAccess.open(output+"/report.json",FileAccess.WRITE)
	report.store_string(JSON.stringify({"passed":passed,"checks":checks,"scope":"Production input reaches short/long score and day/night nature print previews. PNG encoding is compared with every RGBA source pixel; utility input/pause/reopen/close paths checked. Desktop HTML generated but shell/dialog not exercised; native artwork checked separately."},"\t"))
	report.close()
	print(JSON.stringify({"passed":passed,"checks":checks.size()}))
	game.audio.stream = null
	game.audio_cache.clear()
	game.queue_free()
	await process_frame
	quit(0 if passed else 1)
