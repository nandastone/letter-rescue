extends SceneTree
## Ordinary pointer/touch play with an advancing civil clock; no need/pose fixtures.
var game
var checks: Array = []
var touch: bool = false
var base_time: int = 0

func _initialize() -> void:
	call_deferred("run")

func check(value: bool, name: String) -> void:
	checks.append({"name":("touch-girl: " if touch else "mouse-boy: ")+name,"passed":value,"tick":game.tick})

func step() -> void:
	game.date_override = Time.get_datetime_dict_from_unix_time(base_time+int(game.tick/game.TICK_HZ))
	game.advance()

func idle() -> bool:
	return not game.entering and not game.resident.busy and not game.room.busy and game.room.speech.is_empty() and game.tick>=game.room.speech_due and not game.exterior.busy

func wait_for(condition: Callable, limit: int = 50000) -> bool:
	for i in limit:
		if condition.call():
			return true
		step()
	return false

func press(point: Vector2i, down: bool) -> void:
	if touch:
		var event = InputEventScreenTouch.new()
		event.position = Vector2(point)
		event.pressed = down
		game._input(event)
	else:
		game.pointer_input("mouse",down,point)

func offer(type: int) -> bool:
	if not wait_for(idle):
		return false
	var r = game.resident
	var object = r.find(type)
	var bounds = r.tables.objects[type].inside if object==null else r.bounds(object)
	var from = Vector2i(int((bounds[1]+bounds[3])/2),int((bounds[0]+bounds[2])/2))
	press(from,true)
	if r.drag.is_empty() or r.drag.object.type!=type:
		press(from,false)
		return false
	for i in 16:
		step()
	var cr = r.rect()
	var to = Vector2i(int((cr[1]+cr[3])/2),int((cr[0]+cr[2])/2))
	if touch:
		var event = InputEventScreenDrag.new()
		event.position = Vector2(to)
		game._input(event)
	else:
		game.move_pointer(to)
	press(to,false)
	return wait_for(idle)

func run() -> void:
	base_time = int(Time.get_unix_time_from_datetime_dict({"year":1992,"month":1,"day":1,"hour":10,"minute":0,"second":0}))
	for mode in [false,true]:
		touch = mode
		game = load("res://main.tscn").instantiate()
		game.boot_enabled = false
		game.persistence_enabled = false
		root.add_child(game)
		game.set_process(false)
		game.audio_output_enabled = false
		game.random.reset(42)
		press(Vector2i(145 if touch else 95,145),true)
		press(Vector2i(145 if touch else 95,145),false)
		check(wait_for(idle) and game.scene=="inside","selection enters room")
		check(offer(8) and game.resident.pose!=4 and game.resident.find(8)!=null,"rested friend refuses pillow and returns it")
		check(wait_for(func(): return idle() and game.resident.hunger>=3),"original timer makes friend hungry")
		check(offer(18) and game.resident.hunger==1 and game.resident.find(18)==null,"dragging apple feeds friend")
		check(wait_for(func(): return idle() and game.resident.fatigue>=4),"original timer makes friend tired")
		check(offer(8) and game.resident.pose==4 and game.resident.fatigue==1 and game.resident.find(8)==null,"dragging pillow starts nap")
		game.navigate_scene("outside")
		check(game.scene=="outside" and game.resident.pose==4,"yard visit preserves nap")
		game.navigate_scene("inside")
		check(game.scene=="inside" and game.resident.pose==4,"room return preserves nap")
		check(wait_for(func(): return idle() and game.resident.pose!=4 and game.resident.wake_time.is_empty()) and game.resident.fatigue==1 and game.resident.find(8)!=null,"civil clock wakes rested friend and restores pillow")
		check(wait_for(func(): return idle() and game.resident.fatigue>=4) and offer(8) and game.resident.pose==4,"second nap starts through original care controls")
		press(Vector2i(60,185),true)
		press(Vector2i(60,185),false)
		check(wait_for(func(): return game.scene=="music" and game.travel.is_empty()) and game.resident.pose!=4 and game.resident.fatigue==4 and game.resident.find(8)!=null,"music hotspot interrupts nap and restores pillow before travel")
		game.queue_free()
		await process_frame
	var passed = checks.all(func(c): return c.passed)
	var file = FileAccess.open(OS.get_cmdline_user_args()[0],FileAccess.WRITE)
	file.store_string(JSON.stringify({"passed":passed,"checks":checks,"scope":"Mouse/touch control handlers and ordinary game updates from selection, with advancing civil clock. No hunger, fatigue, object, or pose fixtures. Device audio disabled; original sample durations retained."},"\t"))
	file.close()
	print(JSON.stringify({"passed":passed,"checks":checks}))
	quit(0 if passed else 1)
