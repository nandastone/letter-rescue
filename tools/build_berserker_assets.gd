extends SceneTree
## Pack the generated four-pose source into the engine's animation indices.
## godot --headless --path . --script tools/build_berserker_assets.gd
func _initialize() -> void:
	var source := Image.load_from_file("res://tools/art/berserker-source.png")
	source.convert(Image.FORMAT_RGBA8)
	# Remove connected neutral background; enclosed eye highlights stay intact.
	var pending: Array[Vector2i] = [Vector2i.ZERO]
	while not pending.is_empty():
		var p: Vector2i = pending.pop_back()
		if p.x < 0 or p.y < 0 or p.x >= source.get_width() or p.y >= source.get_height():
			continue
		var c := source.get_pixelv(p)
		if c.a == 0 or c.v < 0.48 or c.s > 0.15:
			continue
		source.set_pixelv(p, Color.TRANSPARENT)
		for d in [Vector2i.LEFT, Vector2i.RIGHT, Vector2i.UP, Vector2i.DOWN]:
			pending.append(p + d)
	var palette: Array[Color] = [Color.BLACK, Color.WHITE, Color("#555555"), Color("#aaaaaa"), Color("#ff5555"), Color("#aa0000"), Color("#00ffff"), Color("#00aa00"), Color("#00ff00"), Color("#ffff00"), Color("#0000ff"), Color("#aa5500")]
	for row in range(2):
		var poses: Array[Image] = []
		for col in range(4):
			var cell := source.get_region(Rect2i(col * 443, row * 443, 443, 443))
			var cropped := cell.get_region(cell.get_used_rect())
			cropped.resize(roundi(cropped.get_width() * 32.0 / cropped.get_height()), 32, Image.INTERPOLATE_NEAREST)
			# EGA palette and binary alpha avoid soft/high-resolution edges.
			for y in range(cropped.get_height()):
				for x in range(cropped.get_width()):
					var c := cropped.get_pixel(x,y)
					if c.a == 0:
						continue
					var nearest := Color.BLACK
					var distance := INF
					for candidate in palette:
						var difference := Vector3(c.r-candidate.r,c.g-candidate.g,c.b-candidate.b).length_squared()
						if difference < distance:
							distance = difference
							nearest = candidate
					cropped.set_pixel(x,y,nearest)
			var pose := Image.create(48,40,false,Image.FORMAT_RGBA8)
			# Anchor the torso, not the barrel: run/recoil extend farther behind.
			var offsets := [12, 7, 8, 12]
			pose.blit_rect(cropped, Rect2i(Vector2i.ZERO,cropped.get_size()), Vector2i(offsets[col],8))
			poses.append(pose)
		var atlas := Image.create(48*28,40,false,Image.FORMAT_RGBA8)
		for frame in range(28):
			var pose_index := 0
			if frame in [4,6,8,14,16,18,10,20,24,25]:
				pose_index = 1
			elif frame == 26:
				pose_index = 2
			elif frame == 27:
				pose_index = 3
			var pose: Image = poses[pose_index].duplicate()
			atlas.blit_rect(pose,Rect2i(0,0,48,40),Vector2i(frame*48,0))
		var character := "girl" if row == 0 else "boy"
		assert(atlas.save_png("res://assets/sprites/berserker_%s.png" % character) == OK)
	print("Packed both 28-frame berserker atlases")
	quit()
