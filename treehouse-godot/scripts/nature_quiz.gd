extends RefCounted
## Original animal-identification turns, robot choices and SCR choreography.
const ScrAnimation = preload("res://scripts/animation.gd")
const Renderer = preload("res://scripts/nature_quiz_renderer.gd")
var nature_ref: WeakRef
var nature:
	get:
		return nature_ref.get_ref()
var host
var store
var tables: Dictionary
var renderer
var options: bool = true
var opponent: int = 2
var help: Array = [false,false,true]
var tick: int = 0
var cards: Array = [[],[]]
var secret: Array = [0,0]
var remaining: Array = [255,255]
var asked: Array = [0,0]
var player: int = 1
var available: Array = []
var phase: String = "ready"
var guessing: bool = false
var selected: int = -1
var selected_attribute: int = -1
var answer: String = ""
var notice: String = ""
var winner: int = -1
var robot_due = null
var win_stage = null
var win_animation
var explanation: String = ""
var task: Array = []
var task_due: float = 0
var sample_end = null
var actor_script
var answer_actor
var script_index = null
var divider: bool = false
var question_threshold: int = 0
var question_hidden: int = -1
var hint_due: int = 300
var reminding: bool = false
var reminder_hidden: int = -1
var hint_card: int = -1
var hint_control: bool = false
var guess_hint: bool = false
var robot_spoken: bool = false
var display_player = null
var display_cards = null
var visible_questions = null
var question_mask: int = 0
var waiting: bool = false
var answer_display: bool = false
var revealed: int = 0
var win_phase: int = 0
var other_reveal = null
var candidate_wait: bool = false
var lead_wait: bool = false
var turn_actor
var turn_actor_key: String = ""
var award_requested: bool = false
var busy: bool:
	get:
		return not task.is_empty()

func _init(activity) -> void:
	nature_ref = weakref(activity)
	host = activity.host
	store = activity.store
	tables = activity.tables
	renderer = Renderer.new(activity)

func role() -> int:
	return 0 if player==0 else opponent

func attributes(id: int) -> Array:
	var a = tables.animals[id]
	return a.attributes+[a.active_time]

func speak(id: int, rate: int = 0, fractional: bool = false) -> float:
	return nature.speak(id,rate,fractional)

func stop_sound() -> void:
	host.audio.stop()

func animation(archive: String, id: int, palette: int):
	var a = ScrAnimation.new(store,archive,id,palette,tick)
	a.sound_requested.connect(host.play_sound)
	return a

func op(method: String, args: Array = []) -> Array:
	return [method,args]

func run(steps: Array) -> void:
	sample_end = null
	task = steps
	task_due = tick
	step_task()

func step_task() -> bool:
	if task.is_empty() or tick<task_due:
		return false
	var completed_at: float = tick if sample_end==null else sample_end
	sample_end = null
	while not task.is_empty():
		var item = task.pop_front()
		if item is int or item is float:
			task_due = floor(completed_at)+maxi(1,int(item))
			return true
		if item is Dictionary:
			if item.has("audio_ticks"):
				sample_end = tick+item.audio_ticks
				task_due = sample_end
				return true
			for key in item:
				set(key,item[key])
		else:
			var extra = callv(item[0],item[1])
			if extra is Array:
				task = extra+task
	return true

func perform(index: int, dividing: bool = true) -> Array:
	script_index = index
	var group = 20100+2000*role()
	divider = dividing
	actor_script = animation(host.character if role()==0 else "th",group+index,group)
	return [op("perform_step")]

func perform_step() -> Array:
	actor_script.update(tick)
	if question_threshold and actor_script.frame_updates>question_threshold:
		question_hidden = selected_attribute
		question_threshold = 0
	if not actor_script.done:
		return [1,op("perform_step")]
	if divider:
		stop_sound()
	if script_index<8:
		answer_actor = actor_script
	actor_script = null
	divider = false
	script_index = null
	return []

func reset_hint() -> void:
	hint_due = tick+300

func stop_reminder() -> void:
	if reminding:
		task = []
		reminding = false
		reminder_hidden = -1
		hint_card = -1
		hint_control = false
		guess_hint = false
	reset_hint()

func reminder(explicit: bool = false) -> Array:
	var result: Array = [{"reminding":true}]
	if phase in ["ready","answered","won"]:
		if explicit:
			result.append(op("speak",[1017]))
		result += [{"hint_control":true},8,{"hint_control":false}]
	elif guessing:
		for i in 8:
			if remaining[player]&(1<<i):
				result += [{"hint_card":i},op("hint_sound"),6,{"hint_card":-1}]
	else:
		var sorted = available.duplicate()
		sorted.sort()
		for i in sorted:
			result += [{"reminder_hidden":i},18,{"reminder_hidden":-1},op("speak",[1008]),6]
		result += [{"guess_hint":true},24,{"guess_hint":false}]
	return result+[{"reminding":false},op("reset_hint")]

func hint_sound() -> void:
	speak(1050+nature.random(6))

func robot_think() -> Array:
	robot_spoken = true
	return [maxi(1,int(speak(1011))),op("robot_ready")]

func robot_ready() -> void:
	robot_due = tick

func cleanup() -> void:
	hint_due = tick
	selected = -1
	visible_questions = []
	question_hidden = -1
	question_threshold = 0
	phase = "answered"
	guessing = false
	robot_due = null

func enter_turn() -> Array:
	visible_questions = []
	display_player = null
	display_cards = null
	return [op("deal_question")]

func deal_question() -> Array:
	if available.size()>=3:
		visible_questions = null
		reset_hint()
		robot_due = tick+60 if role()==2 or remaining[player]==(1<<secret[player]) else null
		return []
	while true:
		if question_mask==255:
			question_mask = 0
		var i = nature.random(8)
		while question_mask&(1<<i):
			i = (i+1)%8
		question_mask |= 1<<i
		if i in available:
			continue
		available.append(i)
		return [30,op("reveal_question",[i]),op("deal_question")]
	return []

func reveal_question(i: int) -> void:
	visible_questions.append(i)
	speak(1008)

func enter_guess() -> Array:
	selected = -1
	explanation = ""
	speak(10048)
	visible_questions = []
	return [op("perform",[8]),op("ready_guess")]

func ready_guess() -> void:
	guessing = true
	waiting = true
	hint_due = tick
	robot_due = tick+60 if role()==2 or remaining[player]==(1<<secret[player]) else null

func question(index: int) -> Array:
	speak(10048)
	question_threshold = [[17,17,17],[11,11,12],[10,9,11],[9,9,10],[13,11,12],[13,13,14],[11,11,12],[11,9,12]][index][role()]
	return [op("perform",[index]),op("show_answer",[index]),36,op("help_candidates",[index]),60,op("cleanup")]

func show_answer(index: int) -> void:
	var value = attributes(cards[player][secret[player]])[index]
	answer = nature.strings(5200+index)[value]
	answer_display = true
	asked[player] |= 1<<index
	speak(1008)

func help_candidates(index: int) -> Array:
	var result: Array = []
	if help[role()]:
		var value = attributes(cards[player][secret[player]])[index]
		for i in 8:
			if remaining[player]&(1<<i) and attributes(cards[player][i])[index]!=value:
				result += [op("change_candidate",[i,false]),18]
	return result

func wrong_guess(index: int) -> Array:
	selected = -1
	var result: Array = [op("perform",[11,false])]
	if help[role()]:
		result.append(op("change_candidate",[index,false]))
	return result+[op("speak",[10048]),op("perform",[9]),{"waiting":false},60,op("cleanup")]

func reveal_other(who: int) -> Array:
	display_player = player
	player = who
	if not (revealed&(1<<who)):
		win_stage = "other-shrub"
		other_reveal = who
		win_animation = animation("modules",5600+who,5600)
		return [op("reveal_step",[who])]
	return [op("finish_reveal")]

func reveal_step(who: int) -> Array:
	if not win_animation.done:
		win_animation.update(tick)
		return [1,op("reveal_step",[who])]
	revealed |= 1<<who
	win_phase = 1
	win_animation = null
	other_reveal = null
	return [op("finish_reveal")]

func finish_reveal() -> void:
	win_stage = "done"
	display_player = null
	selected = -1
	explanation = ""

func inspect_winner(who: int) -> void:
	stop_reminder()
	if winner<0 or busy or (win_animation!=null and not win_animation.done):
		return
	run(reveal_other(who))

func draw_turn_actor(surface) -> void:
	if answer_display and answer_actor!=null:
		answer_actor.draw(surface)
		return
	var archive = host.character if role()==0 else "th"
	var group = 20100+2000*role()
	var key = "%s:%d"%[archive,group]
	if turn_actor_key!=key:
		turn_actor_key = key
		turn_actor = ScrAnimation.new(store,archive,group,group)
		while not turn_actor.frame_updates:
			turn_actor.step(0)
		turn_actor.done = true
	turn_actor.draw(surface)

func start() -> void:
	stop_reminder()
	robot_spoken = false
	task = []
	candidate_wait = false
	lead_wait = false
	actor_script = null
	display_player = null
	display_cards = null
	answer_display = false
	visible_questions = null
	waiting = false
	revealed = 0
	win_phase = 0
	question_hidden = -1
	cards = [[],[]]
	remaining = [255,255]
	asked = [0,0]
	winner = -1
	options = false
	win_stage = null
	win_animation = null
	explanation = ""
	award_requested = false
	for who in 2:
		var seen: Array = []
		while cards[who].size()<8:
			var id = nature.random(92)
			var key = attributes(id)
			if key in seen:
				continue
			seen.append(key)
			cards[who].append(id)
		secret[who] = nature.random(8)
	player = nature.random(2)
	if opponent==2:
		player = 1
	phase = "ready"
	available = []
	selected = -1
	selected_attribute = -1
	answer = ""
	guessing = false
	robot_due = null
	nature.save()

func roll() -> bool:
	stop_reminder()
	if busy or options:
		return false
	if phase=="question":
		return reject()
	run(begin_turn())
	return true

func begin_turn() -> Array:
	lead_wait = true
	hint_control = true
	speak(1017)
	return [8,{"hint_control":false},60,{"lead_wait":false},op("next_turn")]

func next_turn() -> Array:
	if winner>=0:
		award_requested = true
		host.rewards.open_nature()
		return []
	display_player = player
	display_cards = phase!="ready"
	player = 1-player
	answer_display = false
	selected = -1
	selected_attribute = -1
	answer = ""
	guessing = false
	explanation = ""
	question_mask = asked[player]
	available = []
	phase = "question"
	robot_due = null
	return [op("enter_turn")]

func ask(index: int) -> bool:
	stop_reminder()
	if busy or guessing or phase!="question" or not index in available:
		return false
	selected = -1
	selected_attribute = index
	explanation = ""
	robot_due = null
	run(question(index))
	return true

func toggle_guess() -> void:
	stop_reminder()
	if busy or options:
		return
	if phase!="question" or guessing or role()==2:
		reject()
		return
	run(enter_guess())

func choose(index: int) -> void:
	stop_reminder()
	if busy or options or cards[player].is_empty():
		return
	if phase=="ready":
		reject()
		return
	if guessing:
		guess(index)
		return
	selected = index
	explanation = ""
	selected_attribute = -1

func guess(index: int) -> bool:
	stop_reminder()
	if busy or phase!="question":
		return false
	if not remaining[player]&(1<<index):
		return reject()
	selected = -1
	guessing = false
	visible_questions = []
	if index==secret[player]:
		winner = player
		phase = "won"
		robot_due = null
		revealed = 1<<player
		win_phase = 2
		speak(1005)
		win_stage = "shrub"
		win_animation = animation("modules",5600+player,5600)
		win_animation.update(tick)
	else:
		run(wrong_guess(index))
	return winner==player

func change_candidate(index: int, keep: bool) -> Array:
	if keep:
		remaining[player] |= 1<<index
	else:
		remaining[player] &= ~(1<<index)
	var duration = speak(1006,16537 if keep else 8269,true)
	var result: Array = []
	if duration:
		candidate_wait = true
		result.append({"audio_ticks":duration})
	return result+[{"candidate_wait":false},op("stop_sound")]

func interrupt_wait() -> bool:
	if not candidate_wait and not lead_wait:
		return false
	if candidate_wait:
		stop_sound()
		sample_end = tick
	task_due = tick
	step_task()
	return true

func reject() -> bool:
	if not busy and not options:
		run(reminder(true))
	return false

func cross_out(index: int) -> void:
	stop_reminder()
	if interrupt_wait() or busy or options or winner>=0:
		return
	if phase=="ready" or role()==2 or help[role()]:
		reject()
		return
	run([op("change_candidate",[index,not bool(remaining[player]&(1<<index))]),op("check_last_candidate")])

func check_last_candidate() -> void:
	if phase=="question" and remaining[player]==(1<<secret[player]):
		robot_due = tick+60

func inspect_attribute(index: int) -> void:
	stop_reminder()
	if busy or (not explanation.is_empty() and selected_attribute==index):
		return
	selected = -1
	selected_attribute = index
	speak(1008)
	explanation = nature.strings(5310)[index]

func update(now: int) -> void:
	tick = now
	if step_task():
		if not busy and not options and phase=="answered" and tick>=hint_due:
			run(reminder())
		return
	if busy:
		return
	if win_animation!=null and not win_animation.done:
		win_animation.update(tick)
		if win_animation.done:
			if win_stage in ["shrub","celebrate"]:
				var celebrate = win_stage=="shrub"
				waiting = false
				win_stage = "celebrate" if celebrate else "retreat"
				var group = 20100+2000*role()
				win_animation = animation(host.character if role()==0 else "th",group+(10 if celebrate else 9),group)
				win_animation.update(tick)
			else:
				stop_sound()
				win_stage = "cleanup"
				run([60,{"win_stage":"done"}])
		return
	if robot_due==null:
		if not options and tick>=hint_due and (win_animation==null or win_animation.done):
			run(reminder())
		return
	if tick<robot_due:
		return
	robot_due = null
	if phase!="question":
		return
	if role()==2 and not robot_spoken:
		run(robot_think())
		return
	robot_spoken = false
	if remaining[player]==(1<<secret[player]) or guessing or available.is_empty():
		if not guessing:
			run(enter_guess())
		else:
			guess(secret[player])
	else:
		var index = nature.random(8)
		while not index in available:
			index = nature.random(8)
		ask(index)

func click(point: Vector2i) -> void:
	if interrupt_wait():
		return
	stop_reminder()
	if busy or (win_animation!=null and not win_animation.done):
		return
	var r = tables.quiz_rectangles
	var o = tables.quiz_options
	if options:
		if nature.hit(o[1],point):
			nature.leave_quiz()
			return
		if nature.hit(o[3],point):
			opponent = 1
		elif nature.hit(o[4],point):
			opponent = 2
		elif nature.hit(o[5],point):
			help[0] = not help[0]
		elif nature.hit(o[6],point) and opponent==1:
			help[1] = not help[1]
		elif nature.hit(o[10],point):
			start()
		nature.save()
		return
	if nature.hit(r[38],point):
		if selected>=0 or not explanation.is_empty():
			selected = -1
			selected_attribute = -1
			explanation = ""
		else:
			reject()
		return
	if winner>=0:
		for i in tables.reveal_rectangles.size():
			if nature.hit(tables.reveal_rectangles[i],point):
				inspect_winner(i)
				return
	if nature.hit(r[9],point):
		nature.leave_quiz()
		return
	if nature.hit(r[11],point):
		options = true
		robot_due = null
		return
	for i in 8:
		if nature.hit(r[1+i],point):
			inspect_attribute(i)
			return
		if nature.hit(r[12+i],point):
			if role()!=2:
				ask(i)
			return
		if nature.hit(r[20+i],point):
			if role()!=2 or phase=="won":
				choose(i)
			return
		if nature.hit(r[28+i],point):
			cross_out(i)
			return
	if nature.hit(r[36],point):
		roll()
	elif nature.hit(r[37],point):
		toggle_guess()

func draw(surface) -> void:
	renderer.draw(surface)

func dispose() -> void:
	task = []
	actor_script = null
	answer_actor = null
	win_animation = null
	turn_actor = null
	renderer = null

