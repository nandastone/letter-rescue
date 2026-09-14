extends SceneTree
## Bootstraps the Krsna vocabulary Pixelorama project and its runtime atlas.
## The .pxo file is the editable source after this script has been run once.

const WORDS = preload("res://scripts/game/krsna_vocabulary.gd").PICTURE_WORDS
const FRAME_COUNT := 2
const SIZE := 24
const ATLAS_PATH := "res://assets/sprites/krsna_words.png"
const SOURCE_PATH := "res://tools/art/pixelorama/krsna-words.pxo"
const PREVIEW_PATH := "res://tools/art/pixelorama/krsna-words-preview.png"

var black := Color8(0, 0, 0)


func _initialize() -> void:
	var images: Array[Image] = []
	for word in WORDS:
		for frame in range(FRAME_COUNT):
			var image := Image.create(SIZE, SIZE, false, Image.FORMAT_RGBA8)
			if not preload("res://tools/art/pixelorama/krsna_pixels.gd").draw_picture(word, image, frame):
				quit(1)
				return
			images.append(image)

	var atlas := Image.create(SIZE * images.size(), SIZE, false, Image.FORMAT_RGBA8)
	atlas.fill(black)
	for i in range(images.size()):
		atlas.blit_rect(images[i], Rect2i(0, 0, SIZE, SIZE), Vector2i(i * SIZE, 0))
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(ATLAS_PATH.get_base_dir()))
	var error := atlas.save_png(ATLAS_PATH)
	if error != OK:
		printerr("Could not save Krsna word atlas: %s" % error)
		quit(1)
		return

	for frame in range(FRAME_COUNT):
		_write_preview(images, frame)
	var cow_preview := images[WORDS.find("cow") * FRAME_COUNT].duplicate()
	cow_preview.resize(192, 192, Image.INTERPOLATE_NEAREST)
	cow_preview.save_png(PREVIEW_PATH.get_base_dir() + "/cow-preview.png")
	if not _write_pixelorama_project(images):
		quit(1)
		return
	print("Wrote %s, %s and both preview frames" % [ATLAS_PATH, SOURCE_PATH])
	quit()


func _write_preview(images: Array[Image], frame: int) -> void:
	var preview_height := ceili(WORDS.size() / 4.0) * 48
	var preview := Image.create(288, preview_height, false, Image.FORMAT_RGBA8)
	preview.fill(Color("121722"))
	for i in range(WORDS.size()):
		var origin := Vector2i((i % 4) * 72, (i / 4) * 48)
		preview.blit_rect(images[i * FRAME_COUNT + frame], Rect2i(0, 0, 24, 24), origin + Vector2i(24, 5))
		preload("res://scripts/core/wr1_text.gd").draw(preview, WORDS[i], origin + Vector2i(36 - WORDS[i].length() * 4, 34), Color("e6e4df"), Color("121722"))
	preview.resize(1152, preview_height * 4, Image.INTERPOLATE_NEAREST)
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(PREVIEW_PATH.get_base_dir()))
	preview.save_png(PREVIEW_PATH if frame == 0 else PREVIEW_PATH.replace(".png", "-2.png"))


func _new_project_data() -> Dictionary:
	var frames: Array[Dictionary] = []
	for word in WORDS:
		for frame in range(FRAME_COUNT):
			frames.append({
				"cels": [{"metadata": {"word": word, "animation_frame": frame}, "opacity": 1.0, "ui_color": "(0.0, 0.0, 0.0, 0.0)", "z_index": 0}],
				"duration": 1.0,
				"metadata": {"word": word, "animation_frame": frame},
			})
	return {
		"author_company": "",
		"author_contact": "",
		"author_display_name": "",
		"author_real_name": "",
		"brushes": [],
		"color_mode": Image.FORMAT_RGBA8,
		"current_frame": 0,
		"current_layer": 0,
		"export_profile": {
			"crop_mode": "0", "current_tab": "1", "direction": "0",
			"directory_path": "\"%s\"" % ProjectSettings.globalize_path(ATLAS_PATH.get_base_dir()).replace("\\", "/"),
			"erase_unselected_area": "false", "export_json": "false", "export_layers": "0",
			"file_format": "0", "file_name": "\"krsna_words\"", "frame_current_tag": "0",
			"include_tag_in_filename": "false", "interpolation": "0", "lines_count": "1",
			"new_dir_for_each_frame_tag": "false", "number_of_digits": "4",
			"number_of_frames": str(WORDS.size() * FRAME_COUNT), "orientation": "0", "repeat_count": "0",
			"resize": "100", "save_quality": "0.75", "separator_character": "\"_\"",
			"sheet_layers_as_separate_files": "false", "split_layers": "false",
		},
		"fps": 1.5,
		"frames": frames,
		"guides": [],
		"layers": [{
			"animated_params": "Dictionary[String, Dictionary]({\n\"opacity\": {}\n})",
			"blend_mode": 0, "clipping_mask": false, "effects": [], "locked": false,
			"metadata": {"frame_order": ", ".join(WORDS)}, "name": "Krsna word pictures",
			"new_cels_linked": false, "opacity": 1.0, "parent": -1, "type": 0,
			"ui_color": "(0.0, 0.0, 0.0, 0.0)", "visible": true,
		}],
		"license": "",
		"metadata": {"frame_order": WORDS, "frames_per_word": FRAME_COUNT},
		"next_keyframe_id": 0,
		"palettes": [],
		"pixelorama_version": "v1.2.2-stable",
		"project_current_palette_name": "",
		"pxo_version": 7,
		"reference_images": [],
		"size_x": SIZE,
		"size_y": SIZE,
		"symmetry_points": [float(SIZE - 2), float(SIZE - 2)],
		"tags": [],
		"tile_mode_x_basis_x": SIZE,
		"tile_mode_x_basis_y": 0,
		"tile_mode_y_basis_x": 0,
		"tile_mode_y_basis_y": SIZE,
		"tilesets": [],
		"user_data": "Two adjacent frames per word: %s" % ", ".join(WORDS),
		"vanishing_points": [],
	}


func _write_pixelorama_project(images: Array[Image]) -> bool:
	var absolute_path := ProjectSettings.globalize_path(SOURCE_PATH)
	DirAccess.make_dir_recursive_absolute(absolute_path.get_base_dir())
	var zip := ZIPPacker.new()
	var error := zip.open(absolute_path)
	if error != OK:
		printerr("Could not create Pixelorama project: %s" % error)
		return false
	_write_zip_file(zip, "data.json", JSON.stringify(_new_project_data()).to_utf8_buffer())
	_write_zip_file(zip, "mimetype", "application/x-pixelorama".to_utf8_buffer())
	_write_zip_file(zip, "preview.png", images[0].save_png_to_buffer())
	for i in range(images.size()):
		var directory := "image_data/frames/%d" % (i + 1)
		_write_zip_file(zip, directory + "/layer_1", images[i].get_data())
		_write_zip_file(zip, directory + "/indices_layer_1", PackedByteArray([0]))
	zip.close()
	return true


func _write_zip_file(zip: ZIPPacker, path: String, bytes: PackedByteArray) -> void:
	zip.start_file(path)
	zip.write_file(bytes)
	zip.close_file()
