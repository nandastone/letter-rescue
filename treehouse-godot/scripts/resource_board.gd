extends RefCounted
## Overlay 3 ownership through initial Money/robot options. Gameplay and
## drawing callers supply current board state; subsequent turns remain separate.
const Assets = preload("res://scripts/resource_startup_assets.gd")
const Title = preload("res://scripts/resource_title.gd")
const Palettes = preload("res://scripts/resource_palette.gd")
const Transfer = preload("res://scripts/resource_room_transfer.gd")

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
	assert(state.entrancePhase == "board-prepared")
	state.boardSurface = Transfer.temporary(state,config.screenBounds)
	draw(state,state.boardPalettes[4000],1)
	Title.emit(observer,"board-background-before",state)
	state.boardBackgroundPalette = Palettes.new(state.catalogs).load_palette(config.backgroundPalette.id,config.backgroundPalette.banks)
	state.entrancePhase = "board-background-prepared"
	Title.emit(observer,"board-background-after",state)

static func prepare_options(state: Dictionary, config: Dictionary, game, observer: Callable = Callable()) -> void:
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
