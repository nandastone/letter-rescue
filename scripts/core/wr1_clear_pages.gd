extends RefCounted
## Text layout is independent of the clean source artwork. These rectangles
## position transparent labels; they never paint into a picture.
static var pages: Dictionary = {}
static var content_episode: int = 0

static func labels(name: String, offset: Vector2i) -> Array:
	if content_episode != Episode.current:
		content_episode = Episode.current
		pages = JSON.parse_string(FileAccess.get_file_as_string(Episode.data_path("clear_text_pages.json")))
	name = name.to_upper().replace("WR1.", "WR%d." % Episode.current)
	var runs: Array = []
	for entry in pages.get(name.to_upper(), []):
		var r: Array = entry.rect
		var rect := Rect2i(int(r[0])+offset.x,int(r[1])+offset.y,int(r[2]),int(r[3]))
		if not entry.text.is_empty():
			runs.append({"rect":Rect2(rect), "text":entry.text, "color":Color(entry.get("color", "ffffff")), "pixels":int(entry.get("pixels", 10)), "align":HORIZONTAL_ALIGNMENT_LEFT if entry.get("align", "center") == "left" else HORIZONTAL_ALIGNMENT_CENTER})
	return runs
