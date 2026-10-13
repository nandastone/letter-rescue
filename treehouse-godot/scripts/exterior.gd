extends RefCounted
## Original yard/hollow hotspots, SCR sequences and discrete nut flight.
var host
var store
var actor = null
var pond = null
var outside_cycle: int = 0
var nuts: Array = []
var sign_waiting: bool = false
var sign_due: int = 0
var flight: Array = []
var flight_index: int = 0
var flight_due: int = 0
var landing: Vector2i
var window = null
var window_queue: Array = []
var window_due: int = 0
var window_variant: int = 7
var window_after: Callable
var busy: bool:
	get: return actor!=null or window!=null or not flight.is_empty() or sign_waiting
var yard_hotspots = [[2,45,52,122],[64,232,184,290],[78,132,106,164],[128,202,160,230],[177,14,200,92],[6,5,35,38],[33,217,64,258],[105,80,184,128],[109,128,188,174]]
var hollow_hotspots = [[81,138,109,184],[95,102,126,148],[131,206,164,263],[26,154,73,224],[18,82,198,271]]

func _init(game) -> void:
	host = game
	store = host.store

func hit_index(areas: Array, point: Vector2i) -> int:
	for i in areas.size():
		var r = areas[i]
		if point.x>=r[1] and point.x<r[3] and point.y>=r[0] and point.y<r[2]:
			return i
	return -1

func enter_yard() -> void:
	outside_cycle = 0
	pond = null
	window_due = host.tick+10800

func enter_hollow() -> void:
	nuts.clear()
	sign_waiting = false

func play(id: int, palette: int, initial_sound: int = 0) -> void:
	actor = host.animation("th",id,palette,false)
	actor.sound_due = host.tick+initial_sound
	actor.callback_requested.connect(func(slot,arg):
		if slot==0:
			host.resident.callback(arg))
	if id>=1000 and id<=1002:
		pond = actor
	actor.update(host.tick)

func click_yard(point: Vector2i) -> void:
	if busy or host.resident.busy:
		return
	var index = hit_index(yard_hotspots,point)
	if not host.resident.selected:
		if index==7:
			host.enter("boy")
		elif index==8:
			host.enter("girl")
		return
	match index:
		0:
			host.room.cloud = (host.room.cloud+1)%7
			host.play_sound(1044)
		1:
			host.set_scene("inside")
		2:
			play(1060,1060)
		3:
			host.set_scene("hollow")
		4:
			play(1000+outside_cycle,1000)
			outside_cycle = (outside_cycle+1)%3
		5:
			play(1301,1300)
		6:
			call_window()

func click_hollow(point: Vector2i) -> void:
	if busy:
		if sign_waiting:
			sign_waiting = false
			host.stop_all_sound()
		return
	var index = hit_index(hollow_hotspots,point)
	if index<0:
		host.set_scene("outside")
	elif index<2:
		play(1401 if index==0 else 1400,1400,host.play_sound(1019))
	elif index==2 and nuts.size()<3:
		toss()
	elif index==3:
		sign_waiting = true
		sign_due = host.tick+maxi(1,host.play_sound(20001))

func toss() -> void:
	landing = [Vector2i(220,99),Vector2i(195,77),Vector2i(219,78)][nuts.size()]
	host.play_sound(10035)
	# Resident flight loop: step along an integer error accumulator; display
	# each twelfth step and the endpoint for eight ticks each.
	var point = Vector2i(234,140)
	var delta = (landing-point).abs()
	var direction = (landing-point).sign()
	var error = int(delta.x/2) if delta.x else -1
	var n = 0
	flight.clear()
	while true:
		var ending = point==landing
		if ending or n%12==0:
			flight.append(point)
		if ending:
			break
		if error>=0:
			point.x += direction.x
			error -= delta.y
		else:
			point.y += direction.y
			error += delta.x
		n += 1
	flight_index = 0
	flight_due = host.tick+8

func call_window() -> void:
	var resident = host.resident
	if resident.pose==4:
		var tasks = resident.tasks
		var operations: Array = []
		for i in 2:
			operations.append(tasks.op(func(): tasks.prepend([tasks.pause(maxi(1,host.play_sound(10123)))])))
			operations.append(tasks.pause(30))
		operations.append(tasks.op(func(): host.audio.stop()))
		tasks.start(operations,true)
		return
	var pillow = resident.find(8)
	window_variant = 7
	if resident.fatigue>=4:
		window_variant = (3 if resident.fatigue==4 else 4) if pillow!=null and pillow.inside else 2
		resident.fatigue_due = host.tick+3600
	elif resident.hunger>=4:
		window_variant = 5 if resident.hunger==4 else 6
		resident.hunger_due = host.tick+3600
	play_window(window_variant)

func play_window(variant: int, complete: Callable = Callable()) -> void:
	window_variant = variant
	window_after = complete
	window_queue = [20400,20400+variant,20401]
	next_window()

func next_window() -> void:
	if window_queue.is_empty():
		window = null
		window_due = host.tick+10800
		var complete = window_after
		window_after = Callable()
		if complete.is_valid():
			complete.call()
		host.resident.schedule_ambient()
		return
	var id = int(window_queue.pop_front())
	window = host.ScrAnimation.new(store,host.character,id,20400,host.tick)
	window.sound_due = host.tick
	if id not in [20400,20401]:
		var reference = weakref(window)
		window.sound_requested.connect(func(sound):
			var active = reference.get_ref()
			if active!=null:
				active.sound_due = host.tick+host.play_sound(sound))
	window.update(host.tick)

func interrupt_audio() -> bool:
	for active in [actor,window]:
		if active!=null and active.done and host.tick<active.sound_due:
			host.audio.stop()
			active.sound_due = host.tick
			update(host.tick)
			return true
	return false

func update(tick: int) -> void:
	if actor!=null:
		actor.update(tick)
		if actor.done and tick>=actor.sound_due:
			host.audio.stop()
			actor = null
			if host.scene!="hollow":
				host.resident.schedule_ambient()
	if window!=null:
		window.update(tick)
		if window.done and tick>=window.sound_due:
			host.audio.stop()
			next_window()
	if sign_waiting and tick>=sign_due:
		sign_waiting = false
		host.stop_all_sound()
	if not flight.is_empty() and tick>=flight_due:
		flight_index += 1
		if flight_index==flight.size():
			flight.clear()
			host.play_sound(10033)
			nuts.append(landing)
		else:
			flight_due = tick+8

func draw_yard(surface) -> void:
	var shape = store.shape("th",171+host.room.cloud)
	surface.draw(store,"th",171+host.room.cloud,170,83-int(shape[0]/2),27-int(shape[1]/2))
	host.resident.draw_objects(surface,false)
	if pond!=null and pond!=actor:
		pond.draw(surface)
	if window!=null:
		window.draw(surface)
	if actor!=null:
		actor.draw(surface)
	host.resident.draw_objects(surface,false,true)

func draw_hollow(surface) -> void:
	surface.draw(store,"th",1448,1400,0,0,2)
	for point in nuts:
		surface.draw(store,"th",1447,1400,point.x-4,point.y-4)
	if actor!=null:
		actor.draw(surface)
	if not flight.is_empty():
		var point = flight[flight_index]
		surface.draw(store,"th",937,930,point.x,point.y)
	surface.draw(store,"th",8,6,304,1)
