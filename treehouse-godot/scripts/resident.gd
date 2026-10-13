extends RefCounted
## Character actions, held objects and persistent object ownership.
const ObjectTasks = preload("res://scripts/object_tasks.gd")
var host
var store
var tables: Dictionary
var pose: int = 0
var hunger: int
var fatigue: int
var hunger_due: int = 7200
var fatigue_due: int = 14400
var ambient_due: int = 0
var long_due: int = 0
var tick: int = 0
var selected: bool = false
var ambient_enabled: bool = true
var objects: Array = []
var active = null
var queue: Array = []
var preparation: Dictionary = {}
var after: Callable
var wake_time: Dictionary = {}
var tasks
var drag: Dictionary = {}
var motion: Dictionary = {}
var object_animation = null
var animation_object = null
var animation_resets: bool = true
var animation_after: Callable
var consuming = null
var sex: int:
	get: return int(host.character=="girl")
var busy: bool:
	get: return active!=null or object_animation!=null or not preparation.is_empty() or not queue.is_empty() or tasks.running or not motion.is_empty() or drag.get("released",false)

func _init(game, initial_objects: bool = true) -> void:
	host = game
	store = game.store
	tables = store.data.room
	tasks = ObjectTasks.new(self)
	hunger = 1+host.random.pick(2)
	fatigue = 1+host.random.pick(2)
	if initial_objects:
		for type in [9,20,8,10,6]:
			create(type)

func rect() -> Array:
	var result = tables.poses[pose].duplicate()
	if sex==0:
		result[0] += 5 if pose==3 else 4 if pose<3 else 0
	return result

func find(type: int):
	for object in objects:
		if object.type==type:
			return object
	return null

func hit(r: Array, point: Vector2i) -> bool:
	return point.x>=r[1] and point.x<r[3] and point.y>=r[0] and point.y<r[2]

func bounds(object: Dictionary) -> Array:
	var b = host.balloon
	return [b.y,b.x,b.y+38,b.x+29] if object.type==6 else object.rect

func set_bounds(object: Dictionary, r: Array) -> void:
	object.rect = r.duplicate()
	if object.type==6:
		host.balloon.x = r[1]
		host.balloon.y = r[0]

func create(type: int, inside: bool = true) -> Dictionary:
	var object = find(type)
	if object==null:
		assert(objects.size()<21,"Original room object capacity exceeded")
		object = {"type":type,"state":1,"inside":inside,"rect":[],"due":0}
		objects.append(object)
	object.state = 1
	object.hidden = false
	object.front = false
	object.nest_mirror = false
	object.erase("food_frame")
	object.inside = inside
	object.rect = tables.objects[type].inside.duplicate() if inside else tables.objects[type].outside.duplicate()
	if type==6:
		host.balloon.hidden = false
		host.balloon.state = 1
	reset_object_timer(object)
	return object

func reset_object_timer(object: Dictionary) -> void:
	var type = int(object.type)
	object.due = tick
	if type==6:
		object.due += 48
		host.balloon.due = object.due
	elif type==11:
		object.due = tick+(6+host.random.pick(10))*60
	elif type==16:
		object.due = tick+(120+host.random.pick(60))*60
	if type!=6:
		schedule_ambient()

func remove(object: Dictionary) -> void:
	objects.erase(object)
	if object.type==6:
		host.balloon.hidden = true

func schedule_ambient() -> void:
	ambient_due = tick+(20+host.random.pick(10))*60

func enter_scene() -> void:
	tick = host.tick
	selected = true
	schedule_ambient()
	long_due = tick+(120+host.random.pick(60))*60
	var nut = find(11)
	if host.scene=="inside" and nut!=null:
		nut.due = tick+(6+host.random.pick(10))*60
		schedule_ambient()
	schedule_ambient()
	for object in objects:
		if object.inside==(host.scene=="inside"):
			if object.type==11:
				object.due = tick+(6+host.random.pick(10))*60
			elif object.type==16:
				object.due = tick+(120+host.random.pick(60))*60
			if object.type!=6:
				schedule_ambient()

func action(id: int, complete: Callable = Callable()) -> void:
	tick = host.tick
	queue.append({"action":id,"after":complete})
	start_next()

func start_next() -> void:
	if active!=null or not preparation.is_empty() or queue.is_empty():
		return
	var entry = queue.pop_front()
	var exempt = bool(tables.exempt[entry.action])
	var variant = 0 if exempt else 200 if pose==1 else 100 if pose==2 else 0
	var id = 20500+int(entry.action)+variant
	var script = store.data.scripts[store.key(host.character,id)]
	var bounds = script.bounds.duplicate()
	var origin = Vector2i(int(bounds[1]),int(bounds[0]))
	if exempt and pose in [1,2]:
		var dx = 59 if pose==1 else -132
		var dy = -3 if pose==1 else 4
		origin += Vector2i(dx,dy)
		bounds = [bounds[0]+dy,bounds[1]+dx,bounds[2]+dy,bounds[3]+dx]
	preparation = {"entry":entry,"id":id,"origin":origin,"bounds":bounds,"due":tick}
	step_preparation()

func step_preparation() -> void:
	if preparation.is_empty() or tick<preparation.due:
		return
	var b = host.balloon
	var r = preparation.bounds
	if host.scene=="inside" and not b.hidden and b.x<r[3] and b.x+29>r[1] and b.y<r[2]+2 and b.y+38>r[0]-2:
		b.y -= 2
		preparation.due = tick+2
		return
	var pending = preparation
	preparation = {}
	active = host.animation(host.character,pending.id,20500,false)
	active.origin = pending.origin
	active.callback_requested.connect(func(slot,arg):
		if slot==0:
			callback(arg))
	after = pending.entry.after
	apply_pose(pending.entry.action)
	active.update(tick)

func apply_pose(action_id: int) -> void:
	if action_id in [6,7,8,9,14,28] and action_id-sex!=6:
		pose = 1
	elif action_id==16:
		pose = 2
	elif action_id in [18,20]:
		pose = 4
	elif action_id==19:
		pose = 3
	elif action_id in [21,22,29,30]:
		pose = 0

func callback(argument: int) -> void:
	if argument<=3:
		var object = create(17+argument)
		var r = object.rect
		var left = 94 if argument==sex else 245
		object.rect = [146-(r[2]-r[0]),left,146,left+r[3]-r[1]]
		if argument!=sex:
			object.rect[0] -= 4
			object.rect[2] -= 4
	elif argument==4:
		create(8)
	elif argument==5:
		create(8,false).rect = [182,122,196,134]
	elif argument==6 and not objects.is_empty():
		remove(objects.back())
	elif argument==7 and not objects.is_empty():
		objects.back().state -= 1
		if objects.back().state<=0:
			remove(objects.back())
	elif argument==8:
		var object = create(5)
		var dx = 59 if pose==1 else -132 if pose==2 else 0
		var dy = -3 if pose==1 else 4 if pose==2 else 0
		object.rect = [142+dy,162+dx,153+dy,185+dx]
		object.front = true
	elif argument==9:
		var bird = find(15)
		if bird!=null:
			bird.state += 1

func finish_action() -> void:
	var complete = after
	after = Callable()
	active = null
	schedule_ambient()
	if complete.is_valid():
		complete.call()
	start_next()

func click_character() -> void:
	if busy:
		return
	if pose==4:
		action(20)
	elif fatigue>=4:
		action(16)
	elif hunger>=4:
		if pose==2:
			action(29)
		action(14)
	else:
		action(23)

func center() -> void:
	if pose==1:
		action(30)
	elif pose==2:
		action(29)

func speak_status() -> void:
	if pose==4:
		host.room.say_time(wake_time,true)
		return
	var sound = 11053 if hunger>=4 else 11054 if fatigue>=4 else 0
	if sound:
		host.room.say([11050,[5],sound])
	else:
		var choice = host.random.pick(3)
		if choice<2:
			host.room.say([11050,[5],11051+choice])
		elif choice==2:
			host.room.say([11055+host.random.pick(1)])
		else:
			var speech: Array = []
			for i in 3:
				speech.append_array([{"sound":11057+host.random.pick(4),"mouth":false},[30]])
			speech.append(11062)
			host.room.say(speech)
	schedule_ambient()

func interrupt_audio() -> bool:
	if object_animation!=null and object_animation.done and tick<object_animation.sound_due:
		host.audio.stop()
		object_animation.sound_due = tick
		update(tick)
		return true
	if active!=null and active.done and tick<active.sound_due:
		host.audio.stop()
		active.sound_due = tick
		update(tick)
		return true
	return false

func update(value: int) -> void:
	tick = value
	if drag.get("click_only",false) and (tick>=drag.due if drag.get("released",false) else tick-drag.since>=15):
		dispatch_press(drag)
	tasks.update(tick)
	step_preparation()
	if object_animation!=null:
		object_animation.update(tick)
		if object_animation.done and (object_animation.id==1300 or tick>=object_animation.sound_due):
			host.audio.stop()
			if object_animation.id==1300 and animation_object!=null:
				remove(animation_object)
			object_animation = null
			animation_object = null
			if animation_resets:
				schedule_ambient()
			var complete = animation_after
			animation_after = Callable()
			if complete.is_valid():
				complete.call()
	if active!=null and not tasks.running:
		active.update(tick)
		if active.done and tick>=active.sound_due:
			host.audio.stop()
			finish_action()
	if not motion.is_empty() and tick>=motion.due:
		motion.object.state = [2,3,4,1][motion.index]
		motion.index += 1
		motion.due = tick+8
		if motion.index==4:
			motion = {}
	if busy or not drag.is_empty() or host.exterior.busy or host.room.busy or not host.room.speech.is_empty() or tick<host.room.speech_due:
		return
	if host.scene=="inside":
		host.service_balloon()
		# A finishing activity can release the room and start another this tick.
		# Service its due window update at that idle boundary as well.
		host.room.update_cloud()
	if pose==4 and not wake_time.is_empty() and Time.get_unix_time_from_datetime_dict(host.now())>=Time.get_unix_time_from_datetime_dict(wake_time):
		tasks.start([tasks.pause(maxi(1,host.play_sound(11028))),tasks.op(func(): wake())],true)
		return
	if not selected or host.scene not in ["inside","outside"]:
		return
	if host.scene=="outside":
		if pose!=4:
			update_needs()
		if not busy and not host.exterior.busy:
			service_environment()
		return
	var nut = find(11)
	if nut!=null and nut.inside and nut.due and tick>nut.due and nut.rect[0]>=178 and nut.rect[1]>=226 and nut.rect[2]<=187 and nut.rect[3]<=250:
		play_object(1403,1400,nut)
		return
	if service_environment():
		return
	if pose!=4:
		update_needs()

func service_environment() -> bool:
	if not ambient_enabled or host.chalk.tool>=0 or host.entering:
		return false
	if tick>ambient_due:
		ambient()
		return true
	var food = find(16)
	if food!=null and tick>food.due:
		if host.scene=="inside":
			tasks.start(tasks.consume_food(food))
		else:
			play_object(1300,1300,food,false)
		return true
	if tick>long_due:
		var pile = find(14)
		if pile!=null:
			consume_pile(pile)
			return true
		schedule_long()
	return false

func ambient() -> void:
	var choice = host.random.pick(7)
	if host.scene=="inside":
		if host.room.is_open:
			choice = 7
		if choice<2:
			var worm = find(12)
			var bird = find(15)
			if worm!=null:
				tasks.start(tasks.worm(worm))
			elif bird!=null:
				click_object(bird)
			else:
				tasks.start(tasks.flyby(),true)
		elif choice<4:
			host.room.interact("chirp")
		elif choice<6:
			host.room.interact("nest")
		elif choice==6:
			host.room.interact("spider")
		elif pose!=4:
			speak_status()
	elif choice<4:
		host.exterior.play(1000+host.exterior.outside_cycle,1000)
		host.exterior.outside_cycle = (host.exterior.outside_cycle+1)%3
	elif choice<6:
		var worm = find(13)
		tasks.start(tasks.take_worm(worm) if worm!=null else tasks.flyby(),true)
	elif choice==6:
		host.exterior.play(1060,1060)

func update_needs() -> void:
	var names = ["fatigue","hunger"] if host.scene=="outside" else ["hunger","fatigue"]
	for name in names:
		if tick<int(get(name+"_due")):
			continue
		var value = int(get(name))
		var other = "fatigue" if name=="hunger" else "hunger"
		var suppressed = value>=4 and int(get(other))==5
		var warn = value==3 or (value>=4 and not suppressed)
		set(name+"_due",tick+(7200 if name=="hunger" else 14400))
		var complete = func():
			if warn and int(get(other))>=3 and host.ScrAnimation.wrap32((int(get(other+"_due"))-tick)<<16)>>16<600:
				set(other+"_due",tick+600)
			if value>=4:
				set(name+"_due",tick+3600)
			if not suppressed:
				set(name,mini(5,int(get(name))+1))
		if not warn:
			complete.call()
		elif host.scene=="outside":
			var pillow = find(8)
			var variant = (5 if value==3 else 6) if name=="hunger" else (3 if value==3 else 4) if pillow!=null and pillow.inside else 2
			host.exterior.play_window(variant,complete)
		else:
			if value>=4 and name=="hunger" and pose==2:
				action(29)
			action((13 if name=="hunger" else 15) if value==3 else (14 if name=="hunger" else 16),complete)
		break
	if host.scene=="outside" and not busy and not host.exterior.busy and hunger<4 and fatigue<4 and tick>=host.exterior.window_due:
		host.exterior.play_window(7)

func draw(surface) -> void:
	if active!=null:
		active.draw(surface)
	else:
		var r = rect()
		surface.draw(store,host.character,20500+[1,1,1,4,15][pose],20500,int(r[1]),int(r[0]))

func draw_objects(surface, inside: bool, front: bool = false, clip: Array = [], min_bottom: int = -999) -> void:
	for object in objects:
		var type = int(object.type)
		var dragging = not drag.is_empty() and drag.object==object
		var above = bool(object.get("front",false)) or (dragging and drag.moved)
		if object.inside!=inside or bool(object.get("hidden",false)) or above!=front or (type==6 and host.balloon.hidden):
			continue
		if dragging and drag.get("newly_created",false) and tick-drag.since<15:
			continue
		if bounds(object)[2]<=min_bottom:
			continue
		if type==16:
			var frame = int(object.get("food_frame",7))
			if frame:
				surface.draw(store,"th",int(store.palette("th",1300).first)+frame-1,1300,int(object.rect[1]),int(object.rect[0]),10,clip)
			continue
		var data = tables.objects[type]
		var state = int(host.balloon.state if type==6 else object.state)
		var relative = int(data.states[state%10])
		if relative==0:
			continue
		var r = bounds(object)
		var image = store.image("th",int(store.palette("th",data.palette).first)+relative-1,int(data.palette),true)
		if object.get("nest_mirror",false) or (type==0 and state>=2 and state<=4 and r[1]<160):
			image = image.duplicate()
			image.flip_x()
		var visible = clip
		if type==10:
			visible = r if clip.is_empty() else [maxi(r[0],clip[0]),maxi(r[1],clip[1]),mini(r[2],clip[2]),mini(r[3],clip[3])]
		surface.blit(image,int(r[1]),int(r[0]),true,visible)

func begin(point: Vector2i) -> bool:
	if busy:
		return false
	for i in range(objects.size()-1,-1,-1):
		var object = objects[i]
		if object.inside!=(host.scene=="inside") or (object.type==6 and host.balloon.hidden) or not hit(bounds(object),point):
			continue
		objects.remove_at(i)
		objects.append(object)
		drag = {"object":object,"rect":bounds(object).duplicate(),"start":point,"point":point,"since":tick,"moved":false,
			"click_only":object.type in [0,9,10,14,15,16] or (host.scene!="inside" and object.type==1) or (object.type==7 and object.state==5)}
		return true
	return false

func fruit(type: int, point: Vector2i) -> void:
	var object = create(type)
	drag = {"object":object,"rect":object.rect.duplicate(),"start":point,"point":point,"since":tick,"moved":false}

func move(point: Vector2i) -> bool:
	if drag.is_empty():
		return false
	if drag.get("released",false):
		return true
	drag.point = point
	if drag.get("click_only",false) or tick-drag.since<15:
		return true
	var delta = point-drag.start
	drag.moved = drag.moved or absi(delta.x)>=2 or absi(delta.y)>=2
	if drag.moved:
		var r = drag.rect
		set_bounds(drag.object,[r[0]+delta.y,r[1]+delta.x,r[2]+delta.y,r[3]+delta.x])
	return true

func end(cancel: bool = false) -> void:
	if drag.is_empty():
		return
	var d = drag
	drag = {}
	if cancel:
		set_bounds(d.object,d.rect)
		return
	if not d.moved and (d.get("click_only",false) or tick-d.since<30):
		if d.get("click_only",false):
			d.released = true
			d.due = tick+1
			drag = d
		else:
			click_object(d.object)
		return
	tasks.start(tasks.release_drag(d))

func dispatch_press(d: Dictionary) -> void:
	drag = {}
	click_object(d.object,d.start)
	if d.get("released",false) and drag.get("newly_created",false):
		end()

func click_object(object: Dictionary, point = null) -> void:
	if busy:
		return
	match int(object.type):
		0,1,5: tasks.start(tasks.departure(object))
		6:
			host.play_sound(10011)
			object.state = int(object.state)+1
			host.balloon.state = object.state
			if object.state>=4:
				remove(object)
		7:
			if object.state!=5:
				object.state = int(object.state)%4+1
			host.play_sound(1007)
		2:
			host.play_sound(10028)
			motion = {"object":object,"index":0,"due":tick}
		9: tasks.start(tasks.nuts(object))
		10: tasks.start(tasks.basket(object,point))
		12,13: tasks.start(tasks.worm(object))
		15:
			host.play_sound(12025)
			tasks.start(tasks.perched_departure())
		14: consume_pile(object)
		16:
			if host.scene=="inside":
				tasks.start(tasks.consume_food(object))
			else:
				play_object(1300,1300,object,false)

func schedule_long() -> void:
	long_due = tick+(120+host.random.pick(60))*60
	var nut = find(11)
	if host.scene=="inside" and nut!=null:
		nut.due = tick+(6+host.random.pick(10))*60
		schedule_ambient()
	schedule_ambient()

func consume_pile(pile: Dictionary) -> void:
	if host.scene=="inside":
		pile.state -= 1
		if pile.state==0:
			remove(pile)
		host.play_sound(10037)
		schedule_long()
	else:
		play_object(1402,1400,pile,false,func(): schedule_long())

func play_object(id: int, palette: int, object = null, resets: bool = true, complete: Callable = Callable()) -> void:
	animation_object = object
	animation_resets = resets
	animation_after = complete
	if object!=null:
		objects.erase(object)
		objects.append(object)
	object_animation = host.animation("th",id,palette,false)
	object_animation.callback_requested.connect(func(slot,arg):
		if id==1300:
			if object!=null:
				object.food_frame = 6-arg if arg<4 else 0
		elif slot==0:
			callback(arg))
	object_animation.update(tick)

func interrupt_food() -> bool:
	if consuming==null:
		return false
	tasks.due = tick
	tasks.update(tick)
	return true

func need(name: String, value: int) -> void:
	set(name,clampi(value,1,5))
	set(name+"_due",tick+(7200 if name=="hunger" else 14400))

func offer(object: Dictionary) -> bool:
	if pose==4:
		return false
	var type = int(object.type)
	if type>=17:
		remove(object)
		if hunger>1:
			action(type-16,func():
				need("hunger",hunger-2)
				need("fatigue",fatigue+1))
		else:
			action(type-11)
	elif type==8:
		remove(object)
		if fatigue>=4:
			sleep()
		else:
			action(17)
	elif type==2:
		var released = bounds(object).duplicate()
		remove(object)
		action(24,func():
			var returned = create(2)
			set_bounds(returned,released)
			tasks.start(tasks.place(returned)))
	elif type in [3,4]:
		remove(object)
		action(26 if type==3 else 27,func():
			need("hunger",1)
			need("fatigue",fatigue+1))
	elif type==5:
		remove(object)
		action(25,func():
			var returned = find(5)
			if returned!=null:
				tasks.start(tasks.departure(returned)))
	elif type==11:
		remove(object)
		if hunger==5:
			action(5,func():
				need("hunger",4)
				need("fatigue",fatigue+1))
		else:
			action(10,func():
				var pile = find(14)
				if pile!=null:
					pile.state = mini(4,int(pile.state)+1)
				else:
					create(14,false))
	elif type==12:
		var bird = find(15)!=null
		remove(object)
		action(12 if bird else 11,func():
			if bird:
				tasks.start(tasks.feed_nest(Vector2i(218,95),true),true)
			else:
				create(13,false))
	else:
		return false
	return true

func sleep() -> void:
	var current = host.now()
	var seconds = int(Time.get_unix_time_from_datetime_dict(current))
	seconds += (120 if current.second<=30 else 180)-int(current.second)
	wake_time = Time.get_datetime_dict_from_unix_time(seconds)
	action(18,func():
		host.room.say_time(wake_time,true)
		need("fatigue",1))

func wake(interrupted: bool = false, complete: Callable = Callable()) -> void:
	if pose!=4:
		if complete.is_valid():
			complete.call()
		return
	var finish = func():
		pose = 0
		wake_time = {}
		need("fatigue",4 if interrupted else 1)
		if complete.is_valid():
			complete.call()
	if host.scene!="inside":
		create(8)
		finish.call()
	else:
		action(22 if interrupted else 21,finish)

func draw_nap(surface) -> void:
	if wake_time.is_empty():
		return
	var hour = int(wake_time.hour)%12
	if hour==0:
		hour = 12
	var minute = int(wake_time.minute)
	var shift = 0 if hour>9 else 3
	var items = [[1212,4,142],[1202+hour%10,16-shift,142],[1213,22-shift,142],[1202+int(minute/10),24-shift,142],[1202+minute%10,29-shift,143]]
	if hour>9:
		items.append([1203,11,143])
	for item in items:
		surface.draw(store,"th",item[0],1200,item[1],item[2])

func dispose() -> void:
	# Pending Callables can retain this RefCounted through suspended operations.
	tasks.steps.clear()
	tasks.running = false
	tasks.sprite = {}
	queue.clear()
	preparation.clear()
	active = null
	object_animation = null
	after = Callable()
	animation_after = Callable()
