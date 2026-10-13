extends RefCounted
## Original stage composition; keeps the activity's control flow independent.
var activity: WeakRef
var store
var tables: Dictionary
var surface
var bright_images: Dictionary = {}
var mask_images: Dictionary = {}
var heading_glyphs: Dictionary = {}

func _init(theater) -> void:
	activity = weakref(theater)
	store = theater.store
	tables = theater.tables

func shape(id: int, palette: int, x: int, y: int, mode: int = 10, clip: Array = []) -> void:
	surface.draw(store,"modules",id,palette,x,y,mode,clip)

func mask(archive: String, id: int, x: int, y: int, white: bool = false) -> void:
	var key = "%s:%d:%s"%[archive,id,white]
	if not mask_images.has(key):
		var colors: Array = []
		colors.resize(256)
		colors.fill([255,255,255] if white else [0,0,0])
		mask_images[key] = store.raster(store.shape(archive,id),colors,true)
	surface.blit(mask_images[key],x,y)

func color(c: int) -> Color:
	var rgb = store.palette("modules",3000).colors[[6,12,14,10][c]]
	return Color8(rgb[0],rgb[1],rgb[2])

func measure(value: String, heading: bool = false) -> int:
	var font = store.data.heading_font if heading else store.data.font
	var width = 0
	for character in value:
		var glyph = font.get(str(character.unicode_at(0)))
		width += int(glyph[0]) if glyph!=null else 3 if heading else 4
		if heading:
			width += 1
	return width

func heading(value: String, x: int, y: int) -> void:
	for character in value:
		var code = str(character.unicode_at(0))
		var glyph = store.data.heading_font.get(code)
		if glyph!=null:
			if glyph[0]>0 and glyph[1]>0:
				if not heading_glyphs.has(code):
					heading_glyphs[code] = store.raster(glyph,[[0,0,0],[0,0,0]],true)
				surface.blit(heading_glyphs[code],x,y)
			x += int(glyph[0])+1
		else:
			x += 4

func action_preview(a, selected: Array) -> void:
	if selected[1]<0:
		return
	if a.preview!=null and not a.preview.done:
		a.preview.draw(surface)
	else:
		var action = selected[1]
		var id = 3050+tables.action_preview_shapes[action]
		var raw = store.shape("modules",id)
		var offset = tables.action_preview_offsets[action]
		shape(id,3050,285-int(raw[0]/2)+offset[1],109-int(raw[1]/2)+offset[0])

func draw_sentence(a, selected: Array) -> void:
	var lines: Array = []
	var remaining: String = a.sentence(selected)
	var offset = 0
	while not remaining.is_empty():
		var end = remaining.length()
		while end>0 and measure(remaining.left(end))>200:
			end -= 1
		if end<remaining.length():
			var space = remaining.rfind(" ",end-1)
			if space>0:
				end = space
		lines.append({"value":remaining.left(end),"offset":offset})
		offset += end+1
		remaining = remaining.substr(maxi(1,end)).strip_edges(true,false)
	var phrase_start = 0
	var highlight: Array = []
	for c in (a.order if a.stage_order==null else a.stage_order):
		var value: String = a.phrase(c,selected)
		if value.is_empty():
			continue
		if c==a.presenting:
			highlight = [phrase_start,phrase_start+value.length()+1]
		phrase_start += value.length()+1
	for i in mini(2,lines.size()):
		var line = lines[i]
		var value: String = (" " if i else "")+line.value
		var start = line.offset-(1 if i else 0)
		var x = 100+int(floor((200-measure(line.value))/2.0))
		var y = (176 if lines.size()>1 else 180)+i*10
		if not highlight.is_empty():
			var from = maxi(0,highlight[0]-start)
			var to = mini(value.length(),highlight[1]-start)
			if to>from:
				surface.text(store,value.substr(from,to-from),x+measure(value.left(from))+1,y,color(a.presenting),[176,100,195,300])
		surface.text(store,value,x,y,Color.BLACK,[176,100,195,300])

func draw(target) -> void:
	surface = target
	var a = activity.get_ref()
	var selected: Array = a.selection if a.stage_selection==null else a.stage_selection
	var options: bool = a.options if a.stage_options==null else a.stage_options
	shape(3041,3040,0,0,2)
	if not options:
		var place = selected[2]
		var time = selected[3]
		if place>=0:
			var id = 3100+3*place+(0 if time<0 else tables.time_background_variant[time])
			if ((a.playing and a.valid_play and a.presenting==2) or a.preview_category==2) and int((a.tick-a.phase_start)/12)%2==0:
				if not bright_images.has(id):
					var colors: Array = store.palette("modules",id).colors.duplicate(true)
					for i in range(1,colors.size()):
						for channel in 3:
							var n = mini(63,int(floor(colors[i][channel]*63.0/255+0.5))+6)
							colors[i][channel] = (n<<2)|(n>>4)
					bright_images[id] = store.raster(store.shape("modules",3101+3*place),colors,true)
				surface.blit(bright_images[id],96,51)
			else:
				shape(3101+3*place,id,96,51)
		if time>=0:
			var row = tables.time_shapes[time]
			var pos = tables.time_positions_by_place[maxi(0,place)][time]
			var frame = 0 if a.weather_start==null else 1+int((a.tick-a.weather_start)/row[3])
			if not (a.preview_category==3 and a.tick<a.preview_blink_until and int((a.tick-a.phase_start)/12)%2==0):
				shape(3120+row[1]+frame,3120,pos[1],pos[0])
		if place>=0:
			for item in a.props[place]:
				shape(item.id,item.palette,item.x,item.y)
		var hidden = ((a.playing and a.valid_play and a.presenting==0) or a.preview_category==0) and int((a.tick-a.phase_start)/12)%2==0
		if not hidden:
			if a.actor_animation!=null:
				a.actor_animation.draw(surface)
			elif selected[0]>=0:
				var actor = selected[0]
				var b = a.actor_rect()
				var off = tables.actor_shape_offsets[actor]
				shape(3201+100*actor,3200+100*actor,b[1]+off[1],b[0]+off[0])
	var curtain = tables.curtain_shapes[a.curtain]
	var pos = tables.curtain_positions[a.curtain]
	shape(3040+curtain[0],3040,pos[1],pos[0])
	if curtain[1]:
		shape(3040+curtain[1],3040,pos[3],pos[2])
	shape(3049,3040,259,73)
	for c in 4:
		shape(3003+c+(4 if a.mix_up and a.selection[c]>=0 else 0),3000,27,30+32*c)
	for item in [[3014,20,181],[3015,39,180],[3016,299,24],[3022,304,1],[3023,1,181]]:
		shape(item[0],3000,item[1],item[2])
	if a.category>=0 and a.category<4:
		var b = tables.ui_rects[12+a.category]
		surface.rect(b[1],b[0],b[3]-b[1],b[2]-b[0],color(a.category))
	for item in [[3025,16,53],[3026,19,85],[3027,27,117],[3028,28,149]]:
		mask("modules",item[0],item[1],item[2])
	if options:
		shape(3039,3034,112,77)
		shape(3001,3000,182,79)
		if a.mix_up:
			mask("th",9,184,81,true)
		if a.props_enabled:
			mask("th",9,184,97,true)
	elif not a.opening_editor:
		shape(3035+a.director,3034,61,155)
	if a.props_enabled:
		shape(3024,3000,1,163)
		shape(3011,3000,24,163)
	action_preview(a,selected)
	draw_sentence(a,selected)
	if a.mix_up:
		shape(3012,3000,105,49)
		shape(3013,3000,243,47)
		shape(3002,3000,129,43)
		for i in 4:
			var c = a.order[i]
			if a.selection[c]<0 or (a.token_sprite!=null and a.token_sprite.category==c) or (a.drag.get("type")=="token" and a.drag.active and a.drag.category==c):
				continue
			var b = tables.ui_rects[23+i]
			var raw = store.shape("modules",3003+c)
			if a.presenting==c:
				surface.rect(b[1],b[0],b[3]-b[1],b[2]-b[0],color(c))
			shape(3003+c,3000,int((b[1]+b[3])/2)-int(raw[0]/2),int((b[0]+b[2])/2)-int(raw[1]/2))
	if a.feedback or a.success_feedback:
		var message = store.data.strings["modules:3070"][a.feedback]
		surface.text(store,message,183-int(measure(message)/2),20,Color.BLACK)
		var icons = {2:[[3018,135],[3019,178]],3:[[3018,149]],4:[[3019,149]],5:[[3018,138],[3019,213]]}
		if not a.success_feedback:
			for item in icons.get(a.feedback,[]):
				shape(item[0],3000,item[1],18)
		if a.feedback in [5,6]:
			var corrected = a.corrected_order(a.feedback)
			for i in 4:
				var c = corrected[i]
				if a.selection[c]<0:
					continue
				var b = tables.ui_rects[23+i]
				var raw = store.shape("modules",3018+c)
				shape(3018+c,3000,int((b[1]+b[3])/2)-int(raw[0]/2),int((b[0]+b[2])/2)-23-int(raw[1]/2))
	if a.category>=0 and a.correct_notice_until==null:
		var name = store.data.strings["modules:3060"][a.category]
		heading(name,188-int(measure(name,true)/2),4)
		var boxes = a.choice_bounds()
		for i in boxes.size():
			var b = boxes[i]
			var id: int
			var palette: int
			var x: int
			var y: int
			if a.category==0:
				id = 3981+i
				palette = 3980
				x = b[1]+2
				y = 42-int(store.shape("modules",id)[1])
			elif a.category==1:
				id = 3085+i
				palette = 3050
				x = tables.action_icon_positions[i][1]
				y = tables.action_icon_positions[i][0]
			else:
				if a.category==2:
					id = 3102+3*i
					palette = 3100+3*i
				elif a.category==3:
					id = 3120+tables.time_shapes[i][0]
					palette = 3120
				else:
					var place = a.selection[2]
					palette = 3175 if tables.prop_group[place] else 3145
					id = palette+tables.prop_first[place]+i
				var raw = store.shape("modules",id)
				x = int((b[1]+b[3])/2)-int(raw[0]/2)
				y = 28-int(raw[1]/2)
			shape(id,palette,x,y,2 if a.category==2 else 10)
	if a.correct_notice_until!=null:
		var message = store.data.strings["modules:3070"][7]
		surface.text(store,message,183-int(measure(message)/2),20,Color.BLACK)
	if a.token_sprite!=null:
		shape(3003+a.token_sprite.category,3000,a.token_sprite.x,a.token_sprite.y)
	if a.drag.get("type")=="token" and a.drag.active:
		shape(3003+a.drag.category,3000,a.drag.x,a.drag.y)
	if a.curtain_moving:
		shape(3040+curtain[0],3040,pos[1],pos[0])
		if curtain[1]:
			shape(3040+curtain[1],3040,pos[3],pos[2])
		shape(3049,3040,259,73)
		if not options and not a.opening_editor:
			action_preview(a,selected)
			var r = tables.ui_rects[7]
			var opened = tables.curtain_shapes[3]
			var p = tables.curtain_positions[3]
			shape(3041,3040,0,0,2,r)
			shape(3040+opened[0],3040,p[1],p[0],10,r)
			if opened[1]:
				shape(3040+opened[1],3040,p[3],p[2],10,r)
			shape(3035+a.director,3034,61,155)
