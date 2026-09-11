extends RefCounted
## Exact MSB-first BIOS 8x8 glyphs selected by the original executable.

static func draw(image: Image, text: String, origin: Vector2i, foreground: Color, background: Color) -> void:
	var font: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://data/wr1/bios_font.json"))
	for i in range(text.length()):
		var code := text.unicode_at(i)
		if code >= font.rows.size():
			code = 63
		for y in range(8):
			var bits := int(font.rows[code][y])
			for x in range(8):
				var pixel := origin + Vector2i(i * 8 + x, y)
				if pixel.x >= 0 and pixel.x < image.get_width() and pixel.y >= 0 and pixel.y < image.get_height():
					image.set_pixelv(pixel, foreground if bits & (128 >> x) else background)
