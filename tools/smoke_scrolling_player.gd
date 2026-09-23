extends SceneTree
## Real-scene scrolling regression. Use --capture-scroll with a GPU, then
## python tools/check_scrolling_player.py to measure the rendered player.
var waited := 0
var attached := false

func _initialize() -> void:
	change_scene_to_file.call_deferred("res://scenes/game.tscn")
	process_frame.connect(func():
		waited += 1
		if waited > 4000: quit(1)
		if not attached and current_scene != null and current_scene.is_replay_ready():
			attached = true
			var sampler := Sampler.new()
			sampler.process_priority = 5000
			current_scene.add_child(sampler))

class Sampler extends Node:
	var elapsed := 0.0
	var last_camera := 0.0
	var following := 0
	var samples := 0
	var peak := 0.0
	var marker: Texture2D
	var capture_frame := 0
	func _ready() -> void:
		if "--capture-scroll" in OS.get_cmdline_user_args():
			# Awkward size deliberately exercises integer scaling and black bars.
			get_window().size = Vector2i(997, 650)
			# Keep the actual Sprite2D and its dimensions/transform, replacing only
			# the animated artwork so the player's bounds can be measured exactly.
			var image := Image.create(26 * 24, 32, false, Image.FORMAT_RGBA8)
			image.fill(Color8(123, 17, 231))
			marker = ImageTexture.create_from_image(image)
			DirAccess.make_dir_recursive_absolute("res://testing/output/scroll-frames")
			for filename in DirAccess.get_files_at("res://testing/output/scroll-frames"):
				if filename.ends_with(".png"):
					DirAccess.remove_absolute("res://testing/output/scroll-frames/" + filename)
			RenderingServer.frame_post_draw.connect(func():
				if capture_frame > 0:
					get_viewport().get_texture().get_image().save_png("res://testing/output/scroll-frames/%03d.png" % capture_frame)
					capture_frame = 0)
		Input.action_press("move_right")
	func _process(delta: float) -> void:
		elapsed += delta
		var game = get_parent()
		var player = game.player
		var camera = game.camera
		var sprite = player.original_sprite
		if marker != null: sprite.texture = marker
		if camera.position.x != last_camera:
			following += 1
			last_camera = camera.position.x
		var error: float = sprite.offset.x - camera.offset.x
		if following >= 3 and elapsed < 1.7:
			samples += 1
			peak = maxf(peak, absf(error))
			if "--capture-scroll" in OS.get_cmdline_user_args():
				capture_frame = samples
		if elapsed >= 1.7:
			Input.action_release("move_right")
			print("scrolling: %d samples, %d camera steps, peak relative offset %.3f px" % [samples, following, peak])
			get_tree().quit(1 if samples < 20 or peak > 0.01 else 0)
