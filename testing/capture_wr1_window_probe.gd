extends "res://testing/capture_wr1_replay_frames.gd"
## Exercise the production capture loop across window minimization.
func _initialize() -> void:
	super._initialize()
	process_frame.connect(_window_probe)

func _window_probe() -> void:
	var input = root.get_node_or_null("InputReplay")
	if input == null:
		return
	var source: int = input.source_start_frame + input.current_input_frame
	if source == 1000 and "--probe-minimize" in OS.get_cmdline_user_args():
		root.mode = Window.MODE_MINIMIZED
	if source >= 1020:
		quit()
