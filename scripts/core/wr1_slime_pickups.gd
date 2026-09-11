extends RefCounted
## WR1 a611..a7c5: consume raw marker, restore background, refill, award5.
var attributes: Array
var background_tiles: Array
var positions: Array[Vector2i] = []
var marker_base: int

func configure(data: Dictionary, tiles: Array) -> void:
	attributes = data.attributes
	background_tiles = data.background_tiles
	marker_base = 0x82 + data.books.size()
	positions.clear()
	for entry in tiles:
		var tile := Vector2i(int(entry[0]), int(entry[1]))
		attributes[tile.y * 2][tile.x * 2] = marker_base + positions.size()
		positions.append(tile)

func collect_cell(col: int, row: int) -> Dictionary:
	var index: int = int(attributes[row][col]) - marker_base
	if index < 0 or index >= positions.size() or positions[index] * 2 != Vector2i(col, row):
		return {}
	var tile := positions[index]
	attributes[row][col] = 0x20
	return {"tile": tile, "background": int(background_tiles[tile.y][tile.x]), "reward": 5}

func snapshot() -> Array:
	var result: Array = []
	for tile in positions:
		result.append({"tile_x": tile.x, "tile_y": tile.y, "attribute": int(attributes[tile.y * 2][tile.x * 2])})
	return result
