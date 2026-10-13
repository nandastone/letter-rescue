extends SceneTree
var game
var checks: Array = []
var touch: bool = false
var label: String

func _initialize() -> void:
	call_deferred("run")

func check(value: bool, name: String) -> void:
	checks.append({"name":label+": "+name,"passed":value,"tick":game.tick})
	if not value:
		print(JSON.stringify(checks.back()))

func click(x: int, y: int) -> void:
	game.move_pointer(Vector2i(x,y))
	if touch:
		var event = InputEventScreenTouch.new()
		event.position = Vector2(x,y)
		event.pressed = true
		game._input(event)
		event.pressed = false
		game._input(event)
	else:
		game.pointer_input("mouse",true,game.pointer)
		game.pointer_input("mouse",false,game.pointer)

func wait_for(condition: Callable, limit: int = 60000) -> bool:
	for i in limit:
		if condition.call():
			return true
		game.advance()
	return false

func settle() -> bool:
	return wait_for(func(): return game.travel.is_empty() and not game.maze.busy)

func control(index: int) -> void:
	var r = game.maze.t.ui_rects[index]
	click(int((r[1]+r[3])/2),int((r[0]+r[2])/2))

func choose(direction: int) -> void:
	var p = game.maze.t.sign_positions[game.maze.node][direction]
	click(p[1]+14,p[0]+13)

func slot(index: int) -> void:
	click(111+25*(index%3),77+23*int(index/3))

func run() -> void:
	for variant in 2:
		touch = bool(variant)
		label = "touch-girl" if touch else "mouse-boy"
		game = load("res://main.tscn").instantiate()
		game.boot_enabled = false
		game.persistence_enabled = false
		root.add_child(game)
		game.set_process(false)
		game.audio_output_enabled = false
		game.random.reset(123456)
		game.capture_sound_events = true
		click(145 if touch else 95,145)
		check(wait_for(func(): return game.scene=="inside"),"character enters room")
		click(60,185)
		check(wait_for(func(): return game.scene=="music" and game.travel.is_empty()),"piano transfer completes")
		click(30,155)
		check(game.travel.get("maze",false),"maze button begins smoke and bucket transfer")
		check(wait_for(func(): return game.scene=="maze"),"maze entrance begins tutorial")
		var m = game.maze
		if touch:
			click(210,180)
		check(settle() and m.phase=="play" and m.earned==0 and not m.tutoring,"tutorial completes or skips through ordinary input")
		check(m.songs.size()==6 and m.history.size()==6 and m.type==4,"first challenge uses six distinct songs and instrument sounds")
		var wrong = (m.correct+1)%4
		choose(wrong)
		check(m.busy,"sign click begins challenge sequence")
		check(settle() and wrong in m.wrong and m.earned==0 and not m.hard,"wrong answer returns to same challenge without a note")
		choose((m.correct+2)%4)
		check(settle() and m.wrong_count==2 and not m.hint,"second error runs correct-sign hint and settles")
		var scene = m.node
		var direction = m.correct
		choose(direction)
		check(settle() and m.earned==1 and m.node==m.t.neighbors[scene][direction],"correct answer earns note and walks to neighboring scene")
		check(m.can_guess,"earned note enables song guessing")
		control(3)
		var wait = int(ceil(game.store.data.pcm["digisnd:1004"].decode_cycles*game.TICK_HZ/(1000.0*game.store.data.platform.cpu_cycles_per_millisecond)))
		check(m.loading_sound and not m.chooser,"cold drawer waits for recovered decoder work")
		click(210,180)
		check(m.loading_sound,"click does not bypass pending decoder work")
		game.advance(maxi(0,wait-1))
		check(not m.chooser,"drawer remains closed before decoder deadline")
		game.advance()
		check(m.chooser and not m.loading_sound,"drawer begins at decoder deadline")
		check(settle() and m.chooser,"drawer opens to song choices")
		var wrong_song = (m.secret+1)%6
		slot(wrong_song)
		check(settle() and wrong_song in m.eliminated and m.guess_locked and not m.chooser,"wrong guess closes drawer and locks guess until next note")
		choose(m.correct)
		check(settle() and m.earned==2 and m.hard and m.can_guess,"two successful signs advance difficulty and unlock guess")
		check(wait_for(func(): return m.automatic_listening),"idle timer automatically repeats target sound")
		choose(m.correct)
		check(settle() and m.earned==3,"click during automatic audition remains pending and answers sign")
		control(3)
		check(m.chooser and not m.loading_sound,"warm drawer reuses prepared sound")
		check(settle(),"warm drawer settles")
		slot(m.secret)
		check(settle() and m.phase=="win" and m.earned==m.song[0],"correct early guess completes victory choreography")
		control(8)
		check(m.busy and m.replaying,"victory replay uses full song")
		check(settle() and m.phase=="win","full victory song finishes")
		var old_songs = m.songs.duplicate()
		var previous_secret = m.secret
		control(7)
		check(settle() and m.phase=="play" and m.earned==0,"new-maze control walks out and starts next round")
		var differences = 0
		for i in mini(old_songs.size(),m.songs.size()):
			differences += int(old_songs[i]!=m.songs[i])
		check(m.songs.size()==6 and differences==1 and m.songs[previous_secret] not in old_songs,"new round replaces only the solved song")
		control(1)
		check(game.scene=="music" and game.travel.get("maze",false),"back arrow begins bucket return to music")
		check(settle() and game.scene=="music","return smoke restores piano")
		click(30,155)
		check(wait_for(func(): return game.scene=="maze"),"reentry opens maze")
		click(210,180)
		check(settle() and m.phase=="play","reentry choreography remains interruptible")
		control(0)
		check(game.scene=="inside" and not game.travel.is_empty(),"global exit starts room return transfer")
		check(settle() and game.scene=="inside","global exit restores room")
		game.queue_free()
		await process_frame
	var passed = checks.all(func(c): return c.passed)
	var file = FileAccess.open(OS.get_cmdline_user_args()[0],FileAccess.WRITE)
	file.store_string(JSON.stringify({"passed":passed,"checks":checks,"scope":"Fresh mouse/boy and touch/girl production controls, normal game ticks and deterministic session seed. Reads answers to select signs; does not inject maze states, rewards or difficulty. Tests full/skipped tutorial, errors, guessed songs, decoder waits, automatic-audition interruption, victory, replay, new round and exits. Audio output is disabled."},"\t"))
	file.close()
	print(JSON.stringify({"passed":passed,"count":checks.size(),"failures":checks.filter(func(c): return not c.passed)}))
	quit(0 if passed else 1)
