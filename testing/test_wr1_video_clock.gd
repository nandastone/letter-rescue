extends SceneTree
const Video = preload("res://scripts/legacy/wr1_video_clock.gd")
var failures := 0
var checks := 0

func check(condition: bool, message: String) -> void:
	checks += 1
	if not condition:
		failures += 1
		push_error(message)

func solid(color: Color) -> Image:
	var result := Image.create(320, 200, false, Image.FORMAT_RGB8)
	result.fill(color)
	return result

func _initialize() -> void:
	check(not Video.valid_timing({"period": NAN}) and not Video.valid_timing({"page": 0.5})
		and not Video.valid_timing({"frame_start": 1.0}), "Reject invalid hardware checkpoints")
	check(Video.valid_timing({"frame_start": -0.013, "page": 1}), "Accept a mid-scanout checkpoint")
	check(Video.valid_timing(JSON.parse_string('{"page":1}')), "JSON numeric pages are valid")
	var video = Video.new()
	var red := solid(Color.RED)
	var blue := solid(Color.BLUE)
	video.reset(red)
	video.write_page(0.001, 1, blue)
	video.select_page(0.001, 1)
	blue.fill(Color.GREEN) # Submissions own their pixels.
	video.advance(0.0128)
	check(video.image().get_pixel(0, 0) == Color.RED, "Page select must wait for latch and scanout")
	video.advance(video.period + 0.0128)
	check(video.image().get_pixel(0, 0) == Color.BLUE, "Completed scanout uses the latched owned page")
	var returned: Image = video.image()
	returned.fill(Color.WHITE)
	check(video.image().get_pixel(0, 0) == Color.BLUE, "Consumers cannot mutate completed video")

	video.reset(red)
	video.write_page(0.010, 0, solid(Color.BLUE))
	video.advance(0.0128)
	check(video.image().get_pixel(0, 149) == Color.RED and video.image().get_pixel(0, 150) == Color.BLUE,
		"A write between chunks must mix two renders at row 150")
	var partitioned = Video.new()
	partitioned.reset(red)
	partitioned.write_page(0.010, 0, solid(Color.BLUE))
	for time in [0.002, 0.004, 0.008, 0.010, 0.0128]:
		partitioned.advance(time)
	check(partitioned.image().get_data() == video.image().get_data(), "Host call frequency cannot change video timing")
	print("WR1 video clock: %d checks, %d failures" % [checks, failures])
	quit(1 if failures else 0)
