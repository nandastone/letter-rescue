extends SceneTree
var game
var checks: Array = []

func _initialize() -> void:
	call_deferred("run")

func check(value: bool, name: String) -> void:
	checks.append({"name":name,"passed":value,"tick":game.tick})

func wait_for(condition: Callable, limit: int = 10000) -> bool:
	for i in limit:
		if condition.call():
			return true
		game.advance()
	return false

func key(code: int, down: bool) -> void:
	var event = InputEventKey.new()
	event.keycode = code
	event.pressed = down
	game._input(event)

func click(point: Vector2i) -> void:
	game.pointer_input("mouse",true,point)
	game.pointer_input("mouse",false,point)

func run() -> void:
	game = load("res://main.tscn").instantiate()
	game.boot_enabled = false
	game.persistence_enabled = false
	root.add_child(game)
	game.set_process(false)
	game.audio_output_enabled = false
	click(Vector2i(95,145))
	check(wait_for(func(): return game.scene=="inside"),"select boy and enter room")
	click(Vector2i(60,185))
	check(not game.travel.is_empty(),"piano hotspot starts original room transition")
	check(wait_for(func(): return game.scene=="music" and game.travel.is_empty()),"transition reaches music")
	game.capture_sound_events = true
	for item in game.music.tables.keys:
		var code = item.keyboard.unicode_at(0)
		key(code,true)
		check(game.music.notes.get("key:%d"%code,-1)==int(item.pitch),"keyboard pitch %d"%int(item.pitch))
		key(code,false)
		check(game.music.notes.is_empty(),"keyboard release %d"%int(item.pitch))
	var event = InputEventScreenTouch.new()
	event.position = Vector2(92,180)
	event.pressed = true
	game._input(event)
	check(game.music.notes.get("touch:0",-1)==0,"touch plays low C")
	var drag = InputEventScreenDrag.new()
	drag.position = Vector2(110,180)
	game._input(drag)
	check(game.music.notes.get("touch:0",-1)==2,"held touch moves to adjacent note")
	game._notification(Node.NOTIFICATION_APPLICATION_FOCUS_OUT)
	check(game.music.notes.is_empty() and game.held.is_empty(),"focus loss releases held music input")
	key(KEY_Z,true)
	check(not game.music.notes.is_empty(),"window-focus regression starts with a held physical note")
	game._notification(Node.NOTIFICATION_WM_WINDOW_FOCUS_OUT)
	check(game.music.notes.is_empty() and game.held.is_empty(),"window focus loss releases held music input")
	key(KEY_Z,false)
	click(Vector2i(66,145))
	check(game.music.playing,"play button starts song")
	check(wait_for(func(): return not game.music.playing),"song completes through normal updates")
	click(Vector2i(280,150))
	check(game.music.mode==1,"score-size button selects two staffs")
	click(Vector2i(17,125))
	check(game.music.selector.open,"family button opens instrument selector")
	click(Vector2i(285,7))
	check(not game.music.selector.open,"selector returns to piano")
	key(KEY_ESCAPE,true)
	check(game.scene=="inside" and not game.travel.is_empty(),"Escape begins return transition")
	check(wait_for(func(): return game.travel.is_empty()) and game.scene=="inside","return transition completes indoors")
	game.render()
	var path = OS.get_cmdline_user_args()[0]
	game.surface.image.save_png(path.get_basename()+".png")
	var passed = checks.all(func(c): return c.passed)
	var file = FileAccess.open(path,FileAccess.WRITE)
	file.store_string(JSON.stringify({"passed":passed,"checks":checks,"sounds":game.sound_events,"scope":"Production controls/updates from selection through music and return. Mouse, touch, every original keyboard key, held-note movement, focus cleanup, song completion and selector navigation. No gameplay state injection; audio device disabled."},"\t"))
	file.close()
	print(JSON.stringify({"passed":passed,"checks":checks}))
	game.queue_free()
	await process_frame
	quit(0 if passed else 1)
