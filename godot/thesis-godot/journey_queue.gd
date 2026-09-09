@tool
extends Line2D
class_name JourneyQueue

@export var target_switches: Array[JourneySwitch] = []
@export var target_exits: Array[Polygon2D] = []
@export_enum(
	"fixed",
	"round_robin",
	"least_targeted"
) var transition_type: String = "fixed"
@export var release_interval_seconds: float = 10.0
