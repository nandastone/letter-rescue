extends SceneTree
var checks := 0
var failures := 0

func check(ok: bool, message: String) -> void:
	checks += 1
	if not ok:
		failures += 1
		push_error(message)

func _initialize() -> void:
	var grid: Array = []
	var bg: Array = []
	for y in range(4):
		grid.append([0,0,0,0,0,0,0,0])
		bg.append([255,255,255,255])
	var data := {"attributes":grid,"background_tiles":bg}
	var letters = preload("res://scripts/wr1_letters.gd").new()
	letters.configure(data, [[0,1],[1,1],[2,1],[3,1]], "cup")
	check(grid[2] == [123,0,124,0,125,0,32,0], "Stamp only the mystery word's length")
	var wrong: Dictionary = letters.collect_cell(4,2)
	check(wrong.reward == 5 and not wrong.advanced and letters.prefix == 0, "Out-of-order pickup pays five, without advancement")
	check(grid[2][4] == 32 and letters.collect_cell(4,2).is_empty(), "Wrong-order letter is still consumed")
	check(letters.collect_cell(0,2).advanced and letters.prefix == 1, "Correct letter advances")
	check(letters.collect_cell(2,2).advanced and letters.prefix == 2, "Second correct letter advances")
	check(letters.collect_cell(4,2).is_empty() and letters.prefix == 2, "No second reward from a removed letter")
	letters.configure(data, [[0,1],[1,1],[2,1]], "cup")
	var reward := 0
	for col in [0,2,4]:
		var result: Dictionary = letters.collect_cell(col,2)
		reward += result.reward
		check(result.complete == (col == 4), "Completion only on final correct letter")
	check(reward == 110, "Final letter awards 100 instead of an additional five")
	letters.configure(data, [[0,1],[1,1],[2,1]], "pop")
	check(letters.collect_cell(4,2).advanced, "Repeated letters match by character, not position")
	check(letters.collect_cell(2,2).advanced and letters.collect_cell(0,2).complete, "Repeated letters can complete in alternate positional order")
	print("WR1 letters: %d checks, %d failures" % [checks, failures])
	quit(1 if failures else 0)
