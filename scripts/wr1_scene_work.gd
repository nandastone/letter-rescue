extends RefCounted
## Recover renderer work from the current scene. No saved outcomes or timings.
var renderer = preload("res://scripts/wr1_renderer_work.gd").new()
var descriptor: Dictionary
var images := {}
var cache := {}
var overlay: Dictionary
var sprite_work := {}

func supports_world(game: Node, p: RefCounted) -> bool:
	if game.original_entrance_timer != 0:
		return false
	var camera := Vector2i(p.camera_x,p.camera_y)
	if camera.x > 0 and p.x < 144:
		camera.x -= 1
	elif camera.x < p.width-36 and p.x > 144:
		camera.x += 1
	if camera.y > 0 and p.y < 108:
		camera.y -= 1
	elif camera.y < p.height-19 and p.y > 132:
		camera.y += 1
	for actor in game.original_gruzzles.actors:
		if actor.state == 23:
			return false # Rescue scoring calls are outside the work planner.
		if actor.state == 24 or (game.original_gruzzles.death and actor.state >= 0 and actor.state < 24):
			var pos := Vector2i((actor.gx-camera.x)*8+16,(actor.gy-camera.y)*8+9)
			if pos.x < 0 or pos.y < 0 or pos.x >= 320 or pos.y >= 200:
				return false
	return true

func _init() -> void:
	renderer.configure()
	descriptor = JSON.parse_string(FileAccess.get_file_as_string("res://data/wr1/drawing_device.json"))
	overlay = JSON.parse_string(FileAccess.get_file_as_string("res://data/wr1/recap_overlay_work.json")).work
	for filename in ["gruzzle_frames", "benny_frames"]:
		var table: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://data/wr1/%s.json" % filename))
		for item in table.frames:
			var record: Array = item.record
			var header := PackedByteArray(descriptor.player_images[0].header)
			var width: int = record[4]
			var height: int = record[5]
			header.encode_u16(10, width-1)
			header.encode_u16(12, height-1)
			header.encode_u16(20, ((width+15)/16)*2)
			header.encode_u16(44, width)
			header.encode_u16(46, height)
			header.encode_u16(48, (width+7)/8)
			images[str(int(record[0]))] = Array(header)
			images[str(int(record[2]))] = Array(header)

func world_seconds(game: Node, p: RefCounted) -> float:
	var animation = game.original_picture_animation
	var model = game.word_manager.original_model
	var actors = game.original_gruzzles
	var prefix := {"animation_enabled":int(animation.enabled), "player_x":p.x,"player_y":p.y,
		"camera_x":p.camera_x,"camera_y":p.camera_y,"attr_width":p.width,"attr_height":p.height,
		"render_page":actors.render_page,"counters":Array(animation.timers),"phases":Array(animation.frames),
		"word_slots":Array(model.completion_order),"source_rects":[[],[]]}
	for phase in range(2):
		for i in range(7):
			prefix.source_rects[phase].append([i*24,phase*24,i*24+23,phase*24+23])
	var columns: Array = []
	for x in range(p.width/2):
		var column: Array = []
		for y in range(p.height/2):
			var tile: Vector2i = game.bg_tilemap.get_cell_atlas_coords(Vector2i(x,y))
			column.append([-32,-32] if tile.x < 0 else [tile.x*16,tile.y*16])
		columns.append(column)
	var animated: Array = game.level_data.get("animations", []).duplicate(true)
	for i in range(game.anim_cells.size()):
		var cell: Vector2i = game.anim_cells[i]
		var tile: Vector2i = game.anim_base_atlas[i]
		columns[cell.x][cell.y] = [tile.x*16,tile.y*16]
	var background := {"full_redraw":int(game.level_data.get("backdrop",0) != 0),
		"color":int(game.level_data.bg_colour_ega),"source_columns":columns}
	var pickups: Array = []
	for cell in game.original_letters.positions:
		pickups.append([cell.x,cell.y])
	var tiles := {"phase":p.background_frame,"animated_count":animated.size(),"animated":animated,"pickups":pickups}
	var doors := {"theme":int(game.player.original_character == "girl"),"exit_x":int(game.level_data.exit_door[0]*2),
		"exit_y":int(game.level_data.exit_door[1]*2),"entrance_x":0,"entrance_y":0,"entrance_timer":game.original_entrance_timer}
	assert(doors.entrance_timer == 0, "Scene work adapter currently starts after the entrance disappears")
	var locations: Array = []
	for cell in model.slots:
		locations.append([cell.x*8,cell.y*8,int(p.attributes[cell.y][cell.x])])
	locations.sort_custom(func(a: Array,b: Array) -> bool: return a[1]<b[1] if a[0]==b[0] else a[0]<b[0])
	var matching := {"active":int(model.active_slot>=0),"active_index":model.active_index,
		"source_x":-1,"source_y":-1,"last_x":model.last_touched.x,"last_y":model.last_touched.y,
		"picture_offset":model.picture_offset,"locations":locations,"word_rects":[]}
	if model.active_slot>=0:
		matching.source_x=model.slots[model.active_slot].x
		matching.source_y=model.slots[model.active_slot].y
	for i in range(7):
		matching.word_rects.append([168+(i%2)*72,(i/2)*18,239+(i%2)*72,(i/2)*18+17])
	var player := {"visible":int(game.player.original_sprite.visible),"frame":p.frame,
		"images":descriptor.player_images.slice(0,2)}
	var enemies: Array = []
	for a in actors.actors:
		enemies.append({"x":a.gx,"y":a.gy,"type":a.type,"state":a.state,"animation_index":a.animation_index})
	var drips: Array = []
	if game.original_drips != null:
		for drip in game.original_drips.drips:
			drips.append({"x":drip.x,"y":drip.y,"frame":drip.frame})
	var actor_state := {"data_segment":1,"enemy_count":enemies.size(),"drip_count":drips.size(),
		"animation_frames":Array(actors.WALK),"enemies":enemies,"drips":drips}
	# The DOS list can repeat a coordinate; those repeated blits still cost
	# work even though Godot stores only one tile at that coordinate.
	var foreground: Array = game.level_data.get("fg_tiles", []).duplicate(true)
	var reward = game.original_reward
	var tail := {"score":0,"action_busy":int(actors.action_busy),"death":int(actors.death),"slime_reward":10,
		"miss_timer":actors.miss_timer,"miss_x":actors.miss_grid.x,"miss_y":actors.miss_grid.y,
		"reward_timer":reward.ticks,"reward_x":reward.grid.x,"reward_y":reward.grid.y,"reward_bonus":reward.bonus,
		"reward_text":_caption(str(reward.amount)),"perfect_text":_caption("Bonus #3"),"bonus_text":_caption("Bonus #1"),
		"foreground_count":foreground.size(),"foreground":foreground,"rescue_frames":Array(actors.SLIME)}
	var key := JSON.stringify([prefix,background,tiles,doors,matching,player,actor_state,tail])
	if cache.has(key):
		return cache[key]
	var result: Dictionary = renderer.complete(prefix,descriptor.graphics,background,tiles,doors,matching,player,actor_state,images,tail)
	var seconds := _seconds(result.work)
	cache[key] = seconds
	return seconds

func _caption(value: String) -> Dictionary:
	var bytes := value.to_ascii_buffer()
	bytes.append(0)
	return {"pointer":1,"bytes":Array(bytes)}

func recap_seconds(game: Node, p: RefCounted, event: Dictionary) -> float:
	if event.kind not in ["helper", "dissolve"]:
		return -1.0 # Keep the separate transfer-loop profile.
	var page: int = 1 - game.original_gruzzles.render_page
	var key := str([event.frame,event.position,page])
	if not sprite_work.has(key):
		var path: Array = []
		for op in range(1,3):
			var offset: int = (0xa306 if op == 1 else 0x8e91) + event.frame * 128
			var device: Dictionary = descriptor.graphics.duplicate(true)
			device.image_header = images[str(offset)]
			device.args = [page,event.position.y,event.position.x,op,offset,1]
			path.append_array(renderer.graphics.masked_sprite(device))
			path.append(["retf",0x16995])
		sprite_work[key] = _seconds(path)
	var kind: String = "panel" if event.kind == "helper" and event.order >= 0 else event.kind
	return world_seconds(game,p) + sprite_work[key] + float(overlay[kind].seconds)

func _seconds(path: Array) -> float:
	var cpu = preload("res://scripts/wr1_hardware.gd").new()
	cpu.cycle_left = 27000
	cpu.run_driver(path)
	return cpu.observed_time()/1000.0
