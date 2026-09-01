import jupedsim as jps
from geometry import SceneGeometry

def build_journeys(sim: jps.Simulation, 
                   scene: SceneGeometry,
                   switch_position: tuple[float, float],
                   switch_radius: float):
    exit_ids = _build_exit_stages(sim, scene)
    
    switch_id = sim.add_waypoint_stage(
        switch_position,
        switch_radius,
    )
    
    journey = jps.JourneyDescription([
        switch_id,
        *exit_ids # spread exit ids
    ])
    
    journey.set_transition_for_stage(switch_id, jps.Transition.create_least_targeted_transition(exit_ids))
    journey_id = sim.add_journey(journey)
    
    return [(journey_id, switch_id)]

def _build_exit_stages(sim: jps.Simulation, scene: SceneGeometry) -> list[int]:
    exit_ids = [
        sim.add_exit_stage(exit_area) for exit_area in scene.exit_areas
    ]
    
    return exit_ids
    # journey_id = sim.add_journey(jps.JourneyDescription([exit_id]))
    # journeys.append((journey_id, exit_id))
