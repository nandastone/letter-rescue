extends RefCounted
const Selector = preload("res://scripts/music_selector.gd")
const Editor = preload("res://scripts/music_editor.gd")
## Original listening books, pitched samples, piano input and score display.
var host
var store
var tables: Dictionary
var books: Array = [[],[]]
var song_id: int = 20
var instrument: int = 11
var mode: int = 0
var repeating: bool = false
var playing: bool = false
var events: Array = []
var position: int = -1
var cursor: int = 0
var due: int = 0
var notes: Dictionary = {}
var audition_pitch: int = -1
var audition_due: int = 0
var performance = null
var idle_frame: int = -1
var idle_due: int = 600
var contents: int = 0
var note_events: Array = []
var capture_notes: bool = false
var selector
var editor
var written: Dictionary = {}
var dialog: Dictionary = {}
var control_pressed: bool = false
var print_view: Image = null
var page: int:
	get: return int(editor.index[mode]) if editor.enabled else song_id
var terminal: bool:
	get: return page==(42 if editor.enabled else 24)
const BLACK = [1,3,6,8,10,13,15]
var song: Array:
	get: return editor.song if editor.enabled else books[mode][song_id]
var tempo: int:
	get: return int(song[2])
var title: String:
	get: return editor.title if editor.enabled else store.data.strings["modules:101"][song_id]

func _init(game, persistent = null) -> void:
	host = game
	store = host.store
	tables = store.data.music
	selector = Selector.new(game)
	editor = Editor.new(game,game.persistence_enabled if persistent==null else persistent)
	for m in 2:
		for id in 25:
			var raw = store.data.songs["modules:%d"%id].map(func(v): return int(v))
			for field in 3:
				raw[2+field] = int(tables.listening_defaults[field][25*m+id])
			books[m].append(raw)

func enter() -> void:
	idle_frame = -1
	idle_due = host.tick+600

func stop() -> void:
	playing = false
	position = -1
	host.audio.stop()

func release_all() -> void:
	for owner in notes.keys():
		note_up(owner)

func leave() -> void:
	editor.end(true)
	editor.accept_title()
	dialog = {}
	print_view = null
	stop()
	release_all()
	performance = null
	audition_pitch = -1
	selector.open = false
	selector.dispose()

func play_pitch(pitch: int) -> void:
	var id = int(tables.instruments[instrument].sound_id)
	host.play_sample("voices:%d"%id,int(tables.playback_rates[pitch]))
	if capture_notes:
		note_events.append({"tick":host.tick,"pitch":pitch,"instrument":instrument})

func finish_idle() -> void:
	idle_frame = -1
	idle_due = host.tick+60*(10+host.random.pick(20))

func note_down(pitch: int, owner: String) -> void:
	if notes.has(owner) or not dialog.is_empty() or not editor.title_entry.is_empty() or print_view!=null:
		return
	if idle_frame>=0:
		finish_idle()
	release_all()
	stop()
	performance = null
	notes[owner] = pitch
	play_pitch(pitch)
	if contents==0 and not selector.open and not editor.enabled:
		audition_pitch = pitch
		audition_due = host.tick+120
	if editor.editable and not selector.open and contents==0:
		written[owner] = {"mode":mode,"index":editor.index[mode],"position":editor.position}
		editor.write(pitch,-1,false)

func note_up(owner: String) -> void:
	if notes.has(owner):
		notes.erase(owner)
		host.audio.stop()
	if written.has(owner):
		var record = written[owner]
		if mode==record.mode and editor.index[mode]==record.index:
			editor.position = mini(editor.capacity-1,record.position+1)
		written.erase(owner)

func sequence() -> Array:
	var result: Array = []
	for i in int(song[mode]):
		var pitch = int(song[5+2*i])&127
		var duration = int(song[6+2*i])
		if pitch==127:
			continue
		result.append({"pitch":pitch,"source":i,"rest":duration>=8,"ticks":int(tables.tempo_factors[tempo])*int(tables.duration_factors[duration])})
	return result

func toggle_song() -> void:
	if playing:
		stop()
		return
	release_all()
	performance = null
	audition_pitch = -1
	events = sequence()
	cursor = 0
	position = -1
	due = host.tick
	playing = true
	advance_song()

func advance_song() -> void:
	if not playing or host.tick<due:
		return
	host.audio.stop()
	if cursor>=events.size() and repeating and not events.is_empty():
		cursor = 0
	if cursor>=events.size():
		stop()
		return
	position = cursor
	cursor += 1
	var event = events[position]
	if not event.rest:
		play_pitch(event.pitch)
	due = host.tick+int(event.ticks)

func key_at(point: Vector2i) -> int:
	for black in [true,false]:
		for key in tables.keys:
			if (int(key.pitch) in BLACK)==black and host.resident.hit(key.rectangle,point):
				return int(key.pitch)
	return -1

func key_input(event: InputEventKey) -> bool:
	control_pressed = event.ctrl_pressed
	if editor.title_key(event):
		return true
	if print_view!=null:
		if event.pressed and event.keycode in [KEY_ENTER,KEY_SPACE,KEY_ESCAPE]:
			print_view = null
		return true
	if not dialog.is_empty():
		return event.keycode not in [KEY_ENTER,KEY_SPACE,KEY_LEFT,KEY_RIGHT,KEY_UP,KEY_DOWN]
	for key in tables.keys:
		if event.keycode>=32 and event.keycode<=126 and String.chr(event.keycode).to_upper()==key.keyboard:
			var owner = "key:%d"%event.keycode
			if event.pressed and not event.echo:
				var r = key.rectangle
				host.pointer = Vector2i(int((r[1]+r[3])/2),int((r[0]+r[2])/2))
				note_down(int(key.pitch),owner)
			elif not event.pressed:
				note_up(owner)
			return true
	return false

func move(point: Vector2i) -> void:
	if editor.move(point):
		return
	for owner in notes.keys():
		if owner.begins_with("key:"):
			continue
		var pitch = key_at(point)
		if pitch!=notes[owner]:
			note_up(owner)
			if pitch>=0:
				note_down(pitch,owner)

func select_page(id: int) -> void:
	stop()
	release_all()
	contents = 0
	editor.accept_title()
	if editor.enabled:
		editor.select(clampi(id,0,42))
	else:
		song_id = clampi(id,0,24)
		if host.persistence!=null:
			host.persistence.listening_page_changed(song_id)
	instrument = int(song[3])
	audition_pitch = -1
	if terminal:
		repeating = false
		toggle_song()

func set_mode(value: int) -> void:
	stop()
	release_all()
	editor.accept_title()
	contents = 0
	mode = value
	editor.mode = value
	if host.persistence!=null:
		host.persistence.switch_listening_mode(value)
	if editor.enabled:
		editor.select()
	instrument = int(song[3])

func set_composing(value: bool) -> void:
	stop()
	release_all()
	editor.accept_title()
	editor.end(true)
	contents = 0
	editor.enabled = value
	editor.mode = mode
	if value:
		editor.select()
	instrument = int(song[3])
	audition_pitch = -1

func ask(message: String, action: Callable) -> void:
	stop()
	editor.end(true)
	dialog = {"message":message,"action":action,"start":host.tick}

func answer(yes: bool) -> void:
	var previous = dialog
	dialog = {}
	if yes:
		previous.action.call()

func copy_song() -> void:
	if contents or terminal:
		return
	var free = editor.first_free()
	if free<0:
		return
	var raw = song.duplicate()
	raw[3] = instrument
	var name = "My "+title
	ask("copy",func():
		set_composing(true)
		editor.copy(raw,name,free)
		instrument = raw[3])

func erase_song() -> void:
	if not editor.editable or contents:
		return
	if control_pressed:
		ask("erase_all",func():
			editor.clear_all()
			instrument = int(song[3]))
	elif editor.used(mode,page):
		ask("erase",func(): editor.clear())

func audition() -> void:
	stop()
	release_all()
	var group = int(tables.instruments[instrument].animation_group)
	var r = store.data.scripts["th:%d"%group].bounds
	performance = host.ScrAnimation.new(store,"th",group,group,host.tick)
	performance.origin = Vector2i(40-int((r[3]-r[1])/2),92-int(r[2]-r[0]))
	performance.callback_requested.connect(func(slot,_arg):
		if slot==0:
			play_pitch(9))
	performance.update(host.tick)

func click(point: Vector2i, owner: String) -> void:
	if idle_frame>=0:
		finish_idle()
	if print_view!=null:
		print_view = null
		return
	if not editor.title_entry.is_empty():
		editor.accept_title()
		return
	if not dialog.is_empty():
		if host.hit(point,7,40,32,40):
			answer(true)
		elif host.hit(point,43,40,34,40):
			answer(false)
		return
	if selector.open:
		selector.click(point)
		return
	if editor.click(point):
		if editor.drag.get("kind","")=="note":
			notes[owner] = int(song[5+2*editor.drag.index])&127
		return
	var pitch = key_at(point)
	if pitch>=0:
		note_down(pitch,owner)
		return
	audition_pitch = -1
	var x = point.x
	var y = point.y
	if host.hit(point,54,136,29,22):
		toggle_song()
	elif x>=307 and y<15:
		host.navigate_scene("inside")
	elif x<80 and y<108:
		audition()
	elif host.hit(point,305,26,13,9):
		stop()
		contents = 1
	elif contents>0 and host.hit(point,88,27,212,66):
		var col = 0 if x<194 else 1
		var row = int((y-27)/23)
		if row<3 and y<47+23*row:
			select_page((contents-1)*6+col*3+row)
	elif contents>0 and host.hit(point,258,1,23,21):
		select_page(page)
	elif host.hit(point,284,9,19,17):
		var direction = 1 if x-284>y-9 else -1
		if contents:
			if contents+direction>(7 if editor.enabled else 4):
				select_page(0)
			else:
				contents = maxi(1,contents+direction)
		elif page==0 and direction<0:
			stop()
			contents = 7 if editor.enabled else 4
		else:
			select_page(page+direction)
	elif host.hit(point,44,115,47,19):
		stop()
		song[2] = tables.tempo_thresholds.filter(func(boundary): return x>=boundary).size()
		if editor.enabled:
			editor.save()
	elif host.hit(point,265,140,39,17):
		set_mode(1-mode)
	elif host.hit(point,264,161,41,17):
		set_composing(not editor.enabled)
	elif host.hit(point,235,112,25,26):
		erase_song()
	elif host.hit(point,262,112,23,26):
		if editor.editable:
			ask("random",func(): editor.randomize())
		elif not editor.enabled:
			copy_song()
	elif host.hit(point,98,117,26,21):
		song[4] = int(song[4])^1
		if editor.enabled:
			editor.save()
	elif editor.editable and host.hit(point,113,13,145,13):
		editor.begin_title()
	elif point.x>=289 and point.y>=113 and point.y<138:
		if not contents and not terminal and host.preferences.settings.printing:
			ask("print",func():
				var paper = host.Surface.new()
				editor.draw_print(paper)
				print_view = paper.image)
	elif host.hit(point,11,141,40,34):
		host.navigate_scene("maze")
	elif point.x<42 and point.y>=113 and point.y<136:
		stop()
		release_all()
		selector.show()
	elif host.hit(point,54,159,30,22):
		repeating = not repeating
	elif x>=305 and y>=38 and y<95:
		select_page(([0,9,19,29,39] if editor.enabled else [0,5,11,17,23])[mini(4,int((y-38)/12))])

func update(tick: int) -> void:
	if print_view!=null:
		return
	editor.update(tick)
	selector.update(tick)
	if audition_pitch>=0 and notes.is_empty() and idle_frame<0 and tick<=idle_due and tick>=audition_due:
		audition_pitch = -1
	if notes.is_empty() and not selector.open and dialog.is_empty() and editor.title_entry.is_empty() and (tick>idle_due if idle_frame<0 else tick>=idle_due):
		idle_frame += 1
		if idle_frame>=tables.idle_frames.size():
			finish_idle()
		else:
			idle_due = tick+4
	if performance!=null and not performance.done:
		performance.update(tick)
		if performance.done:
			host.audio.stop()
	advance_song()

func glyph(surface, id: int, x: int, y: int, color: Color = Color.BLACK) -> void:
	surface.blit(store.raster(store.shape("modules",id),[[0,0,0],[color.r8,color.g8,color.b8]],true),x,y)

func text_width(value: String, heading: bool = false) -> int:
	var font = store.data.heading_font if heading else store.data.font
	var width = 0
	for c in value:
		width += int(font.get(str(c.unicode_at(0)),[3 if heading else 4])[0])+int(heading)
	return width

func heading(surface, value: String, x: int, y: int, color: Color = Color.BLACK) -> void:
	for c in value:
		var raw = store.data.heading_font.get(str(c.unicode_at(0)))
		if raw!=null:
			if raw[0]>0 and raw[1]>0:
				surface.blit(store.raster(raw,[[0,0,0],[color.r8,color.g8,color.b8]],true),x,y)
			x += int(raw[0])+1
		else:
			x += 4

func draw_score(surface) -> void:
	var event = events[position] if playing and position>=0 else {}
	var single = audition_pitch>=0 and not playing and contents==0 and not editor.enabled
	var count = 30 if mode else 8
	var first = int(int(event.get("source",0))/count)*count
	var t = tables.followup.music
	surface.rect(88,27,212,75,Color.WHITE)
	for row in (2 if mode else 1):
		for j in 5:
			surface.rect(88,28+39*row+6*j if mode else 41+8*j,211 if mode else 206,1,Color.BLACK)
		surface.rect(88,28+39*row if mode else 41,1,25 if mode else 33,Color.BLACK)
		glyph(surface,2302 if mode else 2301,90,27+39*row if mode else 39)
	for i in count:
		if (i not in [6,21] if mode else i!=3) if single else first+i>=song[mode]:
			continue
		var pitch = audition_pitch if single else int(song[5+2*(first+i)])&127
		var flag = int(song[4]) if single else int(song[5+2*(first+i)])>>7
		var d = 4 if single else int(song[6+2*(first+i)])
		if pitch==127:
			continue
		var color = Color8(170,0,0) if editor.enabled and editor.drag.get("kind","")=="note" and editor.drag.index==first+i else Color.BLACK
		var row = int(i/15)
		var col = i%15
		if d>=8:
			glyph(surface,2312+d,105+13*col+int(t.rest_x_offset[0][d-8]) if mode else 114+i*22+[1,1,1,4,4,3,3,3][d-8],28+39*row+int(t.rest_y_offset[0][d-8]) if mode else 41+[6,10,10,7,7,8,8,8][d-8],color)
			continue
		var offset = int(t.pitch_y_offsets[2+flag][pitch] if mode else tables.notation.normal_y_offsets[flag][pitch])
		var x = 110+13*col if mode else 120+i*22
		var y = (56+39*row if mode else 78)-offset
		if not mode:
			glyph(surface,2303 if d<=2 else 2305,x,y,color)
		if d>0:
			surface.rect(x+(4 if mode else 9) if pitch<12 else x,y-(10 if mode else 16) if pitch<12 else y+(4 if mode else 5),1,11 if mode else 18,color)
		if d>=5:
			for n in (2 if d==7 else 1):
				glyph(surface,(2308 if pitch<12 else 2310) if mode else (2307 if pitch<12 else 2309),x+(5 if mode else 10) if pitch<12 else x+1,y-(9 if mode else 15)+(3 if mode else 5)*n if pitch<12 else y+(10-3*n if mode else 16-5*n),color)
		if d in [1,3,5]:
			glyph(surface,2312 if mode else 2311,x+(6 if mode else 11),y+(3 if offset%(6 if mode else 8) else 0),color)
		if pitch<=1-flag:
			surface.rect(x-(2 if mode else 3),y+(2 if mode else 3),9 if mode else 17,1,color)
		if tables.notation.accidentals[pitch]:
			glyph(surface,(2316 if flag else 2314) if mode else (2315 if flag else 2313),x-((4 if flag else 5) if mode else (5 if flag else 6)),y-((2 if flag else 1) if mode else (4 if flag else 2)),color)
		if mode:
			glyph(surface,2304 if d<3 else 2306,x,y,color)
		elif single or (editor.enabled and i in editor.labels):
			var label = tables.note_letters[flag][pitch]+(("b" if flag else "#") if tables.notation.accidentals[pitch] else "")
			heading(surface,label,x+5-int(text_width(label,true)/2),87,color)
		if event.get("source",-1)==first+i:
			if mode:
				var b = t.advanced_markers[i+1]
				glyph(surface,2318 if row else 2319,int(b[1])+4,int(b[0]),Color.RED)
			else:
				glyph(surface,2317,x,33,Color.RED)

func draw_instrument(surface) -> void:
	if performance!=null and not performance.done:
		performance.draw(surface)
		return
	var group = int(tables.instruments[instrument].animation_group)
	var script = store.data.scripts["th:%d"%group]
	var slots: Array = []
	for i in 16:
		slots.append({"shape":0,"x":0,"y":0,"mode":10})
	for instruction in script.code:
		var op = int(instruction[0])
		var bytes = instruction[1]
		if op in [1,7]:
			break
		var slot = slots[op&15]
		match op&240:
			192: slot.shape=host.ScrAnimation.u16(bytes)
			176:
				slot.x=host.ScrAnimation.s16(bytes)
				slot.y=host.ScrAnimation.s16(bytes,2)
			144: slot.mode=host.ScrAnimation.u16(bytes,2)&15
	for slot in slots:
		if slot.shape:
			surface.draw(store,"th",int(store.palette("th",group).first)+slot.shape-1,group,40-int((script.bounds[3]-script.bounds[1])/2)+slot.x,92-int(script.bounds[2]-script.bounds[0])+slot.y,slot.mode,[0,0,99,79])

func draw(surface, instrument_visible: bool = true) -> void:
	if print_view!=null:
		surface.blit(print_view,0,0,false)
		return
	if selector.open:
		selector.draw(surface)
		return
	surface.draw(store,"modules",2201,2200,0,0,2)
	if dialog.is_empty() and instrument_visible:
		draw_instrument(surface)
	for item in [[2246 if editor.enabled else 2245,264,161],[2248 if mode else 2247,265,140],[2244 if repeating else 2243,54,159],[2259,289,113],[2253 if editor.enabled else 2263,235,113],[2255 if editor.enabled else 2257,262,113],[2242 if playing else 2241,56,138],[2249,12,115],[2252 if song[4] else 2251,98,117],[2261,44,115],[2262,[46,55,64,73,82][tempo],127],[2264,258,1],[2265,260,8]]:
		surface.draw(store,"modules",item[0],2240,item[1],item[2],2)
	var rgb = store.palette("modules",2200).colors[3]
	surface.rect(129,111,102,29,Color8(rgb[0],rgb[1],rgb[2]))
	var icon = int(tables.song_icons[0 if editor.enabled else song_id+1])
	var group = 2100+20*((icon&247)>>4)
	if icon:
		surface.draw(store,"modules",group+(icon&15),group,88,6,2)
	surface.draw(store,"th",8,6,304,1)
	var name = tables.instruments[instrument].name
	surface.text(store,name,13+int(floor((57-text_width(name))/2.0)),96,Color.BLACK)
	surface.text(store,title.substr(0,33),113,15,Color.BLACK)
	var number = str(page+1)
	surface.text(store,number,271-int(text_width(number)/2),10,Color.BLACK)
	if editor.enabled:
		for i in 5:
			surface.rect(305,38+i*12,13,9,Color8(182,182,182))
		if not editor.eraser:
			surface.draw(store,"modules",2208,2200,77,105)
	for item in ([["1",311,39],["10",308,51],["20",306,63],["30",306,75],["40",306,87]] if editor.enabled else [["1",311,39],["6",309,51],["12",308,63],["18",308,75],["24",306,87]]):
		surface.text(store,item[0],item[1],item[2],Color.BLACK)
	draw_score(surface)
	editor.draw_palette(surface)
	editor.draw_overlay(surface)
	if terminal:
		for r in [[88,6,22,20],[113,13,145,13],[88,27,212,75],[258,9,23,13]]:
			surface.rect(r[0],r[1],r[2],r[3],Color.WHITE)
		surface.rect(258,8,23,1,Color.BLACK)
		surface.draw(store,"modules",2207,2200,98,27,2)
	if contents:
		draw_contents(surface)
	if idle_frame>=0:
		var r = tables.idle_rect
		surface.draw(store,"modules",2129+int(tables.idle_frames[idle_frame]),2120,int(r[1]),int(r[0]),2)
	var active = notes.values()
	if playing and position>=0 and not events[position].rest:
		active.append(events[position].pitch)
	for black in [false,true]:
		for key in tables.keys:
			if (int(key.pitch) in BLACK)==black and int(key.pitch) in active:
				surface.draw(store,"modules",int(key.pressed_shape),2200,int(key.rectangle[1]),int(key.rectangle[0]),2)
	draw_dialog(surface)

func dispose() -> void:
	dialog = {}
	performance = null
	selector.dispose()

func draw_contents(surface) -> void:
	for r in [[88,27,212,75],[88,6,22,20],[113,13,145,13],[258,9,23,13]]:
		surface.rect(r[0],r[1],r[2],r[3],Color.WHITE)
	surface.rect(258,8,23,1,Color.BLACK)
	heading(surface,"Table of Contents",137,13)
	for slot in 6:
		var i = (contents-1)*6+slot
		var x = 88 if slot<3 else 194
		var y = 27+23*(slot%3)
		var code = 1 if editor.enabled else int(tables.song_icons[i+1])
		var group = 2100+20*(code>>4)
		surface.draw(store,"modules",int(store.palette("modules",group).first)+(code&15)-1,group,x,y,2)
		var lines = [""]
		var name = editor.title_at(mode,i) if editor.enabled else store.data.strings["modules:101"][i]
		for word in name.split(" "):
			var next = lines.back()+(" " if not lines.back().is_empty() else "")+word
			if text_width(next)>81 and not lines.back().is_empty():
				lines.append(word)
			else:
				lines[lines.size()-1] = next
		var top = int(floor((y+y+20-(10*lines.size()-1))/2.0))
		for j in lines.size():
			surface.text(store,lines[j],x+24,top+10*j,Color.BLACK)
	var roman = ["i","ii","iii","iv","v","vi","vii"][contents-1]
	surface.text(store,roman,300-text_width(roman),93,Color.BLACK)

func draw_dialog(surface) -> void:
	if dialog.is_empty():
		return
	surface.rect(5,16,74,65,Color.BLACK)
	surface.rect(6,17,72,63,Color.WHITE)
	var phase = int((host.tick-dialog.start)/12)
	for item in [[82 if host.character=="girl" else 81,25,1 if host.character=="girl" else 8],[83,1,33],[84,79,33],[85,29,81],[86+(phase&1),7,40],[88+[0,1,2,1][phase&3],43,40]]:
		surface.draw(store,"th",item[0],80,item[1],item[2],2 if item[0]>=86 else 10)
	for item in [[11,Color8(0,170,0)],[47,Color8(170,0,0)]]:
		for shadow in [true,false]:
			var x = item[0]+int(shadow)
			var y = 69+int(shadow)
			var color = Color.BLACK if shadow else item[1]
			surface.rect(x+1,y,24,9,color)
			surface.rect(x,y+1,26,7,color)
	surface.text(store,"Yes",16,70,Color.BLACK)
	surface.text(store,"No",55,70,Color.BLACK)
	var lines = {"copy":[["Copy song to",13],["your book?",17]],"erase":[["Erase the",20],["whole song?",14]],"erase_all":[["Erase ALL",20],["songs?",28]],"random":[["Create new",15],["song?",29]],"print":[["Print song?",15]]}[dialog.message]
	for i in lines.size():
		surface.text(store,lines[i][0],lines[i][1],19+10*i,Color.BLACK)
