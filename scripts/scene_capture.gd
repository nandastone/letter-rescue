extends Node
## Shared scene rasterizer. Draws the live scene into an owned 320x200 image
## without swapping it to the window, so capturing never advances gameplay,
## animation or replay input. Legacy drives its VGA video model from this on
## every update; the default game only needs a frozen frame behind menus.
const ClearText = preload("res://scripts/wr1_clear_text.gd")

var game: Node
var enabled := DisplayServer.get_name() != "headless"
var capturing := false
var captures: int = 0
var reference_viewport: SubViewport
var output_layer: CanvasLayer # Legacy's video output layer; excluded from captures.
var output_sprite: Sprite2D # Legacy's displayed video output; excluded from captures.

func display_mask() -> int:
	return 3 if ClearText.enabled() else 2

func _ready() -> void:
	game = get_parent()
	ClearText.configure_window(get_window())
	if not enabled:
		set_physics_process(false)
		set_process(false)
		return # Headless state checks intentionally have no GPU framebuffer.
	get_viewport().canvas_cull_mask = display_mask()
	if ClearText.enabled():
		# The readable display draws the live scene at window resolution. Keep a
		# separate original-size rasterizer for the recovered video/work model.
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
