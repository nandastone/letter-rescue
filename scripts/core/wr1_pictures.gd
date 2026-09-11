extends RefCounted
## Original pictures are opaque 24x24 page copies, using the gameplay palette.
## Some decoded files omit a final border column/row; the page starts black.

static func load_picture(word: String, frame: int = 0) -> Texture2D:
	var path := "res://assets/extracted/wr1_2_png/%s%s.WR1.png" % [word.to_upper(), "2" if frame == 1 else ""]
	if frame == 1 and not ResourceLoader.exists(path):
		return load_picture(word, 0) # 62fe..6337 copies frame0 when WORD2 is absent.
	if not ResourceLoader.exists(path):
		push_warning("Missing original picture: " + path)
		return null
	var source: Image = (load(path) as Texture2D).get_image()
	source.convert(Image.FORMAT_RGBA8)
	for y in range(source.get_height()):
		for x in range(source.get_width()):
			# The archive decoder's default palette has yellow at index6.
			# WR1's live gameplay palette uses EGA brown (native GUN verified).
			if source.get_pixel(x, y) == Color8(170, 170, 0):
				source.set_pixel(x, y, Color8(170, 85, 0))
	var image := Image.create(24, 24, false, Image.FORMAT_RGBA8)
	image.fill(Color.BLACK)
	image.blit_rect(source, Rect2i(0, 0, 24, 24), Vector2i.ZERO)
	return ImageTexture.create_from_image(image)
