extends "res://scripts/nature_renderer.gd"
const RED = Color8(255,85,85)
const GRAY = Color8(170,170,170)
var mirrored: Dictionary = {}

func label(value: String, rect: Array, align: String = "center", vertical: String = "center", ink: Color = Color.BLACK) -> void:
	var lines: Array = []
	for source in value.replace("\r\n","\r").replace("\n","\r").split("\r"):
		var remaining = source
		while width(remaining)>rect[3]-rect[1]:
			var total = 0
			var end = 0
			var legal = 0
			while end<remaining.length():
				var ch = remaining[end]
				total += width(ch)
				if total>rect[3]-rect[1]:
					break
				end += 1
				var next_space = end<remaining.length() and remaining[end]==" "
				if ch=="-" or ((ch!=" " and next_space) if align=="right" else ch==" " or next_space):
					legal = end
			var n = legal if legal else maxi(1,end)
			lines.append(remaining.substr(0,n))
			remaining = remaining.substr(n)
		lines.append(remaining)
	var y = rect[0] if vertical=="top" else rect[2]-lines.size()*10+1 if vertical=="bottom" else rect[0]+int(ceil((rect[2]-rect[0])/2.0))-int(ceil(lines.size()*5.0))
	for line in lines:
		var x = rect[1] if align=="left" else rect[3]-width(line) if align=="right" else int((rect[1]+rect[3])/2)-int(width(line)/2)
		surface.text(store,line,x,y,ink,rect)
		y += 10

func draw(target) -> void:
	surface = target
	var g = owner_ref.get_ref()
	if g.options:
		if g.options_background==null:
			var mode = g.mode
			if not g.played:
				g.mode = 0
			draw_board()
			g.mode = mode
			g.options_background = surface.image.duplicate()
		else:
			surface.blit(g.options_background,0,0,false)
		draw_options()
	else:
		g.options_background = null
		draw_board()

func draw_board() -> void:
	var g = owner_ref.get_ref()
	var rects = tables.game_rects.slice(0,6)+(tables.chip_rects if g.mode else tables.money_rects)
	var role = g.role()
	var dashboard = 4200+10*role
	surface.image.fill(color(4000,13))
	draw_shape(4001,4000,2,83,2)
	draw_shape(dashboard+1,dashboard,0,0,2)
	if g.mode:
		draw_shape(4002,4000,221,8)
		draw_shape(4004,4000,221,73)
		fill([75,226,87,299],RED if g.winner>=0 and not g.ending else Color.WHITE)
		for i in 3:
			center(4420+i,rects[16+i],4400)
	else:
		fill([64,144,75,209],RED if g.winner>=0 and not g.ending else Color.WHITE)
		draw_shape(4003,4000,137,14)
		draw_shape(4005,4000,221,73,2)
	var balance = g.balances[g.player]
	var digits = g.transfer.digits if g.transfer!=null else [int(balance/100),int((balance%100)/10),balance%10]
	for i in 3:
		var r = rects[7+i]
		if g.mode:
			fill([r[0]+1,r[1]-(6 if i==0 else 5),r[2],r[3]+(6 if i==2 else 5)],RED if g.exchange!=null and g.exchange.get("flash",false) and g.exchange.digit==i else Color.WHITE)
		for j in digits[i]:
			draw_shape((4402 if g.mode else 4405)+i,4400,r[1],r[2]-2-j*2)
		if i==2 or (balance>=pow(10,2-i) if g.mode else i>0 or balance>=100):
			label(str(digits[i]),rects[11+i])
	draw_shape(4007 if g.header_hidden else 4006,4000,111,0)
	var goal = "Game Goal: %d Chips"%g.goal() if g.mode else "Game Goal: "+store.data.strings["modules:4000"][g.level()]
	if not g.header_hidden:
		label(g.ending_title if g.ending else "This player WON!" if g.winner>=0 else "This player LOST!" if g.loser>=0 else g.message if not g.message.is_empty() else goal,rects[4])
	draw_shape(8,6,304,1,10,"th")
	draw_shape(4401,4400,rects[6][1],rects[6][0])
	for i in 24:
		center(4400+g.resolved_node_icons.get(i,g.types[i]),tables.node_rects[i],4400)
	if g.node_hint>=0:
		center(4427,tables.node_rects[g.node_hint],4400)
		center(4400+g.resolved_node_icons.get(g.node_hint,g.types[g.node_hint]),tables.node_rects[g.node_hint],4400)
	if not g.ending and (g.winner>=0 or g.loser>=0):
		center(922,rects[2],900,RED if g.hint_red else Color.WHITE,"th")
	elif g.remaining<0 or g.phase=="result" and not g.ending:
		center(4425,rects[2],4400,RED if g.hint_red else Color.WHITE)
	elif g.remaining>0:
		center(4007+g.remaining,rects[2],4000,Color.WHITE)
	else:
		fill(rects[2],Color.WHITE)
	if (not g.options or g.played) and not g.car_hidden:
		var direction = g.directions[g.player]
		var id = 4442+(1 if direction==1 else 2 if direction==3 else 0)+3*role
		var shape = store.shape("modules",id)
		var c = [g.moving.x,g.moving.y] if g.moving!=null else g.center(g.nodes[g.player])
		var car = store.image("modules",id,4400,true)
		if direction==0:
			if not mirrored.has(id):
				var reflected = car.duplicate()
				reflected.flip_x()
				mirrored[id] = reflected
			car = mirrored[id]
		surface.blit(car,int(floor(c[0]))-int(shape[0]/2),int(floor(c[1]))-int(shape[1]/2))
	if not g.rewards.is_empty():
		draw_rewards(rects)
	g.motion.draw(surface)

func draw_rewards(rects: Array) -> void:
	var g = owner_ref.get_ref()
	var revealed = g.phase in ["result","exchange","credit","transfer","ending"] or g.offer_stage in ["revealed","feedback"]
	var payment = g.rewards.size()==1
	for panel in g.rewards.size():
		if not payment and g.motion.panels!=null and panel>=g.motion.panels:
			continue
		var r = rects[14+panel]
		var amount = absi(g.rewards[panel])
		var selected = revealed and not payment and panel==g.chosen
		fill(r,RED if (g.offer_stage=="flash" and panel==g.chosen) or g.offer_hint==panel else GRAY if revealed and not payment and not selected else Color.WHITE)
		if payment and g.payment_hand!=null:
			var h = g.payment_hand
			draw_shape(h.id,h.palette,h.x,h.y,10,"modules",h.clip)
		if payment and g.mode:
			for i in g.paid_chips.size():
				draw_shape(4420+g.paid_chips[i],4400,r[1]+13*(i%3),r[0]+13*int(i/3))
			label("Pay %d"%g.payment_requested,[r[0],r[1]+4,r[2],r[3]-4],"right","bottom")
			continue
		if not g.mode:
			var coins: Array = []
			if panel<g.reward_coins.size():
				coins = g.reward_coins[panel]
			else:
				var left = amount
				for v in tables.coin_values:
					coins.append(int(left/v))
					left %= v
			var cell = 0
			if not payment or g.payment_coins_visible or g.phase=="result":
				for d in 6:
					for j in coins[d]:
						var x = r[1]+1+20*(cell%4)
						var y = r[0]+17*int(cell/4)
						center(4430+d+(6 if selected and g.phase!="selection" else 0),[y,x,y+17,x+20],4400)
						cell += 1
			var shown = g.payment_requested if payment else amount
			var value = "$ %d.%02d"%[int(shown/100),shown%100] if shown>=100 else "%d %s"%[shown,"Cent" if shown==1 else "Cents"]
			label("Pay "+value if payment else value if revealed else "???",[r[0],r[1]+4,r[2],r[3]-4],"center","bottom")
		else:
			if panel==0 or revealed:
				var cell = 0
				var digits = [int(amount/100),int((amount%100)/10),amount%10]
				if selected and g.phase!="selection":
					digits = [0,0,0]
					if g.transfer!=null:
						for d in g.transfer.ops:
							digits[d] += 1
				for d in 3:
					for j in digits[d]:
						draw_shape(4420+d,4400,r[1]+13*(cell%3),r[0]+13*int(cell/3))
						cell += 1
			else:
				center(4415 if g.offer_stage=="bag" else 4414,[r[0]+20,r[1],r[2]-40,r[3]],4400,Color.WHITE if g.offer_stage=="bag" else null)
			var before = g.transfer.before if g.transfer!=null else g.credit_before if g.offer_stage!=null or g.phase=="credit" else g.balances[g.player]-(g.rewards[g.chosen] if revealed and not payment else 0)
			var sum = before+g.rewards[panel]
			label((str(amount) if panel==0 or revealed else "???")+"\r"+(str(sum) if panel==1 or revealed else "???"),[r[2]-19,r[1]+4,r[2]+1,r[3]-4],"right","top")
			surface.text(store,"+",r[1]+2,178,Color.BLACK)
			surface.rect(r[1]+2,185,36,1,Color.BLACK)
	if not payment and g.motion.panels!=0:
		draw_shape(4429,4400,263 if g.mode else 260,128 if g.mode else 101,2)

func mark(index: int, on: bool) -> void:
	var r = tables.options_rects[index]
	fill(r,color(4050,1))
	if on:
		mask("th",9,r[1],r[0],color(4050,5))

func draw_options() -> void:
	var g = owner_ref.get_ref()
	var t = tables.options_rects
	var bg = color(4050,7)
	draw_shape(4051,4050,27,12)
	center(20201,t[22],20200,null,g.host.character)
	mark(1,g.mode==0)
	mark(2,g.mode==1)
	center(4416+g.mode,t[18],4400,bg)
	mark(3,g.opponent==1)
	mark(4,g.opponent==2)
	if g.opponent==2:
		fill(t[21],bg)
	else:
		center(22201,t[23],22200,null,"th")
	var group = 22200 if g.opponent==1 else 24200
	center(group+2,t[24],group,bg,"th")
	for p in (2 if g.opponent==1 else 1):
		for i in 3:
			mark(5+p*3+i,g.levels[p]==i)
			fill(t[11+p*3+i],bg)
			label(store.data.strings["modules:%d"%(4000+g.mode)][i],t[11+p*3+i],"left","top")
		var icon = [31,30,28,19,20,18][3*g.mode+g.levels[p]]
		center(4400+icon,t[19+p],4400,bg)
