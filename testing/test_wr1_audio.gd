extends SceneTree
## Real audio-server output, original scene wiring and song lifecycle.
func _initialize() -> void:
	_run.call_deferred()

func _run() -> void:
	var args := OS.get_cmdline_user_args()
	var output := args[args.find("--audio-output") + 1]
	var recorder := AudioEffectRecord.new()
	AudioServer.add_bus_effect(0, recorder)
	recorder.set_recording_active(true)
	change_scene_to_file("res://scenes/game.tscn")
	await process_frame
	var manager = root.get_node("AudioManager")
	while manager.original == null:
		await process_frame
	var audio = manager.original
	assert(audio.enabled and audio.track == 4 and audio.music.playing)
	for level in range(1, 16):
		var replay: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://testing/fixtures/wr1_demo_level%d_replay.json" % level))
		audio.level(level)
		audio.restore_music_checkpoint(replay.original_music_clock)
	audio.level(1)
	await create_timer(0.3).timeout
	var before: float = audio.music.get_playback_position()
	audio.level(1)
	await create_timer(0.2).timeout
	assert(audio.music.get_playback_position() > before, "Death reload must preserve song position")
	for level in range(1, 4):
		audio.level(level)
		var stream: AudioStreamWAV = audio.music.stream
		assert(stream.loop_mode == AudioStreamWAV.LOOP_FORWARD)
		assert(stream.loop_end == stream.data.size() / 2)
		audio.music.seek(float(stream.loop_end) / stream.mix_rate - 0.12)
		await create_timer(0.4).timeout
		assert(audio.music.playing, "Song stopped at loop boundary")
		var position: float = audio.music.get_playback_position()
		assert(position >= float(stream.loop_begin) / stream.mix_rate and position < float(stream.loop_begin) / stream.mix_rate + 0.7, "Loop position has a gap or wrong boundary")
	audio.set_music_enabled(false)
	assert(audio.music.stream_paused)
	manager.play_original("wrong")
	await create_timer(0.2).timeout
	manager.play_original("step", true)
	assert(audio.effect == "wrong", "Footstep interrupted an active sound")
	manager.play_original("book")
	assert(audio.effect == "book", "A new PC-speaker effect must replace the old one")
	# DOSBox's DC recovery tail is audible after the driver becomes idle.
	audio.speaker.seek(float(audio.manifest.effects.book.logical_duration_samples)/48000.0+0.1)
	manager.play_original("step",true)
	assert(audio.effect == "step", "Speaker recovery tail blocked a new idle-only effect")
	assert(is_equal_approx(audio.music.volume_db,linear_to_db(1.5)) and audio.speaker.volume_db == 0.0)
	await create_timer(0.3).timeout
	for name in ["jump", "slime", "slime_miss", "correct", "mystery_complete", "death", "recap"]:
		manager.play_original(name)
		await create_timer(0.35).timeout
	audio.set_effects_enabled(false)
	assert(not audio.speaker.playing)
	audio.set_effects_enabled(true)
	audio.set_music_enabled(true)
	# Use real controls through the actual scene's movement/contact callbacks.
	while not current_scene.is_replay_ready():
		await process_frame
	Input.action_press("move_right")
	await create_timer(0.8).timeout
	Input.action_release("move_right")
	Input.action_press("jump")
	await create_timer(0.4).timeout
	Input.action_release("jump")
	assert(audio.events.any(func(e): return e.get("name", "") == "step"))
	var evidence := {"events":audio.events.duplicate(true), "track":audio.track}
	change_scene_to_file("res://scenes/main_menu.tscn")
	await process_frame
	assert(manager.original == null, "Menu return left original sound playing")
	await create_timer(0.2).timeout
	recorder.set_recording_active(false)
	var recording := recorder.get_recording()
	assert(recording != null and recording.data.size() > 48000)
	assert(recording.save_to_wav(output) == OK)
	var file := FileAccess.open(output + ".json", FileAccess.WRITE)
	file.store_string(JSON.stringify(evidence))
	AudioServer.remove_bus_effect(0, 0)
	print("Original audio scene, loop, replacement and mixer recording PASS")
	quit()
