extends Node
class_name GeometryExporter

@export var world_scale: float = 0.01875 # agent shoulder-to-shoulder = 0.6m, 64 pixels each, 0.6/32
@export var walkable_area: Polygon2D
@export var entry_areas: Array[Polygon2D] = []
@export var exit_areas: Array[Polygon2D] = []
@export var obstacles: Array[Polygon2D] = []
@export var switches: Array[JourneySwitch] = []
@export var initial_switch: JourneySwitch
@export var queues: Array[JourneyQueue] = []
@export var sim_client: SimClient

func send_geometry() -> void:
	var message := {
		"cmd": "setup_geometry",
		"walkable_area": _polygon_to_scaled_points(walkable_area),
		"entry_areas": entry_areas.map(_entry_to_message),
		"exit_areas": exit_areas.map(_polygon_to_scaled_points),
		"obstacles": obstacles.map(_polygon_to_scaled_points),
		"switches": switches.map(_switch_to_message),
		"initial_switch_id": initial_switch.switch_id if initial_switch else "",
		"queues": queues.map(_queue_to_message).filter(func(q): return not q.is_empty()),
	}
	sim_client.send_message(JSON.stringify(message))

func _entry_to_message(entry: Polygon2D) -> Dictionary:
	var start: JourneySwitch = initial_switch
	if entry is JourneyEntry and entry.starting_switch != null:
		start = entry.starting_switch
	return {
		"polygon": _polygon_to_scaled_points(entry),
		"starting_switch_id": start.switch_id if start else "",
	}

func _polygon_to_scaled_points(poly: Polygon2D) -> Array:
	var points := []
	for local_point in poly.polygon:
		var world_point: Vector2 = poly.to_global(local_point) * world_scale
		points.append([world_point.x, world_point.y])
	return points

func _line_to_scaled_points(line: Line2D) -> Array:
	var points := []
	for local_point in line.points:
		var world_point: Vector2 = line.to_global(local_point) * world_scale
		points.append([world_point.x, world_point.y])
	return points

## parse the switch attribs of each switch into JSON
func _switch_to_message(journey_switch: JourneySwitch) -> Dictionary:
	var world_point := journey_switch.global_position * world_scale
	var target_switch_ids: Array[String] = []
	var target_exit_indices: Array[int] = []
	var target_queue_indices: Array[int] = []

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
	
	for target_queue in journey_switch.target_queues:
		var queue_index := queues.find(target_queue)
		if queue_index < 0:
			push_error(
				"Switch '%s' targets a queue not registered in queues"
				% journey_switch.switch_id
			)
			continue
		target_queue_indices.append(queue_index)
	
	return {
		"id": journey_switch.switch_id,
		"position": [world_point.x, world_point.y],
		"radius": journey_switch.radius_m,
		"target_switch_ids": target_switch_ids,
		"target_exit_indices": target_exit_indices,
		"transition": journey_switch.transition_type,
		"target_queue_indices": target_queue_indices
	}

func _queue_to_message(journey_queue: JourneyQueue) -> Dictionary:
	var target_switch_ids: Array[String] = []
	var target_exit_indices: Array[int] = []
	for target_switch in journey_queue.target_switches:
		target_switch_ids.append(target_switch.switch_id)

	for target_exit in journey_queue.target_exits:
		var exit_index := exit_areas.find(target_exit)
		if exit_index < 0:
			push_error("Queue '%s' targets an exit not registered in exit_areas" % journey_queue.name)
			continue
		target_exit_indices.append(exit_index)

	return {
		"path": _line_to_scaled_points(journey_queue),
		"release_interval_seconds": journey_queue.release_interval_seconds,
		"target_switch_ids": target_switch_ids,
		"target_exit_indices": target_exit_indices,
		"transition": journey_queue.transition_type,
	}

func _on_fix_geometry_button_button_up():
	send_geometry()
