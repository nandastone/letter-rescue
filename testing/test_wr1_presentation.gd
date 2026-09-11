extends SceneTree
## GPU regression: multiple texture/frame changes inside one callback must be
## captured immediately without advancing game state or mutating earlier images.
var failures := 0
var checks := 0

func check(ok: bool, message: String) -> void:
	checks += 1
	if not ok:
		failures += 1
		push_error(message)

func _initialize() -> void:
	run.call_deferred()

func run() -> void:
	assert(DisplayServer.get_name() != "headless", "This check requires GPU rendering")
	assert("--legacy" in OS.get_cmdline_user_args())
	paused = true
	change_scene_to_file("res://scenes/game.tscn")
	while current_scene == null or not current_scene.is_replay_ready():
		await process_frame
	var game = current_scene
	var before: String = JSON.stringify([game.player.original_state.snapshot(), game.original_interaction_snapshot()])
	var layer := CanvasLayer.new()
	layer.layer = 99
	game.add_child(layer)
	var sprite := Sprite2D.new()
	sprite.centered = false
	sprite.position = Vector2(100, 50)
	layer.add_child(sprite)
	var atlas := Image.create(16, 8, false, Image.FORMAT_RGBA8)
	atlas.fill(Color.RED)
	atlas.fill_rect(Rect2i(8, 0, 8, 8), Color.BLUE)
	sprite.texture = ImageTexture.create_from_image(atlas)
	sprite.hframes = 2
	var first: Image = game.original_presentation.rasterize()
	check(first.get_pixel(101, 51) == Color.RED, "First synchronous snapshot draws new sprite")
	sprite.frame = 1
	var second: Image = game.original_presentation.rasterize()
	check(second.get_pixel(101, 51) == Color.BLUE, "Frame changes are visible inside the same callback")
	atlas.fill(Color.GREEN)
	sprite.texture = ImageTexture.create_from_image(atlas)
	var third: Image = game.original_presentation.rasterize()
	check(third.get_pixel(101, 51) == Color.GREEN, "Replaced texture is visible immediately")
	check(first.get_pixel(101, 51) == Color.RED and second.get_pixel(101, 51) == Color.BLUE,
		"Later drawing cannot modify submitted images")
	check(JSON.stringify([game.player.original_state.snapshot(), game.original_interaction_snapshot()]) == before,
		"Rasterization must not advance gameplay or animation state")
	# Exercise the real recap -> player render -> recap overlay call chain. Main
	# gameplay's timer is stale while recap owns elapsed time. A smaller stale
	# remainder used to timestamp the old overlay AFTER its replacement.
	game.original_presentation.video.reset(third)
	game.original_presentation.frame_start = 0.0
	game.original_presentation.frame_end = 0.1
	game.player.original_elapsed = 0.001
	game.player.original_recap = preload("res://scripts/core/wr1_recap.gd").new()
	game.player.original_recap.begin(game.player.original_state, [0,1,2,3,4,5,6], 0.0, true)
	game.original_recap_view = preload("res://scripts/core/wr1_recap_view.gd").new()
	game.add_child(game.original_recap_view)
	game.original_recap_view.configure(game.hud, game.word_manager.words)
	game.player.original_recap.advance(0.1, game.player.original_state,
		game.original_gruzzles.random_word, game.player._present_original, game.present_original_recap)
	var writes: Array = game.original_presentation.video.pending.filter(func(event: Dictionary) -> bool: return event.kind == "write")
	writes.sort_custom(func(a: Dictionary, b: Dictionary) -> bool: return a.sequence < b.sequence)
	check(writes.size() == 2, "Recap helper submits its scene and overlay")
	check(writes.size() == 2 and writes[0].at <= writes[1].at,
		"Recap scene write must not be timestamped after its replacement overlay")
	# A hard-mode partial refill uses the native inclusive fill endpoint (A69D
	# calls 5EB8), unlike successful use, which erases from that endpoint.
	root.get_node("GameManager").current_difficulty = 2
	game.original_gruzzles.slime_used = 4
	game.hud.update_original_slime(4)
	var bucket: Vector2i = game.original_slime_pickups.positions[0]
	game._collect_original_cell(bucket.x * 2, bucket.y * 2)
	check(game.original_gruzzles.slime_used == 2, "Hard bucket restores two slime uses")
	check(game.hud.original_top.get_pixel(33, 20) == Color8(255, 85, 255)
		and game.hud.original_top.get_pixel(34, 20) == Color.BLACK,
		"Partial refill includes the last pink column, as native A69D/5EB8 do")
	# Demo level 10: the 20-book hint remains in page 5 when the next correct
	# letter paints only its collected prefix (A59D..A5FD).
	game.hud.setup_mystery_word("arm", 1)
	game.hud._draw_mystery(true)
	game.hud.update_mystery_letter(1)
	var native_m: Image = Image.load_from_file("res://testing/fixtures/wr1_demo_level10_counter_004000.png").get_region(Rect2i(164, 188, 8, 8))
	var clone_m: Image = game.hud.original_bottom.get_region(Rect2i(164, 4, 8, 8))
	native_m.convert(Image.FORMAT_RGBA8)
	clone_m.convert(Image.FORMAT_RGBA8)
	check(native_m.get_data() == clone_m.get_data(), "Collecting a letter preserves the remaining book hint")
	print("WR1 presentation: %d checks, %d failures" % [checks, failures])
	quit(1 if failures else 0)
