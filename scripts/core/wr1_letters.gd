extends RefCounted
## WR1.EXE 730a..75ad stamps positional markers; a34e..a602 consumes them.
var attributes: Array
var background_tiles: Array
var positions: Array[Vector2i] = []
var word: String
var prefix: int = 0

func configure(data: Dictionary, tiles: Array, mystery: String) -> void:
	attributes = data.attributes
	background_tiles = data.background_tiles
	word = mystery.to_lower()
	prefix = 0
	positions.clear()
	for i in range(tiles.size()):
		var tile := Vector2i(int(tiles[i][0]), int(tiles[i][1]))
		positions.append(tile)
		attributes[tile.y * 2][tile.x * 2] = 0x7b + i if i < word.length() else 0x20

func collect_cell(col: int, row: int) -> Dictionary:
	var index: int = int(attributes[row][col]) - 0x7b
	if index < 0 or index >= mini(word.length(), positions.size()) or positions[index] * 2 != Vector2i(col, row):
		return {}
	attributes[row][col] = 0x20
	var advances: bool = prefix < word.length() and word[index] == word[prefix]
	if advances:
		prefix += 1
	var complete: bool = advances and prefix == word.length()
	var tile := positions[index]
	return {"tile":tile, "background":int(background_tiles[tile.y][tile.x]),
		"reward":100 if complete else 5, "advanced":advances, "complete":complete}

func snapshot() -> Dictionary:
	var letters: Array = []
	for tile in positions:
		letters.append({"tile_x":tile.x,"tile_y":tile.y,"attribute":int(attributes[tile.y * 2][tile.x * 2])})
	return {"mystery_prefix":prefix, "mystery_pickups":letters}
