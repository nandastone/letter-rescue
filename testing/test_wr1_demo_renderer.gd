extends "res://testing/test_wr1_hardware.gd"
## A scenic demo draw exercises empty animated tiles, text and complete world work.
func _initialize() -> void:
	var raw := FileAccess.get_file_as_bytes("res://testing/fixtures/wr1_demo13_recap_renderer.json.gz")
	var fixture: Dictionary = JSON.parse_string(raw.decompress_dynamic(16*1024*1024,FileAccess.COMPRESSION_GZIP).get_string_from_utf8())
	var r: Dictionary = fixture.entry
	var work = preload("res://scripts/wr1_renderer_work.gd").new()
	work.configure()
	var result: Dictionary = work.complete(r.renderer_prefix,r,r.renderer_background,r.renderer_tiles,r.renderer_doors,
		r.renderer_matching,r.renderer_player,r.renderer_actors,r.actor_images,r.renderer_tail)
	var hardware = preload("res://scripts/wr1_hardware.gd").new()
	hardware.configure(r,fixture.event_names)
	hardware.run_driver(result.work)
	compare(roundi(hardware.observed_time()*27000),roundi(float(fixture.expected.pic_ms)*27000),"renderer return cycle")
	compare(hardware.snapshot(),fixture.expected,"renderer hardware")
	compare(result.state,fixture.expected.renderer_prefix,"renderer prefix")
	compare(result.graphics_state,fixture.expected.graphics_state,"renderer graphics")
	print("Demo renderer: %d checks, %d failures" % [checks,failures])
	quit(1 if failures else 0)
