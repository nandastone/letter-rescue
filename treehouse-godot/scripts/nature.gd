extends RefCounted
## Overlay 2 animal classification, facts and independent day/night collages.
const Integers = preload("res://scripts/music_maze.gd")
const Renderer = preload("res://scripts/nature_renderer.gd")
const Quiz = preload("res://scripts/nature_quiz.gd")
var host
var store
var tables: Dictionary
var renderer
var quiz
var time: int = 0
var attribute: int = 0
var values: Array = [0,0,0,0,0,0,0]
var category: int = 3
var selected: int = -1
var fact_index: int = 0
var fact_open: bool = false
var objects: Array = [[],[]]
var drag: Dictionary = {}
var tick: int = 0
var idle_until: int = 240
var undo: Dictionary = {}
var mode: String = "explore"
var erase_task: bool = false
var erase_due: int = 0
var erase_effect: Dictionary = {}
var dialog: Dictionary = {}
var print_view: Image
var storage_enabled: bool = true
var save_path: String = "user://nature.json"
var hide_cursor: bool:
	get:
		return mode=="quiz" and (quiz.actor_script!=null or (quiz.win_animation!=null and not quiz.win_animation.done))

func _init(game, persistent: bool = true) -> void:
	host = game
	store = game.store
	tables = Integers.integers(store.data.nature)
	renderer = Renderer.new(self)
	quiz = Quiz.new(self)
	storage_enabled = persistent
	if persistent:
		restore()

func strings(id: int) -> Array:
	return store.data.strings["modules:%d"%id]

func animal_name(id: int) -> String:
	return strings(5000)[id]

func value_names() -> Array:
	return strings(5200+attribute)

func class_names() -> Array:
	return strings(5208+time)

func matching() -> Array:
	return tables.animals.filter(func(a): return a.active_time==time and a.attributes[attribute]==values[attribute])

func available_classes() -> Array:
	var result: Array = []
	for animal in matching():
		if not animal.category in result:
			result.append(animal.category)
	return result

func animals() -> Array:
	return matching().filter(func(a): return a.category==category)

func facts() -> Array:
	return [] if selected<0 else strings(5100+selected)

func fact() -> String:
	var list = facts()
	return "" if list.is_empty() else list[fact_index%list.size()]

func interact() -> void:
	idle_until = tick+240

func random(count: int) -> int:
	return host.random.pick(count-1)

func speak(id: int, rate: int = 0, fractional: bool = false) -> float:
	var key = "digisnd:%d"%id
	if not store.data.pcm.has(key):
		key = "voices:%d"%id
	if not store.data.pcm.has(key):
		return 0
	if not rate:
		rate = int(store.data.pcm[key].rate)
	var duration = host.play_sample(key,rate)
	if not fractional:
		return duration
	var effective = int(1000000.0/int(1000000.0/rate))
	return Marshalls.base64_to_raw(store.data.pcm[key].pcm).size()/float(effective)*host.TICK_HZ

func select_attribute(index: int, cycle: bool = true) -> void:
	if erase_task:
		return
	speak(1008)
	interact()
	if attribute==index and cycle:
		values[index] = (values[index]+1)%strings(5200+index).size()
	attribute = index
	category = -1
	fact_open = false
	selected = -1
	save()

func select_value(index: int) -> void:
	if not erase_task:
		values[attribute] = index
		select_attribute(attribute,false)

func select_class(index: int) -> void:
	if erase_task or not index in available_classes():
		return
	speak(1008)
	interact()
	category = index
	fact_open = false
	selected = -1
	save()

func toggle_time() -> void:
	if erase_task:
		return
	speak(1042)
	interact()
	time = 1-time
	category = -1
	fact_open = false
	selected = -1
	drag = {}
	for object in objects[time]:
		schedule(object)
	save()

func select_animal(id: int) -> void:
	if erase_task:
		return
	speak(1008)
	interact()
	selected = id
	fact_index = random(maxi(1,facts().size()))
	fact_open = true

func next_fact() -> void:
	if not erase_task:
		fact_index += 1
		fact_open = true

func dismiss_fact() -> void:
	if not erase_task:
		speak(1008)
		fact_open = false

func schedule(object: Dictionary) -> void:
	object.due = tick+(30+random(120) if object.blink else 120+random(360))

func add_animal(id: int, x: int = 210, y: int = 115):
	if objects[time].size()>=40:
		return null
	var shape = store.shape("modules",tables.animals[id].large)
	var object = {"id":id,"x":maxi(131,mini(315-shape[0],x-int(shape[0]/2))),"y":maxi(5,mini(195-shape[1],y-int(shape[1]/2))),"blink":0,"due":0}
	schedule(object)
	objects[time].append(object)
	interact()
	save()
	return object

func request_clear(all_scenes: bool = false) -> void:
	if erase_task:
		return
	speak(1008)
	var count = objects[0].size()+objects[1].size() if all_scenes else objects[time].size()
	dialog = {"message":"Send daytime AND nighttime animals home?" if all_scenes else "Send all animals home?","all":all_scenes,"empty":count==0,"start":tick}
	if not count:
		dialog.message = "No animals to send home!"

func answer_dialog(yes: bool) -> void:
	var previous = dialog
	dialog = {}
	if not yes or previous.get("empty",false):
		return
	if previous.get("print",false):
		renderer.draw(host.surface)
		print_view = host.surface.image.duplicate()
		return
	undo = {"scenes":objects.duplicate(true)}
	if previous.all:
		objects = [[],[]]
		save()
	else:
		erase_task = true
		erase_due = tick
		step_erase()

func step_erase() -> void:
	if tick<erase_due:
		return
	if erase_effect.is_empty():
		if objects[time].is_empty():
			erase_task = false
			save()
			return
		var object = objects[time].pop_back()
		var shape = store.shape("modules",tables.animals[object.id].large)
		erase_effect = {"object":object,"id":923,"x":object.x+int(shape[0]/2),"y":object.y+int(shape[1]/2)}
	elif erase_effect.id==923:
		erase_effect.id = 924
		speak(10034)
	elif erase_effect.id==924:
		erase_effect.id = 925
	else:
		erase_effect = {}
		step_erase()
		return
	erase_due = tick+4

func undo_clear() -> void:
	if erase_task or undo.is_empty():
		return
	objects = undo.scenes
	undo = {}
	save()

func enter_quiz() -> void:
	if erase_task:
		return
	end_drag()
	mode = "quiz"
	quiz.options = true
	quiz.robot_due = null

func leave_quiz() -> void:
	if quiz.interrupt_wait():
		return
	quiz.stop_reminder()
	if quiz.busy or (quiz.win_animation!=null and not quiz.win_animation.done):
		return
	mode = "explore"
	quiz.robot_due = null
	save()

func update(now: int) -> void:
	tick = now
	if not dialog.is_empty() or print_view!=null:
		return
	if erase_task:
		step_erase()
		return
	if mode=="quiz":
		quiz.update(tick)
		return
	if tick<idle_until or not drag.is_empty():
		return
	for object in objects[time]:
		if tick>=object.due:
			object.blink = 1-object.blink
			schedule(object)

func hit(b: Array, point: Vector2i) -> bool:
	return point.x>=b[1] and point.x<b[3] and point.y>=b[0] and point.y<b[2]

func thumbnails() -> Array:
	var result: Array = []
	var x = 8
	var y = 107
	var row_height = 0
	for a in animals():
		var shape = store.shape("modules",a.small)
		if x+shape[0]>122:
			x = 8
			y += row_height
			row_height = 0
		result.append({"animal":a,"rect":[y,x,y+shape[1],x+shape[0]]})
		x += shape[0]+1
		row_height = maxi(row_height,shape[1])
	return result

func begin_drag(point: Vector2i) -> bool:
	if mode=="quiz" or erase_task or not dialog.is_empty() or print_view!=null:
		return false
	var list = objects[time]
	for i in range(list.size()-1,-1,-1):
		var object = list[i]
		var shape = store.shape("modules",tables.animals[object.id].large)
		if hit([object.y,object.x,object.y+shape[1],object.x+shape[0]],point):
			list.remove_at(i)
			list.append(object)
			interact()
			fact_open = false
			drag = {"object":object,"start":[point.x,point.y],"origin":[object.x,object.y],"fresh":false}
			return true
	for item in thumbnails():
		if hit(item.rect,point):
			select_animal(item.animal.id)
			var object = add_animal(item.animal.id,point.x,point.y)
			if object==null:
				return true
			var shape = store.shape("modules",item.animal.large)
			object.x = point.x-int(shape[0]/2)
			object.y = point.y-int(shape[1]/2)
			drag = {"object":object,"start":[point.x,point.y],"origin":[object.x,object.y],"fresh":true}
			return true
	return false

func move_drag(point: Vector2i) -> bool:
	if drag.is_empty():
		return false
	var shape = store.shape("modules",tables.animals[drag.object.id].large)
	drag.object.x = clampi(drag.origin[0]+point.x-drag.start[0],0,320-shape[0])
	drag.object.y = clampi(drag.origin[1]+point.y-drag.start[1],0,200-shape[1])
	return true

func end_drag() -> void:
	if drag.is_empty():
		return
	var object = drag.object
	var fresh = drag.fresh
	var shape = store.shape("modules",tables.animals[object.id].large)
	drag = {}
	if object.x+shape[0]<=131 or object.x>=315 or object.y+shape[1]<=5 or object.y>=195:
		objects[time].pop_back() # Grabbed objects are always raised to the last slot.
		if not fresh:
			speak(10034)
	else:
		object.x = maxi(131,mini(315-shape[0],object.x))
		object.y = maxi(5,mini(195-shape[1],object.y))
		if not fresh:
			schedule(object)
	interact()
	save()

func click(point: Vector2i, ctrl: bool = false) -> void:
	if print_view!=null:
		print_view = null
		return
	if not dialog.is_empty():
		answer_dialog(dialog.get("empty",false) or hit([126,16,166,50],point))
		return
	if erase_task:
		return
	if mode=="quiz":
		quiz.click(point)
		return
	interact()
	var r = tables.rectangles
	for i in 7:
		if hit(r[i+1],point):
			select_attribute(i)
			return
	if hit(r[12],point):
		select_attribute(attribute)
		return
	if fact_open and hit(r[26],point):
		dismiss_fact()
		return
	for i in 10:
		if hit(r[14+i],point):
			select_class(i)
			return
	if hit(r[13],point):
		toggle_time()
	elif hit(r[10],point):
		request_clear(ctrl)
	elif hit(r[9],point):
		if host.preferences.settings.printing:
			dialog = {"message":"Print this Scene?","print":true,"empty":false,"start":tick}
	elif hit(r[11],point):
		enter_quiz()

func saved_state() -> Dictionary:
	var scenes: Array = []
	for list in objects:
		scenes.append(list.map(func(o): return {"id":o.id,"x":o.x,"y":o.y}))
	return {"version":1,"time":time,"attribute":attribute,"values":values.duplicate(),"category":category,"objects":scenes,"opponent":quiz.opponent,"help":quiz.help.duplicate()}

func save() -> void:
	if not storage_enabled:
		return
	var file = FileAccess.open(save_path,FileAccess.WRITE)
	if file!=null:
		file.store_string(JSON.stringify(saved_state()))
		file.close()
		if host.persistence!=null:
			host.persistence.save()
	else:
		push_error("Could not save nature scene")

func valid_integer(value, low: int, high: int) -> bool:
	return (value is int or value is float) and value==int(value) and value>=low and value<=high

func restore() -> void:
	if not FileAccess.file_exists(save_path):
		return
	var value = JSON.parse_string(FileAccess.get_file_as_string(save_path))
	if not value is Dictionary or value.get("version")!=1 or not valid_integer(value.get("time"),0,1) or not valid_integer(value.get("attribute"),0,6) or not valid_integer(value.get("category"),-1,9) or not valid_integer(value.get("opponent"),1,2):
		return
	if not value.get("values") is Array or value.values.size()!=7 or not value.get("objects") is Array or value.objects.size()!=2 or not value.get("help") is Array or value.help.size()!=3:
		return
	for i in 7:
		if not valid_integer(value.values[i],0,strings(5200+i).size()-1):
			return
	for item in value.help:
		if not item is bool:
			return
	for scene_time in 2:
		var list = value.objects[scene_time]
		if not list is Array or list.size()>40:
			return
		for object in list:
			if not object is Dictionary or not valid_integer(object.get("id"),0,91) or not valid_integer(object.get("x"),131,314) or not valid_integer(object.get("y"),5,194):
				return
			var animal = tables.animals[int(object.id)]
			var shape = store.shape("modules",animal.large)
			if animal.active_time!=scene_time or object.x+shape[0]>315 or object.y+shape[1]>195:
				return
	for key in ["time","attribute","values","category","objects"]:
		set(key,Integers.integers(value[key]))
	quiz.opponent = int(value.opponent)
	quiz.help = value.help
	# Animation deadlines belong to the new session clock, as in STATUS.DAT.
	for list in objects:
		for object in list:
			object.blink = 0
			object.due = tick+120

func draw(surface) -> void:
	if print_view!=null:
		surface.blit(print_view,0,0,false)
		return
	if mode=="quiz":
		quiz.draw(surface)
	else:
		renderer.draw(surface)
	if not dialog.is_empty():
		renderer.draw_dialog(surface)

func dispose() -> void:
	quiz.dispose()
	drag = {}
	dialog = {}
	renderer = null
