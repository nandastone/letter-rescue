extends SceneTree
const Startup = preload("res://scripts/core/wr1_startup.gd")

func _initialize() -> void:
	var evidence: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://testing/fixtures/wr1_startup_seed.json"))
	for case in evidence.cases:
		var values: Array = case.date
		var date := {"year":values[0], "month":values[1], "day":values[2],
			"hour":values[3], "minute":values[4], "second":values[5]}
		var tz: String = case.tz if case.tz != null else ""
		var actual: int = Startup.timestamp(date, tz)
		assert(actual == int(case.timestamp), "Native timestamp mismatch: %s %s actual=%d expected=%d" % [values, tz, actual, int(case.timestamp)])
		assert(Startup.seed_from_dos_time(date, tz) == int(case.seed))
	print("Original timestamp and seed cases PASS: ", evidence.cases.size())
	quit()
