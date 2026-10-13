extends RefCounted
## Resident 3BA6: a shared 32-bit session stream.
var seed: int = 0
var initialized: bool = false

func reset(value: int) -> void:
	seed = value&0xffffffff
	initialized = true

func pick(maximum: int) -> int:
	if not initialized:
		var now = Time.get_time_dict_from_system()
		reset(int((now.hour*3600+now.minute*60+now.second)*1193181.0/65536.0))
	seed = (seed*214013+2531011)&0xffffffff
	return (seed>>16)%(maximum+1)
