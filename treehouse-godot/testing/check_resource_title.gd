extends SceneTree
const Assets = preload("res://scripts/resource_startup_assets.gd")
const Startup = preload("res://scripts/resource_startup.gd")
const Title = preload("res://scripts/resource_title.gd")
const Entrance = preload("res://scripts/resource_entrance.gd")
const RoomResources = preload("res://scripts/resource_room.gd")
const Transfer = preload("res://scripts/resource_room_transfer.gd")
const ScrAnimation = preload("res://scripts/animation.gd")
const BoardResources = preload("res://scripts/resource_board.gd")
const BoardGame = preload("res://scripts/boardgame.gd")
const Palettes = preload("res://scripts/resource_palette.gd")
var stages: Dictionary = {}
var checks: Array = []
var movement_timing: Dictionary = {}

class ScriptStore extends RefCounted:
	var data: Dictionary
	func _init(id: int, script: Dictionary) -> void:
		data = {"scripts":{"TH:%d" % id:script}}
	func key(archive: String, id: int) -> String:
		return "%s:%d" % [archive,id]

class BoardHost extends RefCounted:
	const MusicMaze = preload("res://scripts/music_maze.gd")
	const Random = preload("res://scripts/random.gd")
	var store: Dictionary
	var random = Random.new()
	var tick: int = 0
	var sound_handler: Callable
	var sound_events: Array = []
	var audio
	func _init(tables: Dictionary, seed: int) -> void:
		store = {"data":{"boardgame":tables,"strings":{}}}
		random.reset(seed)
	func play_sound(id: int) -> int:
		sound_events.append([tick,id])
		return sound_handler.call(id) if sound_handler.is_valid() else 0

class AudioSink extends RefCounted:
	var stopped: Callable
	func stop() -> void:
		stopped.call()

func observe(label: String, state: Dictionary) -> void:
	var arena = Startup.arena_snapshot(state.memory)
	for block in arena.heap.blocks: block.erase("payload")
	var payloads: Dictionary = {}
	for id in state.memory.resource_payloads:
		var hash = HashingContext.new()
		hash.start(HashingContext.HASH_SHA256)
		hash.update(state.memory.resource_payloads[id])
		payloads[id] = hash.finish().hex_encode()
	var catalogs: Array = []
	for file in state.catalogs.files: catalogs.append(state.catalogs.snapshot(file.handle))
	stages[label] = {"arena":arena,"near":state.memory.near.snapshot(),"dos":state.dos.snapshot(),
		"files":state.catalogs.files.duplicate(true),"catalogs":catalogs,"payloads":payloads}

func _initialize() -> void:
	var output = OS.get_cmdline_user_args()[0]
	var input: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(output+"/fixture.json"))
	var configs: Dictionary = Assets.decode(input.inputs.scenes)
	var title: Dictionary = configs.title
	var entrance: Dictionary = configs.entrance
	var state = Assets.from_data(input.inputs)
	Title.prepare(state,title,observe)
	for i in title.animationOrigins.size():
		if i:
			Title.prepare_animation(state,title.animationPalette.id,title.script,title.animationOrigins[i],
				func(stage,s): observe(stage.replace("animation-","animation-%d-" % (i+1)),s))
		Title.start_animation(state)
		Title.finish_animation(state,title.querySound)
	Title.release_title(state)
	Title.finish_music(state)
	observe("title-complete",state)
	if input.entrance: Entrance.initialize(state,entrance,observe)
	if input.selection != "":
		# Explicit semantic events from this input route; clock integration is
		# separate. No observed resource addresses or allocation requests used.
		Entrance.prepare_idle(state,5)
		for i in 2: Entrance.advance_credit(state,entrance.creditBounds)
		observe("selection-before",state)
		Entrance.select_child(state,entrance,1 if input.selection=="girl" else 0,observe)
		checks.append({"name":"selection releases all four child backgrounds and both palettes","passed":state.entrancePhase=="selected" and state.childPalettes.is_empty() and not state.boyEntranceSaved.descriptor and not state.girlEntranceSaved.descriptor and state.entranceSaved.slice(0,2).all(func(s): return not s.descriptor)})
	if input.room:
		var room: Dictionary = configs.rooms[input.selection].duplicate(true)
		room.cloud = 5
		room.hour = 12
		room.minute = 0
		room.objects = room.objectDefinitions
		RoomResources.open_child(state,room.archive)
		observe("room-before",state)
		RoomResources.prepare(state,room,observe)
	if input.transfer:
		var transfer: Dictionary = configs.transfer
		observe("transfer-before",state)
		Transfer.begin(state,transfer,observe)
		Transfer.start_ring(state)
		var ring = ScrAnimation.new(ScriptStore.new(transfer.palette.id,transfer.script),"TH",transfer.palette.id,transfer.palette.id)
		ring.displayed.connect(func(): Transfer.compose_ring(state))
		for tick in 10000:
			if ring.done: break
			ring.update(tick)
		checks.append({"name":"production SCR interpreter completes ring with 18 displays","passed":ring.done and ring.frame_updates==18})
		Transfer.prepare_bubble(state,transfer.bubble,observe)
		Transfer.start_bubble(state)
		var sounds: Array = []
		var callbacks: Array = []
		var bubble = ScrAnimation.new(ScriptStore.new(transfer.bubble.id,transfer.bubble.script),"TH",transfer.bubble.id,1100)
		bubble.sound_requested.connect(func(id): sounds.append(id); Transfer.play_bubble_sound(state,id))
		bubble.callback_requested.connect(func(slot,argument): callbacks.append([slot,argument]))
		for tick in 10000:
			if bubble.done: break
			bubble.update(tick)
		checks.append({"name":"production SCR interpreter completes bubble with authored sounds and callback","passed":bubble.done and bubble.frame_updates==13 and sounds==[10034,10035] and callbacks==[[0,0]]})
		Transfer.finish(state,transfer.bubble.querySound,observe)
		checks.append({"name":"transfer releases animation, script, inlet and playing sound","passed":state.transferAnimation.disposed and not state.transferScript and not state.inletSaved and not state.transferSound})
		Transfer.release_room(state,observe)
		checks.append({"name":"room release frees saved backgrounds and palette ownership","passed":state.roomPalettes.is_empty() and not state.theaterSaved.descriptor and not state.characterSaved.descriptor and state.roomObjects.all(func(item): return not item.saved.descriptor)})
	if input.board:
		var host = BoardHost.new(input.board_tables,int(input.board_seed))
		var game = BoardGame.new(host,false)
		BoardResources.prepare(state,configs.board,observe)
		game.enter()
		BoardResources.begin_drawing(state,configs.board,observe)
		BoardResources.prepare_options(state,configs.board,game,observe)
		var equal = host.random.seed==int(input.expected_game.seed)
		for field in ["nodes","directions","balances","types"]:
			equal = equal and game.get(field)==Assets.decode(input.expected_game[field])
		checks.append({"name":"production board generates native entry state from one supplied seed","passed":equal})
		BoardResources.finish_options(state,game,observe)
		checks.append({"name":"board/options temporary surfaces released at ready state","passed":state.entrancePhase=="board-options-ready" and not state.boardSurface and not state.boardOptionsSurface})
		if input.get("play",false):
			BoardResources.press_play(state,configs.board,observe)
			# The click completes during the original button flash. The live
			# caller must deliver sound completion; this fixture owns no clock.
			BoardResources.finish_sound(state)
			BoardResources.dismiss_options(state,observe)
			game.prepare_game()
			BoardResources.begin_drawing(state,configs.board)
			BoardResources.finish_drawing(state,game)
			observe("board-redraw-after",state)
			equal = host.random.seed==int(input.expected_started_game.seed)
			for field in ["nodes","directions","balances","types"]:
				equal = equal and game.get(field)==Assets.decode(input.expected_started_game[field])
			checks.append({"name":"production board restart continues RNG without reseeding","passed":equal})
			BoardResources.draw_pawn(state,game)
			BoardResources.prepare_dashboard(state,configs.board,game,observe)
			var descriptor: Dictionary = configs.board.dashboards[game.role()]
			var dashboard = ScrAnimation.new(ScriptStore.new(descriptor.id,descriptor.script),"TH",descriptor.id,descriptor.id)
			var sounds: Array = []
			dashboard.sound_requested.connect(func(id): sounds.append(id); BoardResources.play_sound(state,id))
			for tick in 10000:
				if dashboard.done: break
				dashboard.update(tick)
			checks.append({"name":"production dashboard SCR completes with authored sound","passed":dashboard.done and sounds==[10010]})
			BoardResources.finish_dashboard(state,configs.board,observe)
			# Original first-turn prompt flashes three times (red and white).
			# Each draw owns its temporary surface; elapsed time is separate.
			for i in 6: BoardResources.draw_roll_hint(state,game)
			observe("board-play-after",state)
			if input.get("roll",false):
				game.options = false
				game.played = true
				# This native countdown is an explicit test input, like the
				# entry seed. Live clocks must generate it independently.
				game.hint_due = int(input.roll_hint_countdown)
				var prompts: Array = []
				var sound_clock = {"due":-1,"tick":0}
				host.sound_handler = func(id):
					BoardResources.play_sound(state,id)
					var payload: PackedByteArray = state.memory.resource_payloads[state.boardSound]
					var rate = int(1000000.0/int(1000000.0/payload.decode_u16(1)))
					var duration = ceili((payload.size()-10)*60.0/rate)
					sound_clock.due = sound_clock.tick+duration
					if payload[0]&0x80: sound_clock.due = -1
					return duration
				BoardResources.connect_roll_events(state,game)
				game.roll_prompt_drawn.connect(func(value): prompts.append([sound_clock.tick,value]))
				game.roll_faces_started.connect(func(): observe("board-roll-faces-before",state))
				game.roll_faces_finished.connect(func(): observe("board-roll-faces-after",state))
				observe("board-roll-before",state)
				game.roll()
				var completed = -1
				for tick in range(1,301):
					host.tick = tick
					sound_clock.tick = tick
					if sound_clock.due>=0 and tick>=sound_clock.due:
						BoardResources.finish_sound(state)
						sound_clock.due = -1
					game.update(tick)
					if game.phase=="move" and not game.motion.busy:
						completed = tick
						break
				observe("board-roll-after",state)
				checks.append({"name":"first roll prompt sequence matches original relative PIT ticks","passed":prompts==Assets.decode(input.expected_roll_prompts)})
				checks.append({"name":"first roll sound dispatch matches original relative PIT ticks","passed":host.sound_events==Assets.decode(input.expected_roll_sounds)})
				checks.append({"name":"first roll and pawn blink finish on original relative PIT tick","passed":completed==int(input.expected_roll_complete)})
				checks.append({"name":"first roll continues native RNG and result without reseeding","passed":host.random.seed==int(input.expected_rolled_game.seed) and game.remaining==int(input.expected_rolled_game.remaining)})
				if input.get("move",false):
					BoardResources.connect_move_events(state,game,observe)
					# Let the existing reminder countdown expire through normal
					# update calls before the recorded next mouse action.
					var reminded = false
					for tick in range(game.tick+1,game.tick+301):
						host.tick = tick
						sound_clock.tick = tick
						game.update(tick)
						reminded = reminded or game.motion.reminding
						if reminded and not game.motion.busy: break
					checks.append({"name":"original pending reminder expires without resetting after the roll","passed":reminded and not game.motion.busy})
					host.audio = AudioSink.new()
					host.audio.stopped = func(): BoardResources.finish_sound(state); sound_clock.due = -1
					var owner = weakref(game)
					var started: int = game.tick
					var events: Array = []
					var landed: Dictionary = {}
					game.pawn_travel_started.connect(func(_target): events.append(["movement.begin",sound_clock.tick-started]))
					game.pawn_travel_step.connect(func(): events.append(["pawn.paint",sound_clock.tick-started]))
					game.pawn_travel_finished.connect(func(): events.append(["movement.end",sound_clock.tick-started]))
					game.landing_started.connect(func():
						events.append(["landing.begin",sound_clock.tick-started])
						observe("board-landing-before",state)
						var current = owner.get_ref()
						landed.seed = current.host.random.seed
						for field in ["remaining","nodes","directions"]: landed[field] = current.get(field).duplicate() if current.get(field) is Array else current.get(field))
					observe("board-move-before",state)
					var accepted = game.move(int(input.move_target))
					for tick in range(started+1,started+301):
						host.tick = tick
						sound_clock.tick = tick
						if sound_clock.due>=0 and tick>=sound_clock.due:
							BoardResources.finish_sound(state)
							sound_clock.due = -1
						game.update(tick)
						if not landed.is_empty(): break
					checks.append({"name":"ordinary movement reaches native landing state without RNG injection","passed":accepted and landed==Assets.decode(input.expected_landing_game)})
					var expected_events: Array = Assets.decode(input.expected_move_ticks)
					var actual_steps = events.filter(func(e): return e[0]=="pawn.paint")
					var expected_steps = expected_events.filter(func(e): return e[0]=="pawn.paint")
					var same_cadence = actual_steps.size()==expected_steps.size() and not actual_steps.is_empty()
					if same_cadence:
						for i in actual_steps.size(): same_cadence = same_cadence and actual_steps[i][1]-actual_steps[0][1]==expected_steps[i][1]-expected_steps[0][1]
					checks.append({"name":"pawn frame count and three-tick cadence match after preparation","passed":same_cadence})
					movement_timing = {"actual":events,"expected":expected_events,"exact":events==expected_events,"scope":"Preparation elapsed time remains unmodeled; no absolute movement timing claim."}
	var m = state.memory
	var catalogs = state.catalogs
	var palettes = Palettes.new(catalogs)
	var id: int = title.backgroundPalette.id
	var found = catalogs.resolve("SHPL",id)
	var key = "SHPL:%d" % id
	checks.append({"name":"freed title background clears catalog and cache entries","passed":found.entry.handle==0 and not found.catalog.loader.sources.has(key)})
	var handle = palettes.load_palette(id,title.backgroundPalette.banks)
	m.discard(handle)
	checks.append({"name":"discard retains source backlink for reload","passed":found.entry.handle==handle and found.catalog.loader.sources[key]==handle and m.handle(handle).segment==0})
	var reloaded = catalogs.load_source(found.catalog.handle,"SHPL",id)
	checks.append({"name":"reload preserves handle and restores original bytes","passed":reloaded==handle and m.resource_payloads[handle][4]==found.entry.payload[4]})
	m.free_handle(handle)
	var replacement = m.allocate_handle(8)
	checks.append({"name":"reused handle has no stale source backlink","passed":replacement==handle and found.entry.handle==0 and not found.catalog.loader.sources.has(key) and not m.resource_owners.has(handle)})
	var file = FileAccess.open(output+"/godot.json",FileAccess.WRITE)
	file.store_string(JSON.stringify({"stages":stages,"checks":checks,"movement_timing":movement_timing}))
	file.close()
	quit()
