@tool
extends Marker2D
class_name JourneySwitch

## Stable routing identifier. It must be non-empty and unique in the scene.
@export var switch_id: String = ""

## Distance in metres at which JuPedSim considers this waypoint reached.
@export_range(0.1, 10.0, 0.1) var radius_m: float = 0.5

## Switches that may be targeted after this switch is reached.
@export var target_switches: Array[JourneySwitch] = []

## Exit polygons that may be targeted after this switch is reached.
@export var target_exits: Array[Polygon2D] = []

## Types of switch modes
@export_enum(
	"fixed",
	"round_robin",
	"least_targeted"
) var transition_type: String = "fixed"
