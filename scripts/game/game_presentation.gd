extends "res://scripts/core/scene_capture.gd"
## Default game: the live scene is what you see, drawn at the window's
## resolution. None of the original display hardware is modelled here — no VGA
## scanout or page flipping, no per-update rasterize and GPU read-back, and no
## CPU drawing-cost accounting. The scene is captured only when a menu needs a
## frozen frame to draw over.
var initialized := true

func _ready() -> void:
	super()
	if not enabled:
		return
	# Pixel snapping stays on. Drawing the art at sub-pixel positions makes it
	# shimmer: measured frame by frame while walking, a question block's drawn
	# width oscillated between 62 and 63 device pixels. Snapped, it holds 62,
	# and the smoothing still moves in 1-pixel steps rather than 8-pixel jumps.
	get_viewport().snap_2d_transforms_to_pixel = true
	get_viewport().snap_2d_vertices_to_pixel = true

func initialize() -> void:
	pass

## The frozen frame the frontend draws its menus over.
func frame_image() -> Image:
	return rasterize() if enabled else null

func submit(_page: int, _elapsed_after_event: float = 0.0, _ordinary_draw: bool = false) -> void:
	pass

func prepare_world() -> void:
	pass
