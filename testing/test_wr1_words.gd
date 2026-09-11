extends SceneTree
var checks := 0
var failures := 0

func check(ok: bool, message: String) -> void:
	checks += 1
	if not ok:
		failures += 1
		push_error(message)

func _initialize() -> void:
	var fixture: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://testing/fixtures/wr1_words_stages.json"))
	var stream = preload("res://scripts/core/wr1_words.gd").new()
	stream.next_words()
	check(stream.words == fixture.initial.words and stream.offset == int(fixture.initial.word_cursor), "Initial seven words and cursor")
	var actors = preload("res://scripts/core/wr1_gruzzles.gd").new()
	actors.configure([],0)
	var wraps := 0
	for stage in fixture.loads:
		check(stream.words == stage.begin.words and stream.offset == int(stage.begin.word_cursor), "Cursor persists between native loads")
		actors.rng = int(stage.begin.rng)
		var map: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://data/levels/level_%02d.json" % (int(stage.end.level_index)+1)))
		var starts: Array = []
		for pos in map.gruzzles:
			starts.append([int(pos[0]*2),int(pos[1]*2)])
		var selected: Dictionary = actors.restart(starts,0,true,stream.next_words)
		check(stream.words == stage.end.words, "Native seven-word selection at frame %d" % stage.end.launch_call)
		check(stream.offset == int(stage.end.word_cursor), "Native byte cursor")
		check(actors.rng == int(stage.end.rng), "Loader RNG, including EOF call order")
		for key in selected:
			check(selected[key] == int(stage.end[key]), "Native selection: " + key)
		if stream.offset < int(stage.begin.word_cursor):
			wraps += 1
	check(wraps == 1, "Observed EOF wrap exactly once")
	print("WR1 words: %d checks, %d failures" % [checks, failures])
	quit(1 if failures else 0)
