import random

import jupedsim as jps
from numpy.random import normal
from shapely import Polygon

MEAN_DESIRED_SPEED = 1.34   # m/s, standard pedestrian walking speed
SPEED_STD_DEV = 0.2
SPAWN_POSITION_ATTEMPTS = 20

def spawn_random_agent(sim: jps.Simulation, entry_areas: list[Polygon], journey_starts: list[tuple[int, int]]) -> bool:
    """Choose an entrance and use that entrance's assigned journey start."""
    if len(entry_areas) != len(journey_starts):
        raise ValueError("Each entry area must have exactly one journey start")
    for _ in range(SPAWN_POSITION_ATTEMPTS):
        entry_index = random.randrange(len(entry_areas))
        entry_area = entry_areas[entry_index]
        try:
            positions = jps.distribute_by_number(
                polygon=entry_area,
                number_of_agents=1,
                distance_to_agents=1.0,
                distance_to_polygon=0.2,
                seed=random.randrange(2**32),
            )
        except RuntimeError:
            # This entry may be too small to produce a valid position.
            continue
        if not positions:
            continue

        journey_id, initial_stage_id = journey_starts[entry_index]
        desired_speed = max(
            0.1, float(normal(MEAN_DESIRED_SPEED, SPEED_STD_DEV))
        )
        try:
            sim.add_agent(
                jps.AnticipationVelocityModelAgentParameters(
                    journey_id=journey_id,
                    stage_id=initial_stage_id,
                    position=positions[0],
                    desired_speed=desired_speed,
                    # Keep body-radius clearance without an extra wall buffer:
                    # the station's narrow lanes otherwise leave agents stalled.
                    wall_buffer_distance=0.0,
                )
            )
            return True
        except RuntimeError:
            # The candidate can be too close to an agent already occupying
            # the entry. Try another random position instead.
            continue

    return False
