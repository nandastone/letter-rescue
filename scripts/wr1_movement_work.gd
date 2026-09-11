extends "res://scripts/wr1_graphics_work.gd"
## Source-derived movement, animation and speaker work before contact processing.
## Native fixture checks cover state and timing independently of this planner.
var tables: Dictionary
var state: Dictionary
var attributes: Array

func configure() -> void:
	span_cache.clear()
	var catalogue: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://assets/audio/original/driver_work.json"))
	instructions = catalogue.movement_instructions
	tables = catalogue.movement_tables
	for key in tables:
		for i in range(tables[key].size()):
			tables[key][i] = int(tables[key][i])

func signed(value: int) -> int:
	return (((value + 32768) & 65535) - 32768)

func attr(x: int, y: int) -> int:
	if (not ((0 <= x and x < self.attributes.size())) or not ((0 <= y and y < self.attributes[x].size()))):
		assert(false, 'Original movement read outside the captured attribute map')
	return int(self.attributes[x][y])

func add(key: String, value: int) -> void:
	self.state[key] = signed((self.state[key] + value))

func sound_is(offset: int) -> bool:
	var s = self.state
	return ((s['speaker_segment'] == s['data_segment']) and (s['speaker_offset'] == offset))

func pose(index: int) -> void:
	var facing = self.state['facing']
	if (facing not in [0, 1]):
		assert(false, 'Invalid movement facing')
	self.state['sprite'] = self.tables['poses'][((4 * facing) + index)]

func step(initial: Dictionary, attributes: Array, admission_ax: int = 0) -> Dictionary:
	if (admission_ax != 0):
		assert(false, 'Ordinary admission must have AX=0')
	self.path = []
	self.state = initial.duplicate(true)
	for key in self.state:
		self.state[key] = int(self.state[key])
	self.attributes = attributes
	var s = self.state
	s.merge({'timer':0, 'previous_x':s['x'], 'previous_y':s['y'], 'support':0}, true)
	self._span(0x37a4, 0x37b8)
	if (s['sprite'] == 9):
		self._span(0x37ba, 0x37ba)
		s['sprite'] = 0
	self._span(0x37c0, 0x37dc)
	var support = self.attr((s['gx'] + 1), s['gy'])
	if (support != 0x73):
		self._span(0x37de, 0x37f0)
	if (support in [0x73, 0x74]):
		s['support'] = support
		self._span(0x37f2, 0x3816)
		if (s['speaker_segment'] == s['data_segment']):
			self._span(0x3818, 0x381a)
		var stop = self.sound_is(0x4f6)
		if not (stop):
			self._span(0x381c, 0x382a)
			if (s['speaker_segment'] == s['data_segment']):
				self._span(0x382c, 0x382e)
			stop = self.sound_is(0x526)
		if stop:
			self._span(0x3830, 0x383a)
			s['speaker_index'] = -(1)
		self._span(0x383c, 0x3841)
		if s['recap_pending']:
			assert(false, 'Modal recap interrupts movement')
	self._span(0x384b, 0x3850)
	if s['up']:
		self.up()
	else:
		self._span(0x3852, 0x3852)
		self.down()
	self._span(0x3af1, 0x3afb)
	self.add('phase', 1)
	if (s['phase'] >= 17):
		self._span(0x3afd, 0x3afd)
		s['phase'] = 16
	self.idle()
	self.horizontal()
	self.footstep_exit()
	return {"work":self.path, "state":s}

func up() -> void:
	var s = self.state
	s['idle_ticks'] = 0
	self._span(0x3855, 0x385e)
	var climbing = false
	if (s['support'] == 0x74):
		self._span(0x3860, 0x3878)
		climbing = (self.attr((s['gx'] + 1), (s['gy'] - 2)) == 0x74)
	if not (climbing):
		self._span(0x387a, 0x3890)
		if (self.attr((s['gx'] + 1), (s['gy'] - 1)) == 0x74):
			self._span(0x3892, 0x38aa)
			climbing = (self.attr((s['gx'] + 1), (s['gy'] - 3)) == 0x74)
	if climbing:
		self._span(0x38ac, 0x38b1)
		if (s['sprite'] == 22):
			self._span(0x38b3, 0x38b9)
			s['sprite'] = 23
		else:
			self._span(0x38bb, 0x38bb)
			s['sprite'] = 22
		self._span(0x38c1, 0x38d3)
		s.merge({'phase':0, 'speaker_index':-(1)}, true)
	else:
		self._span(0x38d5, 0x38d9)
		if s['support']:
			self._span(0x38db, 0x38f9)
			self.pose(0)
			s['phase'] = 0
		else:
			self._span(0x38fb, 0x3900)
			if (s['phase'] < 9):
				self._span(0x3902, 0x391b)
				self.pose(1)
			else:
				self._span(0x391d, 0x3933)
				self.pose(3)
	self._span(0x3936, 0x393b)
	if (s['phase'] < 9):
		self._span(0x3940, 0x3945)
		if (s['speaker_index'] < 0):
			self._span(0x3947, 0x394c)
			if (s['sprite'] < 22):
				self._span(0x394e, 0x3953)
				if (s['phase'] == 0):
					self._span(0x3955, 0x395a)
					if s['sound_mode']:
						self._span(0x395c, 0x3966)
						s.merge({'speaker_segment':s['data_segment'], 'speaker_offset':0x4f6, 'speaker_index':0}, true)
		self._span(0x396c, 0x397b)
		self.add('y', -(8))
		self.add('gy', -(1))
		var col = s['gx']
		while true:
			self._span(0x39b0, 0x39b9)
			if not ((signed((s['gx'] + 3)) > col)):
				self._span(0x39bb, 0x39bb)
				break
			self._span(0x397d, 0x3993)
			if (self.attr(col, (s['gy'] - 4)) == 0x73):
				self._span(0x3995, 0x399f)
				self.add('y', 8)
				if (s['phase'] < 9):
					self._span(0x39a4, 0x39aa)
					s['phase'] = 16
				else:
					self._span(0x39a1, 0x39a1)
				self._span(0x3aed, 0x3aed)
				self.add('gy', 1)
				break
			self._span(0x39ad, 0x39ad)
			col = signed((col + 1))
	else:
		self._span(0x393d, 0x393d)
		self._span(0x39be, 0x39c3)
		self._span(0x39c8, 0x39ea)
		self.add('y', 8)
		self.add('gy', 1)
		self.pose(3)

func down() -> void:
	var s = self.state
	self._span(0x39ed, 0x39fb)
	if (s['speaker_segment'] == s['data_segment']):
		self._span(0x39fd, 0x39ff)
	if self.sound_is(0x4f6):
		self._span(0x3a01, 0x3a0b)
		s['speaker_index'] = -(1)
	self._span(0x3a0d, 0x3a11)
	if s['support']:
		self._span(0x3a13, 0x3a18)
		if not (s['down']):
			self._span(0x3a1a, 0x3a1a)
			return
		self._span(0x3a1d, 0x3a21)
		if (s['support'] != 0x74):
			self._span(0x3a23, 0x3a23)
			return
	self._span(0x3a26, 0x3a2a)
	var climbing = (s['support'] == 0x74)
	if not (climbing):
		self._span(0x3a2c, 0x3a42)
		climbing = (self.attr((s['gx'] + 1), (s['gy'] + 1)) == 0x74)
	if climbing:
		self._span(0x3a44, 0x3a5a)
		climbing = (self.attr((s['gx'] + 1), (s['gy'] - 1)) == 0x74)
		if not (climbing):
			self._span(0x3a5c, 0x3a74)
			climbing = (self.attr((s['gx'] + 1), (s['gy'] - 2)) == 0x74)
	if climbing:
		self._span(0x3a76, 0x3a7b)
		if (s['sprite'] == 22):
			self._span(0x3a7d, 0x3a83)
			s['sprite'] = 23
		else:
			self._span(0x3a85, 0x3a8b)
			s['sprite'] = 22
	else:
		self._span(0x3a8d, 0x3aa3)
		self.pose(3)
	self._span(0x3aa6, 0x3abb)
	if (self.attr(s['gx'], (s['gy'] - 1)) == 0x73):
		self._span(0x3abd, 0x3ac1)
		self.add('gx', 1)
		self.add('x', 8)
	self._span(0x3ac6, 0x3add)
	if (self.attr((s['gx'] + 2), (s['gy'] - 1)) == 0x73):
		self._span(0x3adf, 0x3ae3)
		self.add('gx', -(1))
		self.add('x', -(8))
	self._span(0x3ae8, 0x3aed)
	self.add('y', 8)
	self.add('gy', 1)

func idle() -> void:
	var s = self.state
	for item in [['left', 0x3b03, 0x3b08, 0x3b0a], ['right', 0x3b0d, 0x3b12, 0x3b14], ['up', 0x3b17, 0x3b1c, 0x3b1e], ['down', 0x3b21, 0x3b26, 0x3b28]]:
		var key = item[0]
		var start = item[1]
		var end = item[2]
		var skip = item[3]
		self._span(start, end)
		if s[key]:
			self._span(skip, skip)
			return
	self._span(0x3b2b, 0x3b34)
	self.add('idle_ticks', 1)
	if (s['idle_ticks'] > 17):
		self._span(0x3b36, 0x3b3b)
		if (s['sprite'] < 2):
			self._span(0x3b3d, 0x3b4b)
			s['idle_ticks'] = 0
			s['sprite'] ^= 1
			return
		self._span(0x3b4e, 0x3b53)
		if (s['sprite'] < 22):
			self._span(0x3b55, 0x3b60)
			s.merge({'sprite':0, 'idle_ticks':0}, true)
			return
		self._span(0x3b63, 0x3b68)
		if (s['sprite'] != 24):
			self._span(0x3b6a, 0x3b6f)
		if (s['sprite'] in [24, 25]):
			self._span(0x3b74, 0x3b8d)
			self.pose(2)
		else:
			self._span(0x3b71, 0x3b71)
		return
	self._span(0x3b90, 0x3b96)
	if ((s['sprite'] & 65535) <= 25):
		self._span(0x3b98, 0x3b9c)
		if (s['sprite'] in [0, 1, 11, 21, 22, 23]):
			return
		if (s['sprite'] in [10, 25]):
			self._span(0x3bd5, 0x3bd9)
			if s['support']:
				self._span(0x3bdb, 0x3be1)
				s['sprite'] = 9
			return
		if (s['sprite'] in [20, 24]):
			self._span(0x3be3, 0x3be7)
			if s['support']:
				self._span(0x3be9, 0x3bef)
				s['sprite'] = 19
			return
	self._span(0x3bf1, 0x3bf5)
	if (s['left_index'] > -(1)):
		self._span(0x3bf7, 0x3c07)
		s.merge({'left_index':0, 'right_index':-(1), 'sprite':12}, true)
	else:
		self._span(0x3c09, 0x3c0e)
		s.merge({'right_index':0, 'sprite':2}, true)

func horizontal() -> void:
	var s = self.state
	self._span(0x3c14, 0x3c19)
	if s['left']:
		self._span(0x3c1e, 0x3c33)
		s['idle_ticks'] = 0
		self.add('x', -(8))
		self.add('gx', -(1))
		var row = signed((s['gy'] - 4))
		while true:
			self._span(0x3c53, 0x3c57)
			if (row >= s['gy']):
				break
			self._span(0x3c35, 0x3c45)
			if (self.attr(s['gx'], row) == 0x73):
				self._span(0x3c47, 0x3c50)
				self.add('gx', 1)
				self.add('x', 8)
				break
			self._span(0x3c52, 0x3c52)
			row = signed((row + 1))
		self._span(0x3c59, 0x3c6d)
		s.merge({'facing':1, 'right_index':-(1)}, true)
		self.add('left_index', 1)
		if (s['left_index'] > 7):
			self._span(0x3c6f, 0x3c6f)
			s['left_index'] = 0
		self._span(0x3c74, 0x3c7b)
		if (s['previous_y'] == s['y']):
			self._span(0x3c7d, 0x3c82)
			if (s['sprite'] != 9):
				self._span(0x3c84, 0x3c8d)
				if not ((0 <= s['left_index'] and s['left_index'] < 8)):
					assert(false, 'Invalid left animation index')
				s['sprite'] = self.tables['left_walk'][s['left_index']]
	else:
		self._span(0x3c1b, 0x3c1b)
	self._span(0x3c90, 0x3c95)
	if s['right']:
		self._span(0x3c9a, 0x3caa)
		self.add('x', 8)
		self.add('gx', 1)
		var row = signed((s['gy'] - 4))
		while true:
			self._span(0x3cca, 0x3cce)
			if (row >= s['gy']):
				break
			self._span(0x3cac, 0x3cbe)
			if (self.attr((s['gx'] + 2), row) == 0x73):
				self._span(0x3cc0, 0x3cc4)
				self.add('gx', -(1))
				self.add('x', -(8))
			self._span(0x3cc9, 0x3cc9)
			row = signed((row + 1))
		self._span(0x3cd0, 0x3ce9)
		s.merge({'idle_ticks':0, 'facing':0, 'left_index':-(1)}, true)
		self.add('right_index', 1)
		if (s['right_index'] > 7):
			self._span(0x3ceb, 0x3ceb)
			s['right_index'] = 0
		self._span(0x3cf0, 0x3cf7)
		if (s['previous_y'] == s['y']):
			self._span(0x3cf9, 0x3cfe)
			if (s['sprite'] != 9):
				self._span(0x3d00, 0x3d09)
				if not ((0 <= s['right_index'] and s['right_index'] < 8)):
					assert(false, 'Invalid right animation index')
				s['sprite'] = self.tables['right_walk'][s['right_index']]
	else:
		self._span(0x3c97, 0x3c97)

func footstep_exit() -> void:
	var s = self.state
	for item in [[6, 0x3d0c, 0x3d11], [16, 0x3d13, 0x3d18], [3, 0x3d1a, 0x3d1f], [13, 0x3d21, 0x3d26]]:
		var frame = item[0]
		var start = item[1]
		var end = item[2]
		self._span(start, end)
		if (s['sprite'] == frame):
			break
	if (s['sprite'] in [6, 16, 3, 13]):
		self._span(0x3d28, 0x3d2d)
		if (s['speaker_index'] == -(1)):
			self._span(0x3d2f, 0x3d34)
			if s['sound_mode']:
				self._span(0x3d36, 0x3d40)
				s.merge({'speaker_segment':s['data_segment'], 'speaker_offset':0x4ea, 'speaker_index':0}, true)
	self._span(0x3d46, 0x3d4b)
	if s['door_state']:
		self._span(0x3d4d, 0x3d54)
		var at_door = (s['gx'] == s['door_x'])
		if not (at_door):
			self._span(0x3d56, 0x3d5e)
			at_door = (s['gx'] == signed((s['door_x'] - 1)))
		if at_door:
			self._span(0x3d60, 0x3d6a)
			if (s['gy'] == signed((s['door_y'] + 5))):
				self._span(0x3d6c, 0x3d6c)
				s['door_state'] = 2
	self._span(0x3d72, 0x3d79)
	if (s['gy'] >= s['map_height']):
		assert(false, 'Bottom-of-map death bypasses contacts')
