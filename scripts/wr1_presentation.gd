extends "res://scripts/scene_capture.gd"
## Legacy video model: owns video time and immutable page images, and displays
## the VGA scanout result. Every gameplay submission rasterizes the scene.
const Video = preload("res://scripts/wr1_video_clock.gd")
var video = Video.new()
var output_texture: ImageTexture
var initialized := false
var frame_start: float = 0.0
var frame_end: float = 0.0
var queued_page: int = 0
var scanout_enabled := false
var latest: Image
var drawing_work: RefCounted
var previous_camera := Vector2i.ZERO
var last_submission_at: float = 0.0
var scene_work: RefCounted
var prepared_seconds: float = -1.0

func _ready() -> void:
	super()
	var args := LaunchArgs.user_args()
	# Use the same presentation policy in live play and replay. Older recordings
	# lack measured VGA phase; the parity report explicitly marks that assumption.
	scanout_enabled = not "--snapshot-video" in args
	if not enabled:
		return # Headless state checks intentionally have no GPU framebuffer.
	process_physics_priority = -90 # After replay input, before gameplay.
	output_layer = CanvasLayer.new()
	output_layer.layer = 100
	add_child(output_layer)
	output_sprite = Sprite2D.new()
	output_sprite.centered = false
	output_sprite.visibility_layer = 2
	output_layer.add_child(output_sprite)
	if ClearText.enabled():
		# The readable display draws the live scene; the video model still runs
		# against the original-size rasterizer the base class set up.
		output_sprite.hide()

## The frozen frame the frontend draws its menus over.
func frame_image() -> Image:
	return output_texture.get_image() if output_texture != null else null

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
