extends RefCounted
## Minimum CPU work that every ordinary page submission must complete. Terrain,
## actors, cards and text add work; this is not a complete renderer duration.
var graphics = preload("res://scripts/wr1_graphics_work.gd").new()
var descriptor: Dictionary
var cache := {}
var sprite_sizes := {}

func _init() -> void:
	graphics.configure()
	descriptor = JSON.parse_string(FileAccess.get_file_as_string("res://data/wr1/drawing_device.json"))
	var records: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://data/wr1/gruzzle_frames.json"))
	for record in records.frames:
		sprite_sizes[record.kind + str(int(record.index))] = [record.record[4], record.record[5]]

func _seconds(kind: String, args: Array, image_index: int = -1) -> float:
	var key := kind + str(args) + str(image_index)
	if cache.has(key):
		return cache[key]
	var device: Dictionary = descriptor.graphics.duplicate(true)
	device.args = args
	var path: Array
	if kind == "copy":
		path = graphics.copy_rect(device).work
	elif kind == "page":
		path = graphics.draw_page(device).work
	elif kind == "fill":
		path = graphics.fill_rect(device).work
	else:
		if kind.begins_with("entity:"):
			var size: Array = sprite_sizes[kind.trim_prefix("entity:")]
			var header := PackedByteArray(descriptor.player_images[0].header)
			header.encode_u16(10, int(size[0]) - 1)
			header.encode_u16(12, int(size[1]) - 1)
			header.encode_u16(20, ((int(size[0]) + 15) / 16) * 2)
			header.encode_u16(44, size[0])
			header.encode_u16(46, size[1])
			header.encode_u16(48, (int(size[0]) + 7) / 8)
			device.image_header = Array(header)
		else:
			device.image_header = descriptor.player_images[image_index].header
		path = graphics.masked_sprite(device)
	# Execute the recovered driver instructions on an empty hardware queue.
	# IRQ service and all omitted drawing can only add time to this bound.
	var cpu = preload("res://scripts/wr1_hardware.gd").new()
	cpu.cycle_left = 27000
	cpu.run_driver(path)
	var duration: float = cpu.observed_time() / 1000.0
	cache[key] = duration
	return duration

func minimum_seconds(page: int, previous_camera: Vector2i, state: RefCounted, tiled_background: bool, player_visible: bool, background_tiles: TileMapLayer = null, actor_draws: Array = [], foreground_tiles: TileMapLayer = null) -> float:
	var seconds := _seconds("page", [page])
	if tiled_background:
		var shift := (previous_camera - Vector2i(state.camera_x, state.camera_y)) * 8
		seconds += _seconds("copy", [page, 32 + shift.y, 16 + shift.x, 2, 183, 303, 32, 16])
		# The scrolling cache clears and repaints the newly exposed strips.
		var cx: int = state.camera_x
		var cy: int = state.camera_y
		var x0: int = cx / 2
		var y0: int = cy / 2
		var x1: int = x0 + (cx & 1) + 18
		var y1: int = y0 + 10
		if shift.x != 0:
			seconds += _seconds("fill", [2,183,23 if shift.x == 8 else 303,32,16 if shift.x == 8 else 296])
			var x: int = x0 if shift.x == 8 else x1 - 1
			for y in range(y0,y1):
				seconds += _tile_seconds(background_tiles,Vector2i(x,y),page,Vector2i(cx,cy))
		if shift.y != 0:
			seconds += _seconds("fill", [2,39 if shift.y == 8 else 183,303,32 if shift.y == 8 else 176,16])
			var y: int = y0 if shift.y == 8 else y1 - 1
			for x in range(x0,x1):
				seconds += _tile_seconds(background_tiles,Vector2i(x,y),page,Vector2i(cx,cy))
		seconds += _seconds("copy", [2, 32, 16, page, 183, 303, 32, 16])
	else:
		# AD3E..AE0B: scenic maps restore all of page 2 and then repaint every
		# visible background tile. They do not use the scrolling tile cache.
		seconds += _seconds("copy", [page, 0, 0, 2, 199, 319, 0, 0])
		if background_tiles != null:
			var cx: int = state.camera_x
			var cy: int = state.camera_y
			for y in range(cy / 2, cy / 2 + 10):
				for x in range(cx / 2, cx / 2 + (cx & 1) + 18):
					var tile: Vector2i = background_tiles.get_cell_atlas_coords(Vector2i(x, y))
					if tile.x >= 0:
						seconds += _seconds("copy", [page, y * 16 + 32 - cy * 8, x * 16 + 16 - cx * 8,
							3, tile.y * 16 + 15, tile.x * 16 + 15, tile.y * 16, tile.x * 16])
	if player_visible:
		for i in range(2):
			var pointer: int = descriptor.player_images[i].pointer
			seconds += _seconds("sprite", [page, state.y - 32, state.x, i + 1, pointer & 65535, pointer >> 16], i)
	for draw in actor_draws:
		var index: int = draw.frame + (draw.type * 4 if draw.kind == "gruzzle" else 0)
		var x: int = draw.position.x + 16 - state.camera_x * 8
		var y: int = draw.position.y + 32 - state.camera_y * 8
		if x < 0 or y < 0 or x >= 320 or y >= 200:
			continue
		for operation in range(1, 2 if draw.get("mask",false) else 3):
			seconds += _seconds("entity:" + draw.kind + str(index), [page,y,x,operation,1,1])
	if foreground_tiles != null:
		for cell in foreground_tiles.get_used_cells():
			var x: int = cell.x * 16 + 16 - state.camera_x * 8
			var y: int = cell.y * 16 + 32 - state.camera_y * 8
			if x >= 8 and x < 304 and y >= 24 and y < 192:
				var tile := foreground_tiles.get_cell_atlas_coords(cell) * 16
				seconds += _seconds("copy", [page,y,x,3,tile.y+15,tile.x+15,tile.y,tile.x])
	for args in [[page,0,0,5,31,319,0,0], [page,32,0,5,199,15,32,0],
			[page,32,304,5,199,319,32,304], [page,184,0,5,199,319,184,0]]:
		seconds += _seconds("copy", args)
	return seconds + _seconds("page", [page])

func _tile_seconds(tiles: TileMapLayer, cell: Vector2i, page: int, camera: Vector2i) -> float:
	if tiles == null:
		return 0.0
	var tile: Vector2i = tiles.get_cell_atlas_coords(cell)
	if tile.x < 0:
		return 0.0
	var dest := cell * 16 + Vector2i(16,32) - camera * 8
	var source := tile * 16
	return _seconds("copy",[page,dest.y,dest.x,3,source.y+15,source.x+15,source.y,source.x])
