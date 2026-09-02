extends Control
class_name ResizeHandle

@export var target: StatChart       # assign the StatChart/TauPlot node itself
@export var min_size := Vector2(220, 160)

func _ready() -> void:
	mouse_default_cursor_shape = Control.CURSOR_FDIAGSIZE
	mouse_filter = Control.MOUSE_FILTER_STOP  # eat the drag, don't let the plot's hover system grab it

var _dragging := false

func _gui_input(event: InputEvent) -> void:
	if event is InputEventMouseButton and event.button_index == MOUSE_BUTTON_LEFT:
		_dragging = event.pressed
		accept_event()
	elif event is InputEventMouseMotion and _dragging:
		var new_size: Vector2 = (target.size + event.relative).max(min_size)
		target.custom_minimum_size = new_size
		target.size = new_size
		accept_event()

func _on_resized():
	target.queue_refresh()
