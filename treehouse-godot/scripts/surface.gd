extends RefCounted
var image: Image = Image.create(320, 200, false, Image.FORMAT_RGBA8)

func _init() -> void:
	image.fill(Color.BLACK)

func rect(x: int, y: int, w: int, h: int, color: Color) -> void:
	image.fill_rect(Rect2i(x,y,w,h).intersection(Rect2i(0,0,320,200)), color)

func blit(source: Image, x: int, y: int, transparent: bool = true, clip: Array = []) -> void:
	var bounds = Rect2i(0,0,320,200)
	if not clip.is_empty():
		if clip[3]<=clip[1] or clip[2]<=clip[0]:
			return
		bounds = bounds.intersection(Rect2i(int(clip[1]),int(clip[0]),int(clip[3]-clip[1]),int(clip[2]-clip[0])))
	var destination = Rect2i(x,y,source.get_width(),source.get_height()).intersection(bounds)
	if not destination.has_area():
		return
	var region = Rect2i(destination.position-Vector2i(x,y), destination.size)
	if transparent:
		image.blit_rect_mask(source, source, region, destination.position)
	else:
		image.blit_rect(source, region, destination.position)

func draw(store, archive: String, id: int, palette: int, x: int = 0, y: int = 0, mode: int = 10, clip: Array = []) -> void:
	assert(mode in [0,2,10], "Unsupported original drawing mode")
	blit(store.image(archive,id,palette,mode==10),x,y,mode==10,clip)

func text(store, value: String, x: int, y: int, color: Color, clip: Array = []) -> void:
	for character in value:
		var code = character.unicode_at(0)
		if store.data.font.has(str(code)):
			var glyph = store.glyph(code,color)
			blit(glyph,x,y,true,clip)
			x += glyph.get_width()
		else:
			x += 4
