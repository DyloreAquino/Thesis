extends Node
class_name StatisticsManager

@export var density_chart: StatChart

var _elapsed_time: float = 0.0
var _charts: Dictionary[String, StatChart]:
	get:
		return {
			"density": density_chart,
		}

func apply_snapshot(stats_data: Dictionary, delta_time: float) -> void:
	_elapsed_time += delta_time
	for stat_key in stats_data:
		var chart: StatChart = _charts.get(stat_key)
		if chart == null:
			push_warning("StatisticsManager: no chart wired up for stats key '%s'" % stat_key)
			continue
		chart.record(_elapsed_time, stats_data[stat_key])
