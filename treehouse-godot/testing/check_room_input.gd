extends SceneTree
var game
var checks: Array = []

func _initialize() -> void:
	call_deferred("run")

func check(value: bool, name: String) -> void:
	checks.append({"name":name,"passed":value})

func key(code: Key, pressed: bool, shift: bool = false) -> void:
	var event = InputEventKey.new()
	event.keycode = code
	event.pressed = pressed
	event.shift_pressed = shift
	game._input(event)

func touch(point: Vector2, pressed: bool) -> void:
	var event = InputEventScreenTouch.new()
	event.position = point
	event.pressed = pressed
	game._input(event)

func run() -> void:
	game = load("res://main.tscn").instantiate()
	game.boot_enabled = false
	game.persistence_enabled = false
	root.add_child(game)
	game.set_process(false)
	game.scene = "inside"
	game.animations.clear()
	game.balloon.hidden = true
	game.room.enter(game.tick)
	touch(Vector2(66,94),true)
	touch(Vector2(66,94),false)
	check(game.chalk.tool==0,"touch selects white chalk")
	touch(Vector2(80,69),true)
	var drag = InputEventScreenDrag.new()
	drag.position = Vector2(115,69)
	game._input(drag)
	check(game.pointer==Vector2i(82,69),"native chalk motion clamps to two pixels")
	check(game.chalk.bitmap.get_pixel(19,23)==Color.WHITE,"touch stamps white chalk")
	touch(Vector2(115,69),false)
	check(game.chalk.previous==null and game.held.is_empty(),"touch release ends stroke")
	check(not game.pointer_visible,"touch does not draw a mouse cursor")
	game.move_pointer(Vector2i(160,120))
	check(game.chalk.tool==-1,"leaving board returns chalk")
	game.pointer = Vector2i(160,100)
	key(KEY_RIGHT,true)
	check(game.pointer.x==161,"keyboard pointer responds immediately")
	game.advance(2)
	check(game.pointer.x==161,"ordinary pointer waits three ticks")
	game.advance()
	check(game.pointer.x==162,"ordinary pointer advances at its deadline")
	key(KEY_RIGHT,false)
	key(KEY_RIGHT,true,true)
	var accelerated = game.pointer.x
	game.advance()
	check(game.pointer.x==accelerated+1,"Shift pointer advances each tick")
	key(KEY_RIGHT,false)
	touch(Vector2(66,94),true)
	touch(Vector2(66,94),false)
	touch(Vector2(80,69),true)
	key(KEY_RIGHT,true)
	game._notification(Node.NOTIFICATION_APPLICATION_FOCUS_OUT)
	check(game.held.is_empty() and game.pointer_keys.is_empty() and game.chalk.previous==null,"focus loss releases all held input")
	game.chalk.select(6)
	game.chalk.begin(Vector2i(79,69))
	game.chalk.move(Vector2i(77,67),true)
	check(game.chalk.bitmap.get_pixel(19,23)==Color.BLACK,"original eraser geometry removes chalk")
	var passed = checks.all(func(item): return item.passed)
	var file = FileAccess.open(OS.get_cmdline_user_args()[0],FileAccess.WRITE)
	file.store_string(JSON.stringify({"checks":checks,"passed":passed},"\t"))
	file.close()
	print(JSON.stringify({"checks":checks,"passed":passed}))
	game.queue_free()
	quit(0 if passed else 1)
