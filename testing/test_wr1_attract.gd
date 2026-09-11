extends SceneTree
func _initialize() -> void:
	_run.call_deferred()

func _run() -> void:
	var gm := root.get_node("GameManager")
	var replay := root.get_node("InputReplay")
	var session_dir := "res://testing/output/attract-session-%d/" % OS.get_process_id()
	DirAccess.make_dir_recursive_absolute(session_dir)
	gm.progress_path = session_dir + "progress.json"
	preload("res://scripts/wr1_profiles.gd").directory = session_dir + "profiles/"
	gm.current_level = 10 # The original permutation begins with short demo11.
	change_scene_to_file("res://scenes/game.tscn")
	await process_frame
	while current_scene == null or not current_scene.is_replay_ready(): await process_frame
	var game := current_scene
	var presented := "--attract-presented" in OS.get_cmdline_user_args()
	var image_before: Image
	if presented:
		game.process_mode = Node.PROCESS_MODE_DISABLED
		await RenderingServer.frame_post_draw
		image_before = root.get_texture().get_image()
	game.open_original_frontend()
	var menu: Node = game.get_child(game.get_child_count()-1)
	var before: Dictionary = game.original_interaction_snapshot()
	menu.begin_demos()
	while current_scene == game or current_scene == null: await process_frame
	var first := current_scene
	assert(gm.current_level == 11 and replay.demo_mode)
	while current_scene == first or current_scene == null: await process_frame
	assert(gm.current_level == 9,"Natural demo ending did not advance the original attract order")
	for i in range(14):
		while current_scene == null or not current_scene.is_replay_ready() or current_scene.player.original_state.ticks < 2:
			await process_frame
		var previous := current_scene
		menu.next_demo(false)
		while current_scene == previous or current_scene == null: await process_frame
	menu.finish_demos()
	while current_scene != game: await process_frame
	assert(gm.original_demo_host == null and not replay.demo_mode)
	assert(game.original_interaction_snapshot() == before,"Attract playback changed the suspended game")
	assert(menu.state == "menu")
	menu.press(KEY_ESCAPE)
	assert(game.replay_ready)
	if presented:
		await RenderingServer.frame_post_draw
		assert(root.get_texture().get_image().get_data() == image_before.get_data(),"Attract return failed to restore the visible paused game")
	# Also start from the initial menu, with no suspended gameplay scene.
	change_scene_to_file("res://scenes/main_menu.tscn")
	await process_frame
	while current_scene == null: await process_frame
	var main_menu := current_scene
	menu = main_menu.get_child(main_menu.get_child_count()-1)
	menu.open("menu")
	if presented:
		await RenderingServer.frame_post_draw
		image_before = root.get_texture().get_image()
	menu.begin_demos()
	while current_scene == main_menu or current_scene == null or not current_scene.is_replay_ready(): await process_frame
	# Cancel during the interlude, exercising the deferred scene teardown too.
	menu.next_demo()
	while menu.state != "demo_title": await process_frame
	menu.press(KEY_ENTER)
	while menu.state != "menu": await process_frame
	assert(current_scene == main_menu and gm.original_demo_host == null and not replay.demo_mode)
	if presented:
		await RenderingServer.frame_post_draw
		assert(root.get_texture().get_image().get_data() == image_before.get_data(),"Attract return lost the initial menu's viewport")
	menu.begin_demos()
	menu.press(KEY_ESCAPE) # Cancel before the deferred game instantiation.
	for i in range(3): await process_frame
	assert(current_scene == main_menu and gm.original_demo_host == null and not replay.demo_mode,"Cancelled attract start launched a stale game")
	print("Original attract natural ending, all fifteen starts and live-session restoration PASS")
	quit()
