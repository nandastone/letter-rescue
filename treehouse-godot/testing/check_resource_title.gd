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
	func _init(tables: Dictionary, seed: int) -> void:
		store = {"data":{"boardgame":tables}}
		random.reset(seed)

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
	file.store_string(JSON.stringify({"stages":stages,"checks":checks}))
	file.close()
	quit()
