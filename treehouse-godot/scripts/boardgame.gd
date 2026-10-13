extends RefCounted
## Overlay 3: directed roads, money/chip amounts and retained game options.
const Motion = preload("res://scripts/board_motion.gd")
const Renderer = preload("res://scripts/board_renderer.gd")
signal roll_prompt_drawn(value: int)
signal roll_faces_started
signal roll_faces_finished
signal pawn_blink_started
signal pawn_blink_finished
signal node_flash_started(node: int)
signal node_flash_finished
signal pawn_travel_started(target: int)
signal pawn_travel_step
signal pawn_travel_finished
signal landing_started
var host
var store
var tables: Dictionary
var motion
var renderer
var mode: int = 0
var opponent: int = 2
var levels: Array = [0,0]
var saved_levels: Array = [0,0,0,0,0,0]
var options: bool = true
var played: bool = false
var options_background
var hint_red: bool = false
var hint_step: int = 0
var hint_due: int = 300
var tick: int = 0
var phase: String = "ready"
var player: int = 0
var nodes: Array = [7,15]
var directions: Array = [0,2]
var balances: Array = [10,10]
var types: Array
var payment_hand
var payment_coins_visible: bool = false
var paid_chips: Array = []
var remaining: int = -1
var first: bool = true
var winner: int = -1
var loser: int = -1
var rewards: Array = []
var reward_coins: Array = []
var path: Array = []
var moving
var message: String = ""
var roll_frames: Array = []
var roll_due = null
var roll_result: int = 0
var roll_index: int = 0
var offer_hint: int = -1
var node_hint: int = -1
var offer_stage = null
var header_hidden: bool = false
var ending: bool = false
var ending_title: String = ""
var car_hidden: bool = false
var transfer
var transfer_negative_zero: bool = false
var exchange
var resolved_node_icons: Dictionary = {}
var payment_requested: int = 0
var payment_before: int = 0
var payment_loser: int = -1
var chosen: int = 0
var credit_before: int = 0
var storage_enabled: bool = true
var save_path: String = "user://board.json"

func _init(game, persistent: bool = true) -> void:
	host = game
	store = game.store
	tables = game.MusicMaze.integers(store.data.boardgame)
	types = tables.node_types.duplicate()
	motion = Motion.new(self)
	renderer = Renderer.new(self)
	storage_enabled = persistent
	if storage_enabled:
		restore()

func saved_state() -> Dictionary:
	var saved = saved_levels.duplicate()
	saved[3*mode] = levels[0]
	saved[3*mode+opponent] = levels[1]
	return {"version":1,"mode":mode,"opponent":opponent,"levels":saved}

func save() -> void:
	if not storage_enabled:
		return
	var file = FileAccess.open(save_path,FileAccess.WRITE)
	if file==null:
		push_error("Could not save board preferences: %s"%FileAccess.get_open_error())
		return
	file.store_string(JSON.stringify(saved_state()))
	file.close()
	if host.persistence!=null:
		host.persistence.save()

func restore() -> void:
	if not FileAccess.file_exists(save_path):
		return
	var value = JSON.parse_string(FileAccess.get_file_as_string(save_path))
	if not value is Dictionary or value.get("version")!=1 or not value.get("levels") is Array or value.levels.size()!=6:
		return
	if not valid_integer(value.get("mode"),0,1) or not valid_integer(value.get("opponent"),1,2):
		return
	for rank in value.levels:
		if not valid_integer(rank,0,2):
			return
	mode = int(value.mode)
	opponent = int(value.opponent)
	saved_levels = host.MusicMaze.integers(value.levels)
	levels = [saved_levels[3*mode],saved_levels[3*mode+opponent]]

func valid_integer(value, low: int, high: int) -> bool:
	return (value is int or value is float) and value==int(value) and value>=low and value<=high

func speak(id: int) -> int:
	return host.play_sound(id)

func stop_speak() -> void:
	host.audio.stop()

func random(maximum: int) -> int:
	return host.random.pick(maximum)

func role() -> int:
	return 0 if player==0 else opponent

func level() -> int:
	return levels[player]

func goal(who: int = -1) -> int:
	return tables.goals[levels[player if who<0 else who]]

func select_game(next_mode: int = -1, next_opponent: int = -1) -> void:
	saved_levels[3*mode] = levels[0]
	saved_levels[3*mode+opponent] = levels[1]
	if next_mode>=0:
		mode = next_mode
	if next_opponent>=0:
		opponent = next_opponent
	levels = [saved_levels[3*mode],saved_levels[3*mode+opponent]]
	save()

func neighbours(node: int = -1) -> Array:
	return tables.adjacency[nodes[player] if node<0 else node].filter(func(n): return n>=0)

func new_board() -> void:
	resolved_node_icons = {}
	types = tables.node_types.duplicate()
	var n = 0
	while n<3:
		var i = random(23)
		if types[i]!=23:
			types[i] = 23
			n += 1

func clear_offer() -> void:
	offer_hint = -1
	node_hint = -1
	offer_stage = null
	header_hidden = false
	ending = false
	payment_hand = null
	payment_coins_visible = false
	paid_chips = []

func prepare_game() -> void:
	motion.cancel()
	clear_offer()
	car_hidden = false
	options_background = null
	hint_red = false
	hint_step = 0
	hint_due = tick+300
	first = true
	player = 0 if opponent==2 else random(1)
	winner = -1
	loser = -1
	remaining = -1
	phase = "ready"
	rewards = []
	message = ""
	path = []
	moving = null
	roll_due = null
	transfer = null
	exchange = null
	for p in 2:
		var node = random(23)
		while tables.starting_node_exclusions[node]:
			node = random(23)
		nodes[p] = node
		var ds: Array = []
		for d in 4:
			if tables.adjacency[node][d]>=0:
				ds.append(d)
		directions[p] = ds[0]
		for d in ds:
			if d!=1:
				directions[p] = d
				break
		balances[p] = tables.starting_balances[mode][levels[p]]
	new_board()

func enter() -> void:
	tick = host.tick
	prepare_game()
	options = true
	played = false

func start() -> void:
	tick = host.tick
	if opponent==2:
		levels[1] = levels[0]
	save()
	prepare_game()
	options = false
	played = true
	phase = "intro"
	motion.start([motion.op("perform_dashboard"),{"g":{"phase":"ready"}}])

func stop_reminder() -> void:
	if motion.reminding:
		if node_hint>=0: finish_node_flash()
		motion.cancel()
		offer_hint = -1
		node_hint = -1
		hint_due = tick+300

func roll() -> void:
	stop_reminder()
	if motion.busy or options or moving!=null or phase in ["rolling","move","reward","exchange"]:
		return
	speak(1045)
	motion.start([motion.gop("flash_roll_prompt",[true]),12,motion.gop("flash_roll_prompt",[false]),12,motion.gop("continue_roll")])

func flash_roll_prompt(red: bool) -> void:
	hint_red = red
	roll_prompt_drawn.emit(remaining)

func continue_roll() -> Array:
	if winner>=0 or loser>=0:
		host.rewards.open_board()
		return []
	if not first:
		player = 1-player
		new_board()
		rewards = []
		reward_coins = []
		message = ""
		remaining = -1
		phase = "intro"
		return [motion.op("perform_dashboard"),motion.gop("begin_roll")]
	first = false
	begin_roll()
	return []

func begin_roll() -> void:
	roll_faces_started.emit()
	var previous_coins_visible = payment_coins_visible
	clear_offer()
	payment_coins_visible = previous_coins_visible
	hint_red = false
	hint_step = 0
	rewards = []
	reward_coins = []
	message = ""
	phase = "rolling"
	var choices = tables.roll_values[level()].slice(0,tables.roll_counts[level()])
	roll_result = choices[random(choices.size()-1)]
	roll_frames = []
	var previous = -1
	for i in 7:
		var value = choices[random(choices.size()-1)] if mode else 1+random(4)
		while value==previous or (i==6 and value==roll_result):
			value = choices[random(choices.size()-1)] if mode else 1+random(4)
		roll_frames.append(value)
		previous = value
	roll_frames.append(roll_result)
	roll_index = 0
	remaining = roll_frames[0]
	roll_due = tick+6
	roll_prompt_drawn.emit(remaining)
	speak(1045)

func find_path(target: int, steps: int = -1, node: int = -1):
	if steps<0:
		steps = remaining
	if node<0:
		node = nodes[player]
	if steps==0:
		return [] if node==target else null
	for next in neighbours(node):
		var tail = find_path(target,steps-1,next)
		if tail!=null:
			return [next]+tail
	return null

func move(target: int) -> bool:
	stop_reminder()
	if phase!="move" or moving!=null or motion.busy or role()==2:
		return false
	var selected_path = [target] if target in neighbours() else find_path(target)
	if selected_path==null or selected_path.is_empty():
		motion.start([motion.op("reminder",["move",target])])
		return false
	hint_due = tick+300
	motion.start([motion.gop("begin_node_flash",[target]),12,motion.gop("finish_node_flash"),{"g":{"path":selected_path}},motion.gop("next_edge")])
	return true

func begin_node_flash(target: int) -> void:
	node_hint = target
	node_flash_started.emit(target)

func finish_node_flash() -> void:
	node_hint = -1
	node_flash_finished.emit()

func robot_path() -> void:
	var node = nodes[player]
	path = []
	for i in remaining:
		if i==remaining-1:
			var choices = neighbours(node)
			node = choices[0]
			for choice in choices:
				if types[choice]<types[node]:
					node = choice
		else:
			var roads = tables.adjacency[node]
			var next = roads[random(3)]
			while next<0:
				next = roads[random(3)]
			node = next
		path.append(node)
	next_edge()

func center(node: int) -> Array:
	var r = tables.node_rects[node]
	return [(r[1]+r[3])/2.0,(r[0]+r[2])/2.0]

func next_edge() -> void:
	if path.is_empty():
		return
	var from = nodes[player]
	var to = path.pop_front()
	var direction = tables.adjacency[from].find(to)
	assert(direction>=0,"Road path contains a missing edge")
	directions[player] = direction
	var a = center(from)
	var b = center(to)
	pawn_travel_started.emit(to)
	speak(1020+player)
	moving = {"from":from,"to":to,"x":a[0],"y":a[1],"tx":b[0],"ty":b[1],"due":tick+3,"arrived":false}
	step_pawn()

func step_pawn() -> void:
	moving.x += sign(moving.tx-moving.x)*min(2,abs(moving.tx-moving.x))
	moving.y += sign(moving.ty-moving.y)*min(2,abs(moving.ty-moving.y))
	moving.due = tick+3
	pawn_travel_step.emit()

func amounts(type: int) -> Array:
	var rank = level()
	var specs: Array
	if type==26:
		specs = [[4,4,2],[8,9,2],[37,58,2]] if mode else [[5,8,4],[10,15,4],[50,75,4]]
		var v = specs[rank]
		var a = -int((v[0]+random(v[1]))/v[2])
		random(1)
		return [a]
	if mode:
		specs = [[10,3],[21,4],[99,41]] if type==23 else [[4,4],[8,9],[37,58]]
	else:
		specs = [[12,3],[24,6],[114,51]] if type==23 else [[5,6],[10,13],[47,78]]
	var v = specs[rank]
	var a = v[0]+random(v[1])
	var d = 1+random(([1,4,9] if type==23 else [1,2,4])[rank])
	var b = a+(d if random(1) else -d)
	return [a,b if b else 1]

func coins(amount: int) -> Array:
	var result: Array = []
	for i in tables.coin_values.size():
		var value = tables.coin_values[i]
		var n = int(amount/value)
		if i<3 and n>0 and random(1):
			n -= 1
		amount -= n*value
		result.append(n)
	return result

func land() -> void:
	landing_started.emit()
	clear_offer()
	var node = nodes[player]
	var type = types[node]
	var mystery = type==25
	if mystery:
		resolved_node_icons[node] = 25
		type = 24 if random(1) else 26
		types[node] = type
	rewards = amounts(type)
	var phrases = store.data.strings.get("modules:%d"%(3987+type),[])
	message = phrases[random(phrases.size()-1)] if not phrases.is_empty() else ""
	if type==26 and not mode:
		coins(-rewards[0])
		if mystery:
			coins(-rewards[0])
	if type==26:
		payment_requested = -rewards[0]
		payment_before = balances[player]
		payment_loser = player if payment_requested>payment_before else -1
		loser = -1
		phase = "payment"
	else:
		reward_coins = [] if mode else rewards.map(coins)
		phase = "delivery"
	motion.start([motion.op("landing",[type==26])])
	hint_due = tick+300

func choose(index: int) -> void:
	stop_reminder()
	if phase!="reward" or motion.busy or index<0 or index>1:
		return
	chosen = index
	credit_before = balances[player]
	motion.start([motion.op("selection")])

func set_choice_message() -> void:
	var value = rewards[chosen]
	var other = rewards[1-chosen]
	var comparison = "MORE" if value>other else "FEWER" if mode else "LESS"
	message = "Both were the SAME." if value==other else "You picked %s %s%s"%[comparison,"chips" if mode else "money","!" if value>other else "."]

func finish_choice(animate: bool = true) -> void:
	var value = rewards[chosen]
	balances[player] = credit_before+value
	phase = "result"
	if balances[player]>=goal():
		winner = player
	hint_due = tick+300
	if mode:
		start_transfer(credit_before,value,animate)

func start_transfer(before: int, amount: int, animate: bool = true, negative_zero: bool = false) -> void:
	var magnitude = absi(amount)
	var ops: Array = []
	for d in [2,1,0]:
		var unit = int(pow(10,2-d))
		for i in int(magnitude/unit)%(1000 if d==0 else 10):
			ops.append(d)
	transfer = {"before":before,"digits":[int(before/100),int((before%100)/10),before%10],"ops":ops,"sign":signi(amount),"winner":winner,"loser":payment_loser if amount<=0 else loser}
	transfer_negative_zero = amount==0 and negative_zero
	winner = -1
	loser = -1
	balances[player] = before
	if animate:
		motion.start([motion.op("chip_transfer")])

func exchange_chips() -> void:
	if motion.busy and phase=="exchange":
		motion.accepted = true

func update(now: int) -> void:
	tick = now
	if options:
		return
	if motion.busy:
		motion.update(now)
		return
	if phase in ["ready","result"] and tick>=hint_due:
		hint_red = hint_step%2==0
		hint_step += 1
		hint_due = tick+12
		if hint_step==6:
			hint_step = 0
			hint_due = tick+300
	elif (phase=="reward" or phase=="move" and moving==null) and tick>=hint_due:
		motion.start([motion.op("reminder",[phase])])
	elif phase=="rolling" and tick>=roll_due:
		roll_index += 1
		if roll_index<8:
			remaining = roll_frames[roll_index]
			roll_due = tick+6+roll_index
			roll_prompt_drawn.emit(remaining)
			speak(1045)
		else:
			remaining = roll_result
			roll_due = null
			roll_faces_finished.emit()
			phase = "move"
			motion.start([motion.op("robot_turn" if role()==2 else "post_roll")])
	elif moving!=null and tick>=moving.due:
		if not moving.arrived:
			if moving.x!=moving.tx or moving.y!=moving.ty:
				step_pawn()
				return
			moving.arrived = true
			stop_speak()
			nodes[player] = moving.to
			pawn_travel_finished.emit()
			if role()!=2:
				moving.due = tick+12
				return
		nodes[player] = moving.to
		remaining -= 1
		roll_prompt_drawn.emit(remaining)
		speak(1045)
		moving = null
		hint_due = tick+300
		if remaining==0:
			path = []
			land()
		elif not path.is_empty():
			if role()==2:
				next_edge()
			else:
				motion.start([12,motion.gop("next_edge")])

func hit(rect: Array, point: Vector2i) -> bool:
	return point.x>=rect[1] and point.x<rect[3] and point.y>=rect[0] and point.y<rect[2]

func show_options() -> void:
	stop_reminder()
	if not motion.busy and moving==null and phase!="rolling":
		options = true

func click(point: Vector2i) -> void:
	stop_reminder()
	if motion.busy:
		motion.interrupt_speech()
		if phase=="exchange":
			motion.interrupt_exchange()
			if hit(tables.chip_rects[1+exchange.digit],point):
				exchange_chips()
		return
	if options:
		var i = -1
		for n in tables.options_rects.size():
			if hit(tables.options_rects[n],point):
				i = n
				break
		if i==17:
			start()
		elif i in [1,2]:
			select_game(i-1)
		elif i in [3,4]:
			select_game(mode,i-2)
		elif i>=5 and i<=7:
			levels[0] = i-5
		elif i>=8 and i<=10:
			levels[1] = i-8
		save()
		return
	if hit(tables.game_rects[2],point):
		roll()
		return
	if hit(tables.game_rects[1],point) and winner<0 and loser<0:
		motion.start([motion.op("perform_dashboard")])
		return
	if hit(tables.game_rects[5],point):
		speak(1012)
		return
	var rects = tables.chip_rects if mode else tables.money_rects
	if hit(rects[0],point):
		show_options()
		return
	if phase=="exchange":
		if hit(rects[1+exchange.digit],point):
			exchange_chips()
		return
	if phase=="reward":
		if hit(rects[8],point):
			choose(0)
		elif hit(rects[9],point):
			choose(1)
		return
	for i in tables.node_rects.size():
		if hit(tables.node_rects[i],point):
			move(tables.extra_node_map[i-24] if i>=24 else i)
			return

func draw(surface) -> void:
	renderer.draw(surface)

func dispose() -> void:
	motion.cancel()
	motion = null
	renderer = null
