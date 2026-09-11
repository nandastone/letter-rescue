extends "res://scripts/scene_capture.gd"
## Default game: the live scene is what you see, drawn at the window's
## resolution. None of the original display hardware is modelled here — no VGA
## scanout or page flipping, no per-update rasterize and GPU read-back, and no
## CPU drawing-cost accounting. The scene is captured only when a menu needs a
## frozen frame to draw over.
var initialized := true

func initialize() -> void:
	pass

## The frozen frame the frontend draws its menus over.
func frame_image() -> Image:
	return rasterize() if enabled else null

func submit(_page: int, _elapsed_after_event: float = 0.0, _ordinary_draw: bool = false) -> void:
	pass

func prepare_world() -> void:
	pass
