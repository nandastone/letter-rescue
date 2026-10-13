extends RefCounted
## Blocking overlay-3 routines expressed as resumable operations and tick waits.
const ScrAnimation = preload("res://scripts/animation.gd")
var owner_ref: WeakRef
var game:
	get:
		return owner_ref.get_ref()
var queue: Array = []
var running: bool = false
var due: int = 0
var sprite
var dashboard
var exchange_frame
var panels = null
var accepted: bool = false
var speaking: bool = false
var reminding: bool = false
var exchange_interruptible: bool = false
var exchange_interrupted: bool = false
var busy: bool:
	get:
		return running

func _init(board) -> void:
	owner_ref = weakref(board)

func cancel() -> void:
	queue = []
	running = false
	due = 0
	sprite = null
	dashboard = null
	exchange_frame = null
	panels = null
	accepted = false
	speaking = false
	reminding = false
	exchange_interruptible = false
	exchange_interrupted = false

func op(method: String, args: Array = []) -> Array:
	return ["m",method,args]

func gop(method: String, args: Array = []) -> Array:
	return ["g",method,args]

func start(sequence: Array) -> void:
	queue = sequence
	running = true
	due = game.tick
	update(game.tick)

func update(tick: int) -> void:
	if not running or tick<due:
		return
	for guard in 100:
		if queue.is_empty():
			running = false
			sprite = null
			dashboard = null
			exchange_frame = null
			return
		var item = queue.pop_front()
		if item is int or item is float:
			if item>0:
				due = tick+int(item)
				return
		elif item is Dictionary:
			for target in item:
				var object = game if target=="g" else self
				for key in item[target]:
					object.set(key,item[target][key])
		else:
			var object = game if item[0]=="g" else self
			var next = object.callv(item[1],item[2])
			if next is Array:
				queue = next+queue
	assert(false,"Board sequence did not yield")

func perform_dashboard() -> Array:
	var g = game
	var id = 4100+20*g.role()
	dashboard = ScrAnimation.new(g.store,"modules",id,id,g.tick)
	dashboard.sound_requested.connect(g.speak)
	return dashboard_step()

func dashboard_step() -> Array:
	dashboard.update(game.tick)
	if not dashboard.done:
		return [1,op("dashboard_step")]
	dashboard = null
	return []

func post_roll() -> Array:
	var result: Array = [{"g":{"phase":"blink"}}]
	for i in 3:
		result += [{"g":{"car_hidden":true}},12,{"g":{"car_hidden":false}},12]
	return result+[{"g":{"phase":"move"}},op("set_hint")]

func set_hint(delay: int = 300) -> void:
	game.hint_due = game.tick+delay

func robot_turn() -> Array:
	return [60,op("say",[1011]),gop("robot_path")]

func say(id: int) -> Array:
	var ticks = game.speak(id)
	speaking = true
	return [ticks,{"m":{"speaking":false}}] if ticks>0 else [{"m":{"speaking":false}}]

func interrupt_speech() -> void:
	if speaking:
		game.stop_speak()
		due = game.tick

func interrupt_exchange() -> void:
	if exchange_interruptible:
		exchange_interrupted = true
		due = game.tick

func reminder(kind: String, clicked: int = -1) -> Array:
	reminding = true
	var result: Array = []
	if kind=="reward":
		for panel in 2:
			result += [{"g":{"offer_hint":panel}},gop("speak",[10052-panel]),12,{"g":{"offer_hint":-1}}]
	else:
		var nodes = ([clicked] if clicked>=0 else [])+game.neighbours()
		for node in nodes:
			result += [{"g":{"node_hint":node}},12,{"g":{"node_hint":-1}}]
	return result+[{"m":{"reminding":false}},op("set_hint")]

func number(n: int) -> Array:
	var tens = [30,0,20,13,14,15,6,7,8,19]
	var teens = [10,11,12,13,14,15,6,7,8,19]
	var result: Array = []
	if n>=100:
		result += [op("number",[int(n/100)]),5,op("say",[11029])]
		n %= 100
		if n:
			result += [5,op("say",[11150]),5]
	if n:
		if n>=10 and n<20:
			result.append(op("say",[11000+teens[n%10]]))
			if n>=13:
				result += [5,op("say",[11027])]
		else:
			if n>=20:
				result += [op("say",[11000+tens[int(n/10)]]),5,op("say",[11022]),5]
			result.append(op("say",[11000+n%10]))
			if n%10==8:
				result.append(op("say",[11021]))
	return result+[5]

func amount(value: int) -> Array:
	var result: Array = []
	if value<0:
		result += [op("say",[11167]),30]
		value = -value
	if game.mode:
		return result+[op("number",[value]),op("say",[11154 if value==1 else 11155])]
	var dollars = int(value/100)
	var cents = value%100
	if dollars:
		result += [op("number",[dollars]),op("say",[11156 if dollars==1 else 11157])]
		if cents:
			result.append(op("say",[11150]))
	if cents:
		result += [op("number",[cents]),op("say",[11152 if cents==1 else 11153])]
	return result

func selection() -> Array:
	var g = game
	var result: Array = [{"g":{"phase":"selection","offer_stage":"flash"}},gop("speak",[10052-g.chosen]),12,{"g":{"offer_stage":"white"}}]
	if g.mode:
		result += [{"g":{"offer_stage":"bag"}},30]
	else:
		result.append(1)
	result.append({"g":{"offer_stage":"revealed"}})
	if not g.mode:
		result.append(1)
	result += [{"g":{"header_hidden":true}},30,{"g":{"header_hidden":false}},gop("set_choice_message"),{"g":{"offer_stage":"feedback"}}]
	var value = g.rewards[g.chosen]
	var other = g.rewards[1-g.chosen]
	if value==other:
		result.append(op("say",[11151]))
	else:
		result += [op("say",[11163]),10,op("say",[11160 if value>other else 11166 if g.mode else 11158]),10,op("say",[11155 if g.mode else 11159])]
	result += [24,op("amount",[value])]
	return result+([gop("finish_choice",[false]),op("chip_transfer")] if g.mode else [op("money_credit")])

func landing(payment: bool) -> Array:
	panels = 0
	game.header_hidden = true
	var result: Array = [30,{"g":{"header_hidden":false}},op("say",[1027 if payment else 1028])]
	if not payment:
		return result+[op("deliver")]
	result += [{"g":{"phase":"payment"}},op("amount",[-game.payment_requested])]
	if game.mode:
		return result+[gop("start_transfer",[game.payment_before,-mini(game.payment_before,game.payment_requested),false,true]),op("chip_transfer")]
	return result+[op("money_debit",[game.payment_requested,game.payment_before])]

func ending() -> Array:
	var g = game
	if g.winner<0 and g.loser<0:
		return []
	g.ending = true
	g.ending_title = ""
	g.phase = "ending"
	g.header_hidden = true
	var result: Array = [30]
	if g.winner>=0:
		result += [op("say",[1005]),{"g":{"header_hidden":false,"ending_title":"This player WON!"}},op("say",[11164])]
		if g.balances[g.player]>g.goal():
			result.append(op("say",[11161]))
		result.append(op("amount",[g.goal()]))
	else:
		result.append({"g":{"header_hidden":false,"ending_title":"This player LOST!"}})
	return result+[{"g":{"ending":false,"phase":"result","remaining":-1,"hint_step":0}},op("set_hint",[0])]

func deliver(payment: bool = false) -> Array:
	var g = game
	g.phase = "payment" if payment else "delivery"
	panels = 0
	var result: Array = []
	for panel in ([g.mode] if payment else [1] if g.mode else [0,1]):
		var clip = [98,226,194,320] if panel else [19,226,102,320]
		var y = clip[0]+11*panel+10
		for x in range(320,231,-4):
			result += [{"m":{"sprite":{"id":4301 if payment else 4302,"palette":4300,"x":x,"y":y,"clip":clip}}},2]
		if payment:
			return result+[{"g":{"payment_hand":{"id":4301,"palette":4300,"x":232,"y":y,"clip":clip}},"m":{"sprite":null,"panels":null}}]
		result += [{"m":{"panels":2 if g.mode else panel+1}},gop("speak",[1024])]
		for x in range(228,321,4):
			result += [{"m":{"sprite":{"id":4302,"palette":4300,"x":x,"y":y,"clip":clip}}},2]
		result.append({"m":{"sprite":null}})
	return result+[{"m":{"panels":null},"g":{"phase":"reward"}},op("set_hint",[0])]

func travel(id: int, from: Array, to: Array, delay: int = 2, alternate: int = -1) -> Array:
	if alternate<0:
		alternate = id
	var x = int(from[0])
	var y = int(from[1])
	var tx = int(to[0])
	var ty = int(to[1])
	var dx = absi(tx-x)
	var dy = absi(ty-y)
	var sx = signi(tx-x)
	var sy = signi(ty-y)
	var error = int(dx/2) if dx else -1
	var step = 0
	var result: Array = []
	while true:
		var end = x==tx and y==ty
		if end or step%8==0:
			result += [{"m":{"sprite":{"id":id if step%16==0 else alternate,"palette":4400,"x":x,"y":y,"clip":[]}}},delay]
		if end:
			break
		if error>=0:
			x += sx
			error -= dy
		else:
			y += sy
			error += dx
		step += 1
	return result+[{"m":{"sprite":null}}]

func money_credit() -> Array:
	var r = game.tables.money_rects[8+game.chosen]
	game.phase = "credit"
	game.speak(10035)
	return [op("travel",[4414,[r[1]+25,r[0]+24],[204,48],4]),gop("speak",[1025]),gop("finish_choice"),op("ending"),{"g":{"remaining":-1}}]

func money_debit(payment: int, before: int) -> Array:
	game.phase = "payment"
	game.balances[game.player] = before
	return ([60] if payment>before else [])+[op("debit_coins",[mini(payment,before),before])]

func debit_coins(payment: int, before: int) -> Array:
	var g = game
	var r = g.tables.money_rects[8]
	g.rewards = [-payment if before else -g.payment_requested]
	var left = payment
	var coins: Array = []
	for value in g.tables.coin_values:
		coins.append(int(left/value))
		left %= value
	g.reward_coins = [coins]
	var result: Array = []
	if before:
		result += [op("deliver",[true]),op("debit_balance",[before-payment]),60,gop("speak",[10035]),op("travel",[4414,[204,48],[r[1]+25,r[0]+24],4]),gop("speak",[1024]),{"g":{"payment_coins_visible":true}}]
	return result+[{"g":{"loser":g.payment_loser,"phase":"result","remaining":-1}},op("set_hint"),op("ending")]

func debit_balance(value: int) -> void:
	game.phase = "payment"
	game.balances[game.player] = value

func chip_transfer() -> Array:
	var result: Array = [op("deliver",[true])] if game.transfer.sign<0 or game.transfer_negative_zero else []
	return result+[{"g":{"phase":"transfer"}},op("chip_step")]

func chip_step() -> Array:
	var g = game
	var t = g.transfer
	if t.ops.is_empty():
		g.winner = t.winner
		g.loser = t.loser
		g.transfer = null
		g.phase = "result"
		g.remaining = -1
		g.hint_due = g.tick+300
		return [op("ending")]
	var d = t.ops[0]
	var stack = g.tables.chip_rects[1+d]
	if t.sign<0 and t.digits[d]==0:
		var higher = d-1
		while higher>=0 and t.digits[higher]==0:
			higher -= 1
		assert(higher>=0,"Chip payment exceeds available chips")
		return [op("exchange_begin",["borrow",higher]),op("chip_step")]
	t.ops.pop_front()
	if t.sign>0:
		var panel = g.tables.chip_rects[8+g.chosen]
		var cell = t.ops.size()
		return [op("travel",[4420+d,[panel[1]+13*(cell%3),panel[0]+13*int(cell/3)],[stack[1],41]]),gop("speak",[1023]),20,op("credit_chip",[d]),op("chip_step")]
	t.digits[d] -= 1
	g.balances[g.player] -= int(pow(10,2-d))
	g.speak(1025)
	return [20,op("debit_chip",[d]),op("chip_step")]

func credit_chip(d: int) -> Array:
	game.transfer.digits[d] += 1
	game.balances[game.player] += int(pow(10,2-d))
	game.speak(1025)
	return [op("exchange_begin",["carry",d])] if d>0 and game.transfer.digits[d]==10 else []

func debit_chip(d: int) -> Array:
	var g = game
	var panel = g.tables.chip_rects[8]
	var stack = g.tables.chip_rects[1+d]
	var cell = g.transfer.get("paid",0)
	g.transfer.paid = cell+1
	return [op("travel",[4420+d,[stack[1],41],[panel[1]+13*(cell%3),panel[0]+13*int(cell/3)]]),op("paid_chip",[d]),gop("speak",[1023]),20]

func paid_chip(d: int) -> void:
	game.paid_chips.append(d)

const RECORDS = [[8,9,10,21,10,9,8],[11,12,13,20,13,12,11],[8,9,10,21],[11,12,13,20],[3,21,10,9,8,9,10,21,3],[2,20,13,12,11,12,13,20,2],[3,21,10,9,8],[2,20,13,12,11]]

func exchange_begin(kind: String, digit: int) -> Array:
	game.exchange = {"kind":kind,"digit":digit,"flash":false}
	game.phase = "exchange"
	accepted = false
	return exchange_hint()

func exchange_hint() -> Array:
	if accepted:
		return exchange_commit()
	game.exchange.flash = true
	return [6,op("exchange_hint_frames")]

func exchange_hint_frames() -> Array:
	game.exchange.flash = false
	game.speak(1026)
	exchange_interrupted = false
	exchange_interruptible = true
	return exchange_frame_step(0,false)

func exchange_rect() -> Array:
	var e = game.exchange
	var stack = game.tables.chip_rects[1+e.digit]
	return [stack[2]-20,stack[1],stack[2],stack[3]] if e.kind=="carry" else [stack[0]-4,stack[1],stack[0]+16,stack[3]]

func exchange_frame_step(index: int, commit: bool) -> Array:
	var e = game.exchange
	var record = RECORDS[(2-e.digit if e.kind=="carry" else 5-e.digit)+(2 if commit else 0)]
	if index>=record.size() or (not commit and (accepted or exchange_interrupted)):
		exchange_frame = null
		exchange_interruptible = false
		return exchange_apply() if commit else exchange_wait(0)
	exchange_frame = {"shape":4400+record[index],"rect":exchange_rect()}
	return [10,op("exchange_frame_step",[index+1,commit])]

func exchange_wait(count: int) -> Array:
	if count>=60 or accepted:
		return [op("exchange_hint")]
	return [1,op("exchange_wait",[count+1])]

func exchange_commit() -> Array:
	game.phase = "transfer"
	game.speak(1026)
	return exchange_frame_step(0,true)

func exchange_apply() -> Array:
	var g = game
	var e = g.exchange
	var digit = e.digit
	var stack = g.tables.chip_rects[1+digit]
	g.exchange = null
	if e.kind=="carry":
		var target = g.tables.chip_rects[digit]
		g.transfer.digits[digit] = 0
		return [op("travel",[4421 if digit==2 else 4420,[stack[1],57],[target[1],41]]),gop("speak",[1023]),20,op("carry_finish",[digit])]
	var target = g.tables.chip_rects[2+digit]
	g.transfer.digits[digit] -= 1
	return [op("travel",[4408 if digit==1 else 4411,[stack[1],stack[0]-4],[target[1],53]]),op("borrow_finish",[digit]),20]

func carry_finish(digit: int) -> Array:
	game.transfer.digits[digit-1] += 1
	game.speak(1025)
	return [op("exchange_begin",["carry",digit-1])] if digit>1 and game.transfer.digits[digit-1]==10 else []

func borrow_finish(digit: int) -> void:
	game.transfer.digits[digit+1] += 10

func draw(surface) -> void:
	if dashboard!=null:
		dashboard.draw(surface)
	if exchange_frame!=null:
		game.renderer.center(exchange_frame.shape,exchange_frame.rect,4400,Color.WHITE)
	if sprite!=null:
		surface.draw(game.store,"modules",sprite.id,sprite.palette,sprite.x,sprite.y,10,sprite.get("clip",[]))
