import jupedsim as jps
from geometry import SceneGeometry

def build_exit_journeys(sim: jps.Simulation, scene: SceneGeometry) -> list[tuple[int, int]]:
    """Build one single-stage journey for every exit defined in Godot.

    Args:
        scene (SceneGeometry): the SceneGeometry object, taken from Godot scenes

    Returns:
        list[tuple[int, int]]: A list of journey ids and exit ids
    """
    journeys = []
    for exit_area in scene.exit_areas:
        exit_id = sim.add_exit_stage(exit_area.exterior.coords[:-1]) # type: ignore
        journey_id = sim.add_journey(jps.JourneyDescription([exit_id]))
        journeys.append((journey_id, exit_id))
    return journeys