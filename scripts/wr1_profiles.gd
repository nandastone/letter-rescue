extends RefCounted
## Native profile/high-score formats, WR1.EXE 49ff..4bdf / 8d60..8ec8 / 93c3.
static var directory := "user://wr1/"

static func normalized_name(value: String) -> String:
	var result := ""
	for c in value:
		if c == " ":
			c = "_"
		if c.to_lower() in "abcdefghijklmnopqrstuvwxyz0123456789_" and result.length() < 8:
			result += c.to_lower()
	return result.left(1).to_upper() + result.substr(1)

static func load_player(player_name: String) -> Dictionary:
	var name := normalized_name(player_name)
	if name.is_empty():
		return {}
	for extension in [".wr1", ".wr2", ".wr3"]:
		var path: String = directory + name.to_lower() + extension
		if FileAccess.file_exists(path):
			var result := decode(FileAccess.get_file_as_bytes(path))
			if not result.is_empty():
				if extension != ".wr1":
					var words := preload("res://scripts/wr1_words.gd").new()
					words.next_words()
					result.level = 1
					result.score = 0
					result.words = words.words.duplicate()
					result.word_cursor = words.offset
				return result
	return {}

static func decode(bytes: PackedByteArray) -> Dictionary:
	if bytes.size() < 25:
		return {}
	var result := {"level":bytes.decode_u16(0) + 1, "character":bytes.decode_u16(2),
		"word_cursor":bytes.decode_u32(4), "score":bytes.decode_u32(8), "words":[]}
	if result.level > 15 or result.character > 1:
		return {}
	var cursor := 12
	for i in range(7):
		var start := cursor
		while cursor < bytes.size() and bytes[cursor] != 0 and cursor - start <= 32:
			cursor += 1
		if cursor >= bytes.size() or cursor - start > 32:
			return {}
		result.words.append(bytes.slice(start, cursor).get_string_from_ascii().to_lower())
		cursor += 1
	if cursor + 4 > bytes.size():
		return {}
	result.difficulty = bytes.decode_u16(cursor)
	result.custom_keys = bytes.decode_u16(cursor + 2) != 0
	cursor += 4
	if result.difficulty > 2:
		return {}
	result.scancodes = [77, 75, 72, 80, 57]
	if result.custom_keys:
		if cursor + 5 > bytes.size():
			return {}
		result.scancodes = Array(bytes.slice(cursor, cursor + 5))
		cursor += 5
	if cursor + 2 != bytes.size():
		return {}
	result.joystick = bytes.decode_u16(cursor) != 0
	return result

static func encode(profile: Dictionary) -> PackedByteArray:
	var bytes := PackedByteArray()
	bytes.resize(12)
	bytes.encode_u16(0, int(profile.level) - 1)
	bytes.encode_u16(2, int(profile.character))
	bytes.encode_u32(4, int(profile.word_cursor))
	bytes.encode_u32(8, int(profile.score))
	for word in profile.words:
		bytes.append_array(str(word).to_upper().to_ascii_buffer())
		bytes.append(0)
	var tail := PackedByteArray()
	tail.resize(4)
	tail.encode_u16(0, int(profile.difficulty))
	tail.encode_u16(2, int(profile.custom_keys))
	bytes.append_array(tail)
	if profile.custom_keys:
		bytes.append_array(PackedByteArray(profile.scancodes))
	bytes.append(int(profile.joystick))
	bytes.append(0)
	return bytes

static func save_player(player_name: String, profile: Dictionary) -> void:
	var name := normalized_name(player_name)
	if name.is_empty() or profile.get("words", []).size() != 7:
		return
	DirAccess.make_dir_recursive_absolute(directory)
	var file := FileAccess.open(directory + name.to_lower() + ".wr1", FileAccess.WRITE)
	if file != null:
		file.store_buffer(encode(profile))

static func high_scores() -> Array[Dictionary]:
	var result: Array[Dictionary] = []
	var bytes := FileAccess.get_file_as_bytes(directory + "high.wr1") if FileAccess.file_exists(directory + "high.wr1") else PackedByteArray()
	var cursor := 0
	for i in range(10):
		var start := cursor
		while cursor < bytes.size() and bytes[cursor] != 0 and cursor - start <= 8:
			cursor += 1
		if cursor + 5 > bytes.size() or cursor - start > 8:
			break
		var name := bytes.slice(start, cursor).get_string_from_ascii()
		cursor += 1
		result.append({"name":name, "score":bytes.decode_u32(cursor)})
		cursor += 4
	return result

static func update_high_score(player_name: String, score: int) -> void:
	var name := normalized_name(player_name)
	if name.is_empty() or score <= 0:
		return
	var entries := high_scores()
	var found := false
	for entry in entries:
		if entry.name.to_lower() == name.to_lower():
			entry.score = maxi(int(entry.score), score)
			found = true
	if not found:
		entries.append({"name":name, "score":score})
	# Insertion sort preserves native ordering for equal scores.
	for i in range(1, entries.size()):
		var j := i
		while j > 0 and entries[j].score > entries[j-1].score:
			var previous := entries[j-1]
			entries[j-1] = entries[j]
			entries[j] = previous
			j -= 1
	var bytes := PackedByteArray()
	for i in range(10):
		var entry: Dictionary = entries[i] if i < entries.size() else {"name":"", "score":0}
		bytes.append_array(entry.name.to_ascii_buffer())
		bytes.append(0)
		var value := PackedByteArray()
		value.resize(4)
		value.encode_u32(0, int(entry.score))
		bytes.append_array(value)
	DirAccess.make_dir_recursive_absolute(directory)
	var file := FileAccess.open(directory + "high.wr1", FileAccess.WRITE)
	if file != null:
		file.store_buffer(bytes)
