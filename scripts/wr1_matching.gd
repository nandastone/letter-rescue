extends RefCounted
## WR1.EXE c1aa: seven source words and seven reusable picture locations.
## See testing/wr1_matching_research.md. Attributes are shared with movement.

var attributes: Array
var slots: Array[Vector2i] = []
var picture_phase_indices: Array[int] = []
var word_offset: int
var picture_offset: int
var active_slot: int = -1
var active_index: int = 255
var last_touched := Vector2i(-1, -1)
var matched_count: int = 0
var mistakes: int = 0
var completion_order: Array[int] = [9, 9, 9, 9, 9, 9, 9]
var mistakes_for_word: Array[int] = [0, 0, 0, 0, 0, 0, 0]

func configure(data: Dictionary, words_rotation: int, pictures_rotation: int) -> void:
	assert(words_rotation >= 0 and words_rotation < 7)
	assert(pictures_rotation >= 0 and pictures_rotation < 7 and pictures_rotation != words_rotation)
	attributes = data.attributes
	slots.resize(7)
	for entry in data.slots:
		slots[int(entry.slot)] = Vector2i(int(entry.grid[0]), int(entry.grid[1]))
	# The loader caches coordinates in its column-major map scan. Matching
	# uses the attribute ID, but B781 indexes animation phases by that scan.
	var locations: Array[Vector2i] = slots.duplicate()
	locations.sort_custom(func(a: Vector2i, b: Vector2i) -> bool:
		return a.y < b.y if a.x == b.x else a.x < b.x)
	picture_phase_indices.clear()
	for location in slots:
		picture_phase_indices.append(locations.find(location))
	word_offset = words_rotation
	picture_offset = pictures_rotation
	active_slot = -1
	active_index = 255
	last_touched = Vector2i(-1, -1)
	matched_count = 0
	mistakes = 0
	completion_order.fill(9)
	mistakes_for_word.fill(0)

func word_index(slot: int) -> int:
	return (slot + word_offset) % 7

func picture_index(slot: int) -> int:
	return (slot + picture_offset) % 7

func available(slot: int) -> bool:
	var p := slots[slot]
	return int(attributes[p.y][p.x]) < 7

func question_visible(slot: int) -> bool:
	return available(slot) and slots[slot] != last_touched

func scan(gx: int, gy: int, collect_cell: Callable = Callable()) -> Dictionary:
	# Row-major scan stops at the first relevant attr, including the active
	# source / last-touch exclusion; it must not skip it and hit a later cell.
	for row in range(maxi(gy - 5, 0), mini(gy + 1, attributes.size() - 1)):
		for col in range(maxi(gx - 1, 0), mini(gx + 4, attributes[row].size() - 1)):
			var value := int(attributes[row][col])
			if value < (14 if active_slot >= 0 else 7):
				return touch(value % 7)
			if col >= gx and value > 0x7a and collect_cell.is_valid():
				collect_cell.call(col, row)
	return {}

func touch(slot: int) -> Dictionary:
	var location := slots[slot]
	if active_slot < 0:
		if not available(slot) or location == last_touched:
			return {}
		active_slot = slot
		active_index = word_index(slot)
		last_touched = location
		attributes[location.y][location.x] = slot + 7
		return {"kind": "reveal", "word_index": active_index, "source": slot}
	if slot == active_slot:
		return {}
	last_touched = location
	var result := {"word_index": active_index, "source": active_slot, "target": slot}
	if picture_index(slot) == active_index:
		result["kind"] = "correct"
		result["order"] = matched_count
		completion_order[active_index] = matched_count
		matched_count += 1
		result["reward"] = 20 + (500 if matched_count == 7 and mistakes == 0 else 0)
		result["complete"] = matched_count == 7
		if matched_count == 6:
			last_touched.x = -1
	else:
		result["kind"] = "wrong"
		mistakes += 1
		mistakes_for_word[active_index] = 1
		var source := slots[active_slot]
		attributes[source.y][source.x] = active_slot
		result["spawn_grid"] = location + Vector2i(0, 1)
	active_slot = -1
	return result
