extends SceneTree
## Capture actual replay rendering; filenames include the supplied input frame.
var targets: Array[int] = []
var directory: String
var initial_pending := false
var through_ending := false
var replay: Node

func _initialize() -> void:
	run.call_deferred()

func run() -> void:
	var args := OS.get_cmdline_user_args()
	var index := args.find("--capture-source-frames")
	for value in args[index + 1].split(","):
		targets.append(int(value))
	targets.sort()
	index = args.find("--capture-directory")
	directory = args[index + 1]
	DirAccess.make_dir_recursive_absolute(directory)
	initial_pending = "--capture-initial" in args
	# The parity suite also records state in this process. Continue through the
	# game's terminal return after the final requested screenshot.
	through_ending = "--capture-through-replay-end" in args
	replay = root.get_node("InputReplay")
	if initial_pending:
		# Present the checkpoint before admitting any replay input or gameplay tick.
		paused = true
		replay.set_physics_process(false)
	change_scene_to_file("res://scenes/game.tscn")
	process_frame.connect(_queue_capture)

func _queue_capture() -> void:
	# Run after the scene's process callbacks, including snapshot presentation.
	# Normal frame_post_draw signals can stop when a window is minimized.
	_capture.call_deferred()

func _save_frame(filename: String) -> void:
	# Render the real viewport without waiting for an OS window presentation.
	# Gameplay drawing and input advancement remain untouched.
	RenderingServer.force_sync()
	RenderingServer.force_draw(false)
	var path := directory.path_join(filename)
	var image := root.get_texture().get_image()
	if "--capture-reference-video" in OS.get_cmdline_user_args():
		# Clear Text deliberately changes the display. Save it separately while
		# checking the untouched original-resolution video stream against DOSBox.
		assert("--clear-text" in OS.get_cmdline_user_args())
		assert(image.save_png(path.get_basename() + "_clear.png") == OK)
		image = current_scene.original_presentation.output_texture.get_image()
	var status := image.save_png(path)
	if status != OK:
		push_error("Cannot save replay capture: " + path)
		quit(1)
	print("Captured ", path)

func _capture() -> void:
	if current_scene == null or not current_scene.has_method("is_replay_ready") or not current_scene.is_replay_ready():
		return
	assert(not replay.video_capture_active)
	if initial_pending:
		assert(replay.current_input_frame == -1)
		_save_frame("initial.png")
		initial_pending = false
		paused = false
		replay.set_physics_process(true)
		return
	var source: int = replay.source_start_frame + replay.current_input_frame
	if not targets.is_empty() and source > targets[0]:
		push_error("Missed replay capture at source %d; now at %d" % [targets[0],source])
		quit(1)
		return
	if source in targets:
		_save_frame("source_%06d.png" % source)
		targets.erase(source)
	if not through_ending and targets.is_empty():
		quit()
