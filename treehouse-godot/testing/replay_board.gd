extends SceneTree
var game
var output: String
var expected: Image
var matched: int
var results: Array = []
var matched_presentation_ms: float = -1
var presented_frames: int = 0
var observe_checkpoint: String = ""
var checkpoint_name: String = ""
var previous_observation: PackedByteArray
var observations: Array = []

func _initialize() -> void:
	output = OS.get_cmdline_user_args()[0]
	call_deferred("run")

func observe() -> void:
	game.render()

func observe_presentation(frame: Image, milliseconds: float) -> void:
	presented_frames += 1
	if checkpoint_name==observe_checkpoint:
		var pixels = frame.get_data()
		if pixels!=previous_observation:
			previous_observation = pixels
			var filename = "observed-%04d.png"%observations.size()
			frame.save_png(output+"/"+filename)
			observations.append({"image":filename,"milliseconds":milliseconds,"tick":game.tick,"exchange":game.boardgame.exchange.duplicate(true) if game.boardgame.exchange!=null else null,"exchange_frame":game.boardgame.motion.exchange_frame.duplicate(true) if game.boardgame.motion.exchange_frame!=null else null})
	if expected!=null and matched<0 and frame.get_data()==expected.get_data():
		matched = game.tick
		matched_presentation_ms = milliseconds
		frame.save_png(output+"/matched.png")

func busy() -> bool:
	var g = game.boardgame
	return (g.motion.busy or g.moving!=null or g.phase=="rolling") and not (g.phase=="exchange" and not g.motion.accepted)

func run() -> void:
	var fixture = JSON.parse_string(FileAccess.get_file_as_string(output+"/fixture.json"))
	observe_checkpoint = fixture.get("observe","")
	game = load("res://main.tscn").instantiate()
	game.boot_enabled = false
	game.persistence_enabled = false
	root.add_child(game)
	game.set_process(false)
	game.audio_output_enabled = false
	game.capture_sound_events = true
	game.presentation.presented.connect(observe_presentation)
	game.scene = "boardgame"
	game.animations.clear()
	var g = game.boardgame
	var initial = game.MusicMaze.integers(fixture.initial)
	g.storage_enabled = false
	for key in initial:
		if key=="seed":
			game.random.reset(initial.seed)
		else:
			g.set(key.to_snake_case(),initial[key])
	for c in fixture.checkpoints:
		checkpoint_name = c.name
		expected = Image.load_from_file(fixture.reference+"/state/"+c.name+".png")
		expected.convert(Image.FORMAT_RGBA8)
		matched = -1
		matched_presentation_ms = -1
		game.move_pointer(Vector2i(c.point[0],c.point[1]))
		var sound_start = game.sound_events.size()
		if c.name!=fixture.checkpoints[0].name:
			game.pointer_input("mouse",true,game.pointer)
			game.pointer_input("mouse",false,game.pointer)
		observe()
		var elapsed = 0
		while busy() and elapsed<30000:
			game.advance()
			observe()
			elapsed += 1
		var completed = not busy()
		if completed:
			for i in 420:
				game.advance()
				observe()
		var actual: Dictionary = {}
		for key in c.expected:
			actual[key] = game.random.seed if key=="seed" else g.get(key.to_snake_case())
		actual.player = 1-g.loser if g.loser>=0 else g.player
		if matched>=0:
			Image.load_from_file(output+"/matched.png").save_png(output+"/"+c.name+".png")
		else:
			game.presentation.image.save_png(output+"/"+c.name+".png")
		results.append({"name":c.name,"actual":actual.duplicate(true),"completed":completed,"matched_tick":matched,"matched_presentation_ms":matched_presentation_ms,"sounds":game.sound_events.slice(sound_start)})
	var file = FileAccess.open(output+"/godot.json",FileAccess.WRITE)
	file.store_string(JSON.stringify({"checkpoints":results,"presented_frames":presented_frames,"observations":observations,"ending":g.phase=="result" and not g.motion.busy and (g.winner>=0 or g.loser>=0)}))
	file.close()
	game.queue_free()
	await process_frame
	quit()
