extends RefCounted
## Recovered SONGS.DAT records and the original personal-book editing gestures.
var host
var store
var tables
var character_codes: Array
var drag_pitches: Array
var enabled: bool = false
var mode: int = 0
var index: Array = [0,0]
var duration: Array = [4,4]
var position: int = 0
var books: Array = [[],[]]
var titles: Array = [[],[]]
var trailing: Array = [36,0]
var labels: Array = range(30)
var drag: Dictionary = {}
var eraser: bool = false
var cursor_color: Color = Color8(255,255,85)
var random_task: Dictionary = {}
var title_entry: Dictionary = {}
var voice: bool = false
var voice_due: int = 0
var storage_path: String = "user://SONGS.DAT"
var storage_enabled: bool = true
var save_error: Error = OK
var used_flags: Array = []
var usage_content: Dictionary = {}
var music:
	get: return host.music
var capacity: int:
	get: return 30 if mode else 8
var editable: bool:
	get: return enabled and index[mode]<42
var song: Array:
	get: return books[mode][index[mode]]
var title: String:
	get: return title_at(mode,index[mode])
var note_rects: Array:
	get: return tables.advanced_note_rects if mode else tables.intro_note_rects
var markers: Array:
	get: return tables.advanced_markers if mode else tables.intro_markers

func _init(game, persist: bool = true) -> void:
	host = game
	store = game.store
	tables = store.data.music.followup.music
	character_codes = store.data.music.cp437_codes.map(func(v): return int(v))
	drag_pitches = store.data.music.drag_pitches.map(func(row): return row.map(func(v): return int(v)))
	storage_enabled = persist
	for m in 2:
		for i in 43:
			books[m].append(store.data.music.end_songs[m].map(func(v): return int(v)) if i==42 else blank())
			titles[m].append(encode_title(default_title(m,i)))
	if storage_enabled and FileAccess.file_exists(storage_path):
		import_data(FileAccess.get_file_as_bytes(storage_path),false)

func blank() -> Array:
	var raw: Array = []
	raw.resize(65)
	raw.fill(0)
	raw[2] = 3
	raw[3] = 9
	for i in 30:
		raw[5+2*i] = 127
	return raw

func valid(raw: Array, m: int) -> bool:
	if raw.size()!=65:
		return false
	for value in raw:
		if value<0 or value>255 or int(value)!=value:
			return false
	if raw[m]>(30 if m else 8) or raw[2]>=5 or raw[3]>=42 or raw[4]>=2:
		return false
	for i in (30 if m else 8):
		if raw[5+2*i]!=127 and ((int(raw[5+2*i])&127)>16 or raw[6+2*i]>=16):
			return false
	return true

func default_title(m: int, i: int) -> String:
	return "My %s Song #%d"%["Long" if m else "Short",i+1]

func encode_title(value: String) -> Array:
	var result: Array = []
	result.resize(36)
	result.fill(0)
	for i in mini(35,value.length()):
		var code = character_codes.find(value.unicode_at(i))
		result[i] = code if code>0 else 63
	return result

func title_at(m: int, i: int) -> String:
	var result = ""
	for code in titles[m][i]:
		if code==0:
			break
		result += String.chr(character_codes[code])
	return result

func used(m: int, i: int) -> bool:
	if not used_flags.is_empty():
		var at = 43*m+i
		var content = JSON.stringify([books[m][i],titles[m][i]])
		if usage_content.get(at)!=content:
			usage_content[at] = content
			used_flags[at] = int(content_used(m,i))
		return i==42 or used_flags[at]!=0
	return content_used(m,i)

func content_used(m: int, i: int) -> bool:
	return i==42 or books[m][i][m]>0 or title_at(m,i)!=default_title(m,i)

func initialize_usage(flags: Array) -> void:
	assert(flags.size()==86)
	used_flags = flags.duplicate()
	usage_content.clear()
	for m in 2:
		for i in 43:
			usage_content[43*m+i] = JSON.stringify([books[m][i],titles[m][i]])

func first_free() -> int:
	for i in 42:
		if not used(mode,i):
			return i
	return -1

func export_data() -> PackedByteArray:
	var result = PackedByteArray()
	result.resize(8688)
	for m in 2:
		for i in 43:
			var n = 43*m+i
			for j in 65:
				result[65*n+j] = books[m][i][j]
			for j in 36:
				result[0x15d6+36*n+j] = titles[m][i][j]
	result[0x21ee] = trailing[0]
	result[0x21ef] = trailing[1]
	return result

func import_data(data: PackedByteArray, persist: bool = true) -> bool:
	if data.size()!=8688:
		return false
	var next_books: Array = [[],[]]
	var next_titles: Array = [[],[]]
	for m in 2:
		for i in 43:
			var n = 43*m+i
			var raw = Array(data.slice(65*n,65*(n+1)))
			if not valid(raw,m):
				return false
			next_books[m].append(raw)
			next_titles[m].append(Array(data.slice(0x15d6+36*n,0x15d6+36*(n+1))))
	books = next_books
	titles = next_titles
	trailing = Array(data.slice(0x21ee))
	select()
	if persist:
		save()
	return true

func save() -> void:
	if not storage_enabled:
		return
	var file = FileAccess.open(storage_path,FileAccess.WRITE)
	save_error = FileAccess.get_open_error()
	if file!=null:
		file.store_buffer(export_data())
		save_error = file.get_error()
		file.close()
	if save_error!=OK:
		push_error("Unable to save personal songbooks: %s"%error_string(save_error))
	elif host.persistence!=null:
		host.persistence.save()

func select(value: int = -1) -> void:
	labels = range(30)
	end(true)
	eraser = false
	random_task = {}
	if value>=0:
		index[mode] = clampi(value,0,42)
	position = 0
	for i in capacity:
		if song[5+2*i]==127:
			position = i
			break

func write(pitch: int, length: int = -1, advance: bool = true) -> void:
	if not editable or not random_task.is_empty() or music.contents or not title_entry.is_empty():
		return
	if not position in labels:
		labels.append(position)
	song[5+2*position] = pitch|(int(song[4])<<7)
	song[6+2*position] = int(duration[mode])%8 if length<0 else length
	song[mode] = maxi(song[mode],position+1)
	if advance:
		position = mini(capacity-1,position+1)
	save()

func remove(i: int = -1) -> void:
	if not editable:
		return
	song[5+2*(position if i<0 else i)] = 127
	while song[mode]>0 and song[5+2*(song[mode]-1)]==127:
		song[mode] -= 1
	save()

func clear() -> void:
	if not editable:
		return
	for i in 30:
		song[5+2*i] = 127
	song[mode] = 0
	position = 0
	titles[mode][index[mode]] = encode_title(default_title(mode,index[mode]))
	save()

func clear_all() -> void:
	for m in 2:
		for i in 43:
			books[m][i] = store.data.music.end_songs[m].map(func(v): return int(v)) if i==42 else blank()
			titles[m][i] = encode_title(default_title(m,i))
	index = [0,0]
	select(0)
	save()

func copy(raw: Array, name: String, destination: int = -1) -> bool:
	if destination<0:
		destination = first_free()
	if destination<0 or destination>=42:
		return false
	select(destination)
	books[mode][destination] = raw.duplicate()
	song[mode] = mini(capacity,raw[mode])
	titles[mode][destination] = encode_title(name if not name.is_empty() else default_title(mode,destination))
	select()
	labels.clear()
	save()
	return true

func begin_title() -> void:
	if editable and not music.contents:
		title_entry = {"old":title,"value":"","start":host.tick}

func title_key(event: InputEventKey) -> bool:
	if title_entry.is_empty():
		return false
	if not event.pressed:
		return true
	match event.keycode:
		KEY_ENTER: accept_title()
		KEY_ESCAPE: title_entry.value = title_entry.old
		KEY_BACKSPACE,KEY_DELETE: title_entry.value = title_entry.value.left(-1)
		_:
			if event.unicode>=32 and event.unicode<=126:
				var next = title_entry.value+String.chr(event.unicode)
				if next.length()<=35 and 113+music.text_width(next+"_")<258:
					title_entry.value = next
	return true

func accept_title() -> void:
	if title_entry.is_empty():
		return
	var value = title_entry.old if title_entry.value.is_empty() else title_entry.value
	title_entry = {}
	if editable:
		titles[mode][index[mode]] = encode_title(value)
		save()

func randomize() -> void:
	if editable:
		song[4] = 1
		song[mode] = capacity
		random_task = {"index":0,"due":host.tick}

func audition(pitch: int, length: int = -1) -> void:
	music.play_pitch(pitch)
	voice = true
	voice_due = -1 if length<0 else host.tick+int(store.data.music.tempo_factors[song[2]])*int(store.data.music.duration_factors[length])

func update(tick: int) -> void:
	if voice and voice_due>=0 and tick>=voice_due:
		host.audio.stop()
		voice = false
	if random_task.is_empty() or tick<random_task.due:
		return
	var i = int(random_task.index)
	random_task.index += 1
	song[5+2*i] = 128|[0,2,5,7,9,12,14][host.random.pick(6)]
	song[6+2*i] = 0 if i==capacity-1 else [2,3,3,4,4,4,4,4,4,6,6,6,6][host.random.pick(12)]
	random_task.due = tick+6
	if random_task.index==capacity:
		random_task = {}
		save()

func hit(rect: Array, point: Vector2i) -> bool:
	return host.resident.hit(rect,point)

func pitch_at(y: int, i: int) -> int:
	var offset = (56+39*int(i/15) if mode else 78)-y
	return drag_pitches[mode][clampi(offset,0,27 if mode else 36)]

func click(point: Vector2i) -> bool:
	if not editable or not random_task.is_empty() or music.contents or not title_entry.is_empty():
		return false
	if hit([105,77,112,117],point):
		eraser = not eraser
		return true
	var rects = tables.advanced_duration_rects if mode else tables.intro_duration_rects
	for i in rects.size():
		if hit(rects[i],point):
			var d = int(tables.duration_values[mode][i])
			duration[mode] = d%8
			eraser = false
			drag = {"kind":"palette","start":point,"moved":false,"d":d,"anchor":Vector2i(int(rects[i][1]+tables.duration_x_offset[16*mode+i]),int(rects[i][0]+tables.duration_y_offset[16*mode+i]))}
			return true
	if hit(markers[position+1],point):
		drag = {"kind":"marker","start":point,"moved":false}
		return true
	for i in note_rects.size():
		if hit(note_rects[i],point):
			if eraser:
				remove(i)
			elif (int(song[5+2*i])&127)!=127 and song[6+2*i]<8:
				var pitch = int(song[5+2*i])&127
				drag = {"kind":"note","start":point,"index":i,"height":drag_pitches[mode].find(pitch),"moved":false}
				audition(pitch)
			return true
	return false

func move(point: Vector2i) -> bool:
	cursor_color = Color8(255,255,85)
	if eraser and not hit([26,77,112,300],point):
		eraser = false
		var rgb = store.palette("modules",2200).colors[12]
		cursor_color = Color8(rgb[0],rgb[1],rgb[2])
	if drag.is_empty():
		return false
	var delta: Vector2i = point-drag.start
	if absi(delta.x)>2 or absi(delta.y)>2 or drag.kind=="note":
		drag.moved = true
	if not drag.moved:
		return true
	match drag.kind:
		"marker":
			var col = clampi(int(floor(float(point.x-(105 if mode else 114))/(13 if mode else 22))),0,14 if mode else 7)
			position = col+(15 if mode and point.y>=62 else 0)
		"note":
			var height = clampi(int(drag.height)-delta.y,0,27 if mode else 36)
			if not drag.index in labels:
				labels.append(drag.index)
			var pitch = drag_pitches[mode][height]
			if pitch!=(int(song[5+2*drag.index])&127):
				song[5+2*drag.index] = pitch|(int(song[5+2*drag.index])&128)
				audition(pitch)
				save()
		"palette":
			var p: Vector2i = drag.anchor+delta
			var stem = 10 if mode else 16
			drag.point = Vector2i(clampi(p.x,10,304),clampi(p.y,2+stem,172+stem))
	return true

func end(cancel: bool = false) -> void:
	var prior = drag
	drag = {}
	if prior.get("kind","")=="note" or cancel:
		if voice:
			host.audio.stop()
		voice = false
	if prior.is_empty() or cancel:
		return
	if prior.kind=="palette":
		if not prior.moved and prior.d<8:
			audition(9,prior.d)
		elif prior.has("point"):
			for i in note_rects.size():
				if hit(note_rects[i],prior.point):
					position = i
					var pitch = 5 if prior.d>=8 else pitch_at(prior.point.y,i)
					write(pitch,prior.d)
					if prior.d<8:
						audition(pitch,prior.d)
					break

func draw_duration(surface, d: int, x: int, y: int, color: Color) -> void:
	if d>=8:
		music.glyph(surface,2312+d,x,y,color)
		return
	music.glyph(surface,(2303 if d<3 else 2305)+mode,x,y,color)
	if d:
		surface.rect(x+(4 if mode else 9),y-(10 if mode else 16),1,11 if mode else 18,color)
	if d>=5:
		for n in (2 if d==7 else 1):
			music.glyph(surface,2308 if mode else 2307,x+(5 if mode else 10),y-(9 if mode else 15)+n*(3 if mode else 5),color)
	if d in [1,3,5]:
		music.glyph(surface,2312 if mode else 2311,x+(6 if mode else 11),y+3,color)

func draw_palette(surface) -> void:
	if not enabled:
		return
	surface.rect(129,111,102,29,Color.WHITE)
	var rects = tables.advanced_duration_rects if mode else tables.intro_duration_rects
	for i in rects.size():
		var d = int(tables.duration_values[mode][i])
		draw_duration(surface,d,int(rects[i][1]+tables.duration_x_offset[16*mode+i]),int(rects[i][0]+tables.duration_y_offset[16*mode+i]),Color8(170,0,0) if d==duration[mode] else Color.BLACK)

func draw_overlay(surface) -> void:
	if editable and not music.playing:
		var r = markers[position+1]
		music.glyph(surface,(2319 if position<15 else 2318) if mode else 2317,int(r[1])+(4 if mode else 6),int(r[0])+(0 if mode else 4),Color8(0,170,0))
	if drag.get("kind","")=="palette" and drag.moved and drag.has("point"):
		draw_duration(surface,drag.d,drag.point.x,drag.point.y,Color.BLACK)
	if not title_entry.is_empty():
		surface.rect(111,13,149,13,Color8(85,85,255))
		surface.rect(112,14,147,11,Color.WHITE)
		surface.text(store,title_entry.value,113,15,Color.BLACK)
		if int((host.tick-title_entry.start)/6)%2==0:
			surface.text(store,"_",113+music.text_width(title_entry.value),15,Color.BLACK)

func print_rect(surface, clip: Array, x: int, y: int, w: int, h: int) -> void:
	var right = mini(clip[3],x+w)
	var bottom = mini(clip[2],y+h)
	x = maxi(clip[1],x)
	y = maxi(clip[0],y)
	if right>x and bottom>y:
		surface.rect(x,y,right-x,bottom-y,Color.BLACK)

func print_glyph(surface, clip: Array, id: int, x: int, y: int) -> void:
	surface.blit(store.raster(store.shape("modules",id),[[0,0,0],[0,0,0]],true),x,y,true,clip)

func draw_print(surface) -> void:
	var t = store.data.music
	var raw = music.song
	var clip = [68,6,166,317] if mode else [80,60,134,264]
	var top = clip[0]
	var left = clip[1]
	surface.draw(store,"modules",2297+mode,2296,0,0,2)
	var group = 2075 if t.followup.fact_icon_groups[music.instrument] else 2050
	var id = int(store.palette("modules",group).first+t.followup.fact_icon_indices[music.instrument]-1)
	var shape = store.shape("modules",id)
	surface.rect(left,top-34,29,26,Color.WHITE)
	surface.draw(store,"modules",id,group,left+14-int(shape[0]/2),top-21-int(shape[1]/2))
	surface.rect(left,top-34,29,1,Color.BLACK)
	surface.rect(left,top-9,29,1,Color.BLACK)
	surface.rect(left,top-34,1,26,Color.BLACK)
	surface.rect(left+28,top-34,1,26,Color.BLACK)
	var code = int(t.song_icons[0 if enabled else music.song_id+1])
	var pal = 2100+20*(code>>4)
	surface.draw(store,"modules",int(store.palette("modules",pal).first)+(code&15)-1,pal,left+34,top-32,2)
	music.heading(surface,music.title,left+60,top-26)
	surface.rect(left,top,clip[3]-left,clip[2]-top,Color.WHITE)
	for row in mode+1:
		var y = top+1+53*row
		print_rect(surface,clip,left,y,1,33)
		for n in 5:
			print_rect(surface,clip,left,y+8*n,clip[3]-left+1,1)
		print_glyph(surface,clip,2301,left+2,y-2)
	for i in int(raw[mode]):
		var p = int(raw[5+2*i])&127
		var f = int(raw[5+2*i])>>7
		var d = int(raw[6+2*i])
		if p==127:
			continue
		var baseline = (106 if mode else 118)+53*int(i/(15 if mode else 8))
		var slot = (28 if mode else 86)+(19 if mode else 22)*(i%(15 if mode else 8))
		if d>=8:
			print_glyph(surface,clip,2312+d,slot+[3,3,3,6,6,5,5,5][d-8],baseline-37+[8,14,14,11,11,12,12,12][d-8])
			continue
		var dy = int(t.notation.normal_y_offsets[f][p])
		var x = slot+6
		var y = baseline-dy
		if p<=1-f:
			print_rect(surface,clip,x-3,y+3,17,1)
		if t.notation.accidentals[p]:
			print_glyph(surface,clip,2315 if f else (2314 if mode else 2313),x-(5 if f or mode else 6),y-(4 if f else (1 if mode else 2)))
		if d in [1,3,5]:
			print_glyph(surface,clip,2311,x+11,y+(3 if dy%8 else 0))
		if d:
			var up = p<12
			print_rect(surface,clip,x+9 if up else x,y-16 if up else y+5,1,18)
			if d>=5:
				for n in (2 if d==7 else 1):
					print_glyph(surface,clip,2307 if up else 2309,x+10 if up else x+1,y-15+6*n if up else y+16-6*n)
		print_glyph(surface,clip,2303 if d<3 else 2305,x,y)
		if enabled and not mode:
			var label = t.note_letters[f][p]+(("b" if f else "#") if t.notation.accidentals[p] else "")
			music.heading(surface,label,x+5-int(music.text_width(label,true)/2),baseline+9)
