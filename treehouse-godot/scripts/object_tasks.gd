extends RefCounted
## Semantic object operations suspended on game ticks, never wall-clock timers.
var owner: WeakRef
var resident:
	get: return owner.get_ref()
var host:
	get: return resident.host
var steps: Array = []
var due: int = 0
var running: bool = false
var reset_ambient: bool = false
var sprite: Dictionary = {}
var clearing_balloon: bool = false

func _init(actor) -> void:
	owner = weakref(actor)

func op(action: Callable, delay: int = 0) -> Dictionary:
	return {"call":action,"delay":delay}

func pause(delay: int) -> Dictionary:
	return op(Callable(),delay)

func prepend(operations: Array) -> void:
	steps = operations+steps

func start(operations: Array, resets: bool = false) -> void:
	steps = operations
	reset_ambient = resets
	due = host.tick
	running = true
	update(host.tick)

func update(tick: int) -> void:
	if not running or tick<due:
		return
	for budget in 4096:
		if steps.is_empty():
			running = false
			sprite = {}
			if reset_ambient:
				resident.schedule_ambient()
			return
		var entry = steps.front()
		if entry.has("until") and not entry.until.call():
			due = tick+int(entry.delay)
			return
		steps.pop_front()
		if entry.has("call") and entry.call.is_valid():
			entry.call.call()
		if int(entry.delay)>0 and not entry.has("until"):
			due = tick+int(entry.delay)
			return
	assert(false,"Object operations failed to yield")

func clear_balloon(bounds: Array) -> Array:
	return [op(func(): clearing_balloon=true),{"delay":2,"until":func():
		var b = host.balloon
		if host.scene!="inside" or b.hidden or not (b.x<bounds[3] and b.x+29>bounds[1] and b.y<bounds[2]+2 and b.y+38>bounds[0]-2):
			return true
		b.y -= 2
		var object = resident.find(6)
		if object!=null:
			resident.objects.erase(object)
			resident.objects.append(object)
		return false},op(func(): clearing_balloon=false)]

func flight(from: Vector2i, to: Vector2i, ids: Array, palette: int, step: int = 16, delay: int = 10, mirror: bool = false, clip: Array = []) -> Array:
	var result: Array = []
	var point = from
	var delta = (to-from).abs()
	var direction = (to-from).sign()
	var error = int(delta.x/2) if delta.x else -1
	var n = 0
	while true:
		var ending = point==to
		if ending or n%step==0:
			var picture = {"id":ids[0 if n%(2*step)==0 else 1],"palette":palette,"point":point,"mirror":mirror,"clip":clip}
			result.append(op(func(): sprite=picture,delay))
		if ending:
			break
		if error>=0:
			point.x += direction.x
			error -= delta.y
		else:
			point.y += direction.y
			error += delta.x
		n += 1
	result.append(op(func(): sprite={}))
	return result

func release_drag(drag: Dictionary) -> Array:
	var bounds = resident.bounds(drag.object).duplicate()
	var type = int(drag.object.type)
	var inside = bool(drag.object.inside)
	var result: Array = []
	if type!=6:
		result.append(op(func(): resident.remove(drag.object)))
		result.append_array(clear_balloon(bounds))
		result.append(op(func():
			drag.object = resident.create(type,inside)
			resident.set_bounds(drag.object,bounds)))
	result.append(op(func():
		if host.scene=="inside" and resident.hit(resident.rect(),drag.point) and resident.offer(drag.object):
			return
		prepend(place(drag.object))))
	return result

func place(object: Dictionary) -> Array:
	return [op(func():
		var r = resident.bounds(object).duplicate()
		var inside = host.scene=="inside"
		var point = Vector2i(int(floor((r[1]+r[3])/2.0)),int(r[2]))
		var surfaces = resident.tables.surfaces[int(inside)]
		var index = -1
		for i in surfaces.size():
			if inside and (i==5 or (host.room.is_open and i<3)):
				continue
			if resident.hit(surfaces[i],point):
				index = i
				break
		if not inside and index==0:
			index = 1
		if index<0:
			resident.set_bounds(object,resident.tables.objects[object.type].inside if inside else resident.tables.objects[object.type].outside)
		else:
			prepend(settle(object,index,inside,r)))]

func settle(object: Dictionary, index: int, inside: bool, original: Array) -> Array:
	var bottom = resident.tables.surfaces[int(inside)][index][2]
	var target = [bottom-(original[2]-original[0]),original[1],bottom,original[3]]
	var result: Array = []
	if (170>original[0] if not inside and index==1 else bottom>original[2]):
		result.append_array(fall(object,original,target,inside and index==9,Vector2i(50,170) if not inside and index==1 else null))
	else:
		result.append(op(func(): resident.set_bounds(object,target)))
	result.append(op(func():
		resident.reset_object_timer(object)
		if inside and index==0 and object.type in [5,12]:
			prepend(nest_consume(object))
		elif inside and index==9:
			object.inside = false
			if object.type in [3,4,17,18,19,20]:
				resident.remove(object)
				resident.create(16,false)
			elif object.type==12:
				resident.remove(object)
				if resident.find(13)==null:
					resident.create(13,false)
			elif object.type==11:
				resident.remove(object)
				var pile = resident.find(14)
				if pile!=null:
					pile.state = mini(4,int(pile.state)+1)
				else:
					resident.create(14,false)
			else:
				if object.type==7:
					object.state = 5
					host.play_sound(1034)
				resident.set_bounds(object,resident.tables.objects[object.type].outside)
		elif not inside and index==2:
			if object.type==13:
				resident.remove(object)
				if resident.find(12)==null:
					resident.create(12)
			else:
				object.inside = true
				resident.set_bounds(object,resident.tables.objects[object.type].inside)
		elif not inside and index==1:
			var type = int(object.type)
			resident.remove(object)
			if type not in [2,8]:
				host.play_sound(10002)
			host.exterior.play(1004 if type==2 else 1003 if type==8 else 1005,1000)))
	return result

func fall(object: Dictionary, from: Array, to: Array, straight: bool, destination) -> Array:
	var data = resident.tables.objects[object.type]
	var id = int(host.store.palette("th",data.palette).first)+int(data.states[int(object.state)%10])-1
	var delta = int(to[0]-from[0])
	var ending = Vector2i(int(to[1]),int(to[0])) if destination==null else destination
	var result = [op(func(): object.hidden=true)]
	if object.type==1 and delta>36 and not straight:
		var p1 = Vector2i(int(from[1])-40,int(from[0])+int(delta/4))
		var p2 = p1+Vector2i(80,int(delta/2))
		result.append_array(flight(Vector2i(int(from[1]),int(from[0])),p1,[id,id],int(data.palette),6,3))
		result.append_array(flight(p1,p2,[id,id],int(data.palette),6,3,true))
		result.append_array(flight(p2,ending,[id,id],int(data.palette),6,3))
	else:
		if delta>50:
			result.append(op(func(): host.play_sound(10021)))
		result.append_array(flight(Vector2i(int(from[1]),int(from[0])),ending,[id,id],int(data.palette),6,1))
	result.append(op(func():
		object.hidden = false
		resident.set_bounds(object,to)
		if object.type==7 and delta>60:
			object.state = 5
			host.play_sound(1034)))
	return result

func chirp() -> Array:
	return [op(func(): host.room.interact("chirp")),{"delay":1,"until":func(): return not host.room.busy}]

func nest_consume(object: Dictionary) -> Array:
	return chirp()+[op(func(): object.hidden=true)]+chirp()+[op(func(): resident.remove(object))]

func highlight(object: Dictionary) -> Array:
	var result = [op(func():
		resident.objects.erase(object)
		resident.objects.append(object))]
	for i in 3:
		result.append(op(func(): object.hidden=true,12))
		result.append(op(func(): object.hidden=false,12))
	return result

func nuts(bag: Dictionary) -> Array:
	var existing = resident.find(11)
	if existing!=null:
		return highlight(existing)
	var holder = {}
	var result = [op(func():
		bag.state = 2
		host.play_sound(1014)
		holder.object = resident.create(11),4)]
	var positions = [[152,271,161,283],[146,255,155,267],[153,244,162,256],[162,237,171,249],[178,232,187,244]]
	for i in positions.size():
		result.append(op(func():
			holder.object.rect = positions[i]
			if i==2:
				host.play_sound(10038),4))
	result.append(op(func(): bag.state=1))
	return result

func draw(surface) -> void:
	if sprite.is_empty():
		return
	var image = host.store.image("th",sprite.id,sprite.palette,true)
	if sprite.mirror:
		image = image.duplicate()
		image.flip_x()
	surface.blit(image,sprite.point.x,sprite.point.y,true,sprite.clip)

func close_calendar() -> Array:
	return [op(func(): host.room.target=28),{"delay":2,"until":func(): return host.room.height<=28 or host.scene!="inside"}]

func departure(object: Dictionary) -> Array:
	var result: Array = []
	if object.type==0:
		result.append(op(func(): host.play_sound(1031)))
		for i in 3:
			result.append(op(func(): object.state+=1,30))
		result.append(op(func():
			host.play_sound(1036)
			object.state+=1))
	elif object.type==5:
		result.append(op(func(): object.state=2,30))
		result.append(op(func(): host.play_sound(1022)))
	elif object.type==1:
		result.append(op(func(): host.play_sound(1018)))
	result.append(op(func():
		var r = resident.bounds(object)
		var ids = [886,887] if object.type==0 else [889,889] if object.type==1 else [897,898]
		var shape = host.store.shape("th",ids[0])
		var from = Vector2i(int(floor((r[1]+r[3])/2.0))-int(shape[0]/2),int(floor((r[0]+r[2])/2.0))-int(shape[1]/2))
		var right = r[1]<160
		var operations: Array = close_calendar() if right and host.scene=="inside" else []
		operations.append(op(func(): object.hidden=object.type!=0))
		operations.append_array(flight(from,Vector2i(312,48) if right else Vector2i(-30,88),ids,870,16,10,right,[0,0,200,283] if right and host.scene=="inside" else []))
		operations.append(op(func():
			resident.remove(object)
			host.audio.stop()))
		prepend(operations)))
	return result

func bird_flight(from: Vector2i, to: Vector2i, carrying: bool = false, clip: Array = [], remove_existing: bool = true) -> Array:
	var base = (950 if to.y>from.y else 946)+2*int(carrying)
	return [op(func():
		var bird = resident.find(15)
		if bird!=null and remove_existing:
			resident.remove(bird))]+flight(from,to,[base,base+1],930,10,8,to.x>from.x,clip)+[op(func(): resident.schedule_ambient())]

func perched_departure() -> Array:
	return close_calendar()+bird_flight(Vector2i(218,95),Vector2i(132,32),false,[0,163,200,320])

func summon_bird() -> Array:
	return [op(func():
		if resident.find(15)!=null:
			return
		prepend(close_calendar()+bird_flight(Vector2i(312,48),Vector2i(218,95),false,[0,0,200,283])+[op(func(): resident.create(15).rect=[95,218,115,243])]))]

func basket(object: Dictionary, point) -> Array:
	var existing = resident.find(12)
	if existing!=null:
		return highlight(existing)
	if object.state!=1:
		return [op(func():
			object.state = 1
			var worm = resident.create(12)
			worm.rect = [160,6,172,23]
			if point!=null:
				resident.drag = {"object":worm,"rect":worm.rect.duplicate(),"start":point,"point":point,"since":host.tick,"moved":false,"newly_created":true})]
	var result = [op(func(): host.play_sound(1001))]
	for i in 3:
		result.append(op(func(): object.state+=1,8))
	result.append(op(func(): host.play_sound(1010)))
	for i in 3:
		result.append(op(func(): object.state=3 if object.state==4 else 4,8))
	result.append_array(summon_bird())
	return result

func feed_nest(from: Vector2i, from_offer: bool = false) -> Array:
	var result = close_calendar()+chirp()
	if from_offer:
		result.append_array(bird_flight(from,Vector2i(200,86),true))
		from = Vector2i(200,86)
	result.append_array(bird_flight(from,Vector2i(222,74),true))
	var holder = {}
	result.append(op(func():
		holder.bird = resident.create(15)
		holder.bird.state = 2
		holder.bird.nest_mirror = true
		holder.bird.rect = [70,222,90,247]))
	result.append_array(chirp())
	result.append(op(func():
		holder.bird.state = 1
		var worm = resident.create(12)
		worm.rect = [74,240,86,257]
		worm.nest_mirror = true
		prepend(nest_consume(worm))))
	result.append(op(func(): host.play_sound(12025)))
	result.append_array(bird_flight(Vector2i(222,74),Vector2i(312,48),false,[0,0,200,283]))
	return result

func take_worm(object: Dictionary) -> Array:
	var inside = host.scene=="inside"
	var r = object.rect
	var to = Vector2i(int(r[1])+2,int(r[0])-6)
	var from = (Vector2i(218,95) if resident.find(15)!=null else Vector2i(312,48)) if inside else Vector2i(350,10)
	var result = bird_flight(from,to)
	result.append(op(func():
		resident.remove(object)
		var bird = resident.create(15,inside)
		bird.state = 2
		bird.rect = [to.y,to.x,to.y+20,to.x+25],20))
	result.append(op(func():
		if not inside or host.room.is_open or host.random.pick(1):
			prepend(bird_flight(to,Vector2i(-30,88),true))
		else:
			prepend(feed_nest(to))))
	return result

func worm(object: Dictionary) -> Array:
	var result = [op(func(): host.play_sound(1010))]
	for i in 2:
		result.append(op(func(): object.state+=1,12))
		result.append(op(func(): object.state-=1,12))
	if host.scene=="inside":
		result.append_array(close_calendar())
	result.append(op(func():
		host.play_sound(12025)
		prepend(take_worm(object) if resident.find(15)!=null or host.scene=="outside" else summon_bird())))
	return result

func consume_food(object: Dictionary) -> Array:
	return [op(func():
		resident.consuming = object
		host.play_sound(10017),480),op(func():
		host.audio.stop()
		resident.remove(object)
		resident.consuming = null)]

func flyby() -> Array:
	var inside = host.scene=="inside"
	var from = Vector2i(312,48) if inside else Vector2i(350,10)
	var to = Vector2i(-30,88)
	var clip = [0,0,200,283] if inside else []
	if inside:
		if not host.random.pick(1):
			return feed_nest([Vector2i(132,32),Vector2i(312,48),Vector2i(-30,88)][host.random.pick(2)])
		if host.random.pick(1):
			to = Vector2i(132,32)
			clip = [0,163,200,320]
	if host.random.pick(1):
		var temp = from
		from = to
		to = temp
	return bird_flight(from,to,false,clip,false)
