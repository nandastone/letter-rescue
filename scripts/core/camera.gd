extends Camera2D

func apply_original(state: RefCounted) -> void:
	position_smoothing_enabled = false
	limit_left = -1000000
	limit_top = -1000000
	limit_right = 1000000
	limit_bottom = 1000000
	# Screen projection = world + (16,32) - 8*original_camera.
	global_position = Vector2(144 + state.camera_x * 8, 68 + state.camera_y * 8)
	force_update_scroll()
