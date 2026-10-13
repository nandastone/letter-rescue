extends SceneTree
var game
var checks: Array = []

func _initialize() -> void:
	call_deferred("run")

func check(value: bool, name: String) -> void:
	checks.append({"name":name,"passed":value})

func run() -> void:
	game = load("res://main.tscn").instantiate()
	game.boot_enabled = false
	game.persistence_enabled = false
	game.audio_output_enabled = false
	root.add_child(game)
	game.set_process(false)
	game.scene = "maze"
	game.capture_sound_events = true
	game.sound_events.clear()
	game.prepared_samples.erase("voices:12037")
	var m = game.maze
	m.type = 4
	m.choices = [37,37,37,37]
	var seed = game.random.seed
	var events = m.candidate_events(0)
	m.run([m.play(events)])
	check(m.loading_sound,"cold audition enters sound preparation")
	check(game.sound_events.is_empty(),"cold sample does not start before preparation")
	var before = m.motion_due
	m.interrupt()
	check(m.motion_due==before,"loader ignores audition interruption")
	var delay = int(ceil(float(game.store.data.pcm["voices:12037"].decode_cycles)*game.TICK_HZ/10000000.0))
	for i in delay:
		m.update(m.tick+1)
	check(not m.loading_sound and game.sound_events.size()==1,"prepared sample starts after source-derived work")
	check(game.random.seed==seed,"sample preparation consumes no random choices")
	m.cancel()
	game.sound_events.clear()
	m.run([m.play(events)])
	check(not m.loading_sound and game.sound_events.size()==1,"cached audition starts without cold preparation")
	var passed = checks.all(func(c): return c.passed)
	var file = FileAccess.open(OS.get_cmdline_user_args()[0],FileAccess.WRITE)
	file.store_string(JSON.stringify({"passed":passed,"checks":checks,"scope":"Isolated production maze audition; source-derived decoder delay, cold/cache and input ownership."},"\t"))
	file.close()
	game.queue_free()
	await process_frame
	quit(0 if passed else 1)
