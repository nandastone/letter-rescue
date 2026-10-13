extends RefCounted
var owner_ref: WeakRef
var store
var tables: Dictionary
var surface
var masks: Dictionary = {}
var headings: Dictionary = {}

func _init(nature) -> void:
	owner_ref = weakref(nature)
	store = nature.store
	tables = nature.tables

func draw_shape(id: int, palette: int, x: int, y: int, mode: int = 10, archive: String = "modules", clip: Array = []) -> void:
	surface.draw(store,archive,id,palette,x,y,mode,clip)

func fill(b: Array, color: Color) -> void:
	surface.rect(b[1],b[0],b[3]-b[1],b[2]-b[0],color)

func color(palette: int, index: int) -> Color:
	var rgb = store.palette("modules",palette).colors[index]
	return Color8(rgb[0],rgb[1],rgb[2])

func center(id: int, b: Array, palette: int = 5650, background = null, archive: String = "modules") -> void:
	if background!=null:
		fill(b,background)
	var shape = store.shape(archive,id)
	draw_shape(id,palette,int((b[1]+b[3])/2)-int(shape[0]/2),int((b[0]+b[2])/2)-int(shape[1]/2),10,archive)

func width(value: String, heading: bool = false) -> int:
	var result = 0
	var font = store.data.heading_font if heading else store.data.font
	for character in value:
		var glyph = font.get(str(character.unicode_at(0)))
		result += int(glyph[0]) if glyph!=null else 3 if heading else 4
		if heading:
			result += 1
	return result

func text(value: String, x: int, y: int, clip: Array = []) -> void:
	surface.text(store,value,x,y,Color.BLACK,clip)

func heading(value: String, x: int, y: int) -> void:
	for character in value:
		var code = str(character.unicode_at(0))
		var glyph = store.data.heading_font.get(code)
		if glyph==null:
			x += 4
			continue
		if glyph[0]>0 and glyph[1]>0:
			if not headings.has(code):
				headings[code] = store.raster(glyph,[[0,0,0],[0,0,0]],true)
			surface.blit(headings[code],x,y)
		x += int(glyph[0])+1

func centered_text(value: String, b: Array) -> void:
	text(value,int((b[1]+b[3])/2)-int(width(value)/2),int((b[0]+b[2])/2)-4)

func mask(archive: String, id: int, x: int, y: int, foreground: Color) -> void:
	var key = "%s:%d:%s"%[archive,id,foreground.to_html()]
	if not masks.has(key):
		var palette: Array = []
		palette.resize(256)
		palette.fill([foreground.r8,foreground.g8,foreground.b8])
		masks[key] = store.raster(store.shape(archive,id),palette,true)
	surface.blit(masks[key],x,y)

func draw(target) -> void:
	surface = target
	var n = owner_ref.get_ref()
	var r = tables.rectangles
	draw_shape(5401,5400,0,0,2)
	for i in 7:
		center(5651+i,r[i+1],5650,color(5650,8 if i==n.attribute else 2))
	centered_text(n.animal_name(n.selected) if n.fact_open else n.value_names()[n.values[n.attribute]],r[12])
	var available = n.available_classes()
	for i in 10:
		if not i in available:
			fill(r[14+i],Color8(170,170,170))
			continue
		var substitute = -1
		var v = n.values[n.attribute]
		if n.time==1 and i==0 and ((n.attribute==3 and v==1) or (n.attribute==2 and v==0)):
			substitute = 60
		if n.time==1 and i==7 and n.attribute==4 and v==4:
			substitute = 70
		if n.time==0 and i==0 and n.attribute==3 and v==1:
			substitute = 63
		if n.time==0 and i==6 and ((n.attribute==3 and v==2) or (n.attribute==4 and v==1)):
			substitute = 79
		var animal = tables.animals[substitute] if substitute>=0 else null
		center(animal.small if animal!=null else tables.class_icons[n.time][i],r[14+i],animal.palette if animal!=null else 5650,color(5650,8) if i==n.category else Color.WHITE)
	if n.category>=0:
		centered_text(n.class_names()[n.category],[99,6,108,124])
	for item in n.thumbnails():
		var a = item.animal
		if n.fact_open and n.selected==a.id:
			var b = item.rect
			surface.rect(b[1]+1,b[0],b[3]-b[1]-2,b[2]-b[0],color(5650,8))
			surface.rect(b[1],b[0]+1,b[3]-b[1],b[2]-b[0]-2,color(5650,8))
		draw_shape(a.small,a.palette,item.rect[1],item.rect[0])
	if n.fact_open:
		fill(r[26],Color.WHITE)
		var y = 49
		var line = ""
		for word in n.fact().split(" "):
			if not line.is_empty() and width(line+" "+word)>120:
				text(line,5,y,r[26])
				y += 10
				line = word
			else:
				line += ("" if line.is_empty() else " ")+word
		if not line.is_empty():
			text(line,5,y,r[26])
	for i in 3:
		center(5659+i,r[9+i],5650,color(5650,2))
	if n.time==0:
		draw_shape(5501,5500,127,4)
	else:
		draw_shape(5501,5501,127,4,10,"modules",[39,127,196,317])
		draw_shape(5511,5510,128,4)
	for i in n.objects[n.time].size():
		if not n.drag.is_empty() and i==n.objects[n.time].size()-1:
			continue
		var object = n.objects[n.time][i]
		var a = tables.animals[object.id]
		draw_shape(a.large+object.blink,a.palette,object.x,object.y)
	draw_shape(8,6,304,1,10,"th")
	if not n.drag.is_empty():
		var object = n.drag.object
		var a = tables.animals[object.id]
		draw_shape(a.large,a.palette,object.x,object.y)
	if not n.erase_effect.is_empty():
		var e = n.erase_effect
		if e.id==923:
			var object = e.object
			var a = tables.animals[object.id]
			draw_shape(a.large,a.palette,object.x,object.y)
		var shape = store.shape("th",e.id)
		draw_shape(e.id,900,e.x-int(shape[0]/2),e.y-int(shape[1]/2),10,"th")

func draw_dialog(target) -> void:
	surface = target
	var n = owner_ref.get_ref()
	var p = n.dialog
	var lines: Array = []
	var rest: String = p.message
	while not rest.is_empty():
		var count = 0
		var w = 0
		var last = 0
		while count<rest.length():
			w += width(rest[count])
			if w>116:
				break
			if rest[count] in [" ","-"] or (count+1<rest.length() and rest[count+1]==" "):
				last = count+1
			count += 1
		if count!=rest.length():
			count = last if last else maxi(1,count)
		lines.append(rest.left(count))
		rest = rest.substr(count).trim_prefix(" ")
	surface.rect(6,98,118,68,Color.WHITE)
	for i in lines.size():
		text(lines[i],65-int(width(lines[i])/2),112-5*lines.size()+10*i)
	var phase = int((n.tick-p.start)/12)
	var buttons = [["OK",52,Color8(170,0,0)]] if p.get("empty",false) else [["Yes",20,Color8(0,170,0)],["No",84,Color8(170,0,0)]]
	if p.get("empty",false):
		draw_shape(86,80,48,126,2,"th")
	else:
		draw_shape(86+(phase&1),80,16,126,2,"th")
		draw_shape(88+[0,1,2,1][phase&3],80,80,126,2,"th")
	for item in buttons:
		var x = item[1]
		surface.rect(x+2,156,24,9,Color.BLACK)
		surface.rect(x+1,157,26,7,Color.BLACK)
		surface.rect(x+1,155,24,9,item[2])
		surface.rect(x,156,26,7,item[2])
		text(item[0],x+13-int(width(item[0])/2),156)
