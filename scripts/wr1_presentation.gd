extends Node
## Owns video time and immutable page images. The live scene is an offscreen
## rasterizer; drawing it never advances gameplay, animation, or replay input.
const Video = preload("res://scripts/wr1_video_clock.gd")
var video = Video.new()
var output_layer: CanvasLayer
var output_sprite: Sprite2D
var output_texture: ImageTexture
var initialized := false
var frame_start: float = 0.0
var frame_end: float = 0.0
var captures: int = 0
var queued_page: int = 0
var game: Node
var capturing := false
var enabled := DisplayServer.get_name() != "headless"
var scanout_enabled := false
var latest: Image
var drawing_work: RefCounted
var previous_camera := Vector2i.ZERO
var last_submission_at: float = 0.0
var scene_work: RefCounted
var prepared_seconds: float = -1.0
var reference_viewport: SubViewport

func display_mask() -> int:
	return 3 if preload("res://scripts/wr1_clear_text.gd").enabled() else 2

func _ready() -> void:
	game = get_parent()
	preload("res://scripts/wr1_clear_text.gd").configure_window(get_window())
	var args := OS.get_cmdline_user_args()
	# Use the same presentation policy in live play and replay. Older recordings
	# lack measured VGA phase; the parity report explicitly marks that assumption.
	scanout_enabled = not "--snapshot-video" in args
	if not enabled:
		set_physics_process(false)
		set_process(false)
		return # Headless state checks intentionally have no GPU framebuffer.
	process_physics_priority = -90 # After replay input, before gameplay.
	output_layer = CanvasLayer.new()
	output_layer.layer = 100
	add_child(output_layer)
	output_sprite = Sprite2D.new()
	output_sprite.centered = false
	output_sprite.visibility_layer = 2
	output_layer.add_child(output_sprite)
	get_viewport().canvas_cull_mask = display_mask()
	if preload("res://scripts/wr1_clear_text.gd").enabled():
		# The readable display draws the live scene at window resolution. Keep a
		# separate original-size rasterizer for the recovered video/work model.
		output_sprite.hide()
		reference_viewport = SubViewport.new()
		reference_viewport.size = Vector2i(320, 200)
		reference_viewport.disable_3d = true
		reference_viewport.handle_input_locally = false
		reference_viewport.gui_disable_input = true
		reference_viewport.world_2d = get_viewport().world_2d
		reference_viewport.canvas_cull_mask = 5
		reference_viewport.render_target_update_mode = SubViewport.UPDATE_DISABLED
		add_child(reference_viewport)

func _exit_tree() -> void:
	if enabled and is_instance_valid(game) and game.is_inside_tree():
		game.get_viewport().canvas_cull_mask = 0xFFFFFFFF

func rasterize() -> Image:
	assert(not capturing)
	for node in game.find_children("*", "", true, false):
		if node.is_queued_for_deletion() and (node is CanvasItem or node is CanvasLayer):
			node.hide()
	# A submission can occur inside a physics callback, before Godot's usual
	# deferred tile and transform flush. Materialize this scene state now.
	for item in game.find_children("*", "Node2D", true, false):
		if item is TileMapLayer:
			item.update_internals()
		item.force_update_transform()
	# Sprite texture/frame setters defer rebuilding their draw commands. Flush
	# Godot sprite drawing now so a submission cannot retain the previous pose
	# or refer to a dynamic texture that has just been replaced.
	for item in game.find_children("*", "CanvasItem", true, false):
		if item != output_sprite and item.is_visible_in_tree() and (item is Sprite2D or item is TextureRect or item is ColorRect):
			RenderingServer.canvas_item_clear(item.get_canvas_item())
			if item is Sprite2D:
				item.notification(CanvasItem.NOTIFICATION_DRAW)
			elif item is TextureRect and item.texture != null:
				assert(item.stretch_mode == TextureRect.STRETCH_SCALE)
				item.texture.draw_rect(item.get_canvas_item(), Rect2(Vector2.ZERO, item.size), false)
			elif item is ColorRect:
				RenderingServer.canvas_item_add_rect(item.get_canvas_item(), Rect2(Vector2.ZERO, item.size), item.color)
	# Use the root backbuffer without swapping it to the window. CanvasLayers
	# retain their normal viewport/ordering, including temporary recap overlays.
	var layers: Array[CanvasLayer] = []
	var targets: Array[Node] = []
	var source_viewport: Viewport = get_viewport()
	if reference_viewport != null:
		source_viewport = reference_viewport
		reference_viewport.canvas_transform = get_viewport().canvas_transform
		for node in game.find_children("*", "CanvasLayer", true, false):
			if node == output_layer or node.layer >= 100: continue
			layers.append(node)
			targets.append(node.custom_viewport if node.custom_viewport != null else get_viewport())
			node.custom_viewport = reference_viewport
		reference_viewport.render_target_update_mode = SubViewport.UPDATE_ONCE
	else:
		get_viewport().canvas_cull_mask = 1
	capturing = true
	InputReplay.video_capture_active = true
	RenderingServer.force_sync()
	RenderingServer.force_draw(false)
	var image: Image = source_viewport.get_texture().get_image()
	for i in range(layers.size()): layers[i].custom_viewport = targets[i]
	get_viewport().canvas_cull_mask = display_mask()
	InputReplay.video_capture_active = false
	capturing = false
	captures += 1
	image.convert(Image.FORMAT_RGBA8)
	return image

func initialize() -> void:
	if initialized or not enabled:
		return
	var initial: Image = rasterize()
	drawing_work = preload("res://scripts/wr1_drawing_work.gd").new()
	scene_work = preload("res://scripts/wr1_scene_work.gd").new()
	previous_camera = Vector2i(game.player.original_state.camera_x, game.player.original_state.camera_y)
	var timing: Dictionary = InputReplay.original_video_start
	video.reset(initial, timing)
	last_submission_at = 0.0
	queued_page = int(timing.get("page", 0))
	output_texture = ImageTexture.create_from_image(initial)
	output_sprite.texture = output_texture
	latest = initial
	initialized = true

func _physics_process(delta: float) -> void:
	if not game.is_replay_ready():
		return
	if not initialized:
		initialize()
	# The frontend returns a completed image before starting this interval's
	# emulation work. Gameplay can submit several page writes during the interval.
	video.advance(frame_end)
	if scanout_enabled:
		output_texture.update(video.image())
	frame_start = frame_end
	frame_end += InputReplay.original_frame_seconds(delta)

func _process(_delta: float) -> void:
	# Compatibility presentation retains the established frontend behavior while
	# consuming an owned snapshot. Experimental scanout additionally models VGA
	# latency; it needs CPU drawing costs before it can replace this policy.
	if initialized and not scanout_enabled and latest != null:
		output_texture.update(latest)
		latest = null

func submit(page: int, elapsed_after_event: float = 0.0, ordinary_draw: bool = false) -> void:
	if not initialized:
		return
	# Gameplay reports time left after its event, independent of video time.
	var at: float = clampf(frame_end - elapsed_after_event, frame_start, frame_end)
	var state: RefCounted = game.player.original_state
	if ordinary_draw:
		if prepared_seconds >= 0.0:
			at += prepared_seconds
		else:
			at += drawing_work.minimum_seconds(page, previous_camera, state,
				int(game.level_data.get("backdrop", 0)) == 0, game.player.original_sprite.visible, game.bg_tilemap,
				game.original_gruzzles.draws, game.fg_tilemap)
	prepared_seconds = -1.0
	previous_camera = Vector2i(state.camera_x, state.camera_y)
	# Sequential draw calls (including the exit's second world draw) cannot
	# overtake an earlier submission whose mandatory work is still pending.
	at = maxf(at, last_submission_at)
	last_submission_at = at
	var image: Image = rasterize()
	latest = image
	video.write_page(at, page, image)
	video.select_page(at, page)
	queued_page = page

func prepare_world() -> void:
	prepared_seconds = -1.0
	if initialized and scene_work.supports_world(game,game.player.original_state):
		prepared_seconds = scene_work.world_seconds(game,game.player.original_state)
