extends Node
class_name GeometryExporter

@export var world_scale: float = 0.01875 # agent shoulder-to-shoulder = 0.6m, 64 pixels each, 0.6/32
@export var walkable_area: Polygon2D
@export var entry_areas: Array[Polygon2D] = []
@export var exit_areas: Array[Polygon2D] = []
@export var obstacles: Array[Polygon2D] = []
@export var switches: Array[JourneySwitch] = []
@export var initial_switch: JourneySwitch
@export var sim_client: SimClient

func send_geometry() -> void:
	var message := {
		"cmd": "setup_geometry",
		"walkable_area": _polygon_to_scaled_points(walkable_area),
		"entry_areas": entry_areas.map(_polygon_to_scaled_points),
		"exit_areas": exit_areas.map(_polygon_to_scaled_points),
		"obstacles": obstacles.map(_polygon_to_scaled_points),
		"switches": switches.map(_switch_to_message),
		"initial_switch_id": initial_switch.switch_id if initial_switch else ""
	}
	sim_client.send_message(JSON.stringify(message))

func _polygon_to_scaled_points(poly: Polygon2D) -> Array:
	var points := []
	for local_point in poly.polygon:
		var world_point: Vector2 = poly.to_global(local_point) * world_scale
		points.append([world_point.x, world_point.y])
	return points
	
## parse the switch attribs of each switch into JSON
func _switch_to_message(journey_switch: JourneySwitch) -> Dictionary:
	var world_point := journey_switch.global_position * world_scale
	var target_switch_ids: Array[String] = []
	var target_exit_indices: Array[int] = []

	for target_switch in journey_switch.target_switches:
		target_switch_ids.append(target_switch.switch_id)

	for target_exit in journey_switch.target_exits:
		var exit_index := exit_areas.find(target_exit)
		if exit_index < 0:
			push_error(
				"Switch '%s' targets an exit not registered in exit_areas"
				% journey_switch.switch_id
			)
			continue
		target_exit_indices.append(exit_index)

	return {
		"id": journey_switch.switch_id,
		"position": [world_point.x, world_point.y],
		"radius": journey_switch.radius_m,
		"target_switch_ids": target_switch_ids,
		"target_exit_indices": target_exit_indices,
		"transition": journey_switch.transition_type
	}

func _on_fix_geometry_button_button_up():
	send_geometry()
