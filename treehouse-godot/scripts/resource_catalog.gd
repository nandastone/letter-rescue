extends RefCounted
## Archive directories and semantic catalog lookup for source resources.
const Cache = preload("res://scripts/resource_cache.gd")
const Shapes = preload("res://scripts/resource_shape.gd")
var memory
var files: Array = []
var lookup: int = 0
var catalogs: Dictionary = {}

func _init(model) -> void:
	memory = model

static func directory(bytes: PackedByteArray) -> Dictionary:
	assert(bytes.size() >= 8, "Truncated archive")
	var offset = bytes.decode_u32(0)
	var size = bytes.decode_u16(4)
	assert(offset >= 6 and size >= 2 and offset+size == bytes.size(), "Invalid archive directory")
	var count = bytes.decode_u16(offset)
	assert(2+6*count <= size)
	var records: Array = []
	var types: Array = []
	for i in count:
		var at = offset+2+6*i
		var code = bytes.decode_u32(at)
		var relative = bytes.decode_u16(at+4)
		var table = offset+relative
		assert(relative >= 2+6*count and relative+2 <= size)
		var n = bytes.decode_u16(table)
		var ids: Array = []
		var tag = ""
		for shift in [24,16,8,0]:
			var character = (code >> shift) & 255
			if character: tag += String.chr(character)
		assert(relative+2+11*n <= size)
		for j in n:
			var row = table+2+11*j
			var id = bytes.decode_u16(row)
			var beginning = bytes.decode_u32(row+2)
			var length = bytes.decode_u16(row+6)
			var flags = bytes[row+8]
			assert(beginning >= 6 and beginning+1+length <= offset and bytes.decode_u16(row+9) == 0)
			var payload = bytes.slice(beginning+1,beginning+1+length)
			var sum = bytes[beginning]
			for value in payload: sum += value
			assert((sum & 255) == 255, "Invalid resource checksum")
			records.append({"tag":tag,"id":id,"offset":beginning,"length":length,"flags":flags,"handle":0,"row":row-offset,"payload":payload})
			ids.append(id)
		types.append({"tag":tag,"relative":relative,"ids":ids})
	return {"bytes":bytes.slice(offset),"size":size,"records":records,"types":types}

func open(archive: PackedByteArray, filename: String, volume: String, file_handle: int) -> int:
	assert(filename.length() < 64 and volume.length() < 12 and file_handle >= 0 and file_handle <= 65535)
	var data = directory(archive)
	var id = memory.allocate_handle(data.size+80)
	memory.lock(id)
	var file = {"handle":id,"fileHandle":file_handle,"volume":volume,"filename":filename}
	var cache = Cache.new(memory,id)
	var catalog = data
	catalog.merge(file)
	catalog.previous = files[0].handle if not files.is_empty() else 0
	catalog.loader = cache
	files.push_front(file)
	lookup = id
	catalogs[id] = catalog
	for entry in catalog.records:
		if entry.flags & 0x20: load_source(id,entry.tag,entry.id)
	memory.unlock(id)
	return id

func load_source(id: int, tag: String, resource_id: int) -> int:
	assert(catalogs.has(id))
	var catalog: Dictionary = catalogs[id]
	for entry in catalog.records:
		if entry.tag != tag or entry.id != resource_id: continue
		entry.handle = catalog.loader.source("%s:%d" % [tag,resource_id],entry.payload,entry.flags)
		if memory.resource_owners.has(entry.handle): memory.resource_owners[entry.handle].entry = entry
		return entry.handle
	assert(false, "Missing catalog resource %s:%d" % [tag,resource_id])
	return 0

func resolve(tag: String, id: int) -> Dictionary:
	var current = lookup
	var seen: Array = []
	while current:
		assert(not current in seen and catalogs.has(current), "Invalid catalog lookup chain")
		seen.append(current)
		var catalog: Dictionary = catalogs[current]
		for entry in catalog.records:
			if entry.tag == tag and entry.id == id: return {"catalog":catalog,"entry":entry}
		current = catalog.previous
	return {}

func load_shape(id: int, resource_id: int, palette_handle: int) -> int:
	assert(catalogs.has(id))
	var catalog: Dictionary = catalogs[id]
	for entry in catalog.records:
		if entry.tag != "SHAP" or entry.id != resource_id: continue
		if not catalog.has("shape_loader"):
			catalog.shape_loader = Shapes.new(memory,id)
			catalog.shape_loader.sources = catalog.loader.sources
		var key = "SHAP:%d" % resource_id
		var converted = catalog.shape_loader.load_shape(key,entry.payload,palette_handle,entry.flags)
		entry.handle = catalog.loader.sources[key]
		if memory.resource_owners.has(entry.handle): memory.resource_owners[entry.handle].entry = entry
		return converted
	assert(false, "Missing catalog shape: %d" % resource_id)
	return 0

func snapshot(id: int) -> Dictionary:
	var catalog: Dictionary = catalogs[id]
	var h = memory.handle(id)
	var records: Array = []
	for entry in catalog.records:
		var copy: Dictionary = entry.duplicate()
		copy.erase("row")
		copy.erase("payload")
		records.append(copy)
	return {"handle":id,"state":h.state,"segment":h.segment,"archive":catalog.filename.replace("\\","/").get_file().get_basename().to_lower(),"records":records,"types":catalog.types.duplicate(true)}
