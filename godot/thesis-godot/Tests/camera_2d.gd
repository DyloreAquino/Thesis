extends Camera2D

@export_group("Zoom Controls")
@export var zoom_speed: float = 0.1
@export var min_zoom: float = 0.2
@export var max_zoom: float = 5.0
@export var zoom_smoothness: float = 15.0

@export_group("Pan Controls")
@export var pan_button: MouseButton = MOUSE_BUTTON_LEFT

var target_zoom: Vector2 = Vector2.ONE
var is_panning: bool = false

func _ready() -> void:
	target_zoom = zoom

func _input(event: InputEvent) -> void:
	# Pan toggle
	if event is InputEventMouseButton:
		if event.button_index == pan_button:
			is_panning = event.pressed

		# Mouse wheel zoom
		if event.pressed:
			if event.button_index == MOUSE_BUTTON_WHEEL_UP:
				_zoom_camera(1.0 + zoom_speed)
			elif event.button_index == MOUSE_BUTTON_WHEEL_DOWN:
				_zoom_camera(1.0 - zoom_speed)

	# Mouse drag pan
	elif event is InputEventMouseMotion and is_panning:
		position -= event.relative / zoom

func _process(delta: float) -> void:
	zoom = zoom.lerp(target_zoom, zoom_smoothness * delta)

func _zoom_camera(factor: float) -> void:
	var old_zoom = target_zoom
	var new_zoom = (target_zoom * factor).clamp(Vector2(min_zoom, min_zoom), Vector2(max_zoom, max_zoom))
	
	if new_zoom != old_zoom:
		# Shift camera position so zoom focuses on the mouse position
		var actual_factor = new_zoom.x / old_zoom.x
		position += (get_global_mouse_position() - global_position) * (1.0 - 1.0 / actual_factor)
		target_zoom = new_zoom
