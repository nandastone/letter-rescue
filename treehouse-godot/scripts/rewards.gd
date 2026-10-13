extends RefCounted
## Resident AEC7..B564: shared prize selection and delivery choreography.
const Surface = preload("res://scripts/surface.gd")
var host
var store
var tables: Dictionary
var active: bool = false
var shelf: Array = [false,false,false,false,false,false]
var visited: int = 0
var tick: int = 0
var kind: String = "nature"
var role: int = 0
var background: Image
var upper: Array = []
var panel: Array = []
var destination: Array = []
var presentation: Array = []
var rects: Array = []
var choices: Array = []
var phase: String = "choose"
var selected: int = -1
var flash: int = -1
var flash_step: int = 0
var due: int = 0
var sprite = null
var arrived = null
var motion: Array = []
var complete: Callable
var cancelled: Callable

func _init(game) -> void:
	host = game
	store = game.store
	tables = game.MusicMaze.integers(store.data.rewards)

func center(shape: Array, rect: Array) -> Array:
	return [int((rect[1]+rect[3])/2)-int(shape[0]/2),int((rect[0]+rect[2])/2)-int(shape[1]/2)]

func open(activity: String, recipient: int, image: Image, top: Array, box: Array, target: Array, done: Callable, cancel: Callable, supplied = null) -> void:
	kind = activity
	role = recipient
	background = image.duplicate()
	upper = top
	panel = box
	destination = target
	complete = done
	cancelled = cancel
	choices = [] if supplied==null else supplied.duplicate()
	if supplied==null:
		if role==2:
			choices = [0,1,2,3,4,5]
		else:
			while choices.size()<6:
				var value = host.random.pick(7)
				if not value in choices:
					choices.append(value)
	var bounds = [mini(upper[0],panel[0]),mini(upper[1],panel[1]),maxi(upper[2],panel[2]),maxi(upper[3],panel[3])] if kind=="chips" else panel
	presentation = bounds.duplicate() if kind=="nature" else [bounds[0]-4,bounds[1]-4,bounds[2]+4,bounds[3]+4]
	rects = tables.rectangles[kind]
	active = true
	phase = "choose"
	selected = -1
	flash = -1
	flash_step = 0
	due = tick
	sprite = null
	arrived = null

func open_nature() -> void:
	if active:
		return
	var q = host.nature.quiz
	if q.winner<0 or (q.win_animation!=null and not q.win_animation.done):
		return
	var scene = Surface.new()
	q.draw(scene)
	q.player = q.winner
	scene.rect(137,8,25,25,Color.WHITE)
	scene.rect(8,125,156,10,Color.WHITE)
	tick = host.tick
	open("nature",q.role(),scene.image,[6,30,116,128],[6,30,116,128],q.tables.quiz_rectangles[10] if q.role()==2 else [1,304,23,320],q.start,func(): host.navigate_scene("inside"))

func art(slot: int, large: bool = false) -> Dictionary:
	var entry = tables.prizes[choices[slot]+(21 if role==2 else 0)]
	var palette = [870,900,930,960][entry.group]
	var id = int(store.palette("th",palette).first)+(entry.large if large else entry.choice)-1
	return {"id":id,"palette":palette,"shape":store.shape("th",id)}

func open_board() -> void:
	var g = host.boardgame
	if active or g.motion.busy or (g.winner<0 and g.loser<0):
		return
	var scene = Surface.new()
	g.draw(scene)
	var recipient = g.winner if g.winner>=0 else 1-g.loser
	var recipient_role = 0 if recipient==0 else g.opponent
	var r = g.tables.game_rects.slice(0,6)+(g.tables.chip_rects if g.mode else g.tables.money_rects)
	tick = host.tick
	open("chips" if g.mode else "money",recipient_role,scene.image,r[15 if g.mode else 14],r[14 if g.mode else 15],r[10 if recipient_role==2 else 0],g.start,func(): host.navigate_scene("inside"))

func choose(slot: int) -> void:
	if not active or phase!="choose" or slot<0 or slot>=6:
		return
	selected = slot
	flash = slot
	phase = "selected"
	due = tick+12

func interrupt() -> void:
	if active and phase in ["present","settle"]:
		due = tick

func dismiss() -> void:
	if not active:
		return
	if phase!="choose":
		interrupt()
		return
	active = false
	sprite = null
	var callback = cancelled
	complete = Callable()
	cancelled = Callable()
	callback.call()

func click(point: Vector2i) -> void:
	if phase!="choose":
		interrupt()
		return
	if point.x>=304 and point.y<23:
		dismiss()
		return
	for i in rects.size():
		if point.x>=rects[i][1] and point.x<rects[i][3] and point.y>=rects[i][0] and point.y<rects[i][2]:
			choose(i)
			return

func transfer() -> void:
	var a = art(selected)
	var from = center(a.shape,presentation)
	var to = center(a.shape,destination)
	var x = from[0]
	var y = from[1]
	var dx = abs(to[0]-x)
	var dy = abs(to[1]-y)
	var sx = sign(to[0]-x)
	var sy = sign(to[1]-y)
	var error = int(dx/2) if dx else -1
	var step = 0
	motion = []
	host.play_sound(10035)
	while true:
		var end = x==to[0] and y==to[1]
		if end or step%8==0:
			motion += [{"sprite":{"id":a.id,"palette":a.palette,"x":x,"y":y}},3]
		if end:
			break
		if error>=0:
			x += sx
			error -= dy
		else:
			y += sy
			error += dx
		step += 1
	for id in [923,924,925]:
		var shape = store.shape("th",id)
		motion.append({"arrived":{"id":a.id,"palette":a.palette,"x":to[0],"y":to[1]} if id==923 else null})
		if id==924:
			motion.append("pop")
		motion += [{"sprite":{"id":id,"palette":900,"x":to[0]+int(a.shape[0]/2)-int(shape[0]/2),"y":to[1]+int(a.shape[1]/2)-int(shape[1]/2)}},4]
	motion.append({"sprite":null})
	if role==2:
		motion += [{"phase":"settle"},60]
	motion.append("finish")

func update(now: int) -> void:
	tick = now
	if not active or tick<due:
		return
	if phase=="choose":
		flash = flash_step if flash_step<6 else -1
		if flash>=0:
			host.play_sound(1050+host.random.pick(5))
		flash_step += 1
		due = tick+8
		if flash_step==7:
			flash_step = 0
			due = tick+480
		return
	if phase=="selected":
		phase = "present"
		flash = -1
		host.play_sample("digisnd:10024",22050)
		if role==2:
			shelf[selected] = true
			visited = 7
		due = tick+120
		return
	if phase=="present":
		phase = "transfer"
		transfer()
	while not motion.is_empty():
		var item = motion.pop_front()
		if item is int:
			due = tick+item
			return
		if item is Dictionary:
			for key in item:
				set(key,item[key])
		elif item=="pop":
			host.play_sound(10034)
		else:
			if role!=2:
				host.resident.create(choices[selected])
			active = false
			var callback = complete
			complete = Callable()
			cancelled = Callable()
			callback.call()

func draw_centered(surface, id: int, palette: int, rect: Array, archive: String = "th") -> void:
	var pos = center(store.shape(archive,id),rect)
	surface.draw(store,archive,id,palette,pos[0],pos[1])

func draw(surface) -> void:
	if not active:
		return
	surface.blit(background,0,0,false)
	for rect in [upper,panel]:
		surface.rect(rect[1],rect[0],rect[3]-rect[1],rect[2]-rect[0],Color.WHITE)
	if kind!="nature":
		surface.draw(store,"modules",4013 if kind=="money" else 4014,4000,260 if kind=="money" else 263,101 if kind=="money" else 128)
	var group = 20200+2000*role
	var archive = host.character if role==0 else "th"
	if phase in ["choose","selected"]:
		draw_centered(surface,group+2,group,[panel[0],panel[1],panel[0]+36,panel[3]],archive)
		var label = "Pick a Prize"
		var width = 0
		for character in label:
			width += int(store.data.font[str(character.unicode_at(0))][0])
		surface.text(store,label,int((panel[1]+panel[3])/2)-int(width/2),panel[0]+37,Color.BLACK)
		for i in 6:
			var r = rects[i]
			surface.rect(r[1],r[0],r[3]-r[1],r[2]-r[0],Color8(255,85,85) if flash==i else Color.WHITE)
			var a = art(i)
			draw_centered(surface,a.id,a.palette,r)
	else:
		if role==2:
			draw_centered(surface,group+2,group,destination,archive)
		if phase=="present":
			var a = art(selected,true)
			draw_centered(surface,a.id,a.palette,presentation)
		for s in [arrived,sprite]:
			if s!=null:
				surface.draw(store,"th",s.id,s.palette,s.x,s.y)

func draw_shelf(surface) -> void:
	for i in 6:
		if shelf[i]:
			var pos = [[103,67],[157,103],[130,104],[107,103],[132,66],[149,77]][i]
			surface.draw(store,"th",967+i,960,pos[0],pos[1])

func next_view() -> int:
	if visited==15:
		visited = 0
	var i = host.random.pick(3)
	while visited&(1<<i):
		i = (i+1)%4
	visited |= 1<<i
	return i

func dispose() -> void:
	complete = Callable()
	cancelled = Callable()
	motion = []
