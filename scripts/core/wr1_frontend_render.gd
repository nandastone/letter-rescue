extends RefCounted
## Source-derived 320x200 frontend pages; gameplay rasterization is separate.
const Text = preload("res://scripts/core/wr1_text.gd")
const PALETTE := [Color8(0,0,0),Color8(0,0,170),Color8(0,170,0),Color8(0,170,170),
	Color8(170,0,0),Color8(170,0,170),Color8(170,85,0),Color8(170,170,170),
	Color8(85,85,85),Color8(85,85,255),Color8(85,255,85),Color8(85,255,255),
	Color8(255,85,85),Color8(255,85,255),Color8(255,255,85),Color8(255,255,255)]
static var data: Dictionary = {}
static var assets: Dictionary = {}
static var reading := false
static var reading_runs: Array = []

static func begin_reading(active: bool) -> void:
	reading = active
	reading_runs = []

static func align_reading(rect: Rect2, alignment: int = HORIZONTAL_ALIGNMENT_CENTER, pixels: int = 9) -> void:
	if not reading or reading_runs.is_empty(): return
	reading_runs.back().rect = rect
	reading_runs.back().align = alignment
	reading_runs.back().pixels = pixels

static func reading_asset(name: String, x: int, y: int) -> void:
	if reading:
		reading_runs.append_array(preload("res://scripts/core/wr1_clear_pages.gd").labels(name, Vector2i(x,y)))

static func display_asset(name: String) -> Image:
	var source := asset(name)
	return preload("res://scripts/core/wr1_clear_artwork.gd").background(source, name) if reading else source

static func metadata() -> Dictionary:
	if data.is_empty():
		data = JSON.parse_string(FileAccess.get_file_as_string("res://data/wr1/frontend.json"))
	return data

static func asset(name: String) -> Image:
	name = name.to_upper()
	if not assets.has(name):
		var result: Image = (load("res://assets/extracted/wr1_1_png/" + name + ".png") as Texture2D).get_image()
		result.convert(Image.FORMAT_RGBA8)
		# PCX six-bit palette expansion in Pillow yields 87/171. The original
		# EGA registers select exact 85/170 DAC values instead.
		for y in range(result.get_height()):
			for x in range(result.get_width()):
				var color := result.get_pixel(x,y)
				if color.r > 0.6 and color.r < 0.8 and color.g > 0.6 and color.g < 0.8 and color.b < 0.1:
					# The PCX header's yellow entry is reassigned by the game's EGA palette.
					color = PALETTE[12 if name == "WR1.21" else 6]
				result.set_pixel(x,y,Color(round(color.r*3.0)/3.0,round(color.g*3.0)/3.0,round(color.b*3.0)/3.0,color.a))
		assets[name] = result
	return assets[name]

static func blank(color: int = 11) -> Image:
	var result := Image.create(320, 200, false, Image.FORMAT_RGBA8)
	result.fill(PALETTE[color])
	return result

static func outline(image: Image, rect: Rect2i, color: int) -> void:
	image.fill_rect(Rect2i(rect.position, Vector2i(rect.size.x, 1)), PALETTE[color])
	image.fill_rect(Rect2i(rect.position, Vector2i(1, rect.size.y)), PALETTE[color])
	image.fill_rect(Rect2i(rect.position + Vector2i(0, rect.size.y-1), Vector2i(rect.size.x, 1)), PALETTE[color])
	image.fill_rect(Rect2i(rect.position + Vector2i(rect.size.x-1, 0), Vector2i(1, rect.size.y)), PALETTE[color])

static func text(image: Image, value: String, x: int, y: int, fg: int = 0, bg: int = 15) -> void:
	if reading and image.get_width() == 320:
		# The page already supplies its background. A transparent font run must
		# not repaint a BIOS-sized box over the artwork beneath it.
		# BIOS spaces also position columns around the illustrations. Preserve
		# that indentation before handing the visible text to a proportional font.
		var trimmed := value.strip_edges()
		var leading := value.length() - value.lstrip(" ").length()
		reading_runs.append({"rect":Rect2(x+leading*8-1,y-1,trimmed.length()*8+2,10), "text":trimmed.replace(String.chr(156), "£"), "color":PALETTE[fg], "pixels":8, "align":HORIZONTAL_ALIGNMENT_LEFT})
		return
	Text.draw(image, value, Vector2i(x,y), PALETTE[fg], PALETTE[bg])

static func picture(image: Image, name: String, x: int, y: int) -> void:
	var source := display_asset(name)
	image.blit_rect(source, Rect2i(Vector2i.ZERO, source.get_size()), Vector2i(x,y))
	if reading:
		var bounds := Rect2(Vector2(x,y),Vector2(source.get_size()))
		reading_runs = reading_runs.filter(func(run: Dictionary) -> bool: return not bounds.intersects(run.rect))
		reading_asset(name,x,y)

static func screen(entry: Dictionary) -> Image:
	var result := blank()
	# The original PCX loader addresses byte columns in four EGA planes.
	picture(result, entry.asset, int(entry.x) & ~7, int(entry.y))
	return result

static func menu(selected: int, resume: bool = false) -> Image:
	var source: Dictionary = metadata().menu
	var result := blank()
	picture(result, "MENU.WR", 60,10)
	# The lower atlas regions are reusable headings, covered by the menu fill.
	result.fill_rect(Rect2i(67,36,183,144), PALETTE[15])
	for i in range(source.entries.size()):
		var entry: Dictionary = source.entries[i]
		text(result, source.resume_text if i == 0 and resume else entry.text, int(entry.x),int(entry.y))
		align_reading(Rect2(85,36+i*10.5,162,13), HORIZONTAL_ALIGNMENT_LEFT, 10)
	if selected >= 0:
		text(result, source.cursor.text, 74,40+selected*10,4)
		align_reading(Rect2(73,36+selected*10.5,12,13), HORIZONTAL_ALIGNMENT_LEFT, 10)
	return result

static func selector(kind: String, selected: int) -> Image:
	var result := menu(-3)
	if reading: reading_runs.clear()
	result.fill_rect(Rect2i(67,36,183,144), PALETTE[15])
	var region: Dictionary = metadata().atlas_regions[kind+"_heading"]
	var r: Array = region.source_inclusive
	result.blit_rect(display_asset("MENU.WR"), Rect2i(int(r[0]),int(r[1]),int(r[2]-r[0]+1),int(r[3]-r[1]+1)),Vector2i(80,10))
	reading_asset("HEADING_"+kind.to_upper(),80,10)
	if kind == "difficulty":
		for entry in metadata().difficulty.entries:
			text(result,entry.text,int(entry.x),int(entry.y))
		text(result,"*",74,64+selected*12,4)
	return result

static func sound(selected: int, background: Image = null) -> Image:
	var result: Image = blank() if background == null else background.duplicate()
	result.blit_rect(asset("HELP.WR"),Rect2i(192,0,128,40),Vector2i(96,56))
	result.blit_rect(asset("HELP.WR"),Rect2i(192,152,128,40),Vector2i(96,96))
	text(result,"Sound",138,70)
	align_reading(Rect2(103,65,114,16))
	for i in range(3): text(result,metadata().sound.entries[i].text,114,82+i*12)
	text(result,"*",104,82+selected*12,4)
	return result

static func page(kind: String, index: int, context: Dictionary = {}) -> Image:
	var result := blank()
	result.fill_rect(Rect2i(4,4,312,192), PALETTE[15])
	outline(result,Rect2i(4,4,312,192),1)
	var rows: Array = metadata().pages[kind][index]
	for row in rows:
		var value := ""
		for code in row.bytes:
			value += String.chr(int(code)) # Preserve original BIOS/CP437 glyph indices.
		text(result,value,int(row.x),int(row.y),1)
		var heading: bool = row == rows[0] and (kind in ["ordering", "bbs"] or kind == "about" and index == 0 or kind == "instructions" and index in [0,4])
		if heading: align_reading(Rect2(6,int(row.y)-2,308,13))
		if kind == "ordering" and index == 2 and int(row.y) == 26:
			align_reading(Rect2(6,24,308,13))
		if kind == "ordering" and index == 9 and int(row.y) in [136,146,156]:
			align_reading(Rect2(88,int(row.y)-1,222,10), HORIZONTAL_ALIGNMENT_LEFT, 8)
	text(result,"Press any key to continue",48,180,4)
	align_reading(Rect2(6,177,308,15))
	for command in metadata().illustrations[kind][index]:
		illustration(result,command,context)
	return result

static func illustration(image: Image, command: Dictionary, context: Dictionary) -> void:
	var source: Image
	var rect: Rect2i
	var destination := Vector2i(int(command.destination[0]),int(command.destination[1]))
	var masked := false
	match command.kind:
		"mystery_letter":
			var letter: String = str(context.get("mystery_word",context.get("words",["toe"])[0])).left(1).to_lower()
			var code := clampi(letter.unicode_at(0)-97,0,25)
			source = Image.create(16,16,false,Image.FORMAT_RGBA8)
			source.fill(PALETTE[int(context.get("background_color",11))])
			var letters: Image = (load("res://assets/sprites/wr1_letters.png") as Texture2D).get_image()
			source.blend_rect(letters,Rect2i((code%9)*16,(code/9)*16,16,16),Vector2i.ZERO)
			rect = Rect2i(0,0,16,16)
		"atlas":
			var sheet: String = command.sheet
			if sheet == "current_BACKn.WR": sheet = "BACK%d.WR" % int(context.get("tileset",3))
			source = asset(sheet)
			var r: Array = command.source_inclusive
			rect = Rect2i(int(r[0]),int(r[1]),int(r[2]-r[0]+1),int(r[3]-r[1]+1))
		"sprite":
			source = (load("res://"+command.file) as Texture2D).get_image()
			source.convert(Image.FORMAT_RGBA8)
			rect = Rect2i(Vector2i.ZERO,source.get_size())
			masked = true
		"player_sprite":
			source = (load("res://assets/sprites/wr1_%s.png" % ("girl" if int(context.get("character",1)) == 1 else "boy")) as Texture2D).get_image()
			source.convert(Image.FORMAT_RGBA8)
			rect = Rect2i(int(command.frame)*24,0,24,32)
			masked = true
		"word_panel":
			var word: String = context.get("words",["toe","pot"])[int(command.slot)]
			source = Image.create(72,18,false,Image.FORMAT_RGBA8)
			source.fill(Color.BLACK)
			source.fill_rect(Rect2i(2,1,69,15),Color.WHITE)
			text(source,word,32-word.length()*4,4)
			rect = Rect2i(0,0,72,18)
		"picture":
			var word: String = context.get("words",["toe","pot"])[int(command.slot)]
			source = preload("res://scripts/core/wr1_pictures.gd").load_picture(word).get_image()
			rect = Rect2i(0,0,24,24)
	if source != null:
		if masked: image.blend_rect(source,rect,destination)
		else: image.blit_rect(source,rect,destination)
		if reading and command.kind == "word_panel":
			image.fill_rect(Rect2i(destination+Vector2i(2,1),Vector2i(69,15)),Color.WHITE)
			reading_runs.append({"rect":Rect2(Vector2(destination+Vector2i(2,1)),Vector2(69,15)), "text":str(context.get("words",["toe","pot"])[int(command.slot)]).to_lower(), "color":Color.BLACK, "pixels":12})
		if reading and command.kind == "mystery_letter":
			image.fill_rect(Rect2i(destination,Vector2i(16,16)), PALETTE[int(context.get("background_color",11))])
			reading_runs.append({"rect":Rect2(Vector2(destination),Vector2(16,16)), "text":str(context.get("mystery_word",context.get("words",["toe"])[0])).left(1).to_lower(), "color":PALETTE[14], "pixels":12})
		if reading and command.kind == "atlas":
			if command.sheet == "STATIC.WR" and int(command.source_inclusive[0]) == 208:
				image.fill_rect(Rect2i(destination+Vector2i(6,4),Vector2i(13,15)), Color.WHITE)
				reading_runs.append({"rect":Rect2(Vector2(destination+Vector2i(5,3)),Vector2(15,17)), "text":"?", "color":Color.BLACK, "pixels":14})
			elif command.sheet == "current_BACKn.WR" and int(command.source_inclusive[0]) == 304:
				image.fill_rect(Rect2i(destination+Vector2i(1,5),Vector2i(12,6)), PALETTE[13])
				reading_runs.append({"rect":Rect2(Vector2(destination+Vector2i(0,3)),Vector2(14,10)), "text":"book", "color":PALETTE[14], "pixels":5})

static func player_screen(kind: String, name: String, character: int, score: int, level: int, cursor: int = 0) -> Image:
	var source: Dictionary = metadata().player
	var result := blank()
	picture(result,source.base_asset,0,0)
	if kind == "name":
		text(result,name,48,126,15,3)
		if reading:
			reading_runs.back().text = name
			reading_runs.back().caret = cursor
		else:
			outline(result,Rect2i(48+cursor*8,126,10,9),15)
	else:
		var overlay: Dictionary = source.new_overlay if kind == "character" else source.resume_overlay
		picture(result,overlay.asset,int(overlay.x),int(overlay.y))
		if kind == "character":
			for choice in source.characters:
				var r: Array = choice.rectangle
				outline(result,Rect2i(int(r[0]),int(r[1]),int(r[2]-r[0]+1),int(r[3]-r[1]+1)),14 if choice.value == character else 4)
				for inset in [-1,1]:
					outline(result,Rect2i(int(r[0])+inset,int(r[1])+inset,int(r[2]-r[0]+1)-2*inset,int(r[3]-r[1]+1)-2*inset),14 if choice.value == character else 4)
		else:
			text(result,str(score),103-str(score).length()*4,98,15,3)
			align_reading(Rect2(55,96,97,14))
			text(result,str(level),103-str(level).length()*4,132,15,3)
			align_reading(Rect2(55,130,97,14))
	return result
