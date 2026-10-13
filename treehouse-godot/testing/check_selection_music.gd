extends SceneTree
var output: String
var checks: Array = []
var game
var pcm_hashes: Dictionary = {}

func pcm_hash(name: String, stream: AudioStreamWAV) -> void:
	var hash = HashingContext.new()
	hash.start(HashingContext.HASH_SHA256)
	hash.update(stream.data)
	pcm_hashes[name] = hash.finish().hex_encode()

func _initialize() -> void:
	output = OS.get_cmdline_user_args()[0]
	call_deferred("run")

func check(value: bool, name: String) -> void:
	checks.append({"name":name,"passed":value})
	if not value:
		push_error(name)

func run() -> void:
	game = load("res://main.tscn").instantiate()
	game.persistence_enabled = false
	game.audio_output_enabled = false
	root.add_child(game)
	game.set_process(false)
	check(not game.selection_music_active,"selection music is silent during logo")
	pcm_hash("title",game.startup.player.stream)
	game.startup.finish()
	check(game.selection_music_active,"title exit starts selection music")
	var stream = game.selection_audio.stream
	pcm_hash("selection",stream)
	check(stream is AudioStreamWAV and stream.mix_rate==48000,"source-generated selection PCM loads")
	check(stream.loop_mode==AudioStreamWAV.LOOP_FORWARD and stream.loop_begin==0 and stream.loop_end==7285533,"loop spans authored track duration")
	game.render()
	game.surface.image.save_png(output.path_join("selection.png"))
	game.preferences.settings.sound = false
	game.preferences.apply_settings()
	check(game.selection_audio.volume_db==-INF and game.selection_music_active,"muting silences but retains selection playback state")
	game.preferences.settings.sound = true
	game.preferences.apply_settings()
	check(game.selection_audio.volume_db==0.0 and game.selection_audio.stream==stream,"unmuting retains the stream")
	var note = game.store.data.pcm.keys()[0]
	game.play_sample(note,int(game.store.data.pcm[note].rate))
	check(game.selection_audio.stream==stream,"digital sample does not replace FM music")
	game.enter("boy")
	check(game.entering and game.selection_music_active,"selection music continues during character departure")
	for i in 2000:
		game.advance()
		if game.scene=="inside":
			break
	check(game.scene=="inside" and not game.selection_music_active and game.selection_audio.stream==null,"room arrival releases selection music")
	game.select_screen()
	check(game.selection_music_active and game.selection_audio.stream!=null,"return to selection restarts music")
	game.audio.stream = null
	game.audio_cache.clear()
	var passed = checks.all(func(c): return c.passed)
	var report = FileAccess.open(output.path_join("godot.json"),FileAccess.WRITE)
	report.store_string(JSON.stringify({"checks":checks,"pcm_sha256":pcm_hashes,"passed":passed},"\t"))
	report.close()
	game.queue_free()
	await process_frame
	quit(0 if passed else 1)
