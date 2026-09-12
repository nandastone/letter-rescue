extends SceneTree
## The modern page raster must preserve foreground art under text layout bounds.
const Render = preload("res://scripts/core/wr1_frontend_render.gd")
const Artwork = preload("res://scripts/core/wr1_clear_artwork.gd")
const Pages = preload("res://scripts/core/wr1_clear_pages.gd")

func _initialize() -> void:
	var original := Render.asset("WR1.22")
	Render.begin_reading(true)
	var page := Render.screen({"asset":"WR1.22", "x":32, "y":16})
	for y in range(51, 67):
		for x in range(24, 68):
			assert(page.get_pixel(x+32, y+16) == original.get_pixel(x,y), "Copyright heading erased character artwork at %s" % Vector2i(x,y))
	# These are independently chosen source-art regions, including details the
	# old layout-sized boxes cut through. Every pixel must survive unchanged.
	for item in [
		["WR1.22", Rect2i(0,0,68,67)],
		["WR1.22", Rect2i(82,51,13,1)],
		["WR1.22", Rect2i(83,52,11,1)],
		["WR1.22", Rect2i(86,53,7,1)],
		["WR1.22", Rect2i(88,54,4,1)],
		["WR1.20", Rect2i(0,0,192,55)],
		["WR1.33", Rect2i(215,88,40,55)],
		["WR1.33", Rect2i(119,109,82,1)],
		["WR1.33", Rect2i(119,120,82,1)],
		["WR1.30", Rect2i(242,85,40,36)],
		["WR1.31", Rect2i(111,132,40,1)],
		["WR1.21", Rect2i(0,147,320,53)],
		["MENU.WR", Rect2i(7,4,181,2)],
		["HELP.WR", Rect2i(7,4,153,2)],
		["WR1.26", Rect2i(61,5,49,1)],
	]:
		var source := Render.asset(item[0])
		var clean := Artwork.background(source,item[0])
		assert(clean.get_region(item[1]).get_data() == source.get_region(item[1]).get_data(), "Changed artwork: " + item[0])
	# No old letters or shadows may remain in these text-only panel interiors.
	for item in [
		["WR1.22", Rect2i(70,55,100,11), Color8(85,85,255)],
		["WR1.22", Rect2i(24,67,204,83), Color8(85,85,255)],
		["WR1.20", Rect2i(36,65,130,36), Color8(85,85,255)],
		["WR1.23", Rect2i(45,58,111,39), Color8(85,85,255)],
		["MENU.WR", Rect2i(7,6,181,13), Color8(255,85,85)],
		["MENU.WR", Rect2i(27,100,143,13), Color8(255,85,85)],
		["HELP.WR", Rect2i(7,6,153,13), Color8(255,85,85)],
		["HELP.WR", Rect2i(9,26,147,137), Color.WHITE],
		["WR1.11", Rect2i(180,14,125,120), Color.WHITE],
		["WR1.12", Rect2i(20,16,165,81), Color.WHITE],
		["WR1.33", Rect2i(53,9,217,79), Color8(255,85,85)],
		["WR1.34", Rect2i(53,9,217,95), Color8(255,85,85)],
		["WR1.21", Rect2i(140,25,170,105), Color8(85,85,255)],
	]:
		var clean := Artwork.background(Render.asset(item[0]),item[0])
		var rect: Rect2i = item[1]
		for y in range(rect.position.y,rect.end.y):
			for x in range(rect.position.x,rect.end.x):
				assert(clean.get_pixel(x,y) == item[2], "Old text remains: %s at %s" % [item[0],Vector2i(x,y)])
	# Moving a label cannot change the source background, even on a fresh cache.
	var heading: Dictionary = Pages.pages["WR1.22"][0]
	var old_rect: Array = heading.rect
	heading.rect = [0,0,320,200]
	Artwork.backgrounds.clear()
	Render.begin_reading(true)
	assert(Render.screen({"asset":"WR1.22", "x":32, "y":16}).get_data() == page.get_data())
	heading.rect = old_rect
	Render.text(page,"New text",32,67,15,9)
	assert(page.get_pixel(56,67) == original.get_pixel(24,51), "Dynamic label painted a background box")
	Render.begin_reading(false)
	assert(Render.screen({"asset":"WR1.22", "x":32, "y":16}).get_region(Rect2i(Vector2i(32,16),original.get_size())).get_data() == original.get_data(), "Legacy source changed")
	print("Clean artwork: preserved decorations, removed ink, independent layout and legacy source PASS")
	quit()
