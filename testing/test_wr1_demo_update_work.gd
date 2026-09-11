extends "res://testing/test_wr1_hardware.gd"
## Each stage uses its own native entry state; this is a work-cost diagnostic.
var path: Array
var instructions: Dictionary
func span(a: int,b: int) -> void:
	while a<=b:
		var i: Array = instructions[str(a)]
		path.append([i[0],a]);a=int(i[1])
func _initialize() -> void:
	var raw := FileAccess.get_file_as_bytes("res://testing/fixtures/wr1_demo_update_work.json.gz")
	var fixture: Dictionary = JSON.parse_string(raw.decompress_dynamic(16*1024*1024,FileAccess.COMPRESSION_GZIP).get_string_from_utf8())
	instructions = fixture.instructions
	var cases: Array = fixture.cases
	for case in cases:
		var move=preload("res://scripts/legacy/wr1_movement_work.gd").new();move.configure()
		var contact=preload("res://scripts/legacy/wr1_contact_work.gd").new();contact.configure()
		var world=preload("res://scripts/legacy/wr1_renderer_work.gd").new();world.configure()
		var graphics=preload("res://scripts/legacy/wr1_graphics_work.gd").new();graphics.configure()
		var cpu=preload("res://scripts/legacy/wr1_hardware.gd").new();cpu.configure(case.begin,case.names)
		var movement: Dictionary=move.step(case.begin.movement,case.begin.movement_attributes)
		path=movement.work
		span(0x3d7e,0x3d7e)
		var c: Dictionary=case.contact
		var touched: Dictionary=contact.body(c.contact,c.contact_attributes,c)
		path.append_array(touched.work);path.append(["retf",0xc6f8])
		span(0x3d83,0x3d8a)
		if movement.state.y==movement.state.previous_y:
			span(0x3d8c,0x3d91)
			if movement.state.speaker_index == -1:span(0x3d93,0x3d97)
		span(0x3d99,0x3d99)
		span(0x50e8,0x50ff);span(0x23f5f,0x23f6f);span(0x5104,0x510d)
		span(0x5309,0x530b);span(0x53bd,0x53c1);span(0x53c6,0x53c8)
		var w: Dictionary=case.world
		for enemy in w.renderer_actors.enemies:
			span(0x5853,0x5859);span(0x53cb,0x53dc)
			assert(enemy.state == -1)
			var cx: int=w.renderer_prefix.camera_x;var cy: int=w.renderer_prefix.camera_y
			var hidden:=false
			for branch in [[0x5407,0x5418,enemy.x<=cx-2],[0x541a,0x542b,enemy.x>=cx+35],[0x542d,0x543e,enemy.y<=cy-2],[0x5440,0x5451,enemy.y>cy+19]]:
				span(branch[0],branch[1])
				if branch[2]:hidden=true;break
			assert(hidden)
			span(0x5456,0x5461);span(0x5852,0x5852)
		span(0x5853,0x5857);span(0x585c,0x5861)
		span(0x3d9e,0x3d9e)
		var rendered: Dictionary=world.complete(w.renderer_prefix,w,w.renderer_background,w.renderer_tiles,w.renderer_doors,w.renderer_matching,w.renderer_player,w.renderer_actors,w.actor_images,w.renderer_tail)
		path.append_array(rendered.work);path.append(["retf",0xc1a9])
		span(0x3da3,0x3daa);span(0x409b,0x409f)
		var device: Dictionary=w.duplicate(true);device.args=[rendered.state.render_page];device.graphics_state=rendered.graphics_state
		path.append_array(graphics.display_page(device).work);path.append(["retf",0x17695])
		span(0x40a4,0x40a4);span(0x40b1,0x40b6);span(0x40cf,0x40cf)
		cpu.run_driver(path)
		compare(roundi(cpu.observed_time()*27000),roundi(float(case.expected.pic_ms)*27000),"demo update CPU cycle")
		compare(cpu.snapshot(),case.expected,"demo update hardware")
		_check_idle(case,cpu)
	compare(cases.size(),3,"native timing windows")
	print("Demo per-stage update work: %d checks, %d failures" % [checks,failures])
	quit(1 if failures else 0)

func _check_idle(case: Dictionary, completed_cpu: RefCounted) -> void:
	# Continue from the hardware result computed above, not the native end
	# checkpoint. These cases have no IRQ or speaker transition during main.
	var checkpoint: Dictionary = case.idle_checkpoint.duplicate(true)
	checkpoint.initial = case.begin.duplicate(true)
	checkpoint.initial.merge(completed_cpu.snapshot(),true)
	checkpoint.initial.pic_ms = completed_cpu.observed_time()
	checkpoint.initial.cpu_cs = case.begin.cs
	checkpoint.initial.cpu_ip = 0xd72
	checkpoint.initial.clock_state.timer = 0
	assert(int(checkpoint.initial.clock_state.speaker_index) == -1)
	var clock = preload("res://scripts/legacy/wr1_music_clock.gd").new()
	clock.configure(checkpoint)
	var idle = clock.idle
	var cpu = idle.hardware
	while true:
		if cpu.pending == 0:
			cpu.begin_block()
			if cpu.interrupts.irq_check:
				idle._interrupt()
				continue
		if idle.pc == 0x371b and int(idle.game.timer) >= 8:
			cpu.run_driver(clock.dispatch)
			break
		if idle.pc == 0x34ba and cpu.pending == 0 and int(idle.game.timer) < 8:
			@warning_ignore("integer_division")
			var loops: int = (cpu.cycles - 1) / idle.loop_cost
			if loops > 0:
				cpu.cycles -= loops * idle.loop_cost
				idle.ax = int(idle.game.timer)
				idle.carry = true
				idle.zero = false
		var op: String = idle._instruction()
		cpu.pending += 1
		if op.begins_with("j") or cpu.pending == 32:
			cpu.end_block(cpu.pending)
			cpu.pending = 0
	compare(roundi(cpu.observed_time()*27000),roundi(float(case.next_admission.pic_ms)*27000),"local admission CPU cycle")
