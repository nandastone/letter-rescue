extends SceneTree
var game
var checks: Array = []
var output: String
var rich: Dictionary

func _initialize() -> void:
	call_deferred("run")

func check(value: bool, name: String) -> void:
	checks.append({"name":name,"passed":value})
	if not value: print(JSON.stringify(checks.back()))

func write(name: String, data: PackedByteArray) -> void:
	var f = FileAccess.open(output+"/"+name,FileAccess.WRITE)
	f.store_buffer(data)
	f.close()

func snapshot() -> Dictionary:
	var p = game.persistence
	var m = game.music
	var n = game.nature
	var b = game.boardgame
	var t = game.theater
	return {"pages":[p.listening_pages[0],m.editor.index[0],p.listening_pages[1],m.editor.index[1]],"composing":m.editor.enabled,"mode":m.mode,"repeating":m.repeating,"settings":game.preferences.settings.duplicate(),"cloud":game.room.cloud,"nature_time":n.time,"nature_attribute":n.attribute,"nature_values":n.values.duplicate(),"nature_category":n.category,"nature_objects":n.objects.map(func(list): return list.map(func(o): return [o.id,o.x,o.y])),"board_mode":b.mode,"board_opponent":b.opponent,"board_goals":b.saved_levels.duplicate(),"quiz_opponent":n.quiz.opponent,"quiz_help":n.quiz.help.duplicate(),"theater_selection":t.selection.duplicate(),"theater_flags":[t.mix_up,t.props_enabled],"theater_props":t.props.duplicate(true),"room_objects":game.resident.objects.map(func(o): return {"type":o.type,"state":o.state,"inside":o.inside,"rect":game.resident.bounds(o)}),"theater_order":t.order.duplicate(),"theater_actor":t.actor_drag.duplicate(true),"theater_validation":t.previous_validation,"maze_history":game.maze.history.duplicate(),"maze_songs":game.maze.saved_songs.duplicate()}

func run() -> void:
	output = OS.get_cmdline_user_args()[0]
	game = load("res://main.tscn").instantiate()
	game.boot_enabled = false
	game.persistence_enabled = false
	root.add_child(game)
	game.set_process(false)
	game.audio_output_enabled = false
	var p = game.persistence
	for c in JSON.parse_string(FileAccess.get_file_as_string(output+"/fixture.json")):
		var bytes = FileAccess.get_file_as_bytes(output+"/"+c.name+".dat")
		check(p.import_data(bytes),c.name+": accepts complete file")
		check(game.scene=="outside" and not game.resident.selected and game.held.is_empty() and game.travel.is_empty(),c.name+": returns to fresh character selection")
		write(c.name+"-roundtrip.dat",p.export_data())
		if c.name=="rich":
			rich = snapshot()
			check(game.resident.find(15)==null and game.resident.find(7)==null and game.resident.find(8)!=null,"transient bird/spent flower removed and pillow retained")
			check(game.resident.find(6).state==2 and game.balloon.state==2 and game.resident.find(14).state==4,"native object-state normalization")
			check(game.nature.objects[0].size()==2 and game.nature.objects[1].size()==2,"both animal collages restored")
			check(game.theater.props.all(func(list): return list.size()==1),"all six theater prop sets restored")
			check(game.music.editor.used(0,0) and game.music.editor.used(1,0) and not game.music.editor.used(0,1),"STATUS used flags control songbook membership")
		if c.name=="invalid":
			check(p.file.warnings.size()>15,"invalid known values reported")
			check(game.theater.order==[0,1,2,3] and game.boardgame.opponent==1,"invalid order/opponent normalized safely")
			check(game.maze.saved_songs.size()==6,"invalid maze chooser repaired")
		game.preferences.settings.sound = not game.preferences.settings.sound
		write(c.name+"-changed.dat",p.export_data())
	var before = p.export_data()
	check(not p.import_data(PackedByteArray([1,2,3])) and p.export_data()==before,"truncated import rejected without changing state")
	var bytes = FileAccess.get_file_as_bytes(output+"/rich.dat")
	p.import_data(bytes)
	game.music.set_mode(0)
	check(game.music.song_id==3,"mode change restores distinct short listening page")
	game.music.set_mode(1)
	check(game.music.song_id==9,"mode change restores distinct long listening page")
	check(p.export_data()==bytes,"round trip through score modes preserves source bytes")
	game.music.set_composing(false)
	game.music.select_page(5)
	var selected = p.export_data()
	check(selected[0x56]==5 and selected[0x58]==5,"ordinary listening selection synchronizes both pages")
	p.import_data(bytes)
	game.music.editor.titles[0][1] = game.music.editor.encode_title("A new song")
	var changed = p.export_data()
	check(changed[1]==1 and changed[0]==227 and changed[43]==84,"edited song sets its flag and preserves untouched noncanonical flags")
	p.import_data(bytes)
	game.balloon.x += 1
	changed = p.export_data()
	check(changed.decode_u16(0x8ee)==12 and changed.decode_u16(0x8fa)==0xbeef,"moving balloon preserves normalized source state and opaque handle")
	game.resident.find(14).state = 3
	changed = p.export_data()
	check(changed.decode_u16(0x8ec+60+2)==3 and changed.decode_u16(0x8ec+20+2)==5,"normalized room objects retain original record slots when edited")
	p.import_data(FileAccess.get_file_as_bytes(output+"/filtered.dat"))
	var animal = game.nature.objects[0][0]
	animal.x += 1
	var prop = game.theater.props[0][0]
	prop.y += 1
	changed = p.export_data()
	check(changed.decode_u16(0x86)==65535 and changed.decode_s16(0x128+16)==animal.x,"filtered animal edits retain original interleaved slot")
	check(changed.decode_u16(0x796)==65535 and changed.decode_s16(0x3d6+8)==prop.y,"filtered prop edits retain original slot")
	var pillow = game.resident.find(8)
	pillow.rect[1] += 1
	pillow.rect[3] += 1
	changed = p.export_data()
	check(changed.decode_u16(0x8ea)==3,"editing automatically supplied pillow materializes normalized object list")
	write("materialized.dat",changed)
	p.import_data(changed)
	check(game.resident.find(8).rect==game.MusicMaze.integers(pillow.rect) and game.resident.find(15)==null,"materialized object list reloads correctly")
	p.import_data(bytes)
	var songs = game.music.editor.export_data()
	game.rewards.shelf[0] = true
	game.rewards.visited = 7
	game.nature.mode = "quiz"
	game.resident.selected = true
	p.import_data(bytes)
	check(game.music.editor.export_data()==songs,"STATUS import preserves separate song records")
	check(not game.rewards.shelf[0] and game.rewards.visited==0 and game.nature.mode=="explore" and game.boardgame.options and not game.maze.started,"import resets unsaved matches and prize session")
	p.save_path = output+"/persisted.dat"
	p.storage_enabled = true
	p.save()
	check(p.save_error==OK and FileAccess.get_file_as_bytes(p.save_path)==p.export_data(),"binary save writes complete current file")
	var expected = snapshot()
	var saved_path = p.save_path
	var saved_bytes = p.export_data()
	p.storage_enabled = false
	game.queue_free()
	await process_frame
	game = load("res://main.tscn").instantiate()
	game.boot_enabled = false
	game.persistence_enabled = false
	root.add_child(game)
	game.set_process(false)
	game.audio_output_enabled = false
	game.persistence = game.Persistence.new(game,true,saved_path)
	p = game.persistence
	check(snapshot()==expected and p.export_data()==saved_bytes,"fresh runtime file reload restores full saved model without byte drift")
	p.storage_enabled = false
	# Unsafe all-seen history must still permit an actual new round and replacement.
	p.import_data(FileAccess.get_file_as_bytes(output+"/invalid.dat"))
	game.maze.reset()
	game.maze.replace_song()
	check(game.maze.songs.size()==6 and game.maze.history.size()<24,"invalid all-seen maze starts and replaces a song without hanging")
	game.scene = "outside"
	game.maze.cancel()
	var event = InputEventKey.new()
	event.keycode = KEY_F9
	event.pressed = true
	game._input(event)
	check(game.file_exchange.active,"F9 opens file controls")
	var tick = game.tick
	game._process(3)
	check(game.tick==tick,"file controls pause simulation during interchange")
	check(not game.file_exchange.import_data("load-status",PackedByteArray([0])) and game.file_exchange.message.text.contains("not changed"),"file controls explain rejected import")
	check(game.file_exchange.import_data("load-status",bytes) and game.scene=="outside","file controls load original game data")
	check(game.file_exchange.export_data("save-status")==bytes,"file controls export original bytes")
	event.keycode = KEY_ESCAPE
	game._input(event)
	check(not game.file_exchange.active,"Escape returns from file controls")
	write("broken-local.dat",PackedByteArray([1,2,3]))
	var recovered = game.Persistence.new(game,true,output+"/broken-local.dat")
	recovered.save()
	check(FileAccess.get_file_as_bytes(output+"/broken-local.dat.rejected")==PackedByteArray([1,2,3]) and FileAccess.get_file_as_bytes(output+"/broken-local.dat").size()>=2704,"truncated local save is preserved before profile recovery")
	recovered.storage_enabled = false
	var f = FileAccess.open(output+"/godot.json",FileAccess.WRITE)
	f.store_string(JSON.stringify({"checks":checks,"rich":rich},"  "))
	f.close()
	game.queue_free()
	await process_frame
	quit(0)
