extends RefCounted
## Transcribed lettering from the shipped PCX artwork. Rectangles are local to
## each picture and erase only the old ink, within its existing panel.
static var pages: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://data/wr1/clear_text_pages.json"))

static func apply(image: Image, name: String, offset: Vector2i) -> Array:
	var runs: Array = []
	for entry in pages.get(name.to_upper(), []):
		var r: Array = entry.rect
		var rect := Rect2i(int(r[0])+offset.x,int(r[1])+offset.y,int(r[2]),int(r[3]))
		if entry.has("erase"):
			for area in entry.erase:
				image.fill_rect(Rect2i(int(area[0])+offset.x,int(area[1])+offset.y,int(area[2]),int(area[3])), Color(entry.background))
		else:
			image.fill_rect(rect, Color(entry.background))
		if not entry.text.is_empty():
			runs.append({"rect":Rect2(rect), "text":entry.text, "color":Color(entry.get("color", "ffffff")), "pixels":int(entry.get("pixels", 10)), "align":HORIZONTAL_ALIGNMENT_LEFT if entry.get("align", "center") == "left" else HORIZONTAL_ALIGNMENT_CENTER})
	return runs
