extends TauPlot
class_name StatChart

@export var series_name: String = "Value"
@export var y_axis_title: String = ""
@export var buffer_size: int = 300

var _dataset: TauPlot.Dataset
var _series_id: int

func _ready() -> void:
	_dataset = TauPlot.Dataset.new(
		TauPlot.Dataset.Mode.SHARED_X,
		TauPlot.Dataset.XElementType.NUMERIC,
		buffer_size
	)
	_series_id = _dataset.add_series(series_name)

	var x_axis := TauAxisConfig.new()
	x_axis.title = "Time (s)"
	x_axis.include_zero_in_domain = false
	x_axis.domain_padding_mode = TauAxisConfig.DomainPaddingMode.DATA_UNITS
	x_axis.domain_padding_max = 1.0

	var y_axis := TauAxisConfig.new()
	y_axis.title = y_axis_title

	var line_cfg := TauLineConfig.new()

	var pane := TauPaneConfig.new()
	pane.y_left_axis = y_axis
	pane.overlays = [line_cfg]

	var config := TauXYConfig.new()
	config.x_axis = x_axis
	config.panes = [pane]

	var binding := TauXYSeriesBinding.new()
	binding.series_id = _series_id
	binding.pane_index = 0
	binding.overlay_type = TauXYSeriesBinding.PaneOverlayType.LINE
	binding.y_axis_id = TauPlot.AxisId.LEFT

	title = series_name
	plot_xy(_dataset, config, [binding])

func record(x_value: float, y_value: float) -> void:
	_dataset.append_shared_sample(x_value, PackedFloat64Array([y_value]))
