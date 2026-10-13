extends SceneTree
## Native clock fixtures exercise the production presenter, never game timing.
const Presentation = preload("res://scripts/presentation.gd")

func image_at(path: String) -> Image:
	var image = Image.load_from_file(path)
	image.convert(Image.FORMAT_RGBA8)
	return image

func digest(image: Image) -> String:
	var rgb = image.duplicate()
	rgb.convert(Image.FORMAT_RGB8)
	var context = HashingContext.new()
	context.start(HashingContext.HASH_SHA256)
	context.update(rgb.get_data())
	return context.finish().hex_encode()

func _initialize() -> void:
	var output = OS.get_cmdline_user_args()[0]
	var fixture = JSON.parse_string(FileAccess.get_file_as_string(output+"/fixture.json"))
	var p = Presentation.new()
	p.reset(fixture.start,image_at(fixture.initial))
	var next = 0
	var frames: Array = []
	for frame in fixture.frames:
		while next<fixture.commits.size() and fixture.commits[next].milliseconds<=frame.callback:
			var commit = fixture.commits[next]
			p.commit(commit.milliseconds,image_at(commit.image))
			next += 1
		p.advance_to(frame.callback)
		frames.append({"run":frame.run,"hash":digest(p.image),"atomic_hash":digest(p.source),"count":p.count})
	var file = FileAccess.open(output+"/godot.json",FileAccess.WRITE)
	file.store_string(JSON.stringify({"frames":frames},"\t"))
	file.close()
	quit()
