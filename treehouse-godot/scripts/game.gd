extends Node2D
const Resources = preload("res://scripts/resources.gd")
const Surface = preload("res://scripts/surface.gd")
const ScrAnimation = preload("res://scripts/animation.gd")
const Room = preload("res://scripts/room.gd")
const Chalkboard = preload("res://scripts/chalkboard.gd")
const OriginalRandom = preload("res://scripts/random.gd")
const Resident = preload("res://scripts/resident.gd")
const Exterior = preload("res://scripts/exterior.gd")
const Music = preload("res://scripts/music.gd")
const MusicMaze = preload("res://scripts/music_maze.gd")
const Theater = preload("res://scripts/theater.gd")
const Nature = preload("res://scripts/nature.gd")
const Rewards = preload("res://scripts/rewards.gd")
const Telescope = preload("res://scripts/telescope.gd")
const BoardGame = preload("res://scripts/boardgame.gd")
const Preferences = preload("res://scripts/preferences.gd")
const Persistence = preload("res://scripts/persistence.gd")
const FileExchange = preload("res://scripts/file_exchange.gd")
const MazeTransition = preload("res://scripts/maze_transition.gd")
const RoomTransition = preload("res://scripts/room_transition.gd")
const Startup = preload("res://scripts/startup.gd")
const Presentation = preload("res://scripts/presentation.gd")
const TICK_HZ = 1193181.0 / 19886.0
var store
var surface = Surface.new()
var texture: ImageTexture
var presentation = Presentation.new()
var presentation_tick: int = -1
var audio: AudioStreamPlayer
var selection_audio: AudioStreamPlayer
var selection_music_active: bool = false
var fm_sound_id: int = -1
var audio_cache: Dictionary = {}
var prepared_samples: Dictionary = {}
var audio_serial: int = 0
var scene: String = "outside"
var character: String = "boy"
var tick: int = 0
var remainder: float = 0.0
var animations: Array = []
var entrance_queue: Array = []
var entrance_active
var entering: bool = false
var credit: int = 0
var credit_due: int = 600
var pointer = Vector2i(160,100)
var date_override: Dictionary = {}
var dirty: bool = true
var room
var chalk
var random = OriginalRandom.new()
var resident
var exterior
var music
var maze
var theater
var nature
var rewards
var telescope
var boardgame
var preferences
var persistence
var file_exchange
var persistence_enabled: bool = true
var persistence_path: String = "user://STATUS.DAT"
var save_due: int = 120
var pointer_control: bool = false
var travel: Dictionary = {}
var balloon = {"x":96,"y":43,"due":0,"lifting":false,"hidden":false,"state":1}
var held: Dictionary = {}
var pointer_keys: Dictionary = {}
var pointer_key_due: int = 0
var pointer_shift: bool = false
var pointer_visible: bool = true
var sound_events: Array = []
var capture_sound_events: bool = false
var audio_output_enabled: bool = true
var boot_enabled: bool = true
var startup

func now() -> Dictionary:
	return Time.get_datetime_dict_from_system() if date_override.is_empty() else date_override

func _ready() -> void:
	store = Resources.new()
	audio = AudioStreamPlayer.new()
	add_child(audio)
	selection_audio = AudioStreamPlayer.new()
	add_child(selection_audio)
	room = Room.new(self)
	chalk = Chalkboard.new(store)
	chalk.changed.connect(func():
		dirty = true
		if chalk.tool>=0:
			balloon.lifting = true
			balloon.due = tick+2)
	var fresh_profile = persistence_enabled and not FileAccess.file_exists(persistence_path) and not Persistence.has_legacy_profile(persistence_path)
	resident = Resident.new(self,not fresh_profile)
	chalk.returned.connect(func(): resident.schedule_ambient())
	exterior = Exterior.new(self)
	music = Music.new(self)
	maze = MusicMaze.new(self)
	theater = Theater.new(self,persistence_enabled)
	nature = Nature.new(self,persistence_enabled)
	rewards = Rewards.new(self)
	telescope = Telescope.new(self)
	boardgame = BoardGame.new(self,persistence_enabled)
	preferences = Preferences.new(self,persistence_enabled)
	persistence = Persistence.new(self,persistence_enabled,persistence_path)
	file_exchange = FileExchange.new(self)
	add_child(file_exchange)
	texture = ImageTexture.create_from_image(surface.image)
	presentation.presented.connect(present_frame)
	select_screen(not boot_enabled)
	if boot_enabled:
		scene = "title"
		startup = Startup.new(self)
	Input.mouse_mode = Input.MOUSE_MODE_HIDDEN
	get_viewport().mouse_exited.connect(func(): Input.mouse_mode = Input.MOUSE_MODE_VISIBLE)
	get_viewport().mouse_entered.connect(func(): Input.mouse_mode = Input.MOUSE_MODE_VISIBLE if file_exchange.active else Input.MOUSE_MODE_HIDDEN)
	render()

func reset_saved_session() -> void:
	# STATUS does not serialize live activities. Retain the separate song file.
	var songs = music.editor.export_data()
	release_inputs()
	if travel.has("effect"):
		travel.effect.dispose()
	travel.clear()
	for activity in [resident,music,maze,theater,nature,rewards,telescope,boardgame]:
		activity.dispose()
	room = Room.new(self)
	resident = Resident.new(self,false)
	exterior = Exterior.new(self)
	music = Music.new(self,false)
	music.editor.import_data(songs,false)
	music.editor.storage_enabled = persistence_enabled
	maze = MusicMaze.new(self)
	theater = Theater.new(self,false)
	nature = Nature.new(self,false)
	boardgame = BoardGame.new(self,false)
	for activity in [theater,nature,boardgame]:
		activity.storage_enabled = persistence_enabled
	rewards = Rewards.new(self)
	telescope = Telescope.new(self)
	preferences.kind = ""
	preferences.status.clear()
	preferences.background = null
	balloon.lifting = false
	prepared_samples.clear()
	chalk.bitmap.fill(Color.BLACK)

func animation(archive: String, id: int, palette: int, initialize: bool = true):
	var result = ScrAnimation.new(store,archive,id,palette,tick)
	result.sound_due = tick
	var reference = weakref(result)
	result.sound_requested.connect(func(sound):
		var active = reference.get_ref()
		if active!=null:
			active.sound_due = tick+play_sound(sound))
	if initialize:
		result.update(tick)
	return result

func play_sound(id: int) -> int:
	if store.data.fm_music.has(str(id)):
		return play_fm_music(id)
	var key = "digisnd:%d" % id
	if not store.data.pcm.has(key):
		key = "voices:%d" % id
	if not store.data.pcm.has(key):
		return 0
	return play_sample(key,int(store.data.pcm[key].rate))

func play_sample(key: String, requested_rate: int, finite: bool = false) -> int:
	prepared_samples[key] = true
	audio_serial += 1
	if not store.data.pcm.has(key):
		return 0
	var source = store.data.pcm[key]
	var quotient = int(1000000.0/requested_rate)
	var rate = int(1000000.0/quotient) if quotient>0 and quotient<256 else requested_rate
	var cache_key = "%s:%d:%s"%[key,rate,finite]
	if not audio_cache.has(cache_key):
		var original = store.data.pcm[key]
		var samples = Marshalls.base64_to_raw(original.pcm)
		for i in samples.size():
			samples[i] = (samples[i]+128)&255
		var stream = AudioStreamWAV.new()
		stream.format = AudioStreamWAV.FORMAT_8_BITS
		stream.mix_rate = rate
		stream.data = samples
		if original.loop and not finite:
			stream.loop_mode = AudioStreamWAV.LOOP_FORWARD
			stream.loop_begin = int(original.loop_start)
			stream.loop_end = int(original.loop_end)
		audio_cache[cache_key] = stream
	if audio_output_enabled and (preferences==null or preferences.settings.sound):
		# The original owns one digital voice, including repeated samples.
		audio.stop()
		audio.stream = audio_cache[cache_key]
		audio.play()
	var duration = int(ceil(audio_cache[cache_key].data.size()/float(rate)*TICK_HZ))
	if capture_sound_events:
		sound_events.append({"tick":tick,"key":key,"rate":rate,"duration":duration})
	return duration

func prepare_sound(key: String) -> int:
	if prepared_samples.has(key) or not store.data.pcm.has(key):
		return 0
	prepared_samples[key] = true
	return int(ceil(float(store.data.pcm[key].decode_cycles)*TICK_HZ/(1000.0*store.data.platform.cpu_cycles_per_millisecond)))

func start_selection_music() -> void:
	play_fm_music(20000)

func play_fm_music(id: int) -> int:
	stop_fm_music()
	var source = store.data.fm_music[str(id)]
	var stream = load(source.path).duplicate() as AudioStreamWAV
	assert(stream.format==AudioStreamWAV.FORMAT_16_BITS and not stream.stereo,"FM music must retain its source PCM format")
	stream.loop_mode = AudioStreamWAV.LOOP_FORWARD if source.loop else AudioStreamWAV.LOOP_DISABLED
	stream.loop_begin = 0
	stream.loop_end = stream.data.size()/2
	selection_audio.stream = stream
	fm_sound_id = id
	selection_music_active = id==20000
	selection_audio.volume_db = 0.0 if preferences.settings.sound else -INF
	if audio_output_enabled:
		selection_audio.play()
	# The rendered non-looping WAV includes a release tail; blocking gameplay
	# waits for the original sequencer EOT, not that extra rendering buffer.
	var duration = int(ceil(float(source.end_irq)*4971.0/1193182.0*TICK_HZ))
	if capture_sound_events:
		sound_events.append({"tick":tick,"key":"midisnd:%d"%id,"rate":48000,"duration":duration})
	return duration

func stop_selection_music() -> void:
	if fm_sound_id==20000:
		stop_fm_music()

func stop_fm_music() -> void:
	fm_sound_id = -1
	selection_music_active = false
	if selection_audio!=null:
		selection_audio.stop()
		selection_audio.stream = null

func stop_all_sound() -> void:
	audio.stop()
	stop_fm_music()

func select_screen(with_music: bool = true) -> void:
	if resident!=null:
		resident.selected = false
	if room!=null:
		room.leave()
		chalk.select(-1)
		release_inputs()
	scene = "outside"
	entering = false
	entrance_active = null
	entrance_queue.clear()
	credit = 0
	credit_due = tick+600
	animations = [animation("th",8000,8000),animation("th",8001,8001)]
	for item in animations:
		item.done = true
	if with_music:
		start_selection_music()
	dirty = true

func enter(who: String) -> void:
	if entering or scene != "outside":
		return
	character = who
	entering = true
	var selected = 0 if who == "boy" else 1
	entrance_queue = [[selected,8000+selected],[1-selected,8001-selected],[selected,8002+selected]]
	next_entrance()

func next_entrance() -> void:
	if entrance_queue.is_empty():
		set_scene("inside")
		return
	var entry = entrance_queue.pop_front()
	entrance_active = animation("th",entry[1],8000+entry[0])
	animations[entry[0]] = entrance_active
	dirty = true

func set_scene(next: String) -> void:
	if rewards.active:
		if rewards.phase!="choose":
			rewards.interrupt()
			return
		rewards.active = false
		rewards.sprite = null
	# Original A83 stops selection music after the three child scripts finish.
	stop_fm_music()
	if scene=="nature":
		nature.end_drag()
		nature.save()
	if scene=="boardgame":
		boardgame.save()
	if scene=="theater":
		theater.end_drag(true)
		theater.save()
		theater.stop()
	if scene=="maze":
		if maze.phase=="win":
			maze.replace_song()
		maze.cancel()
		maze.started = false
	if scene=="music":
		music.leave()
	room.leave()
	release_inputs()
	chalk.select(-1)
	chalk.returned_color = null
	scene = next
	animations.clear()
	entering = false
	entrance_active = null
	if next=="inside":
		room.enter(tick)
		balloon.due = tick+48
	if next in ["inside","outside"]:
		resident.enter_scene()
	if next=="outside":
		exterior.enter_yard()
	elif next=="hollow":
		exterior.enter_hollow()
	elif next=="music":
		music.enter()
	elif next=="maze":
		maze.tick = tick
		if not maze.started:
			maze.reset(true)
	elif next=="theater":
		theater.tick = tick
	elif next=="nature":
		nature.tick = tick
		nature.interact()
	elif next=="telescope":
		telescope.enter()
	elif next=="boardgame":
		boardgame.enter()
	dirty = true

func navigate_scene(next: String) -> void:
	if scene=="telescope" and telescope.interrupt():
		return
	if rewards.active:
		rewards.dismiss()
		return
	if not travel.is_empty():
		if travel.has("effect"):
			travel.effect.interrupt()
		resident.interrupt_audio()
		return
	if scene=="theater" and not theater.exit_ready:
		theater.leave(func(): navigate_scene(next))
		return
	if scene=="nature" and (nature.erase_task or (nature.mode=="quiz" and nature.quiz.interrupt_wait())):
		return
	if (scene=="music" and next=="maze") or (scene=="maze" and next=="music"):
		var returning = scene=="maze"
		music.stop()
		release_inputs()
		music.performance = null
		if returning:
			set_scene("music")
		travel = {"next":next,"returning":returning,"phase":"effect","maze":true,"effect":MazeTransition.new(self,returning)}
		return
	if scene=="maze" and next=="inside":
		set_scene("inside")
		travel = {"next":"inside","returning":true,"phase":"prepare"}
		update_travel()
		return
	if entering or resident.interrupt_audio() or exterior.interrupt_audio() or room.interrupt_audio():
		return
	if resident.busy or exterior.busy or (scene=="inside" and room.busy):
		return
	if scene=="inside" and next in ["music","nature","theater","boardgame","telescope"]:
		if resident.pose==4:
			resident.wake(true,func(): navigate_scene(next))
			return
		release_inputs()
		travel = {"next":next,"returning":false,"phase":"prepare","variant":["music","nature","theater","boardgame"].find(next),"telescope":next=="telescope"}
		if next=="telescope":
			resident.action(19)
		else:
			resident.center()
		update_travel()
		return
	if scene in ["music","nature","theater","boardgame","telescope"] and next=="inside":
		var from_telescope = scene=="telescope"
		var variant = ["music","nature","theater","boardgame"].find(scene)
		set_scene("inside")
		travel = {"next":"inside","returning":true,"phase":"prepare","variant":variant,"telescope":from_telescope}
		if from_telescope:
			resident.action(28)
		update_travel()
		return
	set_scene(next)

func update_travel() -> void:
	if travel.phase=="prepare":
		if not travel.returning or travel.get("telescope",false):
			resident.update(tick)
			if resident.busy:
				return
		if travel.get("telescope",false):
			if travel.returning:
				travel = {}
			else:
				travel.phase = "pause"
				travel.due = tick+60
			return
		travel.phase = "effect"
		travel.effect = RoomTransition.new(self,travel.get("variant",0),travel.returning)
	elif travel.phase=="pause":
		if tick>=travel.due:
			var next = travel.next
			travel = {}
			set_scene(next)
	else:
		travel.effect.update(tick)
		if travel.effect.done:
			var pending = travel
			pending.effect.dispose()
			travel = {}
			if pending.get("maze",false):
				if pending.returning:
					music.idle_due = tick+600
				else:
					set_scene("maze")
			elif pending.returning:
				for name in ["hunger","fatigue"]:
					if resident.get(name)>=3 and ScrAnimation.wrap32((int(resident.get(name+"_due"))-tick)<<16)>>16<600:
						resident.set(name+"_due",tick+600)
			else:
				set_scene(pending.next)
				if pending.next=="theater":
					theater.enter()

func advance(count: int = 1) -> void:
	for i in count:
		if presentation_tick!=tick:
			render()
		presentation.advance_to((tick+1)*1000.0/TICK_HZ,false)
		advance_tick()
		render()

func advance_tick() -> void:
	tick += 1
	if scene=="title":
		startup.update(tick)
		return
	keyboard_pointer()
	if preferences.active:
		preferences.update(tick)
		return
	if not travel.is_empty():
		update_travel()
		return
	if rewards.active:
		rewards.update(tick)
		return
	if scene=="telescope":
		telescope.update(tick)
		return
	if scene=="boardgame":
		boardgame.update(tick)
		resident.update(tick)
		return
	if scene=="music":
		music.update(tick)
		return
	if scene=="maze":
		maze.update(tick)
		return
	if scene=="theater":
		theater.update(tick)
		return
	if scene=="nature":
		nature.update(tick)
		resident.update(tick)
		return
	if scene=="inside" and room.question=="asking":
		return
	if scene=="inside":
		service_balloon()
		room.update(tick,resident.busy)
	resident.update(tick)
	if scene in ["outside","hollow"]:
		exterior.update(tick)
	if scene == "outside" and not resident.selected and not entering and tick >= credit_due:
		credit = (credit+1)%8
		credit_due = tick+(600 if credit==0 else 360)
	for item in animations:
		item.update(tick)
	if entering and entrance_active.done:
		next_entrance()

func _process(delta: float) -> void:
	if file_exchange.active:
		return
	remainder += delta*TICK_HZ
	var ticks = int(remainder)
	if ticks:
		remainder -= ticks
		advance(ticks)
	if dirty:
		render()
	presentation.advance_to((tick+remainder)*1000.0/TICK_HZ)
	if persistence.storage_enabled and tick>=save_due:
		save_due = tick+120
		persistence.save()

func _input(event: InputEvent) -> void:
	if scene=="title":
		if (event is InputEventKey and event.pressed and not event.echo) or (event is InputEventMouseButton and event.pressed) or (event is InputEventScreenTouch and event.pressed):
			startup.finish()
		return
	if file_exchange.input(event):
		return
	if event is InputEventMouseMotion:
		pointer_visible = true
		move_pointer(Vector2i(get_global_mouse_position()))
	elif event is InputEventMouseButton and event.button_index == MOUSE_BUTTON_LEFT:
		pointer_visible = true
		pointer_input("mouse",event.pressed,Vector2i(get_global_mouse_position()))
	elif event is InputEventScreenTouch:
		pointer_visible = false
		pointer_input("touch:%d" % event.index,event.pressed,Vector2i(event.position))
	elif event is InputEventScreenDrag:
		move_pointer(Vector2i(event.position))
	elif event is InputEventKey:
		if preferences.key_input(event):
			dirty = true
			return
		if rewards.active:
			if event.pressed and not event.echo:
				if event.keycode==KEY_ESCAPE:
					rewards.dismiss()
				else:
					rewards.interrupt()
			return
		pointer_control = event.ctrl_pressed
		if not preferences.active and scene=="music" and travel.is_empty() and music.key_input(event):
			dirty = true
			return
		pointer_shift = event.shift_pressed
		if event.keycode in [KEY_LEFT,KEY_RIGHT,KEY_UP,KEY_DOWN,KEY_KP_5]:
			if event.pressed and not pointer_keys.has(event.keycode):
				pointer_keys[event.keycode] = true
				pointer_key_due = tick
				keyboard_pointer()
			elif not event.pressed:
				pointer_keys.erase(event.keycode)
		elif event.keycode in [KEY_ENTER,KEY_SPACE] and not event.echo:
			pointer_input(str(event.keycode),event.pressed,pointer)
		elif event.pressed and not event.echo and event.keycode==KEY_ESCAPE and not entering:
			if scene=="boardgame":
				if not boardgame.motion.busy:
					navigate_scene("inside")
			elif scene=="nature":
				if not nature.dialog.is_empty():
					nature.answer_dialog(false)
				elif nature.print_view!=null:
					nature.print_view = null
				elif nature.mode=="quiz":
					nature.leave_quiz()
				else:
					navigate_scene("inside")
			elif scene=="maze":
				if maze.chooser:
					maze.close_guess()
				else:
					navigate_scene("music")
			elif scene=="inside" and room.question=="asking":
				room.answer_chalk(pointer)
			else:
				if scene in ["inside","hollow","music","theater","telescope"]:
					navigate_scene("inside" if scene in ["music","theater","telescope"] else "outside")

func pointer_input(owner: String, pressed: bool, point: Vector2i) -> void:
	if pressed:
		held[owner] = true
		activate(point,owner)
	else:
		held.erase(owner)
		if nature!=null:
			nature.end_drag()
		if theater!=null:
			theater.end_drag()
		if music!=null:
			music.note_up(owner)
			music.editor.end()
		chalk.end()
		resident.end()

func release_inputs() -> void:
	if nature!=null:
		nature.end_drag()
	pointer_control = false
	if theater!=null:
		theater.end_drag(true)
	if music!=null:
		music.release_all()
		music.editor.end(true)
	held.clear()
	pointer_keys.clear()
	pointer_shift = false
	if resident!=null:
		resident.end(true)
	if chalk!=null:
		chalk.end()
	if audio!=null:
		audio.stop()

func _notification(what: int) -> void:
	# Web canvas/window blur is a window notification, not application focus.
	if what in [NOTIFICATION_APPLICATION_FOCUS_OUT,NOTIFICATION_WM_WINDOW_FOCUS_OUT]:
		release_inputs()
		if persistence!=null:
			persistence.save()

func _exit_tree() -> void:
	stop_fm_music()
	if startup!=null:
		startup.dispose()
	if persistence!=null:
		persistence.save()
	if resident!=null:
		resident.dispose()
	if music!=null:
		music.dispose()
	if maze!=null:
		maze.dispose()
	if theater!=null:
		theater.dispose()
	if nature!=null:
		nature.dispose()
	if rewards!=null:
		rewards.dispose()
	if telescope!=null:
		telescope.dispose()
	if boardgame!=null:
		boardgame.dispose()
	if travel.has("effect"):
		travel.effect.dispose()

func move_pointer(point: Vector2i) -> void:
	pointer = point
	if preferences.active:
		dirty = true
		return
	if scene=="nature":
		nature.move_drag(point)
		dirty = true
		return
	if scene=="theater":
		theater.move_drag(point)
		dirty = true
		return
	if scene=="music":
		music.move(point)
		dirty = true
		return
	if resident.move(point):
		dirty = true
		return
	if scene=="inside":
		pointer = chalk.move(point,not held.is_empty())
	dirty = true

func keyboard_pointer() -> void:
	if tick<pointer_key_due:
		return
	var dx = 1 if pointer_keys.has(KEY_RIGHT) else -1 if pointer_keys.has(KEY_LEFT) else 0
	var dy = 1 if pointer_keys.has(KEY_DOWN) or pointer_keys.has(KEY_KP_5) else -1 if pointer_keys.has(KEY_UP) else 0
	if dx==0 and dy==0:
		return
	pointer_visible = true
	pointer_key_due = tick+(1 if pointer_shift else 3+(5 if held.has(str(KEY_SPACE)) else 0))
	move_pointer(Vector2i(clampi(pointer.x+dx,0,319),clampi(pointer.y+dy,0,199)))

func activate(point: Vector2i, owner: String = "mouse") -> void:
	pointer = point
	if preferences.active:
		preferences.click(point)
		return
	if rewards.active:
		rewards.click(point)
		dirty = true
		return
	if not travel.is_empty():
		navigate_scene(scene)
		return
	if scene=="telescope":
		telescope.click(point)
		dirty = true
		return
	if scene=="boardgame":
		if point.x>=304 and point.y<23:
			navigate_scene("inside")
		else:
			boardgame.click(point)
		dirty = true
		return
	if scene=="nature":
		if nature.mode=="quiz" and nature.quiz.interrupt_wait():
			return
		if not nature.dialog.is_empty() or nature.print_view!=null:
			nature.click(point,pointer_control)
		elif point.x>=304 and point.y<23:
			navigate_scene("inside")
		elif not nature.begin_drag(point):
			nature.click(point,pointer_control)
		dirty = true
		return
	if scene=="theater":
		if point.x>=304 and point.y<23:
			navigate_scene("inside")
		elif not theater.begin_drag(point):
			theater.click(point)
		dirty = true
		return
	if scene=="maze":
		maze.click(point)
		return
	if scene=="music":
		music.click(point,owner)
		dirty = true
		return
	if resident.interrupt_audio() or exterior.interrupt_audio() or room.interrupt_audio():
		return
	if scene == "outside" and not entering:
		if resident.selected and not exterior.busy and resident.begin(point):
			return
		exterior.click_yard(point)
	elif scene=="hollow":
		exterior.click_hollow(point)
	elif scene=="inside":
		room_click(point)
	dirty = true

func hit(point: Vector2i, x: int, y: int, w: int, h: int) -> bool:
	return Rect2i(x,y,w,h).has_point(point)

func room_click(point: Vector2i) -> void:
	if room.question=="asking":
		room.answer_chalk(point)
		return
	if resident.interrupt_food():
		return
	if room.interrupt_audio() or room.busy or resident.busy:
		return
	stop_all_sound()
	if resident.begin(point):
		return
	if room.is_open and hit(point,162,28,121,82):
		room.toggle()
	elif hit(point,int(resident.rect()[1])+4,int(resident.rect()[0])+4,int(resident.rect()[3]-resident.rect()[1])-8,int(resident.rect()[2]-resident.rect()[0])-8):
		resident.click_character()
	elif hit(point,150,162,47,12) and resident.pose!=0:
		resident.center()
	elif hit(point,4,27,37,35):
		resident.speak_status()
	elif hit(point,160,20,123,20):
		if not room.is_open:
			room.toggle()
	elif hit(point,132,21,22,17):
		room.browse(-1 if point.x-132<38-point.y else 1)
	elif hit(point,58,24,76,11):
		room.read_calendar()
	elif hit(point,163,40,120,40):
		room.next_cloud()
		play_sound(1044)
	elif hit(point,92,108,22,10):
		room.say_time({},false,func(): resident.schedule_ambient())
	elif hit(point,118,129,27,17):
		play_sound(1013)
	elif hit(point,21,6,33,21):
		room.interact("spider")
	elif hit(point,237,81,23,13):
		room.interact("chirp")
	elif hit(point,211,81,72,23):
		room.interact("nest")
	elif hit(point,286,15,32,76):
		if resident.pose==4:
			room.play_home_music()
		else:
			resident.action(31)
	elif hit(point,2,120,34,36):
		if resident.wake_time.is_empty():
			room.say([11028])
		else:
			room.say_time(resident.wake_time,true)
	elif fruit_at(point):
		return
	elif hit(point,242,177,63,23):
		navigate_scene("outside")
	elif hit(point,7,175,99,25):
		navigate_scene("music")
	elif hit(point,138,181,85,19):
		navigate_scene("boardgame")
	elif theater.hit(theater.tables.room_entrance,point):
		navigate_scene("theater")
	elif hit(point,122,99,25,20):
		navigate_scene("nature")
	elif hit(point,167,102,61,55):
		navigate_scene("telescope")
	elif hit(point,49,86,10,11):
		room.ask_chalk()
	elif point.y>=92 and point.y<98:
		var tool = int(floor((point.x-63)/12.0))
		if tool>=0 and tool<7 and point.x<(149 if tool==6 else 73+12*tool):
			chalk.select(tool)
		elif chalk.tool>=0 and hit(point,52,40,105,57):
			chalk.begin(point)
	elif chalk.tool>=0 and hit(point,52,40,105,57):
		chalk.begin(point)

func service_balloon() -> void:
	if room.busy or resident.busy or not resident.drag.is_empty() or balloon.hidden or (tick<balloon.due if balloon.lifting else tick<=balloon.due):
		return
	if balloon.lifting:
		if balloon.x<157 and balloon.x+29>52 and balloon.y<99 and balloon.y+38>38:
			balloon.y -= 2
			balloon.due = tick+2
		else:
			balloon.lifting = false
			balloon.due = tick+48
	elif chalk.tool<0:
		var dx = pointer.x-(balloon.x+14)
		var dy = mini(pointer.y,100)-(balloon.y+19)
		var ax = abs(dx)
		var ay = abs(dy)
		if ax>=2:
			balloon.x += int(sign(dx))*(2 if ax>ay else 1)
		if ay>=2:
			balloon.y += int(sign(dy))*(2 if ay>=ax else 1)
		balloon.due = tick+48

func render() -> void:
	if scene=="title":
		startup.draw(surface)
		commit_frame()
		dirty = false
		return
	if travel.has("effect"):
		travel.effect.draw(surface)
	elif scene=="music":
		music.draw(surface)
	elif scene=="maze":
		maze.draw(surface)
	elif scene=="theater":
		theater.draw(surface)
	elif scene=="nature":
		nature.draw(surface)
	elif scene=="telescope":
		telescope.draw(surface)
	elif scene=="boardgame":
		boardgame.draw(surface)
	elif scene == "outside":
		draw_outside()
	elif scene=="hollow":
		exterior.draw_hollow(surface)
	else:
		draw_inside()
		room.draw_question(surface)
	if scene in ["inside","outside"] and resident.selected and travel.is_empty():
		if resident.object_animation!=null:
			resident.object_animation.draw(surface)
		resident.tasks.draw(surface)
	rewards.draw(surface)
	preferences.draw(surface)
	if preferences.active:
		if pointer_visible:
			draw_pointer()
	elif pointer_visible and (travel.is_empty() or (travel.has("effect") and not travel.effect.hide_pointer)) and not entering and resident.active==null and resident.object_animation==null and not resident.tasks.running and exterior.actor==null and exterior.window==null and not (scene=="inside" and (room.environment!=null or room.chirp_until>tick)):
		if (scene!="theater" or not theater.hide_cursor) and (scene!="nature" or not nature.hide_cursor) and (scene!="telescope" or not telescope.busy):
			draw_pointer()
	commit_frame()
	dirty = false

func commit_frame() -> void:
	var milliseconds = tick*1000.0/TICK_HZ
	# Explicit test/session clock changes start a new scanout; normal gameplay
	# advances continuously one logical tick at a time.
	if presentation_tick<0 or tick<presentation_tick or tick>presentation_tick+1:
		presentation.reset(milliseconds,surface.image)
		present_frame(presentation.image,milliseconds)
	else:
		presentation.commit(maxf(milliseconds,presentation.time_ms),surface.image)
	presentation_tick = tick

func present_frame(frame: Image, _milliseconds: float) -> void:
	texture.update(frame)
	queue_redraw()

func _draw() -> void:
	if texture:
		draw_texture(texture,Vector2.ZERO)

func draw_outside() -> void:
	surface.draw(store,"th64",1,0,0,0,2)
	if resident.selected:
		exterior.draw_yard(surface)
		return
	surface.draw(store,"th64",2,0,2,0)
	surface.draw(store,"th64",3,0,0,109)
	var positions = [[12,60],[12,55],[10,52],[10,52],[10,52],[26,50],[24,49],[27,57]]
	surface.blit(store.raster(store.shape("th",10+credit),[[0,0,0],[0,0,0]],true),positions[credit][0],positions[credit][1])
	# Finished character slots are below the one currently moving.
	for item in animations:
		if item.done:
			item.draw(surface)
	for item in animations:
		if not item.done:
			item.draw(surface)

func draw_inside(character_visible: bool = true, curtain_visible: bool = true) -> void:
	surface.draw(store,"th64",5,4,0,0,2)
	chalk.draw(surface)
	room.draw_cloud(surface)
	room.draw_portrait(surface)
	for item in [[1109,1100,49,121],[1256,1250,211,84],[1251,1250,211,81],[1228,1200,132,21],[926,900,151,182],[919,900,236,117]]:
		if item[0]==1109 and not curtain_visible:
			continue
		surface.draw(store,"th",item[0],item[1],item[2],item[3])
	room.draw_date_clock(surface)
	room.draw_calendar(surface)
	var colors = [Color.WHITE,Color.RED,Color8(247,247,32),Color8(101,4,255),Color8(8,170,0),Color8(255,199,199)]
	for i in 6:
		surface.rect(63+12*i,93,10,2,colors[i])
	surface.rect(135,92,14,3,Color.BLACK)
	surface.rect(136,92,12,1,Color.WHITE)
	surface.rect(136,93,12,2,Color8(170,170,170))
	chalk.draw_tray(surface)
	surface.rect(4,140,30,13,Color.WHITE)
	resident.draw_nap(surface)
	resident.draw_objects(surface,true)
	if character_visible:
		resident.draw(surface)
	resident.draw_objects(surface,true,true)
	room.draw_environment(surface)

func fruit_at(point: Vector2i) -> bool:
	for type in range(17,21):
		if resident.hit(resident.tables.objects[type].inside,point):
			resident.fruit(type,point)
			return true
	return false

func draw_pointer() -> void:
	var data: Array = store.data.cursor
	var foreground = Color8(255,255,85)
	if not preferences.active and scene=="theater" and theater.busy_cursor:
		data = Array(Marshalls.base64_to_raw(store.data.raw["th:CURS:1"]))
	if not preferences.active and scene=="maze" and maze.loading_sound:
		data = Array(Marshalls.base64_to_raw(store.data.raw["th:CURS:1"]))
	if not preferences.active and scene=="music":
		foreground = music.editor.cursor_color
		if music.editor.eraser:
			var rgb = store.palette("modules",2200).colors[12]
			foreground = Color8(rgb[0],rgb[1],rgb[2])
			data = Array(Marshalls.base64_to_raw(store.data.raw["th:CURS:2"]))
	if not preferences.active and scene=="inside":
		if chalk.tool>=0:
			foreground = Color.WHITE if chalk.tool==6 else chalk.colors[chalk.tool]
			data = Array(Marshalls.base64_to_raw(store.data.raw["th:CURS:%d" % (4 if chalk.tool==6 else 3)]))
		elif chalk.returned_color!=null:
			foreground = chalk.returned_color
		elif not room.pending_environment.is_empty():
			data = Array(Marshalls.base64_to_raw(store.data.raw["th:CURS:1"]))
	var music_eraser = not preferences.active and scene=="music" and music.editor.eraser
	var x = pointer.x-ScrAnimation.s16(data,2 if music_eraser else 0)
	var y = pointer.y-ScrAnimation.s16(data,0 if music_eraser else 2)
	for row in 16:
		for col in 16:
			if not (ScrAnimation.u16(data,4+row*2)&(0x8000>>col)):
				var color = foreground if ScrAnimation.u16(data,36+row*2)&(0x8000>>col) else Color.BLACK
				surface.rect(x+col,y+row,1,1,color)
