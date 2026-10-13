extends RefCounted
## Sentence theater, recovered from DOS 1.1 overlay 4.
const ScrAnimation = preload("res://scripts/animation.gd")
const Renderer = preload("res://scripts/theater_renderer.gd")
const Integers = preload("res://scripts/music_maze.gd")
var host
var store
var tables: Dictionary
var renderer
var selection: Array = [-1,-1,-1,-1]
var order: Array = [0,1,2,3]
var category: int = -1
var options: bool = true
var mix_up: bool = false
var props_enabled: bool = false
var tick: int = 0
var preview
var actor_animation
var playing: bool = false
var sequence: Array = []
var wait_until: int = 0
var presenting: int = -1
var weather_start = null
var drag: Dictionary = {}
var actor_drag: Array = []
var props: Array = []
var performances: int = 0
var curtain: int = 3
var curtain_start = null
var curtain_moving: bool = false
var director: int = 0
var phase: String = "idle"
var presentation: Array = []
var presentation_due: int = 0
var leaving: bool = false
var leave_callback: Callable
var stage_selection = null
var stage_options = null
var stage_order = null
var opening_editor: bool = false
var exit_ready: bool = false
var valid_play: bool = true
var phase_start: int = 0
var actor_tail: int = 0
var feedback: int = 0
var success_feedback: bool = false
var previous_validation: int = 0
var token_sequence: Array = []
var token_sprite = null
var token_due: int = 0
var correct_notice_until = null
var preview_category: int = -1
var preview_until: int = 0
var preview_blink_until: int = 0
var storage_enabled: bool = true
var save_path: String = "user://theater.json"
var curtain_voice: int = -1
var hide_cursor: bool:
	get:
		return (actor_animation!=null and not actor_animation.done) or (preview!=null and not preview.done)
var busy_cursor: bool:
	get:
		return curtain_moving or (playing and weather_start!=null)

func _init(game, persistent: bool = true) -> void:
	host = game
	store = game.store
	tables = Integers.integers(store.data.theater)
	storage_enabled = persistent
	for i in 7:
		actor_drag.append([0,0])
	for i in 6:
		props.append([])
	renderer = Renderer.new(self)
	if storage_enabled:
		restore()

func saved_state() -> Dictionary:
	return {"version":1,"mix_up":mix_up,"props_enabled":props_enabled,"selection":selection.duplicate(),"order":order.duplicate(),"actor_drag":actor_drag.duplicate(true),"props":props.duplicate(true),"previous_validation":previous_validation}

func save() -> void:
	if not storage_enabled:
		return
	var file = FileAccess.open(save_path,FileAccess.WRITE)
	if file==null:
		push_error("Could not save the theater play: %s"%FileAccess.get_open_error())
		return
	file.store_string(JSON.stringify(saved_state()))
	file.close()
	if host.persistence!=null:
		host.persistence.save()

func valid_ints(value, count: int, low: int, high: int) -> bool:
	if not value is Array or value.size()!=count:
		return false
	for item in value:
		if not (item is int or item is float) or item!=int(item) or item<low or item>high:
			return false
	return true

func restore() -> void:
	if not FileAccess.file_exists(save_path):
		return
	var value = JSON.parse_string(FileAccess.get_file_as_string(save_path))
	if not value is Dictionary or value.get("version")!=1 or not value.get("mix_up") is bool or not value.get("props_enabled") is bool:
		return
	if not valid_ints(value.get("selection"),4,-1,100) or not valid_ints(value.get("order"),4,0,3) or not valid_ints([value.get("previous_validation")],1,0,6):
		return
	for c in 4:
		if value.selection[c]>=choices(c).size() or value.order.count(float(c))!=1:
			return
	if not value.get("actor_drag") is Array or value.actor_drag.size()!=7 or not value.get("props") is Array or value.props.size()!=6:
		return
	for point in value.actor_drag:
		if not valid_ints(point,2,-320,320):
			return
	for place in 6:
		var list = value.props[place]
		var palette = 3175 if tables.prop_group[place] else 3145
		var first = palette+tables.prop_first[place]
		if not list is Array or list.size()>20:
			return
		for item in list:
			if not item is Dictionary or not valid_ints([item.get("id")],1,first,first+tables.prop_count[place]-1) or item.get("palette")!=palette or not valid_ints([item.get("x")],1,0,319) or not valid_ints([item.get("y")],1,0,199):
				return
	for key in ["mix_up","props_enabled","selection","order","actor_drag","props","previous_validation"]:
		set(key,Integers.integers(value[key]))

func choices(c: int) -> Array:
	var result: Array = []
	if c==4:
		for i in tables.prop_count[maxi(0,selection[2])]:
			result.append("Decoration %d"%(i+1))
	else:
		for value in store.data.strings["modules:%d"%(3000+10*c)]:
			result.append(value.strip_edges())
	return result

func speak(id: int) -> int:
	return host.play_sound(id)

# These two operation queues preserve generator yield boundaries independently:
# curtains/choice presentation and sentence-token movement can overlap.
func op(method: String, args: Array = []) -> Array:
	return [method,args]

func step_queue(name: String) -> void:
	var queue: Array = get(name)
	while not queue.is_empty():
		var item = queue.pop_front()
		if item is int:
			set("presentation_due" if name=="presentation" else "token_due",tick+item)
			return
		if item is Dictionary:
			for key in item:
				set(key,item[key])
		else:
			var extra = callv(item[0],item[1])
			if extra is Array:
				queue.assign(extra+queue)

func run_presentation(steps: Array) -> void:
	presentation = steps
	presentation_due = tick
	update(tick)

func curtain_sound() -> void:
	speak(10032)
	curtain_voice = host.audio_serial

func curtain_stop() -> void:
	if host.audio_serial==curtain_voice:
		host.audio.stop()

func move_curtain(open: bool) -> Array:
	var result: Array = [{"curtain_moving":true},op("curtain_sound")]
	for stage in ([1,2,3] if open else [2,1,0]):
		result.append({"curtain":stage})
		result.append(8)
	return result+[op("curtain_stop"),{"curtain_moving":false}]

func curtain_change(change: Dictionary) -> Array:
	return move_curtain(false)+[change]+move_curtain(true)

func enter() -> void:
	tick = host.tick
	curtain = 0
	run_presentation(move_curtain(true))

func leave(done: Callable) -> void:
	if leaving:
		return
	stop()
	leaving = true
	leave_callback = done
	run_presentation(move_curtain(false)+[{"exit_ready":true},op("complete_leave")])

func complete_leave() -> void:
	var callback = leave_callback
	leave_callback = Callable()
	if callback.is_valid():
		callback.call()

func set_option(name: String, value: bool) -> void:
	if get(name)!=value:
		set(name,value)
		speak(1008)
	save()

func start() -> void:
	var duration = speak(1008)
	stage_options = options
	opening_editor = true
	options = false
	category = -1
	var steps: Array = [duration] if duration>0 else []
	run_presentation(steps+curtain_change({"stage_options":false})+[{"stage_options":null,"opening_editor":false}])
	save()

func show_choices(c: int, sound: bool = true) -> void:
	if options or playing or (c==4 and (not props_enabled or selection[2]<0)):
		return
	if sound:
		speak(1008)
	if not feedback:
		director = 0
	feedback = 0
	success_feedback = false
	preview_category = -1
	presenting = -1
	category = c

func choose(c: int, index: int, from_notebook: bool = false) -> void:
	if options:
		start()
	var previous = selection.duplicate()
	stop()
	feedback = 0
	success_feedback = false
	category = c
	if c==4:
		add_prop(index)
		return
	assert(index>=-1 and index<choices(c).size())
	selection[c] = index
	if c==0:
		for i in 7:
			actor_drag[i] = [0,0]
	if index>=0 and index!=previous[c]:
		stage_selection = previous
		var steps: Array = []
		if mix_up and previous[c]<0 and not from_notebook:
			var a = tables.ui_rects[8+c]
			var b = tables.ui_rects[23+order.find(c)]
			steps += travel_token(c,[int((a[1]+a[3])/2)-10,int((a[0]+a[2])/2)-10],[b[1],b[0]])
		steps += curtain_change({"stage_selection":null}) if c>=2 else [{"stage_selection":null}]
		run_presentation(steps+[op("preview_part",[c])])
	save()

func phrase(c: int, selected = null) -> String:
	if selected==null:
		selected = selection
	return choices(c)[selected[c]] if selected[c]>=0 else ""

func sentence(selected = null) -> String:
	if selected==null:
		selected = selection
	var parts: PackedStringArray = []
	for c in (order if stage_order==null else stage_order):
		var value = phrase(c,selected)
		if not value.is_empty():
			parts.append(value)
	var result = " ".join(parts)
	if selected[0]>=0 and selected[1]>=0 and not result.is_empty():
		result = result.left(1).to_upper()+result.substr(1)+"."
	return result

func validation() -> int:
	if selection[0]<0 and selection[1]<0:
		return 2
	if selection[0]<0:
		return 3
	if selection[1]<0:
		return 4
	var present = order.filter(func(c): return selection[c]>=0)
	var subject = present.find(0)
	var action = present.find(1)
	return 5 if subject>action else 6 if action!=subject+1 else 0

func corrected_order(code: int = -1) -> Array:
	if code<0:
		code = validation()
	var result = order.duplicate()
	var subject = result.find(0)
	var action = result.find(1)
	var a = -1
	var b = -1
	if action>0 and selection[result[action-1]]<0:
		a = action-1
		b = subject
	elif subject<3 and selection[result[subject+1]]<0:
		a = subject+1
		b = action
	elif code==5:
		for i in range(action,subject):
			result[i] = result[i+1]
		result[subject] = 1
	elif code==6:
		for i in range(action,subject+1,-1):
			result[i] = result[i-1]
		result[subject+1] = 1
	if a>=0:
		var old = result[a]
		result[a] = result[b]
		result[b] = old
	return result

func correct() -> void:
	if not mix_up or playing or not token_sequence.is_empty():
		return
	var code = validation()
	previous_validation = code
	if code==0:
		correct_notice_until = tick+120
	elif code<5:
		feedback = code
		category = -1
	else:
		order = corrected_order(code)
		feedback = 0
		previous_validation = 0
	save()

func travel_token(c: int, from: Array, to: Array) -> Array:
	var x = from[0]
	var y = from[1]
	var dx = abs(to[0]-x)
	var dy = abs(to[1]-y)
	var sx = sign(to[0]-x)
	var sy = sign(to[1]-y)
	var error = int(dx/2) if dx else -1
	var step = 0
	var result: Array = [op("speak",[10035])]
	while true:
		var end = x==to[0] and y==to[1]
		if end or step%8==0:
			result += [{"token_sprite":{"category":c,"x":x,"y":y}},4]
		if end:
			break
		if error>=0:
			x += sx
			error -= dy
		else:
			y += sy
			error += dx
		step += 1
	return result+[{"token_sprite":null}]

func move_token(c: int, from: int, to: int) -> Array:
	if selection[c]<0:
		return []
	var a = tables.ui_rects[23+from]
	var b = tables.ui_rects[23+to]
	return travel_token(c,[a[1],a[0]],[b[1],b[0]])

func swap_tokens(from: int, to: int, dragged: bool = false) -> Array:
	var a = order[from]
	var b = order[to]
	var result: Array = [{"stage_order":order.duplicate()}]
	if not dragged:
		result += move_token(a,from,to)
	result.append(op("swap_order",[from,to]))
	return result+move_token(b,to,from)+[{"stage_order":null},op("save")]

func swap_order(from: int, to: int) -> void:
	var old = order[from]
	order[from] = order[to]
	order[to] = old

func shuffle_step(count: int) -> Array:
	if count==0:
		previous_validation = validation()
		save()
		return []
	var a = host.random.pick(3)
	var b = host.random.pick(3)
	while a==b:
		b = host.random.pick(3)
	return swap_tokens(a,b)+[op("shuffle_step",[count-1])]

func shuffle() -> void:
	if not mix_up or playing or not token_sequence.is_empty():
		return
	feedback = 0
	token_sequence = [op("shuffle_step",[5])]
	token_due = tick
	update(tick)

func make_animation(id: int, palette: int, origin = null):
	var value = ScrAnimation.new(store,"modules",id,palette,tick)
	if origin!=null:
		value.origin = Vector2i(origin[0],origin[1])
	value.update(tick)
	return value

func blink_duration(duration: int) -> int:
	return maxi(60,12+24*int(ceil(maxi(0,duration-12)/24.0)))

func preview_part(c: int) -> void:
	var choice = selection[c]
	if choice<0:
		return
	preview_category = c
	preview_until = tick+blink_duration(speak(3000+10*c+choice))
	phase_start = tick
	presenting = c
	if c==1:
		preview = make_animation(3050+choice,3050)
	if c==3:
		preview_blink_until = preview_until
		preview_until += 20

func translation() -> Array:
	var selected = selection if stage_selection==null else stage_selection
	var base = tables.actor_origins_by_place[selected[2]+1][selected[0]]
	var delta = actor_drag[selected[2]+1]
	return [base[0]+delta[0],base[1]+delta[1]]

func actor_rect() -> Array:
	var actor = (selection if stage_selection==null else stage_selection)[0]
	if actor<0:
		return []
	var b = tables.actor_bounds[actor]
	var offset = translation()
	return [b[0]+offset[0],b[1]+offset[1],b[2]+offset[0],b[3]+offset[1]]

func play() -> bool:
	if not token_sequence.is_empty():
		return false
	var code = validation()
	var previous = previous_validation
	stop()
	previous_validation = code
	success_feedback = previous!=0 and code==0
	feedback = (1 if previous in [3,4] else 0) if success_feedback else 0
	if success_feedback:
		category = -1
	valid_play = code==0
	playing = true
	sequence = order.filter(func(c): return selection[c]>=0)
	phase = "clap"
	director = 1
	wait_until = tick+16
	speak(1009)
	return valid_play

func present_next() -> void:
	if sequence.is_empty():
		presenting = -1
		weather_start = null
		phase = "tail" if valid_play else "invalid"
		wait_until = maxi(tick,actor_tail) if valid_play else tick+30
		director = 2 if valid_play else 3
		if valid_play and wait_until<=tick:
			finish()
		return
	var c = sequence.pop_front()
	var choice = selection[c]
	presenting = c
	phase = "phrase"
	phase_start = tick
	var duration = speak(3000+10*c+choice)
	wait_until = tick+duration
	if valid_play and c in [0,2]:
		wait_until = tick+blink_duration(duration)
	if valid_play and c==1:
		var group = 3200+100*selection[0]
		var id = group+choice
		var b = store.data.scripts["modules:%d"%id].bounds
		var offset = translation()
		actor_animation = make_animation(id,group,[b[1]+offset[1],b[0]+offset[0]])
	if c==3:
		if valid_play:
			weather_start = tick
			var row = tables.time_shapes[choice]
			wait_until = maxi(wait_until,tick+(row[2]-1)*row[3])
		wait_until += 20

func stop() -> void:
	playing = false
	sequence = []
	presenting = -1
	preview_category = -1
	actor_animation = null
	weather_start = null
	preview = null
	token_sequence = []
	token_sprite = null
	stage_order = null
	phase = "idle"
	director = 0
	actor_tail = 0
	presentation = []
	stage_selection = null
	stage_options = null
	opening_editor = false
	curtain_moving = false
	curtain = 3
	exit_ready = false
	leaving = false
	leave_callback = Callable()

func finish() -> void:
	playing = false
	actor_animation = null
	phase = "idle"
	performances += 1
	if valid_play:
		director = 0
	else:
		feedback = validation()
		category = -1
		speak(1030)
	save()

func update(now: int) -> void:
	tick = now
	if not presentation.is_empty() and tick>=presentation_due:
		step_queue("presentation")
	if preview_category>=0 and tick>=preview_until:
		preview_category = -1
		presenting = -1
	if correct_notice_until!=null and tick>=correct_notice_until:
		correct_notice_until = null
	if drag.get("type")=="token" and not drag.active and tick-drag.since>=15:
		drag.active = true
		move_drag(Vector2i(drag.pointer[0],drag.pointer[1]))
	if not token_sequence.is_empty() and tick>=token_due:
		step_queue("token_sequence")
	for actor in [actor_animation,preview]:
		if actor!=null and not actor.done:
			actor.update(tick)
	if curtain_start!=null:
		curtain = mini(3,int((tick-curtain_start)/8))
		if curtain==3:
			curtain_start = null
	if weather_start!=null:
		var row = tables.time_shapes[selection[3]]
		if tick-weather_start>=(row[2]-1)*row[3]:
			weather_start = null
	if playing and tick>=wait_until:
		if phase=="clap":
			phase = "pause"
			director = 0
			wait_until = tick+32
		elif phase=="pause":
			director = 2 if valid_play else 0
			present_next()
		elif phase=="phrase" and (actor_animation==null or actor_animation.done) and weather_start==null:
			if valid_play and presenting==1:
				actor_tail = tick+120
			present_next()
		elif phase in ["tail","invalid"]:
			finish()

func add_prop(index: int, position = null):
	var place = selection[2]
	if place<0 or props[place].size()>=20:
		return null
	speak(1008)
	var palette = 3145 if tables.prop_group[place]==0 else 3175
	var id = palette+tables.prop_first[place]+index
	var shape = store.shape("modules",id)
	var item = {"id":id,"palette":palette,"x":int(position[0])-int(shape[0]/2) if position!=null else 160,"y":int(position[1])-int(shape[1]/2) if position!=null else 115}
	props[place].append(item)
	save()
	return item

func hit(rect: Array, point: Vector2i) -> bool:
	return not rect.is_empty() and point.x>=rect[1] and point.x<rect[3] and point.y>=rect[0] and point.y<rect[2]

func begin_drag(point: Vector2i) -> bool:
	if options or playing or not token_sequence.is_empty():
		return false
	if mix_up:
		for i in 4:
			var c = order[i]
			var r = tables.ui_rects[23+i]
			if selection[c]>=0 and hit(r,point):
				show_choices(c,false)
				drag = token_drag(c,i,false,point,[r[1],r[0]])
				return true
			var b = tables.ui_rects[8+i]
			if selection[i]<0 and hit(b,point):
				show_choices(i)
				drag = token_drag(i,order.find(i),true,point,[int((b[1]+b[3])/2)-10,int((b[0]+b[2])/2)-10])
				return true
	var place = selection[2]
	if place>=0:
		for index in props[place].size():
			var item = props[place][index]
			var shape = store.shape("modules",item.id)
			if hit([item.y,item.x,item.y+shape[1],item.x+shape[0]],point):
				drag = {"type":"prop","item":item,"index":index,"start":[point.x,point.y],"origin":[item.x,item.y]}
				return true
	var rect = actor_rect()
	if hit(rect,point):
		drag = {"type":"actor","start":[point.x,point.y],"origin":actor_drag[place+1].duplicate(),"rect":rect,"since":tick,"moved":false}
		return true
	return false

func token_drag(c: int, from: int, notebook: bool, point: Vector2i, origin: Array) -> Dictionary:
	return {"type":"token","category":c,"from":from,"notebook":notebook,"since":tick,"start":[point.x,point.y],"pointer":[point.x,point.y],"origin":origin,"x":origin[0],"y":origin[1],"active":false}

func move_drag(point: Vector2i) -> bool:
	if drag.is_empty():
		return false
	var dx = point.x-drag.start[0]
	var dy = point.y-drag.start[1]
	if drag.type=="token":
		drag.pointer = [point.x,point.y]
		if tick-drag.since<15:
			return false
		drag.active = true
		if abs(dx)>2 or abs(dy)>2:
			drag.x = clampi(drag.origin[0]+dx,2,297)
			drag.y = clampi(drag.origin[1]+dy,2,178)
	elif drag.type=="prop":
		var shape = store.shape("modules",drag.item.id)
		drag.item.x = clampi(drag.origin[0]+dx,0,320-shape[0])
		drag.item.y = clampi(drag.origin[1]+dy,0,200-shape[1])
	else:
		if tick-drag.since<15:
			return false
		drag.moved = drag.moved or abs(dx)>=2 or abs(dy)>=2
		var b = drag.rect
		actor_drag[selection[2]+1] = [drag.origin[0]+maxi(74-b[0],mini(165-b[2],dy)),drag.origin[1]+maxi(103-b[1],mini(261-b[3],dx))]
	return true

func end_drag(cancelled: bool = false) -> void:
	if drag.is_empty():
		return
	var d = drag
	drag = {}
	if d.type=="token":
		if not cancelled:
			if not d.active:
				if not d.notebook:
					preview_part(d.category)
			elif not d.notebook and d.pointer[0]<67:
				choose(d.category,-1)
				previous_validation = 0
			else:
				for target in 4:
					if not hit(tables.ui_rects[23+target],Vector2i(d.pointer[0],d.pointer[1])):
						continue
					if d.notebook:
						swap_order(d.from,target)
						choose(d.category,host.random.pick(choices(d.category).size()-1),true)
					elif target!=d.from:
						token_sequence = swap_tokens(d.from,target,true)
						token_due = tick
						update(tick)
					break
	elif d.type=="actor":
		if not cancelled and not d.moved:
			speak(3000+selection[0])
	else:
		var item = d.item
		var shape = store.shape("modules",item.id)
		var list = props[selection[2]]
		# Dictionary equality is by value. Retain the grabbed slot so two
		# identical overlapping decorations cannot become aliases of one item.
		list.remove_at(d.index)
		if item.x+shape[0]>103 and item.x<261 and item.y+shape[1]>53 and item.y<165:
			item.x = maxi(103,mini(261-shape[0],item.x))
			item.y = maxi(53,mini(165-shape[1],item.y))
			list.append(item)
	save()

func choice_bounds() -> Array:
	var result: Array = []
	if category<0:
		return result
	var count = choices(category).size()
	if category==0:
		var x = 73
		for i in 8:
			var width = int(store.shape("modules",3981+i)[0])
			result.append([15,x,42,x+width])
			x += width+5
	else:
		var width = int(221/count)
		for i in count:
			result.append([15,73+width*i,42,73+width*(i+1)])
	return result

func click(point: Vector2i) -> void:
	var x = point.x
	var y = point.y
	if options:
		if x>=184 and x<192 and y>=81 and y<89:
			set_option("mix_up",not mix_up)
		elif x>=184 and x<192 and y>=97 and y<105:
			set_option("props_enabled",not props_enabled)
		elif x>=182 and x<241 and y>=130 and y<150:
			start()
		return
	if hit(tables.ui_rects[1],point):
		stop()
		options = true
		return
	if playing:
		stop()
		return
	if not token_sequence.is_empty():
		return
	if mix_up and hit(tables.ui_rects[21],point):
		shuffle()
		return
	if mix_up and hit(tables.ui_rects[22],point):
		correct()
		return
	for c in 4:
		if hit(tables.ui_rects[8+c],point):
			show_choices(c)
			return
		if hit(tables.ui_rects[12+c],point):
			host.preferences.open_help(false,false,true)
			return
	var boxes = choice_bounds()
	for i in boxes.size():
		if hit(boxes[i],point):
			if category==4:
				var item = add_prop(i,[x,y])
				if item!=null:
					drag = {"type":"prop","item":item,"index":props[selection[2]].size()-1,"start":[x,y],"origin":[item.x,item.y]}
			else:
				choose(category,i)
			return
	if hit(tables.ui_rects[7],point):
		play()
	elif hit(tables.ui_rects[18],point) and selection[1]>=0:
		preview = make_animation(3050+selection[1],3050)
	elif props_enabled and x<62 and y>=163 and y<178:
		show_choices(4)

func draw(surface) -> void:
	renderer.draw(surface)

func dispose() -> void:
	stop()
	drag = {}
	renderer = null
