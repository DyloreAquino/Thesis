extends Node
class_name GeometryExporter

@export var world_scale: float = 0.01875 # agent shoulder-to-shoulder = 0.6m, 64 pixels each, 0.6/32
@export var walkable_area: Polygon2D
@export var entry_areas: Array[Polygon2D] = []
@export var exit_areas: Array[Polygon2D] = []
@export var sim_client: SimClient
@export var obstacles: Array[Polygon2D] =[]

func send_geometry() -> void:
	var message := {
		"cmd": "setup_geometry",
		"walkable_area": _polygon_to_scaled_points(walkable_area),
		"entry_areas": entry_areas.map(_polygon_to_scaled_points),
		"exit_areas": exit_areas.map(_polygon_to_scaled_points),
		"obstacles": obstacles.map(_polygon_to_scaled_points)
	}
	sim_client.send_message(JSON.stringify(message))

func _polygon_to_scaled_points(poly: Polygon2D) -> Array:
	var points := []
	for local_point in poly.polygon:
		var world_point: Vector2 = poly.to_global(local_point) * world_scale
		points.append([world_point.x, world_point.y])
	return points

func _on_fix_geometry_button_button_up():
	send_geometry()
