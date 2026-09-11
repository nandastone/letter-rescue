extends RefCounted
## WR1.EXE 7170..7309: persistent byte cursor, seven words, randomized EOF skip.
var text: String = ""
var offset: int = 0
var words: Array[String] = []

func _init() -> void:
	text = JSON.parse_string(FileAccess.get_file_as_string("res://data/wr1/word_list.json")).text

func next_words(random_word: Callable = Callable()) -> void:
	var skip := 0
	if text.length() - offset < 56:
		offset = 0
		skip = int(random_word.call()) % 9 + 1
	words.clear()
	for i in range(skip + 7):
		var start := offset
		while offset < text.length() and text[offset] not in [" ","\n"]:
			offset += 1
		var word := text.substr(start, offset - start)
		while offset < text.length() and text[offset] in [" ","\n"]:
			offset += 1
		if i >= skip:
			words.append(word)
	assert(words.size() == 7)
