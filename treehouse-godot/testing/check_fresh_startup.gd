extends SceneTree
var game
var checks: Array = []
var output: String

func _initialize() -> void:
	call_deferred("run")

func check(value: bool, name: String) -> void:
	checks.append({"name":name,"passed":value})
	if not value: print(JSON.stringify(checks.back()))

func run() -> void:
	output = OS.get_cmdline_user_args()[0]
	game = load("res://main.tscn").instantiate()
	game.boot_enabled = false
	game.persistence_enabled = false
	# Pin the platform's BIOS seed before any normal constructor consumes it.
	game.random.reset(0)
	root.add_child(game)
	game.set_process(false)
	game.audio_output_enabled = false
	# Isolated component setup: use the same empty resident constructor as
	# production fresh-profile startup, without accessing the user's saves.
	game.resident.dispose()
	game.random.reset(0)
	game.resident = game.Resident.new(game,false)
	game.persistence = game.Persistence.new(game,true,output+"/STATUS.DAT")
	var p = game.persistence
	check(p.initialization=="fresh","missing profile takes original default path")
	check(p.file.warnings.is_empty(),"fresh values require no repairs")
	check(game.music.song_id==0 and p.listening_pages==[0,0] and not game.music.editor.enabled,"both listening books begin at first page")
	check(game.music.editor.used_flags.all(func(v): return v==0),"all stored personal-song flags start clear, including terminal-page flags")
	check(game.room.cloud==0 and game.resident.objects.map(func(o): return o.type)==[9,10,8] and game.balloon.hidden,"fresh room has original two fixed objects and normalized pillow")
	check(game.nature.objects==[[],[]] and game.nature.time==0 and game.nature.category==-1,"fresh animal scenes are empty with no selected class")
	check(game.nature.quiz.opponent==1 and game.nature.quiz.help==[false,false,true],"fresh quiz uses human opponent and robot-only help")
	check(game.boardgame.opponent==1 and game.boardgame.saved_levels==[0,0,0,0,0,0],"fresh board uses human opponent and lowest goals")
	check(game.theater.selection==[-1,-1,-1,-1] and game.theater.order==[0,1,2,3] and not game.theater.props_enabled and not game.theater.mix_up,"fresh theater has original empty phrase and switches")
	check(game.preferences.settings=={"sound":true,"printing":true,"printer":0,"advanced":false,"speed":false},"fresh preferences follow original initialization")
	check(game.maze.saved_songs==[6,13,7,5,18,12],"fixed platform seed generates six native chooser songs")
	p.save()
	var raw = FileAccess.get_file_as_bytes(output+"/STATUS.DAT")
	var original = FileAccess.open(output+"/fresh.dat",FileAccess.WRITE)
	original.store_buffer(raw)
	original.close()
	check(raw.size()==2704 and p.save_error==OK,"fresh profile persists in original format")
	game.preferences.open_settings()
	game.render()
	game.surface.image.save_png(output+"/preferences.png")
	game.preferences.kind = ""
	var seed = game.random.seed
	var reload = game.Persistence.new(game,true,output+"/STATUS.DAT")
	check(reload.initialization=="loaded" and reload.export_data()==raw,"fresh profile reload preserves all bytes")
	check(game.random.seed==seed,"reloading this three-object profile does not regenerate maze songs")
	# A prior Godot profile still migrates instead of discarding authored state.
	DirAccess.make_dir_recursive_absolute(output+"/legacy")
	var legacy = FileAccess.open(output+"/legacy/preferences.json",FileAccess.WRITE)
	legacy.store_string('{"version":1,"settings":{"sound":false,"printing":true,"printer":1,"advanced":true,"speed":true}}')
	legacy.close()
	game.preferences.settings.sound = false
	game.preferences.settings.advanced = true
	var migrated = game.Persistence.new(game,true,output+"/legacy/STATUS.DAT")
	check(migrated.initialization=="migration" and not game.preferences.settings.sound and game.preferences.settings.advanced,"existing legacy settings are retained by migration")
	# The original missing-STATUS capture retains SONGS.DAT. Its presence alone
	# must not substitute the bundled profile for native fresh settings.
	DirAccess.make_dir_recursive_absolute(output+"/songs-only")
	var editor = game.music.editor
	editor.books[0][0][0] = 1
	editor.books[0][0][5] = 9
	editor.titles[0][0] = editor.encode_title("Retained personal song")
	var song_bytes = editor.export_data()
	var song_file = FileAccess.open(output+"/songs-only/SONGS.DAT",FileAccess.WRITE)
	song_file.store_buffer(song_bytes)
	song_file.close()
	game.resident.dispose()
	game.random.reset(0)
	game.resident = game.Resident.new(game,false)
	var songs_only = game.Persistence.new(game,true,output+"/songs-only/STATUS.DAT")
	check(songs_only.initialization=="fresh","SONGS without STATUS uses native fresh profile")
	check(songs_only.export_data().slice(0,0x8ea)==raw.slice(0,0x8ea),"SONGS-only persistent region equals native fresh defaults")
	check(editor.used_flags.all(func(v): return v==0),"SONGS-only startup clears usage flags through STATUS defaults")
	check(editor.export_data()==song_bytes and FileAccess.get_file_as_bytes(output+"/songs-only/SONGS.DAT")==song_bytes,"fresh STATUS initialization preserves separate song bytes")
	songs_only.save()
	var songs_reload = game.Persistence.new(game,true,output+"/songs-only/STATUS.DAT")
	check(songs_reload.initialization=="loaded" and songs_reload.export_data()==songs_only.export_data(),"SONGS-only fresh profile survives STATUS reload")
	game.persistence = reload
	var passed = checks.all(func(c): return c.passed)
	var file = FileAccess.open(output+"/godot.json",FileAccess.WRITE)
	file.store_string(JSON.stringify({"passed":passed,"checks":checks},"\t"))
	file.close()
	print(JSON.stringify({"passed":passed,"checks":checks.size()}))
	game.audio.stream = null
	game.audio_cache.clear()
	game.queue_free()
	await process_frame
	quit(0 if passed else 1)
