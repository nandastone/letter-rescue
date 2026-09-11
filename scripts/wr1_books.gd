extends RefCounted
## Original loader 6eb4 and pickup a34e: restore background, clear attr, score.

var attributes: Array
var background_tiles: Array
var positions: Array[Vector2i] = []
var collected_count: int = 0

func configure(data: Dictionary) -> void:
	attributes = data.attributes
	background_tiles = data.background_tiles
	positions.clear()
	collected_count = 0
	for entry in data.books:
		var tile := Vector2i(int(entry[0]), int(entry[1]))
		attributes[tile.y * 2][tile.x * 2] = 0x82 + positions.size()
		positions.append(tile)

func collect_cell(col: int, row: int) -> Dictionary:
	var index := int(attributes[row][col]) - 0x82
	if index < 0 or index >= positions.size():
		return {}
	var tile := positions[index]
	if tile * 2 != Vector2i(col, row):
		return {}
	attributes[row][col] = 0x20
	collected_count += 1
	return {"index": index, "tile": tile, "background": int(background_tiles[tile.y][tile.x]),
		"reward": 500 if collected_count == positions.size() else 5}
