extends RefCounted
## Room construction resource ownership. Time, cloud and current objects come
## from the gameplay caller; no recorded allocation sequence is used.
const Assets = preload("res://scripts/resource_startup_assets.gd")
const Title = preload("res://scripts/resource_title.gd")
const Palettes = preload("res://scripts/resource_palette.gd")
const Saved = preload("res://scripts/resource_saved_surface.gd")

static func open_child(state: Dictionary, archive: Dictionary) -> void:
	assert(state.entrancePhase == "selected")
	if state.entranceMusic:
		state.memory.unlock(state.entranceMusic)
		state.entranceMusic = 0
	var file_handle = 0
	for file in state.catalogs.files: file_handle = maxi(file_handle,file.fileHandle)
	state.childCatalog = state.catalogs.open(Marshalls.base64_to_raw(archive.archive),archive.filename,state.catalogs.files[0].volume,file_handle+1)
	state.entrancePhase = "child-open"

static func palette(state: Dictionary, id: int) -> int:
	return state.roomPalettes[id] if state.roomPalettes.has(id) else state.interfacePalettes[id]

static func draw(state: Dictionary, id: int, relative: int) -> void:
	state.memory.free_handle(Title.load_shape(state,palette(state,id),relative))

static func draw_objects(state: Dictionary, objects: Array) -> void:
	for item in objects:
		item.saved = Saved.new(state.memory,item.bounds)
		draw(state,item.palette,item.relative)

static func prepare(state: Dictionary, config: Dictionary, observer: Callable = Callable()) -> void:
	assert(state.entrancePhase == "child-open")
	var m = state.memory
	var c = state.catalogs
	var loader = Palettes.new(c)
	Assets.select_cursor(state,1)
	m.heap.pack(0xffffff)
	var colors = c.resolve("",10)
	assert(not colors.is_empty())
	var color_source = c.load_source(colors.catalog.handle,"",10)
	m.address(color_source)
	m.discardable(color_source)
	for id in [870,900,930,170,6]: m.address(state.interfacePalettes[id])
	var bounds: Array = config.screenBounds
	state.roomSurface = {"rows":m.near.allocate(2*(bounds[2]-bounds[0])),"pixels":m.allocate_raw((bounds[2]-bounds[0])*(bounds[3]-bounds[1]))}
	state.roomPalettes = {}
	for group in config.palettes:
		state.roomPalettes[group.id] = loader.load_palette(group.id,group.banks)
		Title.emit(observer,"room-palette-%d" % group.id,state)
	draw(state,4,1)
	m.discardable(state.roomPalettes[4])
	state.roomPalettes.erase(4)
	for pair in [[900,26],[900,19],[1200,1],[1200,28]]: draw(state,pair[0],pair[1])
	var months = c.resolve("STRL",500)
	var month_source = c.load_source(months.catalog.handle,"STRL",500)
	m.address(month_source)
	m.discardable(month_source)
	state.theaterSaved = Saved.new(m,config.theaterBounds)
	for pair in [[1100,9],[1250,6],[1250,1]]: draw(state,pair[0],pair[1])
	# The calendar keeps the converted cloud alive through its overlay draw.
	var cloud = Title.load_shape(state,palette(state,170),config.cloud+1)
	m.address(cloud)
	draw(state,1200,1)
	m.free_handle(cloud)
	var hour: int = config.hour % 12
	if not hour: hour = 12
	for relative in [27 if hour>9 else 26,hour%10+15,25,int(config.minute/10)+15,config.minute%10+15]: draw(state,1200,relative)
	state.roomObjects = config.objects.duplicate(true)
	Title.emit(observer,"room-objects-before",state)
	draw_objects(state,state.roomObjects)
	Title.emit(observer,"room-objects-after",state)
	var foreground: Array = state.roomObjects.filter(func(item): return item.type==6 or item.bounds[2]>=config.characterBounds[2])
	for i in range(foreground.size()-1,-1,-1): foreground[i].saved.dispose()
	state.characterSaved = Saved.new(m,config.characterBounds)
	draw(state,20500,1)
	draw_objects(state,foreground)
	for i in range(state.roomObjects.size()-1,-1,-1): state.roomObjects[i].saved.dispose()
	draw_objects(state,state.roomObjects)
	m.free_raw(state.roomSurface.pixels)
	m.near.release(state.roomSurface.rows)
	state.roomSurface = null
	Assets.select_cursor(state,0)
	state.entrancePhase = "room"
	Title.emit(observer,"room-complete",state)
