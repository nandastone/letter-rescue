extends SceneTree
## Checks vocabulary substitutions, local art, and Legacy isolation.

func _initialize() -> void:
	var source := load("res://scripts/game/krsna_vocabulary.gd")
	var failures: Array[String] = []
	var original_text: String = JSON.parse_string(FileAccess.get_file_as_string("res://data/wr1/word_list.json")).text
	var original_tokens := original_text.split(" ", false)
	if source.REPLACEMENTS.size() != 17:
		failures.append("expected 17 replacements, got %d" % source.REPLACEMENTS.size())
	for original: String in source.REPLACEMENTS:
		var replacement: String = source.REPLACEMENTS[original]
		if original_tokens.count(original) != 1:
			failures.append("replacement source must occur once: %s" % original)
		if original.length() != replacement.length() and not (original == "teepee" and replacement == "tulsi"):
			failures.append("length changed: %s -> %s" % [original, replacement])
		var picture: Texture2D = source.load_picture(replacement)
		if picture == null or picture.get_width() != 24 or picture.get_height() != 24:
			failures.append("missing 24x24 picture: %s" % replacement)
	if source.display_word("teepee") != "tulsi" or source.display_word("arrow") != "arrow":
		failures.append("tulsi must replace teepee, not arrow")
	if source.display_word("camera") != "kirtan":
		failures.append("kirtan must replace camera")
	if source.display_word("wine") != "milk" or source.display_word("flag") != "flag":
		failures.append("milk must replace wine, not flag")
	if source.PICTURE_WORDS.size() != 19:
		failures.append("expected 19 picture frames")
	var atlas: Texture2D = load(source.ATLAS_PATH)
	if atlas.get_width() != 19 * 24 or atlas.get_height() != 24:
		failures.append("atlas dimensions do not match 19 frames")
	for word: String in source.PICTURE_WORDS:
		if source.load_picture(word) == null:
			failures.append("missing custom picture: " + word)
	for word: String in ["pot", "crown", "teepee", "gun", "wine", "ghost", "scale", "camera"]:
		var vocabulary := preload("res://scripts/core/vocabulary.gd")
		var expected_word: String = word if LaunchArgs.legacy() else source.display_word(word)
		if vocabulary.display_word(word) != expected_word:
			failures.append("mode isolation failed for " + word)
		var actual: Texture2D = vocabulary.load_picture(word)
		var expected_picture: Texture2D = preload("res://scripts/core/wr1_pictures.gd").load_picture(word) if LaunchArgs.legacy() else source.load_picture(expected_word)
		if actual == null or expected_picture == null or actual.get_image().get_data() != expected_picture.get_image().get_data():
			failures.append("wrong mode picture for " + word)
	if source.load_picture("ghee") != null:
		failures.append("ghee picture must be removed")
	for word: String in ["music", "dance", "flag"]:
		if source.load_picture(word) != null or source.display_word(word) != word:
			failures.append("unexpected override for " + word)
		for frame in range(2):
			var restored: Texture2D = preload("res://scripts/core/vocabulary.gd").load_picture(word, frame)
			var original: Texture2D = preload("res://scripts/core/wr1_pictures.gd").load_picture(word, frame)
			if restored.get_image().get_data() != original.get_image().get_data():
				failures.append("original art not restored for " + word)
	_check_shorter_mystery(failures)
	var display := preload("res://scripts/core/vocabulary.gd").display_word("toe")
	var expected := "toe" if LaunchArgs.legacy() else "cow"
	if display != expected:
		failures.append("mode isolation failed: expected %s, got %s" % [expected, display])
	var original_words := preload("res://scripts/core/wr1_words.gd").new()
	original_words.next_words()
	var presented := preload("res://scripts/core/vocabulary.gd").display_words(original_words.words)
	if original_words.words[0] != "toe" or presented[0] != expected:
		failures.append("presentation changed the underlying WR1 word stream")
	if failures:
		for failure in failures:
			printerr("Krsna vocabulary FAILED: " + failure)
		quit(1)
	else:
		print("Krsna vocabulary: 17 replacements, 19 pictures; wine -> milk, music/dance/flag restored, shorter tulsi mystery and mode isolation verified")
		quit()


func _check_shorter_mystery(failures: Array[String]) -> void:
	var data := {"attributes": [], "background_tiles": []}
	for y in range(4):
		data.attributes.append([32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32])
	for y in range(2):
		data.background_tiles.append([0, 0, 0, 0, 0, 0])
	var positions := [[0, 1], [1, 1], [2, 1], [3, 1], [4, 1], [5, 1]]
	var letters := preload("res://scripts/core/wr1_letters.gd").new()
	letters.configure(data, positions, "tulsi")
	if data.attributes[2][10] != 32 or not letters.collect_cell(10, 2).is_empty():
		failures.append("shorter mystery left a sixth letter pickup")
	for i in range(5):
		var result := letters.collect_cell(i * 2, 2)
		if not result.get("advanced", false) or result.get("complete", false) != (i == 4):
			failures.append("tulsi mystery did not complete at five letters")
