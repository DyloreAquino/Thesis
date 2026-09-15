@tool
extends Polygon2D
class_name JourneyEntry

## Agents spawned here begin at this switch. Empty uses GeometryExporter's initial switch.
@export var starting_switch: JourneySwitch
