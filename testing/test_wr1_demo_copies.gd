extends "res://testing/test_wr1_hardware.gd"
## Byte-shifted HUD animation copies, including both traversal directions.
func _initialize() -> void:
	var raw := FileAccess.get_file_as_bytes("res://testing/fixtures/wr1_demo_hud_copies.json.gz")
	var fixture: Dictionary = JSON.parse_string(raw.decompress_dynamic(32*1024*1024,FileAccess.COMPRESSION_GZIP).get_string_from_utf8())
	var work = preload("res://scripts/wr1_graphics_work.gd").new()
	work.configure()
	var forward := 0
	var backward := 0
	for case in fixture.cases:
		var result: Dictionary = work.copy_rect(case.entry)
		var hardware = preload("res://scripts/wr1_hardware.gd").new()
		hardware.configure(case.entry,fixture.event_names)
		hardware.run_driver(result.work)
		compare(roundi(hardware.observed_time()*27000),roundi(float(case.expected.pic_ms)*27000),"HUD copy return cycle")
		compare(hardware.snapshot(),case.expected,"HUD copy hardware")
		compare(result.args,case.expected.args,"HUD clipped copy")
		if result.return_ip == 0x13ef6: forward += 1
		if result.return_ip == 0x1413d: backward += 1
	compare(forward > 0 and backward > 0,true,"Both EGA traversal directions covered")
	print("Demo HUD copies: %d forward, %d backward; %d checks, %d failures" % [forward,backward,checks,failures])
	quit(1 if failures else 0)
