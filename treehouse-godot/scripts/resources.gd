extends RefCounted
## Source graphics and SCR instructions; no native screenshots or JS runtime.
var data: Dictionary
var images: Dictionary = {}

func _init(path: String = "res://data/original.json") -> void:
	data = JSON.parse_string(FileAccess.get_file_as_string(path))
	assert(not data.is_empty(), "Run tools/treehouse/build_godot.py first")
	# Original scene initializer recolors the girl's preview clothing.
	data.palettes["th:8001"].colors[9] = [16, 138, 255]
	data.palettes["th:8001"].colors[10] = [8, 93, 170]

func key(archive: String, id: int) -> String:
	return "%s:%d" % [archive, id]

func shape(archive: String, id: int) -> Array:
	return data.shapes[key(archive, id)]

func palette(archive: String, id: int) -> Dictionary:
	return data.palettes[key(archive, id)]

func raster(raw: Array, colors: Array, transparent: bool) -> Image:
	var indices = Marshalls.base64_to_raw(raw[2])
	var pixels = PackedByteArray()
	pixels.resize(indices.size() * 4)
	for i in indices.size():
		var color = colors[indices[i]]
		pixels[4*i] = int(color[0])
		pixels[4*i+1] = int(color[1])
		pixels[4*i+2] = int(color[2])
		pixels[4*i+3] = 0 if transparent and indices[i] == 0 else 255
	return Image.create_from_data(int(raw[0]), int(raw[1]), false, Image.FORMAT_RGBA8, pixels)

func image(archive: String, id: int, palette_id: int, transparent: bool) -> Image:
	var cache_key = "%s:%d:%d:%s" % [archive, id, palette_id, transparent]
	if not images.has(cache_key):
		images[cache_key] = raster(shape(archive, id), palette(archive, palette_id).colors, transparent)
	return images[cache_key]

func glyph(code: int, color: Color) -> Image:
	var cache_key = "font:%d:%s" % [code, color.to_html()]
	if not images.has(cache_key):
		images[cache_key] = raster(data.font[str(code)], [[0,0,0], [color.r8,color.g8,color.b8]], true)
	return images[cache_key]
