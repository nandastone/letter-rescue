extends SceneTree
var game
var checks: Array = []
var touch: bool = false
var label: String

func _initialize() -> void:
	call_deferred("run")

func check(value: bool, name: String) -> void:
	checks.append({"name":label+": "+name,"passed":value,"tick":game.tick})
	if not value:
		print(JSON.stringify(checks.back()))

func pointer(down: bool, x: int, y: int) -> void:
	game.move_pointer(Vector2i(x,y))
	if touch:
		var event = InputEventScreenTouch.new()
		event.position = Vector2(x,y)
		event.pressed = down
		game._input(event)
	else:
		game.pointer_input("mouse",down,Vector2i(x,y))

func click(x: int, y: int) -> void:
	pointer(true,x,y)
	pointer(false,x,y)

func wait_for(condition: Callable, limit: int = 6000) -> bool:
	for i in limit:
		if condition.call():
			return true
		game.advance()
	return false

func settled() -> bool:
	return wait_for(func(): return game.travel.is_empty() and game.theater.presentation.is_empty() and game.theater.token_sequence.is_empty() and not game.theater.playing and not game.theater.hide_cursor and game.theater.preview_category<0)

func run() -> void:
	for variant in 2:
		touch = bool(variant)
		label = "touch-girl" if touch else "mouse-boy"
		game = load("res://main.tscn").instantiate()
		game.boot_enabled = false
		game.persistence_enabled = false
		root.add_child(game)
		game.set_process(false)
		game.audio_output_enabled = false
		game.capture_sound_events = true
		game.random.reset(123456)
		game.theater.dispose()
		game.theater = game.Theater.new(game,false)
		click(145 if touch else 95,145)
		check(wait_for(func(): return game.scene=="inside"),"character enters room")
		click(62,134)
		check(not game.travel.is_empty() and game.travel.variant==2,"curtains hotspot starts original theater transfer")
		check(wait_for(func(): return game.scene=="theater") and settled(),"theater entrance and opening curtains finish")
		var a = game.theater
		click(187,85)
		click(187,101)
		check(a.mix_up and a.props_enabled,"options respond to input")
		click(210,140)
		check(settled() and not a.options,"start opens sentence editor")
		for c in 4:
			click(35,40+32*c)
			var b = a.choice_bounds()[[0,0,1,1][c]]
			click(int((b[1]+b[3])/2),int((b[0]+b[2])/2))
			check(settled() and a.selection[c]==[0,0,1,1][c],"notebook category %d selects and previews"%c)
		check(a.sentence()=="The baby blows bubbles in the jungle at night.","original sentence assembled")
		click(80,172)
		check(a.playing and a.valid_play,"director starts valid performance")
		check(settled() and a.performances==1,"spoken and animated performance completes")
		pointer(true,151,58)
		game.advance(16)
		game.move_pointer(Vector2i(173,58))
		pointer(false,173,58)
		check(settled() and a.validation()==5,"held sentence token swaps subject and action")
		click(80,172)
		check(settled() and a.feedback==5,"invalid sentence performs then displays grammar feedback")
		click(255,54)
		check(a.validation()==0,"correct button repairs word order")
		click(36,169)
		check(a.category==4,"props notebook opens recovered decorations")
		var box = a.choice_bounds()[0]
		pointer(true,int((box[1]+box[3])/2),28)
		game.move_pointer(Vector2i(180,120))
		pointer(false,180,120)
		check(a.props[1].size()==1 and a.props[1][0].x>=103 and a.props[1][0].y>=53,"decoration dragged onto stage")
		var decoration = a.props[1][0]
		pointer(true,decoration.x+1,decoration.y+1)
		game.move_pointer(Vector2i(5,5))
		pointer(false,5,5)
		check(a.props[1].is_empty(),"decoration dropped outside stage is removed")
		# Overlapping equal dictionaries must remain two separate decorations.
		a.add_prop(0,[130,115])
		a.add_prop(0,[220,115])
		var first = a.props[1][0].duplicate()
		var second = a.props[1][1]
		pointer(true,second.x+1,second.y+1)
		game.move_pointer(Vector2i(first.x+1,first.y+1))
		pointer(false,first.x+1,first.y+1)
		pointer(true,first.x+1,first.y+1)
		game.move_pointer(Vector2i(first.x+20,first.y+1))
		pointer(false,first.x+20,first.y+1)
		check(a.props[1].size()==2 and a.props[1][0].x==first.x and a.props[1][1].x!=first.x,"overlapping identical decorations drag independently")
		a.props[1].clear()
		var rect = a.actor_rect()
		pointer(true,int((rect[1]+rect[3])/2),int((rect[0]+rect[2])/2))
		game.advance(16)
		game.move_pointer(Vector2i(240,135))
		pointer(false,240,135)
		check(a.actor_drag[2]!=[0,0],"actor can be moved inside stage bounds")
		click(115,55)
		check(settled() and a.order.size()==4,"shuffle completes all five animated swaps")
		# Validate file persistence with a dedicated temporary Godot user file.
		a.storage_enabled = true
		a.save_path = "user://theater-control-check.json"
		a.save()
		var restored = game.Theater.new(game,false)
		restored.save_path = a.save_path
		restored.restore()
		check(restored.saved_state()==a.saved_state(),"saved selections, props, options and actor positions reload")
		var file = FileAccess.open(a.save_path,FileAccess.WRITE)
		file.store_string('{"version":1,"selection":[900]}')
		file.close()
		var before = restored.saved_state()
		restored.restore()
		check(restored.saved_state()==before,"malformed save is rejected without partial mutation")
		DirAccess.remove_absolute(ProjectSettings.globalize_path(a.save_path))
		a.storage_enabled = false
		restored.dispose()
		click(311,10)
		check(a.leaving and a.curtain_moving,"exit closes stage curtains first")
		check(wait_for(func(): return game.scene=="inside" and game.travel.is_empty()),"theater return transfer finishes in retained room")
		click(62,134)
		check(wait_for(func(): return game.scene=="theater") and settled() and a.selection==[0,0,1,1],"reentry retains the play")
		game.queue_free()
		await process_frame
	var passed = checks.all(func(item): return item.passed)
	var output = OS.get_cmdline_user_args()[0]
	var file = FileAccess.open(output,FileAccess.WRITE)
	file.store_string(JSON.stringify({"passed":passed,"checks":checks,"scope":"Fresh mouse/boy and touch/girl sessions through production pointer routing; bounded original state updates, performances, dragging, persistence and room transfers. No rendered/audio timing parity claim."},"  "))
	file.close()
	print(JSON.stringify({"passed":passed,"checks":checks.size()}))
	quit(0 if passed else 1)
