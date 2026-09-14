extends RefCounted
## Chooses the vocabulary presented by each game without changing WR1's
## internal word stream. Legacy always sees the recovered words and pictures.

static func display_word(original_word: String) -> String:
	if LaunchArgs.legacy():
		return original_word
	return load("res://scripts/game/krsna_vocabulary.gd").display_word(original_word)


static func display_words(original_words: Array) -> Array[String]:
	var result: Array[String] = []
	for word in original_words:
		result.append(display_word(str(word)))
	return result


static func load_picture(word: String, frame: int = 0) -> Texture2D:
	if not LaunchArgs.legacy():
		var custom: Texture2D = load("res://scripts/game/krsna_vocabulary.gd").load_picture(display_word(word))
		if custom != null:
			return custom
	return preload("res://scripts/core/wr1_pictures.gd").load_picture(word, frame)
