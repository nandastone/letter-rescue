extends RefCounted
## Calendar, clock, moving window and environment; original resident routines.
var host
var store
var date: Dictionary
var cloud: int = 5
var cloud_x: int = 195
var cloud_due: int = 0
var height: int = 28
var target: int = 28
var due: int = 0
var tick: int = 0
var pending_date: Dictionary = {}
var calendar_read: bool = false
var calendar_read_open: bool = false
var sliding: bool = false
var portrait_frame: int = 0
var speech: Array = []
var speech_due: int = 0
var speech_complete: Callable
var music_waiting: bool = false
var music_due: int = 0
var environment = null
var pending_environment: String = ""
var chirp_until: int = 0
var chirp_start: int = 0
var clear_due: int = 0
var question: String = ""
var question_accept: bool = false
var question_due: int = 0
var question_start: int = 0
var question_background: Image
var blank: bool = false
var is_open: bool:
	get: return target==98
var busy: bool:
	get: return music_waiting or height!=target or calendar_read or environment!=null or not pending_environment.is_empty() or chirp_until>tick or not question.is_empty()

func _init(game) -> void:
	host = game
	store = game.store
	date = host.now()

func enter(value: int) -> void:
	tick = value
	cloud_due = tick+300

func leave() -> void:
	if music_waiting:
		host.stop_all_sound()
	music_waiting = false
	sliding = false
	calendar_read = false
	pending_date = {}
	environment = null
	pending_environment = ""
	chirp_until = 0
	speech.clear()
	speech_complete = Callable()
	question = ""
	blank = false

func slide(value: int) -> void:
	target = value
	due = tick+2
	if height != target:
		host.play_sound(10031)
		sliding = true

func toggle() -> void:
	slide(28 if is_open else 98)

func browse(delta: int) -> void:
	var changed = Time.get_datetime_dict_from_unix_time(Time.get_unix_time_from_datetime_dict(date)+delta*86400)
	if changed.year >= 1980:
		choose_date(changed)

func choose_date(value: Dictionary) -> void:
	if height>28:
		pending_date = value.duplicate()
		slide(28)
	else:
		date = value.duplicate()
		read_calendar()

func read_calendar() -> void:
	say_date()
	calendar_read = true
	calendar_read_open = not is_open

func next_cloud() -> void:
	if height>28 or is_open:
		return
	cloud = (cloud+1)%7
	cloud_x = 223-int(store.shape("th",171+cloud)[0]/2)

func say(queue: Array, complete: Callable = Callable()) -> void:
	speech = queue.duplicate(true)
	speech_complete = complete
	speech_due = tick
	service_speech()

func service_speech() -> void:
	if tick<speech_due:
		return
	if speech.is_empty():
		var complete = speech_complete
		speech_complete = Callable()
		if complete.is_valid():
			complete.call()
		if portrait_frame==932:
			portrait_frame = 931
		return
	var part = speech.pop_front()
	portrait_frame = 931 if part is Array or (part is Dictionary and not part.get("mouth",true)) else 932
	var sound = int(part.sound) if part is Dictionary else 0 if part is Array else int(part)
	speech_due = tick+(int(part[0]) if part is Array else host.play_sound(sound))

func number_speech(value: int, leading_zero: bool = false) -> Array:
	var tens = [30,0,20,13,14,15,6,7,8,19]
	var teens = [10,11,12,13,14,15,6,7,8,19]
	var result: Array = []
	if value==0:
		return [[5]]
	if value>=10 and value<20:
		result.append(11000+teens[value%10])
		if value>=13:
			result.append_array([[5],11027])
	else:
		if value>=20 or leading_zero:
			result.append_array([11000+tens[int(value/10)],[5]])
		if value>=20:
			result.append_array([11022,[5]])
		result.append(11000+value%10)
		if value%10==8:
			result.append(11021)
	result.append([5])
	return result

func say_time(date_value: Dictionary = {}, wake: bool = false, complete: Callable = Callable()) -> void:
	var current = host.now() if date_value.is_empty() else date_value
	var hour = int(current.hour)%12
	if hour==0:
		hour = 12
	var queue = [11028,[15],11026] if wake else [11023]
	queue.append_array([[15],11000+hour])
	if hour==8:
		queue.append(11021)
	queue.append([20])
	queue.append_array(number_speech(int(current.minute),true))
	queue.append_array([[20],11024+int(current.hour>=12)])
	say(queue,complete)

func say_date() -> void:
	var day = int(date.day)
	var weekday = Time.get_datetime_dict_from_unix_time(Time.get_unix_time_from_datetime_dict(date)).weekday
	var teens = [10,11,12,13,14,15,6,7,8,19]
	var queue = [11120+weekday,[30],11099+int(date.month),[12]]
	if day<=12:
		queue.append(11129+day)
	elif day<20:
		queue.append_array([11000+teens[day%10],[5],11142])
	else:
		queue.append(11020 if day<30 else 11013)
		if day%10==0:
			queue.append(11143)
		else:
			queue.append_array([11022,[5],11129+day%10])
	say(queue)

func interact(kind: String) -> bool:
	if busy or (kind in ["nest","chirp"] and (is_open or height>28)):
		return false
	slide(28)
	pending_environment = kind
	clear_due = tick
	return true

func begin_environment() -> void:
	var kind = pending_environment
	var area = Rect2i(0,0,283,84) if kind=="spider" else Rect2i(207,74,74,30) if kind=="nest" else Rect2i(237,81,23,13)
	var b = host.balloon
	if not b.hidden and b.x<area.end.x and b.x+29>area.position.x and b.y<area.end.y+2 and b.y+38>area.position.y-2:
		if tick>=clear_due:
			b.y += 2 if kind=="spider" else -2
			clear_due = tick+2
		return
	pending_environment = ""
	if kind=="chirp":
		chirp_start = tick
		chirp_until = tick+mini(180,host.play_sound(1041))
	else:
		var id = 1080 if kind=="spider" else 1250
		environment = host.animation("th",id,id)

func finish_environment() -> void:
	host.audio.stop()
	environment = null
	host.resident.schedule_ambient()

func interrupt_audio() -> bool:
	if music_waiting:
		music_waiting = false
		host.stop_all_sound()
		return true
	if environment==null or not environment.done or tick>=environment.sound_due:
		return false
	finish_environment()
	return true

func play_home_music() -> void:
	# Resident main 15B9: blocking Home music when the child is asleep.
	music_waiting = true
	music_due = host.tick+host.play_sound(20001)

func ask_chalk() -> void:
	if busy:
		return
	host.chalk.select(-1)
	question = "closing" if height>28 else "clearing"
	pending_date = {}
	target = 28
	blank = false
	due = tick+2
	question_due = tick

func answer_chalk(point: Vector2i) -> void:
	if question!="asking":
		return
	question = "answered"
	question_accept = Rect2i(178,47,34,40).has_point(point)
	target = 28
	due = host.tick+2

func update_question() -> void:
	if question.is_empty() or height!=target:
		return
	if question=="closing":
		question = "clearing"
	if question=="answered":
		question = "clear-board" if question_accept else ""
		if question.is_empty():
			blank = false
			# Main 16F2 calls BC43 after either answer, after calendar closure.
			host.resident.schedule_ambient()
	if question in ["clearing","clear-board"]:
		var area = [28,162,110,283] if question=="clearing" else [38,52,99,157]
		var b = host.balloon
		if not b.hidden and b.x<area[3] and b.x+29>area[1] and b.y<area[2]+2 and b.y+38>area[0]-2:
			if tick>=question_due:
				b.y -= 2
				question_due = tick+2
		elif question=="clearing":
			blank = true
			question = "opening"
			slide(98)
		else:
			question = ""
			blank = false
			host.chalk.clear()
			host.resident.schedule_ambient()
	elif question=="opening":
		question = "asking"
		question_start = tick
		host.draw_inside()
		question_background = host.surface.image.duplicate()

func update_cloud() -> void:
	if is_open or height!=28 or busy or tick<cloud_due:
		return
	cloud_x += 1
	if cloud_x>283:
		cloud = (cloud+1)%7
		cloud_x = 163-int(store.shape("th",171+cloud)[0])
	cloud_due = tick+300

func update(value: int, modal: bool = false) -> void:
	tick = value
	if music_waiting and tick>=music_due:
		music_waiting = false
		host.stop_all_sound()
	if height!=target and not sliding:
		host.play_sound(10031)
		sliding = true
	if not modal:
		update_cloud()
	if height!=target and not sliding:
		host.play_sound(10031)
		sliding = true
	if tick>=due and height!=target:
		height += int(sign(target-height))*10
		due = tick+2
		if height==target:
			host.audio.stop()
			sliding = false
			if height==28:
				cloud_due = tick+300
			if height==28 or question.is_empty():
				if height==98:
					host.resident.schedule_ambient()
				else:
					host.resident.enter_scene()
		if height==28 and not pending_date.is_empty():
			date = pending_date
			pending_date = {}
			read_calendar()
	if height==28 and not pending_environment.is_empty():
		begin_environment()
	if environment!=null:
		environment.update(tick)
		if environment.done and tick>=environment.sound_due:
			finish_environment()
	if chirp_until and tick>=chirp_until:
		chirp_until = 0
		host.resident.schedule_ambient()
	service_speech()
	if calendar_read and speech.is_empty() and tick>=speech_due:
		calendar_read = false
		if calendar_read_open:
			slide(98)
	update_question()

func text_width(value: String) -> int:
	var width = 0
	for c in value:
		width += int(store.data.font.get(str(c.unicode_at(0)),[4])[0])
	return width

func date_label() -> String:
	return "%s %d, %d" % [store.data.strings["th:500"][int(date.month)-1],date.day,date.year]

func draw_cloud(surface) -> void:
	var shape = store.shape("th",171+cloud)
	surface.draw(store,"th",171+cloud,170,cloud_x,55-int(shape[1]/2),10,[30,163,80,283])

func draw_portrait(surface) -> void:
	if portrait_frame:
		surface.draw(store,"th",portrait_frame,930,25,43,2)

func draw_date_clock(surface) -> void:
	var label = date_label()
	surface.rect(58,24,76,11,Color.WHITE)
	surface.text(store,label,96-int(text_width(label)/2),25,Color8(255,85,85))
	var current = host.now()
	var hour = int(current.hour)%12
	if hour==0:
		hour = 12
	var minute = int(current.minute)
	surface.rect(92,108,22,10,Color.BLACK)
	for item in [[1227 if hour>9 else 1226,95],[1215+hour%10,97],[1225,102],[1215+int(minute/10),104],[1215+minute%10,109]]:
		surface.draw(store,"th",item[0],1200,item[1],110,2)

func draw_calendar(surface) -> void:
	var clip = [28,162,height,283]
	if height>28:
		surface.rect(162,28,121,height-28,Color.WHITE)
		if blank:
			surface.draw(store,"th",1201,1200,162,height)
			return
		var values = store.data.strings["th:%d" % (1000+int(date.month))]
		var heading = values[2*(int(date.day)-1)]
		var body = values[2*(int(date.day)-1)+1]
		surface.text(store,heading,222-int(text_width(heading)/2),28,Color.BLACK,clip)
		var line = ""
		var lines: Array = []
		for word in body.split(" "):
			var next = word if line.is_empty() else line+" "+word
			if text_width(next)>118 and not line.is_empty():
				lines.append(line)
				line = word
			else:
				line = next
		if not line.is_empty():
			lines.append(line)
		for i in lines.size():
			surface.text(store,lines[i],164,39+10*i,Color.BLACK,clip)
	surface.draw(store,"th",1201,1200,162,height)

func draw_environment(surface) -> void:
	if environment!=null:
		if environment.id==1250:
			surface.rect(211,81,70,23,Color8(195,227,255))
		environment.draw(surface)
	if chirp_until>tick:
		surface.draw(store,"th",920+int((tick-chirp_start)/8)%2,900,241,82)

func draw_question(surface) -> void:
	if question!="asking":
		return
	surface.image.copy_from(question_background)
	surface.rect(168,29,110,58,Color.WHITE)
	var message = "Erase Chalkboard?"
	surface.text(store,message,223-int(text_width(message)/2),33,Color.BLACK)
	var phase = int((host.tick-question_start)/12)
	surface.draw(store,"th",86+(phase&1),80,178,47,2)
	surface.draw(store,"th",88+[0,1,2,1][phase&3],80,234,47,2)
	for item in [["Yes",182,Color8(0,170,0)],["No",238,Color8(170,0,0)]]:
		var x = item[1]
		surface.rect(x+2,77,24,9,Color.BLACK)
		surface.rect(x+1,78,26,7,Color.BLACK)
		surface.rect(x+1,76,24,9,item[2])
		surface.rect(x,77,26,7,item[2])
		surface.text(store,item[0],x+13-int(text_width(item[0])/2),77,Color.BLACK)
