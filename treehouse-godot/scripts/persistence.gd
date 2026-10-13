extends RefCounted
## Shared saved state. Live matches, clocks, character choice and prizes reset.
const StatusFile = preload("res://scripts/status_file.gd")
var host
var file
var storage_enabled: bool
var save_path: String = "user://STATUS.DAT"
var save_error: Error = OK
var listening_pages: Array = [20,20]
var last_song: int = 20
var loading: bool = false
var last_written: PackedByteArray
var object_slots: Array = []
var animal_slots: Array = [[],[]]
var prop_slots: Array = [[],[],[],[],[],[]]
var initialization: String = "loaded"

static func has_legacy_profile(path: String) -> bool:
	# SONGS.DAT is also an original DOS file, independent of STATUS.DAT.
	# Only the earlier Godot JSON saves identify a profile needing migration.
	for name in ["preferences.json","nature.json","theater.json","board.json"]:
		if FileAccess.file_exists(path.get_base_dir().path_join(name)):
			return true
	return false

func _init(game, persistent: bool = true, path: String = "user://STATUS.DAT") -> void:
	host = game
	storage_enabled = persistent
	save_path = path
	var exists = persistent and FileAccess.file_exists(save_path)
	var raw = PackedByteArray()
	var read_error: Error = OK
	if exists:
		var source = FileAccess.open(save_path,FileAccess.READ)
		read_error = FileAccess.get_open_error()
		if source!=null:
			raw = source.get_buffer(source.get_length())
			read_error = source.get_error()
			source.close()
		if read_error!=OK:
			storage_enabled = false
			save_error = read_error
	if raw.size()>=StatusFile.SIZE:
		file = StatusFile.new(raw)
		apply()
		last_written = raw.duplicate()
	else:
		var legacy = has_legacy_profile(save_path)
		if persistent and not legacy:
			fresh()
		else:
			# Preserve profiles authored before shared STATUS support. Isolated
			# historical component fixtures also retain their established baseline.
			initialization = "migration" if persistent else "isolated"
			file = StatusFile.new(Marshalls.base64_to_raw(host.store.data.status))
			if persistent:
				load_maze()
			file.initialize = true
			capture()
			file.initialize = false
		if read_error!=OK:
			file.warnings.append("Local STATUS.DAT could not be read; automatic saves disabled")
		elif exists:
			var backup = save_path+".rejected"
			var index = 1
			while FileAccess.file_exists(backup):
				backup = save_path+".rejected-%d"%index
				index += 1
			var target = FileAccess.open(backup,FileAccess.WRITE)
			save_error = FileAccess.get_open_error()
			if target!=null:
				target.store_buffer(raw)
				save_error = target.get_error()
				target.close()
			# Never replace an unreadable save if its original bytes cannot be kept.
			storage_enabled = save_error==OK
			file.warnings.append("Truncated local STATUS.DAT; source preserved at "+backup if storage_enabled else "Truncated local STATUS.DAT; automatic saves disabled")

func fresh() -> void:
	# Main 7ECF: clear the saved region, initialize sentinels/options,
	# create the two permanent room objects, then overlay 1:8A7B chooses songs.
	# Include the pillow subsequently required by main 038A normalization.
	initialization = "fresh"
	var raw = PackedByteArray()
	raw.resize(StatusFile.SIZE)
	raw.fill(0)
	file = StatusFile.new(raw)
	for at in [0x62,0x64,0x3a8,0x3b6,0x3bc]: file.put(at,1)
	file.put(0x72,-1)
	for i in 4:
		file.put(0x3c2+2*i,-1)
		file.put(0x8a2+2*i,i)
	var chosen: Array = []
	while chosen.size()<6:
		var id = host.random.pick(23)
		if id in chosen: continue
		file.put(0x8da+2*chosen.size(),id)
		file.put(0x8aa+2*id,1)
		chosen.append(id)
	file.put(0x8ea,3)
	for i in 3:
		var type = [9,10,8][i]
		var at = 0x8ec+20*i
		file.put(at,type)
		file.put(at+2,1)
		file.put(at+4,1)
		var bounds = host.store.data.room.objects[type].inside
		for j in 4: file.put(at+6+2*j,int(bounds[j]))
	apply()

func apply() -> void:
	loading = true
	var m = host.music
	var e = m.editor
	e.enabled = bool(file.field(0x5a))
	m.mode = file.field(0x5c)
	e.mode = m.mode
	m.repeating = bool(file.field(0x5e))
	e.index = [file.valid(file.data[0x57],0,42,0,"Short song page"),file.valid(file.data[0x59],0,42,0,"Long song page")]
	listening_pages = [file.valid(file.data[0x56],0,24,0,"Listening page"),file.valid(file.data[0x58],0,24,0,"Listening page")]
	m.song_id = listening_pages[m.mode]
	last_song = m.song_id
	e.initialize_usage(Array(file.data.slice(0,86)))
	m.instrument = int(m.song[3])
	host.preferences.settings = {"advanced":bool(file.field(0x60)),"sound":bool(file.field(0x62,0,1,1)),"printing":bool(file.field(0x64,0,1,1)),"printer":file.field(0x66),"speed":bool(file.field(0x6a))}
	host.preferences.apply_settings()
	host.room.cloud = file.field(0x6c,0,6,5)
	load_objects()
	load_nature()
	load_board()
	load_theater()
	load_maze()
	capture()
	loading = false

func load_objects() -> void:
	var resident = host.resident
	resident.tick = host.tick
	resident.objects.clear()
	object_slots.clear()
	var seen = {}
	for i in file.field(0x8ea,0,21,0):
		var at = 0x8ec+20*i
		var type = file.word(at)
		var state = file.word(at+2)
		var inside = file.word(at+4)
		var r = []
		for j in 4:
			r.append(file.signed(at+6+2*j))
		if type>20 or inside>1 or seen.has(type) or r[0]>=r[2] or r[1]>=r[3]:
			file.warnings.append("Room object %d"%(i+1))
			continue
		if type==15 or (type==7 and state==5):
			continue
		seen[type] = true
		var normalized = clampi(state%10,1,3) if type==6 else clampi(state,1,4) if type in [7,14] else 1
		var object = {"type":type,"state":normalized,"inside":bool(inside),"rect":r,"due":host.tick,"hidden":false,"front":false,"nest_mirror":false}
		resident.objects.append(object)
		object_slots.append(i)
		if type in [11,16]:
			object.due = host.tick+(6+host.random.pick(10) if type==11 else 120+host.random.pick(60))*60
	if not seen.has(8):
		resident.create(8)
		object_slots.append(-1)
	host.balloon.hidden = not seen.has(6)
	var balloon = resident.find(6)
	if balloon!=null:
		host.balloon.x = balloon.rect[1]
		host.balloon.y = balloon.rect[0]
		host.balloon.state = balloon.state
		host.balloon.due = host.tick+48

func load_nature() -> void:
	var n = host.nature
	n.time = file.field(0x6e)
	n.attribute = file.field(0x70,0,6)
	for i in 7:
		n.values[i] = file.field(0x74+2*i,0,n.strings(5200+i).size()-1)
	n.category = file.valid(file.signed(0x72),-1,8+n.time,-1,"Animal class")
	if n.category not in n.available_classes():
		n.category = -1
	n.objects = [[],[]]
	animal_slots = [[],[]]
	for time in 2:
		for i in file.field(0x82+2*time,0,40):
			var slot = 2*i+time
			var id = file.word(0x86+2*slot)
			if id>=n.tables.animals.size() or n.tables.animals[id].active_time!=time:
				file.warnings.append("Placed animal")
				continue
			var shape = host.store.shape("modules",n.tables.animals[id].large)
			var y = file.signed(0x126+8*slot)
			var x = file.signed(0x128+8*slot)
			if x<131 or y<5 or x+shape[0]>315 or y+shape[1]>195:
				file.warnings.append("Animal position")
				continue
			n.objects[time].append({"id":id,"x":x,"y":y,"blink":0,"due":host.tick+120})
			animal_slots[time].append(i)
	n.quiz.opponent = file.field(0x3b6,1,2,1)
	for i in 3:
		n.quiz.help[i] = bool(file.field(0x3b8+2*i))

func load_board() -> void:
	var g = host.boardgame
	g.mode = file.field(0x3a6)
	g.opponent = file.field(0x3a8,1,2,1)
	for i in 6:
		g.saved_levels[i] = file.field(0x3aa+2*i,0,2)
	g.levels = [g.saved_levels[3*g.mode],g.saved_levels[3*g.mode+g.opponent]]

func load_theater() -> void:
	var t = host.theater
	t.mix_up = bool(file.field(0x3be))
	t.props_enabled = bool(file.field(0x3c0))
	for i in 4:
		t.selection[i] = file.valid(file.signed(0x3c2+2*i),-1,[7,7,5,3][i],-1,"Sentence choice")
		t.order[i] = file.field(0x8a2+2*i,0,3,i)
	if t.order.duplicate().reduce(func(a,v):
		if v not in a: a.append(v)
		return a,[]).size()!=4:
		file.warnings.append("Sentence order")
		t.order = [0,1,2,3]
	t.previous_validation = file.field(0x8e8,0,6)
	for i in 7:
		t.actor_drag[i] = [file.signed(0x886+4*i),file.signed(0x888+4*i)]
	t.props = [[],[],[],[],[],[]]
	prop_slots = [[],[],[],[],[],[]]
	for place in 6:
		for i in file.field(0x3ca+2*place,0,20):
			var slot = 20*place+i
			var code = file.word(0x796+2*slot)
			var palette = 3175 if t.tables.prop_group[place] else 3145
			var y = file.signed(0x3d6+8*slot)
			var x = file.signed(0x3d8+8*slot)
			if (code>>8)!=t.tables.prop_group[place] or (code&255)<t.tables.prop_first[place] or (code&255)>=t.tables.prop_first[place]+t.tables.prop_count[place] or x<0 or y<0 or x>=320 or y>=200:
				file.warnings.append("Theater decoration")
				continue
			t.props[place].append({"id":palette+(code&255),"palette":palette,"x":x,"y":y})
			prop_slots[place].append(i)

func load_maze() -> void:
	var m = host.maze
	m.history.clear()
	m.saved_songs.clear()
	for i in 24:
		if file.word(0x8aa+2*i):
			m.history.append(i)
	for i in 6:
		var song = file.field(0x8da+2*i,0,23,i)
		if song in m.saved_songs:
			file.warnings.append("Duplicate maze song")
			for candidate in 24:
				if candidate not in m.saved_songs:
					song = candidate
					break
		m.saved_songs.append(song)
	# A valid chooser means reset never rejection-samples an all-seen history.
	# The regular replacement path handles the native all-seen rollover.
	m.songs.clear()

func capture() -> void:
	var m = host.music
	var e = m.editor
	if m.song_id!=last_song:
		listening_pages = [m.song_id,m.song_id]
	last_song = m.song_id
	file.array(0x56,[listening_pages[0],e.index[0],listening_pages[1],e.index[1]],true)
	var p = host.preferences.settings
	for field in [[0x5a,int(e.enabled)],[0x5c,m.mode],[0x5e,int(m.repeating)],[0x60,int(p.advanced)],[0x62,int(p.sound)],[0x64,int(p.printing)],[0x66,p.printer],[0x6a,int(p.speed)],[0x6c,host.room.cloud]]:
		file.scalar(field[0],field[1])
	for mode in 2:
		for i in 43:
			var at = mode*43+i
			var used = e.used(mode,i)
			if file.changed("used%d"%at,used):
				file.data[at] = int(used)
	var objects = []
	for object in host.resident.objects:
		objects.append([object.type,object.state,int(object.inside)]+host.resident.bounds(object))
	file.scalar(0x8ea,objects.size())
	var rewrite = file.changed("object-order",objects.map(func(o): return o[0]))
	for i in objects.size():
		if i<object_slots.size() and object_slots[i]<0 and file.changed("new-object%d"%i,objects[i]):
			rewrite = true
	if rewrite or object_slots.size()!=objects.size():
		object_slots = range(objects.size())
		file.put(0x8ea,objects.size())
	for i in objects.size():
		if object_slots[i]<0:
			continue
		for j in 7:
			var at = 0x8ec+20*object_slots[i]+2*j
			file.scalar(at,objects[i][j])
			if rewrite:
				file.put(at,objects[i][j])
	capture_nature()
	capture_board()
	capture_theater()
	var maze = host.maze
	var history = []
	for i in 24:
		history.append(int(i in maze.history))
	file.array(0x8aa,history)
	var songs = maze.songs if not maze.songs.is_empty() else maze.saved_songs
	if not songs.is_empty():
		file.array(0x8da,songs)

func listening_page_changed(id: int) -> void:
	listening_pages = [id,id]
	last_song = id

func switch_listening_mode(mode: int) -> void:
	host.music.song_id = listening_pages[mode]
	last_song = host.music.song_id

func capture_nature() -> void:
	var n = host.nature
	file.scalar(0x6e,n.time)
	file.scalar(0x70,n.attribute)
	file.scalar(0x72,n.category)
	file.array(0x74,n.values)
	file.scalar(0x3b6,n.quiz.opponent)
	file.array(0x3b8,n.quiz.help.map(func(v): return int(v)))
	for time in 2:
		var list = n.objects[time]
		file.scalar(0x82+2*time,list.size())
		var rewrite = file.changed("animal-order%d"%time,list.map(func(o): return o.id))
		if rewrite or animal_slots[time].size()!=list.size():
			animal_slots[time] = range(list.size())
			file.put(0x82+2*time,list.size())
		for i in list.size():
			var o = list[i]
			var slot = 2*animal_slots[time][i]+time
			var shape = host.store.shape("modules",n.tables.animals[o.id].large)
			file.scalar(0x86+2*slot,o.id)
			var rect = [o.y,o.x,o.y+int(shape[1]),o.x+int(shape[0])]
			file.array(0x126+8*slot,rect)
			if rewrite:
				file.put(0x86+2*slot,o.id)
				for j in 4: file.put(0x126+8*slot+2*j,rect[j])

func capture_board() -> void:
	var g = host.boardgame
	file.scalar(0x3a6,g.mode)
	file.scalar(0x3a8,g.opponent)
	file.array(0x3aa,g.saved_state().levels)

func capture_theater() -> void:
	var t = host.theater
	file.scalar(0x3be,int(t.mix_up))
	file.scalar(0x3c0,int(t.props_enabled))
	file.array(0x3c2,t.selection)
	file.array(0x8a2,t.order)
	file.scalar(0x8e8,t.previous_validation)
	for i in 7:
		file.array(0x886+4*i,t.actor_drag[i])
	for place in 6:
		var list = t.props[place]
		file.scalar(0x3ca+2*place,list.size())
		var rewrite = file.changed("prop-order%d"%place,list.map(func(o): return o.id))
		if rewrite or prop_slots[place].size()!=list.size():
			prop_slots[place] = range(list.size())
			file.put(0x3ca+2*place,list.size())
		for i in list.size():
			var o = list[i]
			var slot = 20*place+prop_slots[place][i]
			var shape = host.store.shape("modules",o.id)
			var code = ((1 if o.palette==3175 else 0)<<8)|(o.id-o.palette)
			var rect = [o.y,o.x,o.y+int(shape[1]),o.x+int(shape[0])]
			file.scalar(0x796+2*slot,code)
			file.array(0x3d6+8*slot,rect)
			if rewrite:
				file.put(0x796+2*slot,code)
				for j in 4: file.put(0x3d6+8*slot+2*j,rect[j])

func export_data() -> PackedByteArray:
	capture()
	return file.data.duplicate()

func save() -> void:
	if not storage_enabled or loading:
		return
	var bytes = export_data()
	if bytes==last_written:
		return
	var target = FileAccess.open(save_path,FileAccess.WRITE)
	save_error = FileAccess.get_open_error()
	if target!=null:
		target.store_buffer(bytes)
		save_error = target.get_error()
		target.close()
		if save_error==OK:
			last_written = bytes
	if save_error!=OK:
		push_error("Could not save STATUS.DAT: %s"%error_string(save_error))

func import_data(bytes: PackedByteArray) -> bool:
	if bytes.size()<StatusFile.SIZE:
		return false
	loading = true
	host.reset_saved_session()
	file = StatusFile.new(bytes)
	apply()
	host.select_screen()
	save()
	return true
