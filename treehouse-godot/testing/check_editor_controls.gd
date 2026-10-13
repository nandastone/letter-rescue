extends SceneTree
var game
var checks: Array = []
var path: String

func _initialize() -> void:
	path = OS.get_cmdline_user_args()[0]
	call_deferred("run")

func check(value: bool, name: String) -> void:
	checks.append({"name":name,"passed":value})

func click(x: int, y: int) -> void:
	game.move_pointer(Vector2i(x,y))
	game.pointer_input("mouse",true,game.pointer)
	game.pointer_input("mouse",false,game.pointer)

func key(code: int, pressed: bool = true, unicode: int = 0, ctrl: bool = false) -> void:
	var event = InputEventKey.new()
	event.keycode = code
	event.pressed = pressed
	event.unicode = unicode
	event.ctrl_pressed = ctrl
	game._input(event)

func wait_for(condition: Callable) -> bool:
	for i in 10000:
		if condition.call():
			return true
		game.advance()
	return false

func run() -> void:
	game = load("res://main.tscn").instantiate()
	game.boot_enabled = false
	game.persistence_enabled = false
	root.add_child(game)
	game.set_process(false)
	game.audio_output_enabled = false
	game.music.editor = game.music.Editor.new(game,false)
	var m = game.music
	var e = m.editor
	click(95,145)
	check(wait_for(func(): return game.scene=="inside"),"original entrance")
	click(60,185)
	check(wait_for(func(): return game.scene=="music" and game.travel.is_empty()),"piano transition")
	click(274,169)
	check(e.enabled and e.editable and m.title=="My Short Song #1","compose button opens personal short book")
	key(KEY_Z)
	check(e.song[0]==1 and e.song[5]==0 and e.position==0,"held key writes at insertion marker")
	key(KEY_Z,false)
	check(e.position==1 and m.notes.is_empty(),"release advances insertion marker")
	key(KEY_X)
	game._notification(Node.NOTIFICATION_APPLICATION_FOCUS_OUT)
	check(e.position==2 and m.notes.is_empty() and game.held.is_empty(),"focus loss releases and advances held note")
	click(181,19)
	check(not e.title_entry.is_empty() and e.title_entry.value=="","title begins with blank input")
	key(KEY_A,true,97)
	key(KEY_ESCAPE)
	check(e.title_entry.value=="My Short Song #1" and game.scene=="music","Escape restores title and keeps editing")
	click(295,101)
	click(181,19)
	for c in "Tune":
		key(c.to_upper().unicode_at(0),true,c.unicode_at(0))
	key(KEY_ENTER)
	key(KEY_ENTER,false)
	check(e.title=="Tune" and e.title_entry.is_empty() and e.song[0]==2,"typing title does not play piano notes")
	click(311,30)
	var before = e.song.duplicate()
	key(KEY_C)
	key(KEY_C,false)
	check(m.contents==1 and e.song==before,"contents auditions without writing")
	click(269,13)
	check(m.contents==0 and e.index[0]==0,"page number closes contents")
	click(275,149)
	check(e.mode==1 and e.title=="My Long Song #1" and e.song[1]==0,"long book remains independent")
	key(KEY_Z)
	key(KEY_Z,false)
	click(275,149)
	check(e.mode==0 and e.title=="Tune" and e.song[0]==2,"short book restored after mode change")
	click(245,125)
	check(m.dialog.get("message","")=="erase","erase asks confirmation")
	click(59,70)
	check(m.dialog.is_empty() and e.song[0]==2,"declining erase preserves song")
	click(274,169)
	click(273,125)
	check(m.dialog.get("message","")=="copy","listening copy asks confirmation")
	click(23,70)
	check(e.enabled and e.index[0]==1 and e.title.begins_with("My ") and e.labels.is_empty(),"copy uses first free page without overwriting authored song")
	click(273,125)
	click(23,70)
	check(not e.random_task.is_empty(),"random button begins original staggered generation")
	check(wait_for(func(): return e.random_task.is_empty()) and e.song[0]==8 and e.song[4]==1 and e.song[20]==0,"random song fills eight notes and ends with whole note")
	click(298,125)
	check(m.dialog.get("message","")=="print","print asks confirmation")
	click(23,70)
	check(m.print_view!=null and m.print_view.get_size()==Vector2i(320,200),"print produces original score sheet")
	key(KEY_Z)
	check(m.notes.is_empty(),"print view blocks piano input")
	key(KEY_ESCAPE)
	check(m.print_view==null and game.scene=="music","Escape closes print view")
	var bytes = e.export_data()
	check(bytes.size()==8688,"SONGS.DAT has original length")
	var replacement = m.Editor.new(game,false)
	check(replacement.import_data(bytes,false) and replacement.export_data()==bytes,"all records and titles round trip byte exactly")
	var corrupt = bytes.duplicate()
	corrupt[2] = 255
	check(not replacement.import_data(corrupt,false) and replacement.export_data()==bytes,"invalid record rejects entire import without mutation")
	check(not replacement.import_data(bytes.slice(0,8687),false),"truncated file rejected")
	var accented = "Café üß"
	replacement.titles[0][0] = replacement.encode_title(accented)
	check(replacement.title_at(0,0)==accented,"CP437 title characters round trip")
	e.storage_enabled = true
	e.storage_path = path.get_basename()+".SONGS.DAT"
	e.save()
	check(e.save_error==OK and FileAccess.get_file_as_bytes(e.storage_path)==bytes,"save writes original binary file")
	check(replacement.import_data(FileAccess.get_file_as_bytes(e.storage_path),false) and replacement.export_data()==bytes,"saved file reloads without data loss")
	e.storage_enabled = false
	key(KEY_CTRL,true,0,true)
	click(245,125)
	check(m.dialog.get("message","")=="erase_all","Ctrl erase asks to clear both books")
	click(23,70)
	key(KEY_CTRL,false)
	check(e.books.all(func(book): return book.slice(0,42).all(func(raw): return raw[0]==0 and raw[1]==0)) and e.books[0][42]==game.store.data.music.end_songs[0].map(func(v): return int(v)),"erase all resets both books and preserves ending")
	var passed = checks.all(func(c): return c.passed)
	var file = FileAccess.open(path,FileAccess.WRITE)
	file.store_string(JSON.stringify({"passed":passed,"checks":checks,"scope":"Production mouse/keyboard controls and normal ticks from character selection through both composing books, titles, contents, copy/random/erase/print, plus binary persistence validation. Storage is isolated to the report directory. Device audio disabled."},"\t"))
	file.close()
	print(JSON.stringify({"passed":passed,"checks":checks}))
	game.queue_free()
	await process_frame
	quit(0 if passed else 1)
