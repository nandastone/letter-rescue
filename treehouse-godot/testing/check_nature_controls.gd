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

func pointer(down: bool, point: Vector2i) -> void:
	game.move_pointer(point)
	if touch:
		var event = InputEventScreenTouch.new()
		event.position = point
		event.pressed = down
		game._input(event)
	else:
		game.pointer_input("mouse",down,point)

func click(x: int, y: int) -> void:
	pointer(true,Vector2i(x,y))
	pointer(false,Vector2i(x,y))

func rect_click(rect: Array) -> void:
	click(int((rect[1]+rect[3])/2),int((rect[0]+rect[2])/2))

func wait_for(condition: Callable, limit: int = 12000) -> bool:
	for i in limit:
		if condition.call():
			return true
		game.advance()
	return false

func quiz_idle() -> bool:
	var q = game.nature.quiz
	return not q.busy and (q.win_animation==null or q.win_animation.done)

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
		game.random.reset(123456)
		game.nature.dispose()
		game.nature = game.Nature.new(game,false)
		click(145 if touch else 95,145)
		check(wait_for(func(): return game.scene=="inside"),"character enters room")
		click(134,109)
		check(not game.travel.is_empty() and game.travel.variant==1,"nature picture starts original transfer")
		check(wait_for(func(): return game.scene=="nature" and game.travel.is_empty()),"nature opens from room")
		var n = game.nature
		var q = n.quiz
		var thumb = n.thumbnails()[0]
		var point = Vector2i(thumb.rect[1]+2,thumb.rect[0]+2)
		pointer(true,point)
		game.move_pointer(Vector2i(210,110))
		pointer(false,Vector2i(210,110))
		check(n.objects[0].size()==1 and n.fact_open and not n.fact().is_empty(),"thumbnail drag places animal and shows original fact")
		var saved = n.objects[0][0].duplicate()
		check(wait_for(func(): return n.objects[0][0].blink==1),"placed animal blinks through normal updates")
		rect_click(n.tables.rectangles[13])
		check(n.time==1 and n.objects[1].is_empty() and n.objects[0].size()==1,"night preserves independent daytime collage")
		rect_click(n.tables.rectangles[13])
		check(n.time==0 and n.objects[0][0].x==saved.x,"day restores animal placement")
		rect_click(n.tables.rectangles[10])
		check(not n.dialog.is_empty(),"clear asks original confirmation")
		click(95,145)
		check(n.dialog.is_empty() and n.objects[0].size()==1,"No keeps the collage")
		rect_click(n.tables.rectangles[10])
		click(32,145)
		check(wait_for(func(): return not n.erase_task) and n.objects[0].is_empty(),"Yes erases animals through puff sequence")
		rect_click(n.tables.rectangles[11])
		check(n.mode=="quiz" and q.options,"guessing button opens game options")
		rect_click(n.tables.quiz_options[5])
		rect_click(n.tables.quiz_options[10])
		check(not q.options and q.phase=="ready" and q.help[0] and q.cards[0].size()==8 and q.cards[1].size()==8,"game starts with two unique candidate hands and Help")
		rect_click(n.tables.quiz_rectangles[5])
		check(not q.explanation.is_empty(),"definitions work before first roll")
		rect_click(n.tables.quiz_rectangles[38])
		check(q.explanation.is_empty(),"information panel dismisses definition")
		rect_click(n.tables.quiz_rectangles[36])
		check(wait_for(func(): return q.phase=="question" and quiz_idle()) and q.player==0 and q.available.size()==3,"roll deals three questions to child")
		var attribute = q.available[0]
		rect_click(n.tables.quiz_rectangles[12+attribute])
		check(wait_for(func(): return q.phase=="answered" and quiz_idle()) and q.asked[0]&(1<<attribute) and not q.answer.is_empty(),"asking plays original actor and records answer")
		check(q.remaining[0]&(1<<q.secret[0]),"Help preserves the secret candidate")
		rect_click(n.tables.quiz_rectangles[36])
		check(wait_for(func(): return q.player==1 and q.phase=="answered" and quiz_idle()),"robot asks and eliminates candidates autonomously")
		rect_click(n.tables.quiz_rectangles[36])
		check(wait_for(func(): return q.player==0 and q.phase=="question" and quiz_idle()),"roll returns turn to child")
		rect_click(n.tables.quiz_rectangles[37])
		check(wait_for(func(): return q.guessing and quiz_idle()),"guess button plays approach animation")
		rect_click(n.tables.quiz_rectangles[20+q.secret[0]])
		check(wait_for(func(): return q.phase=="won" and q.win_stage=="done" and quiz_idle()) and q.winner==0,"correct guess completes reveal and victory")
		rect_click(n.tables.reveal_rectangles[1])
		check(wait_for(func(): return quiz_idle() and q.revealed==3),"other hidden animal can be revealed")
		rect_click(n.tables.quiz_rectangles[36])
		check(wait_for(func(): return game.rewards.active),"victory die opens original prize chooser")
		var prize = game.rewards.choices[0]
		rect_click(game.rewards.rects[0])
		check(wait_for(func(): return not game.rewards.active) and game.resident.find(prize)!=null and q.phase=="ready","chosen prize is delivered and next game starts")
		rect_click(n.tables.quiz_rectangles[9])
		check(n.mode=="explore","quiz return restores nature browser")
		n.add_animal(36)
		# Isolated file path avoids changing the player's persistent nature scene.
		n.storage_enabled = true
		n.save_path = "user://nature-control-check.json"
		n.save()
		var restored = game.Nature.new(game,false)
		restored.save_path = n.save_path
		restored.restore()
		check(restored.saved_state()==n.saved_state(),"nature preferences and collages reload")
		check(restored.objects[0][0].due==120 and restored.objects[0][0].blink==0,"reloaded animal animation uses new session clock")
		DirAccess.remove_absolute(ProjectSettings.globalize_path(n.save_path))
		n.storage_enabled = false
		restored.dispose()
		click(311,10)
		check(wait_for(func(): return game.scene=="inside" and game.travel.is_empty()) and game.resident.find(prize)!=null,"return keeps earned prize in room")
		game.queue_free()
		await process_frame
	var passed = checks.all(func(item): return item.passed)
	var file = FileAccess.open(OS.get_cmdline_user_args()[0],FileAccess.WRITE)
	file.store_string(JSON.stringify({"passed":passed,"checks":checks,"scope":"Fresh mouse/boy and touch/girl production controls, through collage, questions, automatic robot turn, victory, original prize delivery, new game, persistence and room return. Answers are read to select inputs; progress is not injected."},"  "))
	file.close()
	print(JSON.stringify({"passed":passed,"checks":checks.size()}))
	quit(0 if passed else 1)
