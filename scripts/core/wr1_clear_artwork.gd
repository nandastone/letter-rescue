extends RefCounted
## Prepare text-free source pictures once, before page composition. Cleanup
## coordinates describe original ink, never the replacement label's bounds.
static var masks: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://data/wr1/clear_artwork.json"))
static var backgrounds: Dictionary = {}

static func background(source: Image, name: String) -> Image:
	name = name.to_upper()
	if backgrounds.has(name): return backgrounds[name]
	var clean := source.duplicate()
	if name == "WR1.21":
		_title_background(clean, source)
	for area in masks.get(name, []):
		var r: Array = area.rect
		var rect := Rect2i(int(r[0]), int(r[1]), int(r[2]), int(r[3]))
		rect = rect.intersection(Rect2i(Vector2i.ZERO, source.get_size()))
		var ink: Array[Color] = []
		for color in area.ink: ink.append(Color(color))
		for y in range(rect.position.y, rect.end.y):
			for x in range(rect.position.x, rect.end.x):
				if source.get_pixel(x, y) in ink:
					clean.set_pixel(x, y, Color(area.background))
		# Some character outlines share a colour with the adjacent lettering.
		# Restore those source pixels explicitly instead of erasing their shape.
		for keep in area.get("preserve", []):
			var rect_to_keep := Rect2i(int(keep[0]),int(keep[1]),int(keep[2]),int(keep[3]))
			clean.blit_rect(source,rect_to_keep,rect_to_keep.position)
	backgrounds[name] = clean
	return clean

static func _title_background(clean: Image, source: Image) -> void:
	# Extend the board's surviving top and right edges behind the old logo.
	# The yellow episode strip and the characters in front of it stay intact.
	for y in range(130):
		for x in range(130, 320):
			if x < 134 and y >= 32: continue
			var color := source.get_pixel(120, y) if y < 25 else Color8(85,85,255)
			if y < 19 or x >= 315: color = Color8(85,255,255)
			elif y >= 25 and x >= 310: color = source.get_pixel(x,180)
			clean.set_pixel(x,y,color)
	for y in range(132, 147):
		for x in range(180, 275):
			if source.get_pixel(x,y) == Color8(170,0,0): clean.set_pixel(x,y,Color8(255,255,85))
