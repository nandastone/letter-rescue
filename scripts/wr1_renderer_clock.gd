extends RefCounted
## One renderer checkpoint through display selection and ordinary idle admission.
## IRQs during rendering/display and death/exit transitions remain boundaries.

var idle = preload("res://scripts/wr1_idle_clock.gd").new()
var checkpoints := {}
var result: Dictionary
var display_state: Dictionary

func configure(cmf: PackedByteArray, initial: Dictionary, names: Dictionary) -> void:
	idle.configure(cmf, initial, names)
	checkpoints = {}

func _checkpoint(name: String) -> void:
	checkpoints[name] = {"hardware":idle.hardware.snapshot(), "cycle":roundi(idle.hardware.observed_time() * 27000.0)}

func _work(path: Array) -> void:
	assert(not idle.hardware.interrupts.irq_check, "Renderer/display IRQ preemption")
	idle.hardware.run_driver(path)
	# This path never acknowledges a PIC interrupt, so any newly pending IRQ
	# stays visible. Never silently report an interrupted renderer as exact.
	assert(not idle.hardware.interrupts.irq_check, "Renderer/display IRQ preemption")

func finish_render(render: Dictionary, post: Dictionary, initial_display: Dictionary, return_cs: int) -> void:
	assert(not render.tail.death and int(post.door_state) != 2, "Death/exit transition after renderer")
	var renderer = preload("res://scripts/wr1_renderer_work.gd").new()
	renderer.configure()
	result = renderer.complete(render.initial_prefix, render.graphics, render.background, render.tiles,
		render.doors, render.matching, render.player, render.actors, render.actor_images, render.tail)
	_work(result.work)
	_checkpoint("renderer_return")
	var work = preload("res://scripts/wr1_graphics_work.gd").new()
	work.configure()
	work._span(0xc1a9, 0xc1a9)
	work._span(0x3da3, 0x3daa)
	work._span(0x409b, 0x409f)
	_work(work.path)
	_checkpoint("display_entry")
	var initial: Dictionary = render.graphics.duplicate(true)
	initial.graphics_state = result.graphics_state
	initial.display_state = initial_display
	initial.args = [result.state.render_page]
	var display: Dictionary = work.display_page(initial)
	_work(display.work)
	display_state = display.state
	_checkpoint("display_return")
	work.path = []
	work._span(0x17695, 0x17695)
	work._span(0x40a4, 0x40a4)
	work._span(0x40b1, 0x40b6)
	work._span(0x40cf, 0x40cf)
	_work(work.path)
	_checkpoint("update_done")
	idle.pc = 0x40d2
	idle.cs = return_cs
	idle.ax = 0
	idle.carry = false
	idle.zero = ((int(post.iteration) + 1) & 65535) == 0

func until_admission(input_events: Array = []) -> int:
	assert(checkpoints.has("update_done"), "Rendering has not completed")
	return idle.until_admission(2000000, input_events)

