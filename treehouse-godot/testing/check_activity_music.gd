extends SceneTree
var game
var checks: Array = []
var hashes: Dictionary = {}

func _initialize() -> void:
	call_deferred("run")

func check(value: bool, name: String) -> void:
	checks.append({"name":name,"passed":value})
	if not value:
		push_error(name)

func run() -> void:
	game = load("res://main.tscn").instantiate()
	game.boot_enabled = false
	game.persistence_enabled = false
	game.audio_output_enabled = false
	root.add_child(game)
	game.set_process(false)
	for id in [20001,20100,20101,20102,20103]:
		var ticks = game.play_sound(id)
		var stream = game.selection_audio.stream as AudioStreamWAV
		var source = game.store.data.fm_music[str(id)]
		check(game.fm_sound_id==id and not game.selection_music_active,"dispatch %d"%id)
		check(stream.format==AudioStreamWAV.FORMAT_16_BITS and stream.mix_rate==48000 and not stream.stereo,"lossless PCM %d"%id)
		check((stream.loop_mode==AudioStreamWAV.LOOP_FORWARD)==bool(source.loop),"original loop flag %d"%id)
		check(ticks==int(ceil(float(source.end_irq)*4971.0/1193182.0*game.TICK_HZ)),"sequencer duration %d"%id)
		var hash = HashingContext.new()
		hash.start(HashingContext.HASH_SHA256)
		hash.update(stream.data)
		hashes[str(id)] = hash.finish().hex_encode()
		game.play_sound(10033)
		check(game.fm_sound_id==id and game.selection_audio.stream==stream,"digital voice preserves FM %d"%id)
		game.preferences.settings.sound = false
		game.preferences.apply_settings()
		check(game.selection_audio.volume_db==-INF,"mute FM %d"%id)
		game.preferences.settings.sound = true
		game.preferences.apply_settings()
		check(game.selection_audio.volume_db==0.0,"unmute FM %d"%id)
	game.set_scene("hollow")
	check(game.fm_sound_id==-1,"scene exit releases FM")
	game.exterior.click_hollow(Vector2i(180,45))
	check(game.fm_sound_id==20001 and game.exterior.sign_waiting,"hollow sign starts Home")
	check(game.exterior.sign_due-game.tick==327,"Home blocks through EOT, excluding release tail")
	game.exterior.update(game.exterior.sign_due-1)
	check(game.exterior.sign_waiting,"Home still waits before EOT")
	game.exterior.update(game.exterior.sign_due)
	check(not game.exterior.sign_waiting and game.fm_sound_id==-1,"Home completion stops all")
	game.exterior.click_hollow(Vector2i(180,45))
	game.exterior.click_hollow(Vector2i(160,100))
	check(not game.exterior.sign_waiting and game.fm_sound_id==-1,"click interrupts sign music")
	game.set_scene("inside")
	game.resident.pose = 4
	game.room_click(Vector2i(300,40))
	check(game.room.music_waiting and game.fm_sound_id==20001,"sleeping child hotspot starts Home")
	check(game.room.interrupt_audio() and not game.room.music_waiting and game.fm_sound_id==-1,"sleeping child music interrupt consumes input")
	game.room.play_home_music()
	game.room.update(game.room.music_due)
	check(not game.room.music_waiting and game.fm_sound_id==-1,"sleeping child Home ends at EOT")
	var m = game.maze
	var incoming = m.walk(9,1,true)
	var outgoing = m.walk(9,0,false)
	check(incoming.back().get("method","")=="stop_sound","incoming walk ends with original forced stop")
	check(outgoing.all(func(e): return not e is Dictionary or e.get("method","")!="stop_sound"),"outgoing walk retains accompaniment for incoming path")
	game.play_sound(20100)
	m.cancel()
	check(game.fm_sound_id==-1,"cancel releases frog music")
	game.play_sound(20101)
	m.stop_sound()
	check(game.fm_sound_id==-1,"maze forced stop releases FM")
	var passed = checks.all(func(c): return c.passed)
	var report = FileAccess.open(OS.get_cmdline_user_args()[0],FileAccess.WRITE)
	report.store_string(JSON.stringify({"passed":passed,"checks":checks,"pcm_sha256":hashes,"scope":"Component controls with audio output disabled; not native waveform or continuous gameplay timing proof."},"\t"))
	report.close()
	game.queue_free()
	await process_frame
	quit(0 if passed else 1)
