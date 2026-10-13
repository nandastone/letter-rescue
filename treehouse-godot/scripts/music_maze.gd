extends RefCounted
## Overlay 1: generated challenges and tick-suspended maze choreography.
var host
var store
var t: Dictionary
var music: Dictionary
var history: Array = []
var type_history: Array = [0,0]
var pattern_history: Array = [[0,0],[0,0],[0,0],[0,0]]
var family_history: int = 0
var supported_types: int = 4
var first_timbre: bool = true
var songs: Array = []
var saved_songs: Array = []
var secret: int = 0
var departure_song: int = -1
var started: bool = false
var introduced: bool = false
var round_replaced: bool = false
var round_prepared: bool = false
var initial_advanced: bool = false
var hard: bool = false
var phase: String = ""
var node: int = 0
var earned: int = 0
var streak: int = 0
var excluded: int = 2
var type: int = 0
var correct: int = 0
var choices: Array = [0,0,0,0]
var wrong: Array = []
var wrong_count: int = 0
var eliminated: Array = []
var guess_locked: bool = false
var feedback: int = -1
var hint: bool = false
var actor: Array = [0,0]
var actor_animation: int = 3
var actor_frame: int = 0
var frog: bool = false
var frog_point: Array = [150,130]
var frog_animation: int = 3
var frog_frame: int = 0
var point_sprite: Dictionary = {}
var large_intro: bool = false
var intro_node: int = -1
var player_visible: bool = true
var revealed_signs: int = 4
var tutoring: bool = false
var walking: bool = false
var loading_sound: bool = false
var accelerate: bool = false
var dim_other: int = -1
var roller: int = -1
var falling: Dictionary = {}
var landed: int = -1
var chooser: bool = false
var drawer_y: int = -1
var drawer_slots: Array = []
var guess_highlight: int = -1
var question_blank: bool = false
var control_flash: int = -1
var replaying: bool = false
var automatic_listening: bool = false
var dismiss_after_motion: bool = false
var current_event: Dictionary = {}
var audio_queue: Array = []
var audio_due: int = 0
var voice: bool = false
var voice_serial: int = -1
var target_due: int = 0
var hint_due: int = 0
var steps: Array = []
var motion_due: int = 0
var running: bool = false
var revision: int = 0
var tick: int = 0
var mirrors: Dictionary = {}
var active_song: int:
	get: return departure_song if departure_song>=0 else int(songs[secret])
var song: Array:
	get: return store.data.songs["modules:%d"%active_song]
var title: String:
	get: return store.data.strings["modules:101"][active_song]
var busy: bool:
	get: return running
var can_guess: bool:
	get: return earned>0 and not guess_locked and phase=="play" and not busy

func _init(game) -> void:
	host = game
	store = host.store
	t = integers(store.data.music.maze)
	music = store.data.music

static func integers(value):
	if value is Array:
		return value.map(integers)
	if value is Dictionary:
		var result = {}
		for key in value:
			result[key] = integers(value[key])
		return result
	return int(value) if typeof(value)==TYPE_FLOAT else value

func pick(count: int) -> int:
	return host.random.pick(count-1)

func cycle(mask: int, count: int, exclude: int = 0) -> Array:
	mask |= exclude
	var start = pick(count)
	var choice = start
	while mask&(1<<choice):
		choice = (choice+1)%count
		if choice==start:
			mask = exclude
	return [choice,mask|(1<<choice)]

func replace_song() -> void:
	if round_replaced or songs.is_empty():
		return
	for id in songs:
		if id not in history:
			history.append(id)
	if history.size()==24:
		history = songs.duplicate()
	var id = pick(24)
	while id in history:
		id = pick(24)
	history.append(id)
	songs[secret] = id
	round_replaced = true

func setup_round() -> void:
	departure_song = -1
	secret = pick(6)
	eliminated = []
	earned = 0
	streak = 0
	node = pick(9)
	excluded = 2
	phase = "play"
	actor = t.centers[node].duplicate()
	actor_animation = 3
	actor_frame = 0
	challenge(true)
	round_prepared = true
	intro_node = node

func difficulty(value: bool) -> void:
	initial_advanced = value
	hard = value

func reset(entry: bool = false) -> void:
	if phase=="win":
		replace_song()
	cancel()
	roller = -1
	falling = {}
	landed = -1
	dim_other = -1
	guess_highlight = -1
	if not saved_songs.is_empty():
		songs = saved_songs.duplicate()
		saved_songs.clear()
		for id in songs:
			if id not in history:
				history.append(id)
	elif songs.is_empty():
		while songs.size()<6:
			var id = pick(24)
			while id in history:
				id = pick(24)
			history.append(id)
			songs.append(id)
	if not started:
		hard = initial_advanced
	started = true
	round_replaced = false
	round_prepared = false
	earned = 0
	frog = false
	if entry or not introduced:
		var tutor = not introduced
		introduced = true
		run([invoke("introduction",[tutor])])
	else:
		setup_round()
		run([invoke("round_entry")])

func cancel() -> void:
	stop_voice()
	host.stop_fm_music()
	audio_queue = []
	steps = []
	running = false
	revision += 1
	chooser = false
	drawer_y = -1
	drawer_slots = []
	question_blank = false
	current_event = {}
	tutoring = false
	walking = false
	loading_sound = false
	accelerate = false
	dismiss_after_motion = false
	automatic_listening = false
	point_sprite = {}
	large_intro = false
	player_visible = true
	revealed_signs = 4
	frog_point = [150,130]
	frog_animation = 3
	frog_frame = 0

func ambiguous(a: int, b: int) -> bool:
	return a==b or ([20,21].has(a) and [20,21].has(b)) or ([13,11].has(a) and [13,11].has(b)) or ([17,7].has(a) and [17,7].has(b))

func challenge(first: bool = false) -> void:
	wrong = []
	wrong_count = 0
	guess_locked = false
	feedback = -1
	hint = false
	actor_animation = 3
	actor_frame = 0
	var level = int(hard)
	correct = pick(4)
	while correct==excluded:
		correct = pick(4)
	excluded = t.opposite_direction[correct]
	var exclude = 0
	for i in supported_types:
		exclude |= int(not t.enabled_types[level][i])<<i
	if first:
		type = 4 if first_timbre else (2 if hard else 1)
	else:
		var result = cycle(type_history[level],supported_types,exclude)
		type = result[0]
		type_history[level] = result[1]
	type_history[0] |= 1<<type
	type_history[1] |= 1<<type
	choices = [0,0,0,0]
	if type==4:
		var families = integers(music.followup.members)
		if hard:
			var a = pick(7)
			var b = pick(7)
			while a==b:
				b = pick(7)
			for pair in [[a,0],[b,1]]:
				var members = families[pair[0]]
				var d = int(pair[1])
				choices[d] = members[pick(members.size())]
				var value = members[pick(members.size())]
				while ambiguous(choices[d],value):
					value = members[pick(members.size())]
				choices[d+2] = value
		else:
			var result = cycle(family_history,7)
			var family = result[0]
			family_history = result[1]
			choices[correct] = families[family][pick(families[family].size())]
			var used = [family]
			for d in 4:
				if d==correct:
					continue
				family = pick(7)
				while family in used:
					family = pick(7)
				used.append(family)
				choices[d] = families[family][pick(families[family].size())]
	else:
		var key = ["rhythm_sets","pitch_sets","melody_sets","accidental_sets"][type]
		var sets = t[key][level] if type==3 else t[key]
		var result = cycle(pattern_history[type][level],t.challenge_set_counts[level][type])
		pattern_history[type][level] = result[1]
		var answers = sets[result[0]]
		var used: Array = []
		choices[correct] = answers[0]
		for d in 4:
			if d==correct:
				continue
			var i = 1+pick(3)
			while i in used:
				i = 1+pick(3)
			used.append(i)
			choices[d] = answers[i]
	reset_idle()

func reset_idle() -> void:
	target_due = tick+360
	hint_due = tick+900

func sample_ticks(key: String) -> int:
	var sample = store.data.pcm[key]
	var q = int(1000000.0/sample.rate)
	var rate = int(1000000.0/q) if q>0 and q<256 else int(sample.rate)
	return int(ceil(Marshalls.base64_to_raw(sample.pcm).size()/float(rate)*host.TICK_HZ))

func candidate_events(direction: int, visible: bool = false) -> Array:
	var member = choices[direction]
	if type==4:
		return [{"pitch":9,"instrument":member,"finite":true,"ticks":sample_ticks("voices:%d"%int(music.instruments[member].sound_id))}]
	var pitches = [9,9,9] if type==0 else t[["","pitch_patterns","melody_patterns","accidental_patterns"][type]][member]
	var result: Array = []
	for i in pitches.size():
		result.append({"pitch":pitches[i],"instrument":9,"ticks":t.sound_ticks[t.rhythm_patterns[member][i]] if type==0 else 25,"sign":direction if visible else -1,"note":i})
	return result

func melody(full: bool = false, raw: Array = []) -> Array:
	if raw.is_empty():
		raw = song
	var result: Array = []
	for i in (int(raw[1]) if full else earned):
		var pitch = int(raw[5+2*i])&127
		if pitch!=127:
			result.append({"pitch":pitch,"rest":raw[6+2*i]>=8,"instrument":9,"score_index":i,"ticks":int(music.tempo_factors[int(raw[2])])*int(music.duration_factors[int(raw[6+2*i])])})
	return result

func intro_melody(slot: int) -> Array:
	var raw = store.data.songs["modules:%d"%int(songs[slot])].duplicate()
	raw[1] = raw[0]
	return melody(true,raw)

func sequence(events: Array) -> int:
	stop_voice()
	current_event = {}
	audio_queue = events.duplicate()
	audio_due = tick
	step_audio()
	var duration = 0
	for event in events:
		duration += int(event.ticks)
	return duration

func step_audio() -> void:
	if tick<audio_due:
		return
	stop_voice()
	current_event = {} if audio_queue.is_empty() else audio_queue.pop_front()
	if not current_event.is_empty():
		if not current_event.get("rest",false):
			var id = int(music.instruments[int(current_event.instrument)].sound_id)
			host.play_sample("voices:%d"%id,int(music.playback_rates[int(current_event.pitch)]),current_event.get("finite",false))
			voice = true
			voice_serial = host.audio_serial
		audio_due = tick+int(current_event.ticks)

func stop_voice() -> void:
	if voice and voice_serial==host.audio_serial:
		host.audio.stop()
	voice = false

func sound(id: int) -> void:
	host.play_sound(id)

func frog_voice() -> void:
	sound(20100+pick(4))

func state(values: Dictionary) -> Dictionary:
	return {"state":values}

func invoke(method: String, args: Array = []) -> Dictionary:
	return {"method":method,"args":args}

func play(events: Array) -> Dictionary:
	return {"audio":events}

func run(operations: Array) -> void:
	steps = operations
	motion_due = tick
	running = true
	revision += 1
	update(tick)

func update_motion() -> void:
	var version = revision
	for budget in 100000:
		if steps.is_empty():
			running = false
			return
		var op = steps.pop_front()
		if op is int:
			motion_due = tick+maxi(1,op)
			return
		if op.has("state"):
			for key in op.state:
				set(key,op.state[key])
		elif op.has("method"):
			var result = callv(op.method,op.args)
			if revision!=version:
				return
			if result is Array:
				steps = result+steps
		elif op.has("audio"):
			# Overlay 1:97C9 shows the busy cursor around instrument loading.
			# Audition 3BEF and notation playback prepare their instrument before
			# starting any sample. Reuse the shared decoded-sample cache/work.
			if not op.audio.is_empty():
				var instrument = int(op.audio[0].instrument)
				var key = "voices:%d"%int(music.instruments[instrument].sound_id)
				var delay = host.prepare_sound(key)
				if delay>0:
					loading_sound = true
					steps = [delay,state({"loading_sound":false}),op]+steps
					continue
			motion_due = tick+maxi(1,sequence(op.audio))
			return
		elif op.has("walk_delay") and not accelerate:
			motion_due = tick+maxi(1,op.walk_delay)
			return
	assert(false,"Maze operation failed to yield")

func update(now: int) -> void:
	tick = now
	if (not audio_queue.is_empty() or voice) and tick>=audio_due:
		step_audio()
	if running and tick>=motion_due:
		update_motion()
	if not busy and dismiss_after_motion:
		dismiss_after_motion = false
		if chooser:
			close_guess()
	if not busy and phase=="win" and tick>=hint_due:
		run([invoke("win_hint")])
	if not busy and phase=="play" and not chooser:
		if tick>=hint_due:
			run([invoke("idle_hint")])
		elif tick>=target_due:
			hear_target(true)

func listen(events: Array, replay: bool = false, automatic: bool = false) -> Array:
	return [state({"automatic_listening":automatic,"replaying":replay}),play(events),state({"current_event":{},"replaying":false,"automatic_listening":false}),invoke("finish_listen",[automatic])]

func finish_listen(automatic: bool) -> void:
	if automatic:
		target_due = tick+360
	else:
		reset_idle()

func hear_target(automatic: bool = false) -> void:
	if phase=="play" and not busy:
		run(listen(candidate_events(correct),false,automatic))

func hear_song() -> void:
	if not busy:
		run(listen(melody(phase=="win"),true))

func choose(direction: int) -> void:
	if phase=="play" and not busy and not chooser and direction not in wrong:
		run([invoke("choice_sequence",[direction])])

func animate_actor(who: int, animation: int) -> Array:
	var result: Array = []
	for frame in t.animation_count[animation][who]:
		result.append(state({"frog_animation" if who else "actor_animation":animation,"frog_frame" if who else "actor_frame":frame}))
		result.append(maxi(1,t.animation_delay[animation]))
	result.append(state({"frog_animation" if who else "actor_animation":3,"frog_frame" if who else "actor_frame":0}))
	return result

func appear(point: Array) -> Array:
	return [state({"frog":true,"frog_point":point.duplicate()}),invoke("sound",[10033]),invoke("animate_actor",[1,13]),12]

func disappear() -> Array:
	return [invoke("sound",[10034]),invoke("animate_actor",[1,14]),state({"frog":false})]

func disappointed() -> Array:
	var result: Array = [30]
	for n in 2:
		result.append_array([state({"frog_animation":15}),invoke("sound",[10051]),10,state({"frog_animation":3}),10,state({"frog_animation":16}),invoke("sound",[10052]),10,state({"frog_animation":3}),10])
	return result+[30]

func jumps(who: int, count: int) -> Array:
	var result: Array = []
	for n in count:
		result.append_array([invoke("sound",[10045]),invoke("animate_actor",[who,9]),invoke("sound",[10046]),12])
	return result

func point_frog(target: Array) -> Array:
	var fy = int(frog_point[0])
	var fx = int(frog_point[1])
	var cy = fy-19
	var ty = int(target[0])
	var tx = int(target[1])
	var right = tx>fx
	var x = fx+(10 if ty>cy else 8) if right else fx-(22 if ty<cy else 21)
	var y = fy+1-(11 if ty>cy else 18) if right else fy+1-(18 if ty<cy else 10)
	var id = 22050 if (ty>cy if right else ty<cy) else 22051
	var dx = absi(tx-x)
	var dy = absi(ty-y)
	var sx = signi(tx-x)
	var sy = signi(ty-y)
	var error = int(dx/2) if dx else -1
	var n = 0
	var result: Array = [invoke("animate_actor",[1,12 if right else 11]),invoke("sound",[1016])]
	while true:
		var ending = x==tx and y==ty
		if ending or n%8==0:
			result.append_array([state({"point_sprite":{"id":id,"x":x,"y":y}}),1])
		if ending:
			break
		if error>=0:
			x += sx
			error -= dy
		else:
			y += sy
			error += dx
		n += 1
	return result+[state({"point_sprite":{},"frog_animation":3})]

func introduction(tutor: bool) -> Array:
	var result: Array = [state({"tutoring":tutor,"intro_node":-1,"node":9,"phase":"intro","large_intro":true,"frog":true,"frog_point":[150,42],"player_visible":true}),invoke("frog_voice"),invoke("walk",[9,1,true]),invoke("frog_voice"),invoke("walk_frog_left",[78])]
	if not tutor:
		result.append_array([invoke("frog_voice"),invoke("walk",[9,0,false])])
	return result+[invoke("setup_round"),state({"large_intro":false}),invoke("tutorial_scene",[tutor])]

func tutorial_scene(tutor: bool) -> Array:
	if not tutor:
		return [invoke("round_entry")]
	var result: Array = [state({"player_visible":false,"revealed_signs":0,"frog":true}),invoke("walk",[node,2,true,1])]
	for d in 4:
		var point = t.sign_positions[node][d]
		result.append_array([invoke("point_frog",[[point[0]+(23 if d==1 else 13),point[1]+14]]),state({"revealed_signs":d+1}),play(candidate_events(d,true)),30])
	return result+[90,play(candidate_events(correct)),30,invoke("frog_voice"),invoke("walk",[node,correct,false,1]),state({"frog":false,"tutoring":false,"player_visible":true}),invoke("round_entry")]

func round_entry() -> Array:
	return [invoke("frog_voice"),state({"player_visible":true,"revealed_signs":4}),invoke("walk",[node,2,true]),play(candidate_events(correct)),invoke("reset_idle")]

func walk_frog_left(distance: int) -> Array:
	var result: Array = [state({"frog_animation":4,"frog_frame":0}),t.animation_delay[4]]
	var point = frog_point.duplicate()
	var frame = 0
	for n in range(0,distance,2):
		point[1] -= 2
		frame += 1
		result.append_array([state({"frog_point":point.duplicate(),"frog_frame":frame}),t.animation_delay[4]])
	return result+[state({"frog":false,"frog_animation":3,"frog_frame":0})]

func choice_sequence(direction: int) -> Array:
	return [state({"feedback":direction}),12,state({"feedback":-1}),play(candidate_events(direction,true)),12,invoke("appear",[t.sign_actor_targets[node][direction]]),invoke("resolve_choice",[direction])]

func resolve_choice(direction: int) -> Array:
	if direction!=correct:
		streak = 0
		difficulty(false)
		return [invoke("disappointed"),invoke("disappear"),invoke("wrong_choice",[direction]),invoke("reset_idle")]
	streak += 1
	if streak==2:
		difficulty(true)
	dim_other = direction
	return [invoke("point_frog",[[106,67]]),invoke("reward"),24,invoke("disappear"),60,invoke("earned_note",[direction])]

func wrong_choice(direction: int) -> Array:
	wrong.append(direction)
	wrong_count += 1
	return [invoke("flash_hint")] if wrong_count>=2 else []

func earned_note(direction: int) -> Array:
	earned += 1
	landed = -1
	if earned>=song[0]:
		return [invoke("drawer",[true]),state({"guess_highlight":secret}),play(melody()),12,invoke("drawer",[false]),invoke("jumps",[0,1]),invoke("victory")]
	return [play(melody()),12,invoke("sound",[10045]),invoke("animate_actor",[0,8]),invoke("sound",[10046]),12,invoke("frog_voice"),invoke("walk",[node,direction,false]),invoke("next_node",[direction])]

func next_node(direction: int) -> Array:
	node = t.neighbors[node][direction]
	dim_other = -1
	challenge()
	return [invoke("walk",[node,t.opposite_direction[direction],true]),play(candidate_events(correct)),invoke("reset_idle")]

func idle_hint() -> Array:
	var result: Array = []
	for d in 4:
		result.append_array([state({"feedback":d}),12,state({"feedback":-1})])
	return result+[invoke("reset_hint")]

func win_hint() -> Array:
	return [state({"control_flash":0}),18,state({"control_flash":-1}),12,state({"control_flash":1}),18,state({"control_flash":-1}),invoke("reset_hint")]

func reset_hint() -> void:
	hint_due = tick+900

func flash_hint() -> Array:
	var result: Array = []
	for i in 3:
		result.append_array([state({"hint":true}),12,state({"hint":false})])
		if i<2:
			result.append(12)
	return result+[invoke("reset_hint")]

func stop_sound() -> void:
	host.stop_all_sound()

func reward() -> Array:
	var i = earned
	var end = 76+13*i
	var result: Array = [invoke("sound",[1002])]
	for x in range(60,end+1):
		result.append_array([state({"roller":x}),1])
	result.append_array([invoke("stop_sound"),20,invoke("sound",[1000])])
	var raw = int(song[5+2*i])
	var finish = 147-int(music.followup.music.pitch_y_offsets[2+(raw>>7)][raw&127])
	for y in range(107,finish+1):
		result.append(state({"falling":{"index":i,"y":y,"landed":y==finish}}))
		if y==finish:
			result.append(invoke("sound",[10025]))
		result.append(2)
	result.append_array([state({"falling":{},"landed":i}),20,invoke("sound",[1002])])
	for x in range(end,59,-1):
		result.append_array([state({"roller":x}),1])
	return result+[invoke("stop_sound"),state({"roller":-1})]

func walk(scene: int, direction: int, incoming: bool, who: int = 0) -> Array:
	var path = t.walk_paths[scene][direction].duplicate(true)
	if not path.is_empty():
		path.back()[1] += t.offscreen_walk_extension[path.back()[0]]
	var point = t.centers[scene].duplicate()
	if incoming:
		for segment in path:
			for axis in 2:
				point[axis] += t.direction_vectors[segment[0]][axis]*segment[1]
		path.reverse()
		for segment in path:
			segment[0] = t.opposite_direction[segment[0]]
	var result: Array = [state({"walking":true,"accelerate":false,"frog_point" if who else "actor":point.duplicate()})]
	for segment in path:
		var d = int(segment[0])
		var animation = int(t.walking_animation_ids[d])
		var left = int(segment[1])
		var frame = 0
		result.append_array([state({"frog_animation" if who else "actor_animation":animation,"frog_frame" if who else "actor_frame":0}),{"walk_delay":t.animation_delay[animation]}])
		while left>0:
			var amount = mini(left,t.step_size[d])
			left -= amount
			for axis in 2:
				point[axis] += t.direction_vectors[d][axis]*amount
			frame += 1
			result.append_array([state({"frog_point" if who else "actor":point.duplicate(),"frog_frame" if who else "actor_frame":frame}),{"walk_delay":t.animation_delay[animation]}])
	result.append(state({"walking":false,"accelerate":false,"frog_animation" if who else "actor_animation":3,"frog_frame" if who else "actor_frame":0}))
	# Overlay 1:7A93 stops all channels after incoming movement. Outgoing
	# 7AA6 keeps the accompaniment across the scene change and incoming path.
	if incoming:
		result.append(invoke("stop_sound"))
	return result

func drawer(open: bool) -> Array:
	var delay = host.prepare_sound("digisnd:%d"%(1004 if open else 1003))
	return ([state({"loading_sound":true}),delay,state({"loading_sound":false})] if delay>0 else [])+[invoke("draw_drawer",[open])]

func draw_drawer(open: bool) -> Array:
	if open:
		drawer_slots = range(6).filter(func(i): return i not in eliminated)
		question_blank = false
	chooser = true
	sound(1004 if open else 1003)
	var result: Array = []
	for y in (range(106,59,-2) if open else range(62,107,2)):
		result.append_array([state({"drawer_y":y}),2])
	result.append(state({"drawer_y":-1,"chooser":open}))
	if not open:
		result.append_array([state({"guess_highlight":-1,"question_blank":false}),invoke("reset_idle")])
	return result

func open_guess() -> void:
	if can_guess:
		stop_voice()
		audio_queue = []
		run([invoke("drawer",[true])])

func close_guess() -> void:
	if busy:
		dismiss_after_motion = true
		interrupt()
	else:
		run([invoke("drawer",[false])])

func interrupt() -> void:
	if loading_sound:
		return
	if tutoring:
		if not round_prepared:
			setup_round()
		var scene = intro_node
		cancel()
		node = scene
		frog = false
		run([invoke("round_entry")])
	elif walking:
		accelerate = true
		motion_due = tick
	elif not current_event.is_empty():
		stop_voice()
		audio_queue = []
		current_event = {}
		audio_due = tick
		motion_due = tick
	elif busy:
		motion_due = tick

func guess(slot: int) -> void:
	if chooser and slot not in eliminated and not busy:
		run([state({"guess_highlight":slot}),play(intro_melody(slot)),state({"guess_locked":true,"question_blank":true}),invoke("resolve_guess",[slot])])

func resolve_guess(slot: int) -> Array:
	if slot==secret:
		return [invoke("sound",[1005]),sample_ticks("digisnd:1005"),invoke("drawer",[false]),invoke("jumps",[0,int(song[0])-earned]),invoke("victory")]
	eliminated.append(slot)
	return [invoke("appear",[[135,197]]),invoke("disappointed"),invoke("disappear"),invoke("drawer",[false])]

func victory() -> Array:
	chooser = false
	return [24,invoke("appear",[t.sign_actor_targets[node][1]]),invoke("jumps",[1,1]),invoke("frog_voice"),invoke("frog_climb"),invoke("frog_voice"),invoke("walk",[node,1,false]),invoke("victory_arrival")]

func frog_climb() -> Array:
	var result: Array = [state({"frog_animation":5})]
	var point = frog_point.duplicate()
	for i in 36:
		point[0] -= 2
		result.append_array([state({"frog_point":point.duplicate(),"frog_frame":frog_frame+i+1}),t.animation_delay[5]])
	return result+[state({"frog":false})]

func victory_arrival() -> Array:
	node = 9
	phase = "arrival"
	actor = [150,162]
	actor_animation = 3
	actor_frame = 0
	frog = true
	frog_point = [150,130]
	frog_animation = 3
	frog_frame = 0
	earned = int(song[0])
	return [invoke("walk",[9,3,true]),play(melody(true)),state({"phase":"win"}),invoke("reset_hint")]

func end_control(again: bool) -> Array:
	departure_song = active_song
	replace_song()
	var result: Array = [state({"control_flash":0 if again else 1}),18,state({"control_flash":-1}),invoke("frog_voice")]
	if again:
		var distance = 0
		for part in t.walk_paths[9][0]:
			distance += int(part[1])
		distance += int(t.offscreen_walk_extension[t.walk_paths[9][0].back()[0]])
		return result+[invoke("walk_frog_left",[distance]),invoke("frog_voice"),invoke("walk",[9,0,false]),invoke("reset")]
	return result+[invoke("walk",[9,1,false]),invoke("leave",["music"])]

func leave(destination: String) -> void:
	host.navigate_scene(destination)

func click(point: Vector2i) -> void:
	var rects = t.ui_rects
	if host.resident.hit(rects[0],point):
		leave("inside")
		return
	if host.resident.hit(rects[1],point) and phase!="win":
		leave("music")
		return
	if busy and automatic_listening:
		interrupt()
		update_motion()
		running = false
		steps = []
	if busy:
		interrupt()
		return
	if phase=="win":
		if host.resident.hit(rects[7],point):
			run([invoke("end_control",[true])])
		elif host.resident.hit(rects[6],point) or host.resident.hit(rects[2],point):
			run([invoke("end_control",[false])])
		elif host.resident.hit(rects[8],point):
			hear_song()
		else:
			run([invoke("win_hint")])
		return
	if chooser:
		for i in 6:
			if host.resident.hit([66+23*int(i/3),101+25*(i%3),88+23*int(i/3),121+25*(i%3)],point):
				guess(i)
				return
		close_guess()
		return
	if host.resident.hit(rects[3],point):
		open_guess()
		return
	if host.resident.hit(rects[4],point):
		if earned:
			hear_song()
		else:
			run([state({"replaying":true}),12,state({"replaying":false}),invoke("reset_idle")])
		return
	for d in 4:
		var p = t.sign_positions[node][d]
		if host.resident.hit([p[0],p[1],p[0]+36,p[1]+29],point):
			choose(d)
			return
	hear_target()

func dispose() -> void:
	steps.clear()
	audio_queue.clear()

func glyph(surface, id: int, x: int, y: int, color: Color = Color.BLACK) -> void:
	host.music.glyph(surface,id,x,y,color)

func icon(surface, id: int, x: int, y: int) -> void:
	var code = int(music.song_icons[id+1])
	var pal = 2100+20*((code&247)>>4)
	surface.draw(store,"modules",int(store.palette("modules",pal).first)+(code&15)-1,pal,x,y,2)

func note(surface, raw: int, d: int, x: int, base_y: int, rest_x: int, rest_y: int, dropping: bool = false, highlight: bool = false) -> void:
	var color = Color8(255,85,85) if highlight else Color.BLACK
	var p = raw&127
	var f = raw>>7
	if p==127:
		return
	var g = music.followup.music
	var off = int(g.pitch_y_offsets[2+f][p])
	var y = base_y-off
	if d>=8:
		glyph(surface,2312+d,rest_x+int(g.rest_x_offset[0][d-8]),rest_y+int(g.rest_y_offset[0][d-8]),color)
		return
	if p<=1-f and not dropping:
		surface.rect(x-2,y+2,9,1,color)
	if music.notation.accidentals[p]:
		glyph(surface,2316 if f else 2314,x-(4 if f else 5),y-(2 if f else 1),color)
	if d in [1,3,5]:
		glyph(surface,2312,x+6,y+(3 if off%6 else 0),color)
	if d:
		surface.rect(x+4 if p<12 else x,y-10 if p<12 else y+4,1,11,color)
	if d>=5:
		for i in (2 if d==7 else 1):
			glyph(surface,2308 if p<12 else 2310,x+5 if p<12 else x+1,y-9+3*i if p<12 else y+10-3*i,color)
	glyph(surface,2304 if d<3 else 2306,x,y,color)

func draw(surface) -> void:
	var red = Color8(255,85,85)
	var gray = Color8(170,170,170)
	surface.draw(store,"modules",2341+node,2340,0,0,2)
	if not large_intro:
		surface.draw(store,"th",8,6,304,1)
	if phase in ["win","arrival"] or large_intro:
		if not large_intro:
			icon(surface,active_song,30,16)
			surface.text(store,title,55,25,Color.BLACK)
		surface.rect(30,37,212,75,Color.WHITE)
		for r in 2:
			for j in 5:
				surface.rect(30,38+39*r+6*j,211,1,Color.BLACK)
			surface.rect(30,38+39*r,1,25,Color.BLACK)
			glyph(surface,2302,32,37+39*r)
		for i in (0 if large_intro else int(song[1])):
			note(surface,int(song[5+2*i]),int(song[6+2*i]),52+13*(i%15),66+39*int(i/15),47+13*(i%15),38+39*int(i/15),false,current_event.get("score_index",-1)==i)
		surface.rect(1,96,27,24,red if control_flash==0 else Color.WHITE)
		surface.draw(store,"modules",2357,2340,2,101)
		surface.rect(272,54,27,24,red if control_flash==1 else Color.WHITE)
		surface.draw(store,"modules",2358,2340,273,56)
	else:
		surface.draw(store,"th",7,6,280,1)
		surface.draw(store,"modules",2351,2340,55,107,2)
		surface.draw(store,"modules",2353,2340,60 if roller<0 else roller,104)
		for j in 5:
			surface.rect(65,119+6*j,122,1,Color.BLACK)
		surface.rect(65,119,1,25,Color.BLACK)
		glyph(surface,2302,67,118)
		surface.rect(189,136,13,16,red if replaying else (Color.WHITE if earned else gray))
		glyph(surface,2336,189,136)
		if earned and not guess_locked:
			glyph(surface,2335,189,119)
		for i in earned+int(landed>=0):
			note(surface,int(song[5+2*i]),int(song[6+2*i]),87+13*i,147,82+13*i,119,false,current_event.get("score_index",-1)==i)
		if not falling.is_empty():
			var i = int(falling.index)
			var p = int(song[5+2*i])
			var off = int(music.followup.music.pitch_y_offsets[2+(p>>7)][p&127])
			note(surface,p,int(song[6+2*i]),87+13*i,falling.y+off,82+13*i,falling.y,not falling.landed)
		for d in 4:
			var y = int(t.sign_positions[node][d][0])
			var x = int(t.sign_positions[node][d][1])
			var member = int(choices[d])
			var yy = y+(10 if d==1 else 0)
			var fill = red if feedback==d or (hint and correct==d) else (gray if d in wrong or (dim_other>=0 and d!=dim_other) else Color.WHITE)
			surface.rect(x,y,29,36,Color.BLACK)
			surface.rect(x+1,y+1,29,36,Color.BLACK)
			surface.rect(x+1,y+1,27,34,Color.WHITE)
			surface.draw(store,"modules",2352,2340,x+9,y+37)
			surface.rect(x,y+(10 if d==1 else 25),29,1,Color.BLACK)
			glyph(surface,2328+d,x+10,y+(2 if d==1 else 27))
			if d>=revealed_signs:
				continue
			if type==4:
				surface.rect(x,yy,29,26,Color.BLACK)
				surface.rect(x+1,yy+1,27,24,fill)
				var pal = 2075 if music.followup.fact_icon_groups[member] else 2050
				var id = int(store.palette("modules",pal).first+music.followup.fact_icon_indices[member]-1)
				var shape = store.shape("modules",id)
				surface.draw(store,"modules",id,pal,x+14-int(shape[0]/2),yy+13-int(shape[1]/2))
			else:
				surface.rect(x+1,yy+1,27,24,fill)
				for j in 5:
					surface.rect(x+2,yy+2+5*j,25,1,Color8(85,85,85))
				surface.rect(x+2,yy+2,1,21,Color8(85,85,85))
				var pitches = [9,9,9] if type==0 else t[["","pitch_patterns","melody_patterns","accidental_patterns"][type]][member]
				for n in pitches.size():
					var p = int(pitches[n])
					var duration = int(t.rhythm_patterns[member][n]) if type==0 else 0
					var f = int(t.accidental_flags[member][n]) if type==3 else 0
					var accidental = bool(music.notation.accidentals[p])
					var gx = x+2+(3+7*n if type in [0,2] else (5+10*n if type==1 else 7+12*n-(f if accidental else 2)))
					var gy = yy+2+int(t.challenge_note_y[f][p])
					var color = red if current_event.get("sign",-1)==d and current_event.get("note",-1)==n else Color.BLACK
					glyph(surface,2332+(2 if p>=11 else 0)+duration,gx,gy,color)
					if accidental:
						glyph(surface,2314+2*f,gx+f-5,gy-f+8,color)
	if player_visible:
		draw_actor(surface,0,actor,actor_animation,actor_frame)
	if frog:
		draw_actor(surface,1,frog_point,frog_animation,frog_frame)
	if not point_sprite.is_empty():
		surface.draw(store,"th",point_sprite.id,22000,point_sprite.x,point_sprite.y)
	if chooser:
		var bar = 60 if drawer_y<0 else drawer_y
		var clip = [60,95,112,177]
		surface.draw(store,"modules",2355,2340,95,bar+4,2,clip)
		surface.draw(store,"modules",2354,2340,95,bar,10,clip)
		for i in 6:
			if i in drawer_slots:
				var x = 101+25*(i%3)
				var y = bar+6+23*int(i/3)
				var code = int(music.song_icons[songs[i]+1])
				var pal = 2100+20*(code>>4)
				if guess_highlight==i:
					var top = maxi(60,y-2)
					var bottom = mini(112,y+24)
					if bottom>top:
						surface.rect(x-2,top,24,bottom-top,red)
				surface.draw(store,"modules",int(store.palette("modules",pal).first)+(code&15)-1,pal,x,y,2,clip)
		surface.draw(store,"modules",2356,2340,95,107)
		surface.rect(189,119,13,16,Color.WHITE if question_blank else red)
		if not question_blank:
			glyph(surface,2335,189,119)

func draw_actor(surface, who: int, point: Array, animation: int, frame: int) -> void:
	var archive = "th" if who else host.character
	var pal = 22000 if who else 20000
	var count = maxi(1,t.animation_count[animation][who])
	var n = frame%count
	var index = t.animation_first[animation][who]+(count-1-n if t.animation_reverse[animation] else n)
	var id = int(store.palette(archive,pal).first)+index
	var key = "%s:%d:%s"%[archive,id,t.animation_mirror[animation]]
	if not mirrors.has(key):
		var picture = store.raster(store.shape(archive,id),store.palette(archive,pal).colors,true)
		if t.animation_mirror[animation]:
			picture.flip_x()
		mirrors[key] = picture
	surface.blit(mirrors[key],int(point[1])-17,int(point[0])-(38 if who else 40))
