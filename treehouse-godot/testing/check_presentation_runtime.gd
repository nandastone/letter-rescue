extends SceneTree
## Host callback batching must not discard logical framebuffer commits.
var checks: Array = []

func _initialize() -> void:
	call_deferred("run")

func sample(step: float, count: int) -> Dictionary:
	var game = load("res://main.tscn").instantiate()
	game.persistence_enabled = false
	game.audio_output_enabled = false
	game.date_override = {"year":1992,"month":1,"day":1,"hour":12,"minute":0,"second":0}
	root.add_child(game)
	game.set_process(false)
	var frames: Array = []
	game.presentation.presented.connect(func(frame: Image, milliseconds: float):
		var hash = HashingContext.new()
		hash.start(HashingContext.HASH_SHA256)
		hash.update(frame.get_data())
		frames.append({"milliseconds":milliseconds,"hash":hash.finish().hex_encode()}))
	for i in count:
		game._process(step)
	var result = {"frames":frames,"tick":game.tick,"time_ms":game.presentation.time_ms,"scene":game.scene}
	game.free()
	return result

func run() -> void:
	var split = sample(1.0/256,1024)
	var batched = sample(1.0,4)
	checks.append({"name":"split and batched callbacks reach the same logical tick","passed":split.tick==batched.tick})
	checks.append({"name":"four seconds generate more than 240 VGA presentations","passed":split.frames.size()>240})
	checks.append({"name":"batched callbacks preserve every presentation pixel hash and timestamp","passed":split.frames==batched.frames})
	checks.append({"name":"fractional presentation time is independent of callback size","passed":absf(split.time_ms-batched.time_ms)<0.000001})
	var distinct = {}
	for frame in split.frames:
		distinct[frame.hash] = true
	checks.append({"name":"comparison spans changing title images","passed":distinct.size()>5})
	var passed = checks.all(func(c): return c.passed)
	var file = FileAccess.open(OS.get_cmdline_user_args()[0],FileAccess.WRITE)
	file.store_string(JSON.stringify({"passed":passed,"checks":checks,"presentations":split.frames.size(),"distinct_frames":distinct.size(),"scope":"Production game _process and presenter under host callback batching; fixed-date title component, not browser or native timing proof."},"\t"))
	file.close()
	quit(0 if passed else 1)
