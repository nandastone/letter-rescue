extends SceneTree
var game
var checks: Array = []
var output: String

func _initialize() -> void:
	call_deferred("run")

func check(value: bool, name: String) -> void:
	checks.append({"name":name,"passed":value})
	if not value:
		print(JSON.stringify(checks.back()))

func key(code: int, control: bool = false, alt: bool = false) -> void:
	for pressed in [true,false]:
		var event = InputEventKey.new()
		event.keycode = code
		event.ctrl_pressed = control
		event.alt_pressed = alt
		event.pressed = pressed
		game._input(event)

func click(point: Vector2i, touch: bool = false) -> void:
	for pressed in [true,false]:
		if touch:
			var event = InputEventScreenTouch.new()
			event.position = point
			event.pressed = pressed
			game._input(event)
		else:
			game.pointer_input("mouse",pressed,point)

func context(expected: int) -> void:
	check(game.preferences.context()==expected,"context %d"%expected)

func run() -> void:
	output = OS.get_cmdline_user_args()[0]
	game = load("res://main.tscn").instantiate()
	game.boot_enabled = false
	game.persistence_enabled = false
	root.add_child(game)
	game.set_process(false)
	game.audio_output_enabled = false
	var p = game.preferences
	p.storage_enabled = false
	game.theater.storage_enabled = false
	game.nature.storage_enabled = false
	game.boardgame.storage_enabled = false
	game.music.editor.storage_enabled = false
	# Rendering fixtures contain only modal state/pointer, never source pixels.
	for raw in JSON.parse_string(FileAccess.get_file_as_string(output+"/fixture.json")):
		var c = game.MusicMaze.integers(raw)
		p.kind = ""
		p.status.clear()
		p.background = Image.create(320,200,false,Image.FORMAT_RGBA8)
		p.background.fill(Color.BLACK)
		game.scene = "theater" if c.name.begins_with("help-theater") else "outside"
		if c.kind=="help":
			p.kind = "help"
			for layout in game.store.data.help:
				if int(layout.context)==c.context:
					p.layout = game.MusicMaze.integers(layout)
		elif c.kind=="settings":
			p.kind = "settings"
			p.settings = c.settings
		else:
			p.status = {"label":c.label,"background":p.background,"due":180}
		game.pointer = Vector2i(c.pointer[0],c.pointer[1])
		p.draw(game.surface)
		game.draw_pointer()
		game.surface.image.save_png(output+"/"+c.name+".png")
	p.kind = ""
	p.status.clear()
	game.scene = "outside"
	context(18)
	game.resident.selected = true
	context(19)
	game.resident.selected = false
	game.scene = "music"
	game.music.editor.enabled = false
	context(0)
	game.music.editor.enabled = true
	context(15)
	game.music.selector.open = true
	game.music.selector.category = -1
	context(6)
	game.music.selector.category = 0
	context(7)
	game.music.selector.open = false
	game.scene = "maze"
	game.maze.large_intro = false
	game.maze.phase = "playing"
	context(8)
	game.maze.large_intro = true
	context(17)
	game.scene = "theater"
	game.theater.options = true
	context(13)
	game.theater.options = false
	for flags in [[false,false,2],[true,true,20],[false,true,21],[true,false,22]]:
		game.theater.mix_up = flags[0]
		game.theater.props_enabled = flags[1]
		context(flags[2])
	game.scene = "boardgame"
	var g = game.boardgame
	g.options = true
	context(10)
	g.options = false
	g.phase = "ready"
	context(3)
	g.phase = "reward"
	g.mode = 0
	context(16)
	g.mode = 1
	context(24)
	g.exchange = {"digit":0}
	context(25)
	g.winner = 0
	context(23)
	g.exchange = null
	g.winner = -1
	game.scene = "nature"
	game.nature.mode = "explore"
	context(1)
	game.nature.mode = "quiz"
	var q = game.nature.quiz
	q.options = true
	context(11)
	q.options = false
	q.phase = "ready"
	context(26)
	q.phase = "question"
	q.help[q.role()] = false
	context(9)
	q.help[q.role()] = true
	context(27)
	q.winner = 0
	context(28)
	game.scene = "outside"
	game.pointer = Vector2i.ZERO
	key(KEY_F1,true,true)
	check(p.kind=="help" and p.layout.context==29,"dedication via Ctrl Alt F1")
	p.close()
	game.pointer = Vector2i(160,100)
	key(KEY_F1)
	check(p.kind=="help" and p.layout.context==18,"F1 opens welcome help")
	var saved = p.background.get_data()
	var seed = game.random.seed
	game.advance(30)
	check(p.background.get_data()==saved and game.random.seed==seed,"modal freezes underlying activity and RNG")
	game.move_pointer(Vector2i(10,10))
	key(KEY_ESCAPE)
	click(Vector2i(10,10))
	check(p.kind=="help" and not p.closing,"outside Escape and click leave help open")
	key(KEY_F2)
	check(p.kind=="help","F2 cannot nest settings")
	game.move_pointer(Vector2i(160,100))
	key(KEY_ESCAPE)
	check(p.closing,"inside Escape starts Done feedback")
	game.advance(19)
	check(p.active,"help remains during 20-tick close")
	game.advance()
	check(not p.active and game.music.idle_due==game.tick+600,"help closes and resets music idle")
	check(game.resident.ambient_due>=game.tick+1200 and game.resident.ambient_due<=game.tick+1800,"room ambient deadline resets from modal close time")
	key(KEY_F1)
	click(Vector2i(160,100),true)
	click(Vector2i(160,100),true)
	check(not p.active,"touch interrupts closing wait")
	key(KEY_F2)
	check(p.kind=="settings","F2 opens preferences")
	for row in 5:
		var name = ["sound","printing","printer","advanced","speed"][row]
		var before = p.settings[name]
		click(Vector2i(160,64+14*row),bool(row%2))
		check(p.settings[name]!=before and p.flash==row and p.due==game.tick+12,"toggle row %d with feedback"%row)
	game.advance(12)
	check(game.maze.hard==p.settings.advanced,"maze uses chosen difficulty")
	game.pointer = Vector2i(10,10)
	var event = InputEventKey.new()
	event.keycode = KEY_RIGHT
	event.pressed = true
	game._input(event)
	check(game.pointer.x==11,"keyboard pointer moves within modal")
	event.pressed = false
	game._input(event)
	key(KEY_V,true)
	check(p.status.get("label")=="Version 1.1" and p.kind=="settings","Ctrl V overlays existing modal")
	game.advance(179)
	check(not p.status.is_empty(),"status remains for 179 ticks")
	game.advance()
	check(p.status.is_empty() and p.kind=="settings","status expires after 180 ticks into preferences")
	var sound_before = p.settings.sound
	key(KEY_S,true)
	check(p.settings.sound!=sound_before and not p.status.is_empty(),"Ctrl S toggles sound within modal")
	click(Vector2i(10,10))
	check(p.status.is_empty() and p.kind=="settings","input dismisses status without reaching settings")
	click(Vector2i(10,10))
	check(p.active,"outside click does not close settings")
	key(KEY_ESCAPE)
	check(not p.active,"Escape closes settings")
	game.music.playing = true
	key(KEY_F1)
	key(KEY_F2)
	check(not p.active,"playing music blocks F1 and F2")
	game.music.playing = false
	game.held["mouse"] = true
	key(KEY_F1)
	check(not p.active,"held input blocks global help")
	game.held.clear()
	game.scene = "theater"
	game.theater.options = false
	var r = game.theater.tables.ui_rects[12]
	click(Vector2i((r[1]+r[3])/2,(r[0]+r[2])/2))
	check(p.kind=="help" and p.layout.context==22,"theater notebook help accepts pointer activation")
	p.close()
	game.scene = "outside"
	p.storage_enabled = true
	p.save_path = output+"/preferences-save.json"
	p.save()
	var restored = game.Preferences.new(game,false)
	restored.save_path = p.save_path
	restored.restore()
	check(restored.settings==p.settings,"all five preferences survive reload")
	var before = restored.settings.duplicate()
	var invalid = FileAccess.open(p.save_path,FileAccess.WRITE)
	invalid.store_string('{"version":1,"settings":{"sound":false,"printing":true,"printer":0.5,"advanced":true,"speed":false}}')
	invalid.close()
	restored.restore()
	check(restored.settings==before,"invalid save rejected atomically")
	p.storage_enabled = false
	game.music.editor.enabled = false
	game.set_scene("music")
	p.settings.printing = false
	click(Vector2i(295,120))
	check(game.music.dialog.is_empty(),"printing off blocks music print prompt")
	p.settings.printing = true
	click(Vector2i(295,120))
	check(game.music.dialog.get("message")=="print","printing on enables music print prompt")
	game.music.answer(false)
	game.set_scene("nature")
	game.nature.mode = "explore"
	r = game.nature.tables.rectangles[9]
	var point = Vector2i((r[1]+r[3])/2,(r[0]+r[2])/2)
	p.settings.printing = false
	click(point)
	check(game.nature.dialog.is_empty(),"printing off blocks nature print prompt")
	p.settings.printing = true
	click(point)
	check(game.nature.dialog.get("print",false),"printing on enables nature print prompt")
	game.nature.answer_dialog(false)
	game.scene = "outside"
	game.audio_output_enabled = true
	p.settings.sound = true
	var sample = game.store.data.pcm.keys()[0]
	var rate = int(game.store.data.pcm[sample].rate)
	var duration = game.play_sample(sample,rate)
	check(game.audio.playing,"sound on dispatches original PCM")
	game.resident.selected = true
	key(KEY_F1)
	check(not p.active,"active sound with loaded character blocks help")
	p.settings.sound = false
	p.apply_settings()
	check(not game.audio.playing and game.play_sample(sample,rate)==duration and not game.audio.playing,"mute stops playback and retains animation duration")
	game.resident.selected = false
	game.audio.stream = null
	game.audio_cache.clear()
	var passed = checks.all(func(c): return c.passed)
	var file = FileAccess.open(output+"/controls.json",FileAccess.WRITE)
	file.store_string(JSON.stringify({"passed":passed,"checks":checks},"  "))
	file.close()
	print(JSON.stringify({"passed":passed,"checks":checks.size()}))
	game.queue_free()
	await process_frame
	# Let the audio thread release the stopped test voice before engine shutdown.
	await create_timer(0.1).timeout
	quit(0)
