extends Node2D
class_name Agent

var start_pos: Vector2
var target_pos: Vector2
var interval: float = 0.1
var t: float = 0.0

func set_target_position(new_target: Vector2, interval: float) -> void:
	start_pos = global_position
	target_pos = new_target
	self.interval = max(interval, 0.001)
	t = 0.0

func _process(delta: float) -> void:
	if t >= interval:
		return
	t += delta
	var progress = clamp(t / interval, 0.0, 1.0)
	global_position = start_pos.lerp(target_pos, progress)
	var movement := target_pos - start_pos
	if movement.length() > 0.001:
		rotation = movement.angle()
