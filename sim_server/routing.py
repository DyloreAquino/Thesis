import jupedsim as jps

from geometry import SceneGeometry
from queues import resample_path

# pipeline is: 
# exits -> switches -> parse to journey -> expand each switch to their targets ->
# build array with all journeys and init switch
def build_journeys(
    sim: jps.Simulation, scene: SceneGeometry
) -> tuple[list[tuple[int, int]], list[int]]:
    """Build the Godot-authored switch graph as one JuPedSim journey."""
    exit_ids = _build_exit_stages(sim, scene)
    queue_ids = _build_queue_stages(sim, scene)
    switch_stage_ids = {
        switch.switch_id: sim.add_waypoint_stage(
            switch.position, switch.radius
        )
        for switch in scene.switches.values()
    }

    journey = jps.JourneyDescription(
        [*switch_stage_ids.values(), *exit_ids, *queue_ids]
    )
    
    for switch in scene.switches.values():
        target_stage_ids = [switch_stage_ids[t] for t in switch.target_switch_ids]
        target_stage_ids.extend(queue_ids[i] for i in switch.target_queue_indices)
        target_stage_ids.extend(exit_ids[i] for i in switch.target_exit_indices)

        journey.set_transition_for_stage(
            switch_stage_ids[switch.switch_id],
            _build_transition(switch.transition, target_stage_ids),
        )
    
    for i, queue in enumerate(scene.queues):
        target_stage_ids = [switch_stage_ids[t] for t in queue.target_switch_ids]
        target_stage_ids.extend(exit_ids[j] for j in queue.target_exit_indices)
        journey.set_transition_for_stage(queue_ids[i], _build_transition(queue.transition, target_stage_ids))

    journey_id = sim.add_journey(journey)

    # Keep starts aligned with entry_areas: each entrance owns its starting stage.
    return [
        (journey_id, switch_stage_ids[switch_id])
        for switch_id in scene.entry_start_switch_ids
    ], queue_ids

# determine transition type from attrib
def _build_transition(
    transition_type: str, target_stage_ids: list[int]
) -> jps.Transition:
    if transition_type == "fixed":
        return jps.Transition.create_fixed_transition(target_stage_ids[0])
    if transition_type == "least_targeted":
        return jps.Transition.create_least_targeted_transition(target_stage_ids)
    if transition_type == "round_robin":
        return jps.Transition.create_round_robin_transition(
            [(stage_id, 1) for stage_id in target_stage_ids]
        )
    raise ValueError(f"Unknown transition type: {transition_type}")


def _build_exit_stages(
    sim: jps.Simulation, scene: SceneGeometry
) -> list[int]:
    return [
        sim.add_exit_stage(exit_area) for exit_area in scene.exit_areas
    ]

def _build_queue_stages(
    sim: jps.Simulation, scene: SceneGeometry
) -> list[int]:
    QUEUE_SPACING_METERS = 1.0
    return [
        sim.add_queue_stage(resample_path(list(queue.path), QUEUE_SPACING_METERS))
        for queue in scene.queues
    ]
