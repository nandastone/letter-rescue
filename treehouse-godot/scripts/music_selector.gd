extends RefCounted
var host
var store
var tables
var open: bool = false
var category: int = -1
var info: int = 0
var fact: int = 0
var performance = null
var still = null
var still_instrument: int = -1
var music:
	get: return host.music

func _init(game) -> void:
	host = game
	store = game.store
	tables = store.data.music.followup

func facts() -> Array:
	return store.data.strings.get("modules:%d"%info,[])

func show(value: int = -1) -> void:
	open = true
	category = value
	performance = null
	if value>=0:
		info = value
		fact = 0

func animation(tick: int, sound: bool = false):
	var group = int(store.data.music.instruments[music.instrument].animation_group)
	var r = store.data.scripts["th:%d"%group].bounds
	var result = host.ScrAnimation.new(store,"th",group,group,tick)
	result.origin = Vector2i(1,199-int(r[2]-r[0]))
	if sound:
		result.callback_requested.connect(func(slot,_argument):
			if slot==0:
				music.play_pitch(9))
	result.update(tick)
	return result

func audition() -> void:
	host.audio.stop()
	performance = animation(host.tick,true)

func select(id: int) -> void:
	fact = (fact+1)%maxi(1,facts().size()) if info==id else 0
	info = id
	music.release_all()
	music.instrument = id
	music.song[3] = id
	if music.editor.enabled:
		music.editor.save()
	audition()

func update(tick: int) -> void:
	if open and performance!=null and not performance.done:
		performance.update(tick)
		if performance.done:
			host.audio.stop()

func click(point: Vector2i) -> void:
	var rects = tables.menu_rectangles if category<0 else tables.instrument_rectangles
	if host.resident.hit(rects[0],point):
		open = false
		host.navigate_scene("inside")
		return
	if host.resident.hit(rects[1],point):
		open = false
		performance = null
		host.audio.stop()
		return
	if category<0:
		for i in 7:
			if host.resident.hit(rects[2+i],point):
				show(i)
				return
	else:
		if host.resident.hit(rects[2],point):
			show()
			return
		if host.resident.hit(rects[3],point):
			select(category)
			return
		for i in [4,5,6]:
			if host.resident.hit(rects[i],point):
				fact = (fact+1)%maxi(1,facts().size())
				return
		for i in tables.members[category].size():
			var id = int(tables.members[category][i])
			var shape = store.shape("modules",2401+10*category+i)
			var x = int(tables.portrait_x[id])
			var y = int(tables.portrait_y[id])
			if host.resident.hit([y-6,x-6,y+int(shape[1])+6,x+int(shape[0])+6],point):
				select(id)
				return
	if point.x<63 and point.y>100:
		audition()

func heading(surface, value: String, bounds: Array, outline: bool = true) -> void:
	var font = store.data.heading_font
	var x = int(floor((bounds[1]+bounds[3])/2.0))-int(music.text_width(value,true)/2)
	var y = int(floor((bounds[0]+bounds[2])/2.0))-int((int(font[str(value.unicode_at(0))][1])+1)/2)
	if outline:
		for dy in range(-1,2):
			for dx in range(-1,2):
				music.heading(surface,value,x+dx,y+dy)
	music.heading(surface,value,x,y,Color8(170,170,170) if outline else Color.BLACK)

func fill(surface, bounds: Array, color: Color) -> void:
	surface.rect(int(bounds[1]),int(bounds[0]),int(bounds[3]-bounds[1]),int(bounds[2]-bounds[0]),color)

func draw(surface) -> void:
	var palette = store.palette("modules",2270).colors
	surface.draw(store,"modules",2271 if category<0 else 2272,2270,0,0,2)
	if category<0:
		for i in 3:
			var r = tables.menu_rectangles[2+i]
			var rgb = palette[int(tables.category_palette_index[i])]
			var c = Color8(rgb[0],rgb[1],rgb[2])
			surface.rect(r[1]+1,r[0]+2,r[3]-r[1],r[2]-r[0]-2,Color.BLACK)
			surface.rect(r[1]+2,r[0]+1,r[3]-r[1]-2,r[2]-r[0],Color.BLACK)
			surface.rect(r[1],r[0]+1,r[3]-r[1],r[2]-r[0]-2,c)
			surface.rect(r[1]+1,r[0],r[3]-r[1]-2,r[2]-r[0],c)
		for i in 7:
			heading(surface,store.data.music.instruments[i].name,tables.menu_rectangles[2+i])
	else:
		var r = tables.instrument_rectangles
		for i in tables.members[category].size():
			var id = int(tables.members[category][i])
			surface.draw(store,"modules",2401+10*category+i,2400+10*category,int(tables.portrait_x[id]),int(tables.portrait_y[id]))
		surface.draw(store,"modules",2273,2270,259,3)
		var rgb = palette[int(tables.category_palette_index[category])]
		fill(surface,r[3],Color8(rgb[0],rgb[1],rgb[2]))
		heading(surface,store.data.music.instruments[category].name,r[3])
		heading(surface,store.data.music.instruments[info].name,[102,227,114,305],false)
		surface.rect(63,144,120,48,Color.WHITE)
		surface.draw(store,"modules",2001+(20 if info==21 else info),2000,63,144,2)
		var box = r[4]
		fill(surface,box,Color.WHITE)
		surface.rect(box[1],box[0],box[3]-box[1],1,Color.BLACK)
		surface.rect(box[1],box[2]-1,box[3]-box[1],1,Color.BLACK)
		surface.rect(box[1],box[0],1,box[2]-box[0],Color.BLACK)
		surface.rect(box[3]-1,box[0],1,box[2]-box[0],Color.BLACK)
		var group = 2075 if tables.fact_icon_groups[info] else 2050
		var id = int(store.palette("modules",group).first)+int(tables.fact_icon_indices[info])-1
		var shape = store.shape("modules",id)
		surface.draw(store,"modules",id,group,int(floor((box[1]+box[3])/2.0))-int(shape[0]/2),int(floor((box[0]+box[2])/2.0))-int(shape[1]/2))
		var lines: Array = []
		var line = ""
		var values = facts()
		for word in (values[fact] if not values.is_empty() else "").split(" "):
			var next = line+(" " if not line.is_empty() else "")+word
			if music.text_width(next)>113:
				lines.append(line)
				line = word
			else:
				line = next
		lines.append(line)
		var y = 160-int(lines.size()*10/2)
		for i in lines.size():
			surface.text(store,lines[i],193,y+10*i,Color.BLACK,r[6])
	surface.draw(store,"th",8,6,304,1)
	surface.draw(store,"th",7,6,280,1)
	if performance!=null and not performance.done:
		performance.draw(surface)
	else:
		if still_instrument!=music.instrument:
			still = animation(0)
			still_instrument = music.instrument
		still.draw(surface)

func dispose() -> void:
	performance = null
	still = null
