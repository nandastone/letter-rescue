extends RefCounted
## Overlay 3 ownership through the initial Money/robot dashboard animation.
## Gameplay supplies board state; sound completion and animation events are
## explicit so the live caller can preserve their lifetimes across frames.
const Assets = preload("res://scripts/resource_startup_assets.gd")
const Title = preload("res://scripts/resource_title.gd")
const Palettes = preload("res://scripts/resource_palette.gd")
const Transfer = preload("res://scripts/resource_room_transfer.gd")
const SavedSurface = preload("res://scripts/resource_saved_surface.gd")
const AnimationMemory = preload("res://scripts/resource_animation.gd")

static func draw(state: Dictionary, palette: int, relative: int) -> void:
	state.memory.free_handle(Title.load_shape(state,palette,relative))

static func prepare(state: Dictionary, config: Dictionary, observer: Callable = Callable()) -> void:
	assert(state.entrancePhase == "room-released")
	Assets.select_cursor(state,1)
	state.boardPalettes = {}
	var loader = Palettes.new(state.catalogs)
	Title.emit(observer,"board-before",state)
	for palette in config.palettes:
		state.boardPalettes[palette.id] = loader.load_palette(palette.id,palette.banks)
		Title.emit(observer,"board-palette-%d" % palette.id,state)
	state.entrancePhase = "board-prepared"

static func begin_drawing(state: Dictionary, config: Dictionary, observer: Callable = Callable()) -> void:
	assert(state.entrancePhase in ["board-prepared","board-restarting"])
	state.boardSurface = Transfer.temporary(state,config.screenBounds)
	draw(state,state.boardPalettes[4000],1)
	Title.emit(observer,"board-background-before",state)
	state.boardBackgroundPalette = Palettes.new(state.catalogs).load_palette(config.backgroundPalette.id,config.backgroundPalette.banks)
	state.entrancePhase = "board-background-prepared"
	Title.emit(observer,"board-background-after",state)

static func finish_drawing(state: Dictionary, game) -> void:
	assert(state.entrancePhase == "board-background-prepared")
	assert(game.mode == 0 and game.opponent == 2 and game.player == 0, "Initial resource sequence covers Money/robot")
	var m = state.memory
	var rectangles: Array = game.tables.game_rects.slice(0,6)+game.tables.money_rects
	draw(state,state.boardBackgroundPalette,1)
	m.discardable(state.boardBackgroundPalette)
	state.boardBackgroundPalette = 0
	draw(state,state.boardPalettes[4000],3)
	draw(state,state.boardPalettes[4000],5)
	var strings = state.catalogs.resolve("STRL",4000)
	var text = state.catalogs.load_source(strings.catalog.handle,"STRL",4000)
	m.address(text)
	m.discardable(text)
	var balance: int = game.balances[0]
	var digits = [int(balance/100),int(balance/10)%10,balance%10]
	for i in 3:
		var a: Array = rectangles[7+i]
		var b: Array = rectangles[11+i]
		var surface = Transfer.temporary(state,[mini(a[0],b[0]),mini(a[1],b[1]),maxi(a[2],b[2]),maxi(a[3],b[3])])
		for j in digits[i]: draw(state,state.boardPalettes[4400],5+i)
		Transfer.release_surface(state,surface)
	draw(state,state.interfacePalettes[6],2)
	draw(state,state.boardPalettes[4400],1)
	for type in game.types: draw(state,state.boardPalettes[4400],type)
	draw(state,state.boardPalettes[4000],6)
	var hint = Transfer.temporary(state,rectangles[2])
	draw(state,state.boardPalettes[4400],25)
	Transfer.release_surface(state,hint)
	Transfer.release_surface(state,state.boardSurface)
	state.boardSurface = null
	state.entrancePhase = "board-drawn"

static func prepare_options(state: Dictionary, config: Dictionary, game, observer: Callable = Callable()) -> void:
	finish_drawing(state,game)
	Assets.select_cursor(state,0)
	state.boardOptionsSurface = Transfer.temporary(state,config.screenBounds)
	Title.emit(observer,"board-options-before",state)
	state.boardOptionsPalette = Palettes.new(state.catalogs).load_palette(config.optionsPalette.id,config.optionsPalette.banks)
	state.entrancePhase = "board-options-prepared"
	Title.emit(observer,"board-options-after",state)

static func centered(state: Dictionary, palette: int, relative: int, bounds: Array) -> void:
	var surface = Transfer.temporary(state,bounds)
	draw(state,palette,relative)
	Transfer.release_surface(state,surface)

static func finish_options(state: Dictionary, game, observer: Callable = Callable()) -> void:
	assert(state.entrancePhase == "board-options-prepared")
	assert(game.mode == 0 and game.opponent == 2)
	var rectangles: Array = game.tables.options_rects
	var m = state.memory
	var ui: int = state.interfacePalettes[6]
	var board: int = state.boardPalettes[4400]
	draw(state,state.boardOptionsPalette,1)
	draw(state,state.boardPalettes[20200],1)
	draw(state,ui,3)
	centered(state,board,16,rectangles[18])
	draw(state,ui,3)
	centered(state,state.boardPalettes[24200],2,rectangles[24])
	draw(state,ui,3)
	centered(state,board,[31,30,28][game.levels[0]],rectangles[19])
	var strings = state.catalogs.resolve("STRL",4000)
	for i in 3:
		var surface = Transfer.temporary(state,rectangles[11+i])
		var text = state.catalogs.load_source(strings.catalog.handle,"STRL",4000)
		m.address(text)
		m.discardable(text)
		Transfer.release_surface(state,surface)
	Title.emit(observer,"board-options-painted",state)
	Transfer.release_surface(state,state.boardOptionsSurface)
	state.boardOptionsSurface = null
	state.entrancePhase = "board-options-ready"

static func play_sound(state: Dictionary, id: int) -> void:
	if id in [1020,1021]: Assets.select_cursor(state,1)
	var sound = Assets.load_sound(state,id)
	if state.get("boardSound",0): state.memory.unlock(state.boardSound)
	state.boardSound = sound
	if sound: state.memory.lock(sound)
	if id in [1020,1021]: Assets.select_cursor(state,0)

static func finish_sound(state: Dictionary) -> void:
	if state.get("boardSound",0): state.memory.unlock(state.boardSound)
	state.boardSound = 0

static func press_play(state: Dictionary, config: Dictionary, observer: Callable = Callable()) -> void:
	assert(state.entrancePhase == "board-options-ready")
	Title.emit(observer,"board-play-before",state)
	play_sound(state,config.clickSound)
	state.entrancePhase = "board-play-pressed"

static func dismiss_options(state: Dictionary, observer: Callable = Callable()) -> void:
	assert(state.entrancePhase == "board-play-pressed")
	# Button inversion and saving preferences do not own resource buffers.
	state.memory.discardable(state.boardOptionsPalette)
	state.boardOptionsPalette = 0
	state.entrancePhase = "board-restarting"
	Title.emit(observer,"board-restart-before",state)

static func draw_pawn(state: Dictionary, game) -> void:
	assert(state.entrancePhase == "board-drawn")
	state.boardPawnSaved = SavedSurface.new(state.memory,pawn_bounds(game,game.nodes[game.player]))
	paint_pawn(state,game)
	state.entrancePhase = "board-pawn-drawn"

static func pawn_bounds(game, node: int) -> Array:
	var bounds: Array = game.tables.node_rects[node]
	return [bounds[0]-1,bounds[1]-3,bounds[2]+1,bounds[3]+3]

static func paint_pawn(state: Dictionary, game) -> void:
	var relative = 42
	if game.directions[game.player] == 1: relative = 43
	if game.directions[game.player] == 3: relative = 44
	if game.player: relative += 3*game.opponent
	draw(state,state.boardPalettes[4400],relative)

static func prepare_dashboard(state: Dictionary, config: Dictionary, game, observer: Callable = Callable()) -> void:
	assert(state.entrancePhase == "board-pawn-drawn")
	Title.emit(observer,"board-dashboard-before",state)
	var descriptor: Dictionary = config.dashboards[game.role()]
	var palette = Palettes.new(state.catalogs).load_palette(descriptor.id,descriptor.banks)
	state.boardDashboardPalette = palette
	Assets.select_cursor(state,1)
	var found = state.catalogs.resolve("SCR",descriptor.id)
	state.boardDashboardScript = state.direct.load_copy(found.entry.payload,found.catalog.handle,found.entry.handle)
	var list = state.catalogs.resolve("PSL",descriptor.id)
	var list_handle = state.catalogs.load_source(list.catalog.handle,"PSL",descriptor.id)
	var sounds: PackedByteArray = state.memory.resource_payloads[list_handle]
	state.memory.address(list_handle)
	for i in sounds.decode_u16(0):
		state.memory.address(list_handle)
		Assets.load_sound(state,sounds.decode_u16(2+2*i))
	state.memory.free_handle(list_handle)
	var data: PackedByteArray = state.memory.resource_payloads[palette]
	state.memory.address(palette)
	state.boardDashboard = AnimationMemory.prepare(state.memory,descriptor.script,data.decode_u16(2),palette,
		func(relative): return Title.load_shape(state,palette,relative))
	Assets.select_cursor(state,0)
	state.entrancePhase = "board-dashboard-playing"

static func finish_dashboard(state: Dictionary, config: Dictionary, observer: Callable = Callable()) -> void:
	assert(state.entrancePhase == "board-dashboard-playing")
	var queried = Assets.load_sound(state,config.querySound)
	if queried: state.memory.address(queried)
	finish_sound(state)
	state.boardDashboard.dispose()
	state.memory.discardable(state.boardDashboardPalette)
	state.boardDashboardPalette = 0
	state.direct.release(state.boardDashboardScript)
	state.boardDashboardScript = 0
	state.entrancePhase = "board-playing"
	Title.emit(observer,"board-dashboard-after",state)

static func draw_roll_hint(state: Dictionary, game) -> void:
	assert(state.entrancePhase == "board-playing")
	centered(state,state.boardPalettes[4400],25,game.tables.game_rects[2])

static func draw_roll_prompt(state: Dictionary, game, value: int) -> void:
	assert(state.entrancePhase == "board-playing")
	if value<0: draw_roll_hint(state,game)
	elif value>0: centered(state,state.boardPalettes[4000],7+value,game.tables.game_rects[2])

static func begin_pawn_blink(state: Dictionary) -> void:
	assert(state.entrancePhase == "board-playing" and not state.has("boardBlinkSaved"))
	state.boardBlinkSaved = SavedSurface.new(state.memory,state.boardPawnSaved.bounds)

static func finish_pawn_blink(state: Dictionary) -> void:
	state.boardBlinkSaved.dispose()
	state.erase("boardBlinkSaved")

static func connect_roll_events(state: Dictionary, game) -> void:
	var owner = weakref(game)
	game.roll_prompt_drawn.connect(func(value): draw_roll_prompt(state,owner.get_ref(),value))
	game.pawn_blink_started.connect(func(): begin_pawn_blink(state))
	game.pawn_blink_finished.connect(func(): finish_pawn_blink(state))

static func begin_node_flash(state: Dictionary, game, node: int) -> void:
	var bounds: Array = game.tables.node_rects[node]
	state.boardNodeSaved = SavedSurface.new(state.memory,bounds)
	var surface = Transfer.temporary(state,bounds)
	# These centered draws use background -1, so they draw into the existing
	# temporary surface without allocating another one (main 6C2E).
	draw(state,state.boardPalettes[4400],27)
	draw(state,state.boardPalettes[4400],game.types[node])
	Transfer.release_surface(state,surface)

static func finish_node_flash(state: Dictionary) -> void:
	state.boardNodeSaved.dispose()
	state.erase("boardNodeSaved")

static func begin_travel(state: Dictionary, game, target: int) -> void:
	var from = pawn_bounds(game,game.nodes[game.player])
	var to = pawn_bounds(game,target)
	var bounds = [mini(from[0],to[0]),mini(from[1],to[1]),maxi(from[2],to[2]),maxi(from[3],to[3])]
	state.boardTravelSurface = Transfer.temporary(state,bounds)
	state.boardPawnSaved.dispose()
	state.boardPawnSaved = SavedSurface.new(state.memory,to)
	state.boardTravelSaved = SavedSurface.new(state.memory,bounds)

static func finish_travel(state: Dictionary) -> void:
	state.boardTravelSaved.dispose()
	Transfer.release_surface(state,state.boardTravelSurface)
	state.erase("boardTravelSaved")
	state.erase("boardTravelSurface")

static func connect_move_events(state: Dictionary, game, observer: Callable = Callable()) -> void:
	var owner = weakref(game)
	game.node_flash_started.connect(func(node): begin_node_flash(state,owner.get_ref(),node))
	game.node_flash_finished.connect(func(): finish_node_flash(state))
	game.pawn_travel_started.connect(func(target):
		Title.emit(observer,"board-movement-before",state)
		begin_travel(state,owner.get_ref(),target))
	game.pawn_travel_step.connect(func(): paint_pawn(state,owner.get_ref()))
	game.pawn_travel_finished.connect(func():
		finish_travel(state)
		Title.emit(observer,"board-movement-after",state))
