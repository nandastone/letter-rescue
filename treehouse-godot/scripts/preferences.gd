extends RefCounted
## Resident F1/F2 modals. Layout/text comes from recovered TXT4 and FONT0.
var host
var store
var settings: Dictionary = {"sound":true,"printing":true,"printer":0,"advanced":false,"speed":false}
var kind: String = ""
var background: Image
var layout: Dictionary = {}
var flash: int = -1
var due: int = 0
var closing: bool = false
var status: Dictionary = {}
var glyphs: Dictionary = {}
var storage_enabled: bool = true
var save_path: String = "user://preferences.json"
var active: bool:
	get:
		return not kind.is_empty() or not status.is_empty()

func _init(game, persistent: bool = true) -> void:
	host = game
	store = host.store
	storage_enabled = persistent
	if storage_enabled:
		restore()

func save() -> void:
	if not storage_enabled:
		return
	var file = FileAccess.open(save_path,FileAccess.WRITE)
	if file==null:
		push_error("Could not save preferences: %s"%FileAccess.get_open_error())
		return
	file.store_string(JSON.stringify({"version":1,"settings":settings}))
	file.close()
	if host.persistence!=null:
		host.persistence.save()

func restore() -> void:
	if not FileAccess.file_exists(save_path):
		return
	var value = JSON.parse_string(FileAccess.get_file_as_string(save_path))
	if not value is Dictionary or value.get("version")!=1 or not value.get("settings") is Dictionary:
		return
	var candidate = value.settings
	for key in ["sound","printing","advanced","speed"]:
		if not candidate.get(key) is bool:
			return
	if not (candidate.get("printer") is int or candidate.get("printer") is float) or candidate.printer<0 or candidate.printer>1 or candidate.printer!=int(candidate.printer):
		return
	for key in settings:
		settings[key] = int(candidate[key]) if key=="printer" else candidate[key]
	apply_settings()

func apply_settings() -> void:
	if not settings.sound:
		host.audio.stop()
	if host.selection_audio!=null:
		host.selection_audio.volume_db = 0.0 if settings.sound else -INF
	host.maze.initial_advanced = settings.advanced
	host.maze.hard = settings.advanced

func allowed(help: bool, pointer_activation: bool = false) -> bool:
	if active or not host.travel.is_empty() or host.entering or host.rewards.active or host.resident.busy or host.room.busy or host.music.playing or (not pointer_activation and not host.held.is_empty()):
		return false
	if host.room.question=="asking" or (host.audio.playing and host.resident.selected):
		return false
	if not host.music.dialog.is_empty() or not host.music.editor.title_entry.is_empty() or host.music.print_view!=null:
		return false
	if host.scene=="maze" and host.maze.busy:
		return false
	if host.scene=="theater" and host.theater.playing:
		return false
	if host.scene=="nature":
		if not host.nature.dialog.is_empty() or host.nature.print_view!=null or host.nature.erase_task:
			return false
		if host.nature.mode=="quiz" and host.nature.quiz.busy:
			return false
	if host.scene=="boardgame" and host.boardgame.motion.busy and not (help and host.boardgame.exchange!=null):
		return false
	return true

func context() -> int:
	match host.scene:
		"music":
			if host.music.selector.open:
				return 6 if host.music.selector.category<0 else 7
			return 15 if host.music.editor.enabled else 0
		"maze":
			return 17 if host.maze.large_intro or host.maze.phase in ["win","arrival"] else 8
		"theater":
			var t = host.theater
			return 13 if t.options else 20 if t.mix_up and t.props_enabled else 22 if t.mix_up else 21 if t.props_enabled else 2
		"boardgame":
			var g = host.boardgame
			return 10 if g.options else 23 if g.winner>=0 or g.loser>=0 else 25 if g.exchange!=null else (24 if g.mode else 16) if g.phase=="reward" else 3
		"nature":
			var q = host.nature.quiz
			return 1 if host.nature.mode!="quiz" else 11 if q.options else 28 if q.winner>=0 else 26 if q.phase!="question" else 27 if q.help[q.role()] else 9
	return 19 if host.resident.selected else 18

func prepare() -> void:
	host.chalk.select(-1)
	host.release_inputs()
	var visible = host.pointer_visible
	host.pointer_visible = false
	host.render()
	host.pointer_visible = visible
	background = host.surface.image.duplicate()
	flash = -1
	due = 0
	closing = false

func open_settings() -> void:
	if not allowed(false):
		return
	prepare()
	kind = "settings"
	host.dirty = true

func open_help(control: bool = false, alt: bool = false, pointer_activation: bool = false) -> void:
	if not allowed(true,pointer_activation):
		return
	var selected = 29 if control and alt and host.pointer.x<2 and host.pointer.y<2 else context()
	for candidate in store.data.help:
		if int(candidate.context)==selected:
			layout = host.MusicMaze.integers(candidate)
			break
	prepare()
	kind = "help"
	host.dirty = true

func close() -> void:
	if not active:
		return
	kind = ""
	closing = false
	background = null
	save()
	host.resident.tick = host.tick
	host.resident.schedule_ambient()
	host.music.idle_due = host.tick+600
	host.dirty = true

func update(tick: int) -> void:
	if not status.is_empty():
		if tick>=status.due:
			status.clear()
		return
	if closing and tick>=due:
		close()

func show_status(label: String) -> void:
	var visible = host.pointer_visible
	host.pointer_visible = false
	host.render()
	host.pointer_visible = visible
	status = {"label":label,"background":host.surface.image.duplicate(),"due":host.tick+180}
	host.dirty = true

func toggle(row: int) -> void:
	if kind!="settings" or row<0 or row>4:
		return
	var key = ["sound","printing","printer","advanced","speed"][row]
	settings[key] = 1-int(settings[key]) if row==2 else not settings[key]
	apply_settings()
	flash = row
	due = host.tick+12
	save()
	host.dirty = true

func click(point: Vector2i) -> void:
	if not status.is_empty():
		status.clear()
		host.dirty = true
		return
	if kind=="help":
		var r = layout.rectangle
		if point.x>=r[1] and point.x<r[3] and point.y>=r[0] and point.y<r[2]:
			if closing:
				close()
			else:
				closing = true
				due = host.tick+20
	elif kind=="settings":
		if point.x>=242 and point.x<282 and point.y>=136 and point.y<148:
			close()
		elif point.x>=34 and point.x<286 and point.y>=61 and point.y<131:
			toggle(int((point.y-61)/14))
	host.dirty = true

func key_input(event: InputEventKey) -> bool:
	if not status.is_empty():
		if event.pressed and not event.echo:
			status.clear()
		return true
	if event.ctrl_pressed and event.pressed and not event.echo and event.keycode in [KEY_S,KEY_V]:
		if event.keycode==KEY_S:
			settings.sound = not settings.sound
			apply_settings()
		show_status(("Sound is On" if settings.sound else "Sound is Off") if event.keycode==KEY_S else "Version 1.1")
		return true
	if not active:
		if event.pressed and not event.echo and event.keycode in [KEY_F1,KEY_F2]:
			if event.keycode==KEY_F1:
				open_help(event.ctrl_pressed,event.alt_pressed)
			else:
				open_settings()
			return true
		return false
	if event.keycode in [KEY_LEFT,KEY_RIGHT,KEY_UP,KEY_DOWN,KEY_KP_5]:
		return false
	if event.pressed and not event.echo and event.keycode in [KEY_ESCAPE,KEY_ENTER,KEY_SPACE,KEY_S,KEY_D,KEY_G,KEY_H,KEY_J,KEY_L,KEY_SEMICOLON,KEY_Z,KEY_X,KEY_C,KEY_V,KEY_B,KEY_N,KEY_M,KEY_COMMA,KEY_PERIOD,KEY_SLASH]:
		if kind=="help":
			click(host.pointer)
		elif event.keycode in [KEY_ESCAPE,KEY_ENTER]:
			close()
	return true

func colors() -> Dictionary:
	if host.scene=="theater":
		var p = store.palette("modules",3000).colors
		return {"blue":Color8(p[12][0],p[12][1],p[12][2]),"white":Color8(p[1][0],p[1][1],p[1][2]),"red":Color8(p[10][0],p[10][1],p[10][2])}
	return {"blue":Color8(85,85,255),"white":Color.WHITE,"red":Color8(255,85,85)}

func heading(surface, text: String, x: int, y: int, color: Color = Color.BLACK) -> void:
	var width = 0
	for ch in text:
		var glyph = store.data.heading_font.get(str(ch.unicode_at(0)))
		width += (int(glyph[0]) if glyph!=null else 4)+1
	x -= int(width/2)
	for ch in text:
		var code = str(ch.unicode_at(0))
		var glyph = store.data.heading_font.get(code)
		if glyph!=null:
			if glyph[0]>0 and glyph[1]>0:
				var key = code+color.to_html()
				if not glyphs.has(key):
					glyphs[key] = store.raster(glyph,[[0,0,0],[color.r8,color.g8,color.b8]],true)
				surface.blit(glyphs[key],x,y)
			x += int(glyph[0])+1
		else:
			x += 5

func done_button(surface, top: int, bottom: int, face: Color) -> void:
	for r in [[top+2,243,bottom,283],[top+1,244,bottom+1,282]]:
		surface.rect(r[1],r[0],r[3]-r[1],r[2]-r[0],Color.BLACK)
	for r in [[top+1,242,bottom-1,282],[top,243,bottom,281]]:
		surface.rect(r[1],r[0],r[3]-r[1],r[2]-r[0],face)
	heading(surface,"Done",262,top+2)

func draw(surface) -> void:
	if not status.is_empty():
		var c = colors()
		surface.blit(status.background,0,0,false)
		surface.rect(108,176,104,16,c.red)
		surface.rect(109,177,102,14,c.white)
		heading(surface,status.label,160,180)
		return
	if kind.is_empty():
		return
	surface.blit(background,0,0,false)
	var c = colors()
	if kind=="help":
		var r = layout.rectangle
		surface.rect(r[1],r[0],r[3]-r[1],r[2]-r[0],Color.BLACK)
		surface.rect(r[1]+1,r[0]+1,r[3]-r[1]-2,r[2]-r[0]-2,c.white)
		heading(surface,layout.title,160,layout.title_glyph_top,c.blue)
		for i in layout.body_lines.size():
			surface.text(store,layout.body_lines[i].replace("\r",""),layout.body_x,layout.body_glyph_top+i*layout.body_line_step,Color.BLACK)
		done_button(surface,r[2]-16,r[2]-4,c.red if closing else c.blue)
		return
	surface.rect(32,43,256,109,Color.BLACK)
	surface.rect(33,44,254,107,c.white)
	heading(surface,"PREFERENCES",160,47,c.blue)
	var rows = ["Sound is ON/off" if settings.sound else "Sound is on/OFF","Printing is ON/off" if settings.printing else "Printing is on/OFF","Printer: Not Selected","Music Game Level: beginner/ADVANCED" if settings.advanced else "Music Game Level: BEGINNER/advanced","Speed Optimization is ON/off" if settings.speed else "Speed Optimization is on/OFF"]
	for i in 5:
		if flash==i and host.tick<due:
			surface.rect(34,61+14*i,252,14,c.red)
		heading(surface,rows[i],160,63+14*i)
	done_button(surface,136,148,c.blue)
