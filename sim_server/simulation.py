"""Owns the JuPedSim Simulation, agent spawning and journey setup."""

import pathlib
import random

import jupedsim as jps
from geometry import SceneGeometry
from numpy.random import normal

MEAN_DESIRED_SPEED = 1.34   # m/s, standard pedestrian walking speed
SPEED_STD_DEV = 0.2
MIN_SPAWN_INTERVAL = 0.5     # simulated seconds
MAX_SPAWN_INTERVAL = 2.0
SPAWN_POSITION_ATTEMPTS = 20

class CrowdSimulation:
    def __init__(self, 
                 scene: SceneGeometry, 
                 trajectory_file: str = "output.sqlite",
                 sim_parameters: dict = None):
        self.sim_parameters = sim_parameters or {}
        self.sim = jps.Simulation(
            model=jps.AnticipationVelocityModel(),
            geometry=scene.walkable_area,
            trajectory_writer=jps.SqliteTrajectoryWriter(
                output_file=pathlib.Path(trajectory_file)
            ),
        )
        self._entry_areas = scene.entry_areas
        self._exit_journeys = self._build_exit_journeys(scene)
        self._agents_left_to_spawn = max(
            0, int(self.sim_parameters.get("agent_count", 20))
        )
        self._next_spawn_time = random.uniform(
            MIN_SPAWN_INTERVAL, MAX_SPAWN_INTERVAL
        )

    def _build_exit_journeys(self, scene: SceneGeometry) -> list[tuple[int, int]]:
        """Build one single-stage journey for every exit defined in Godot.

        Args:
            scene (SceneGeometry): the SceneGeometry object, taken from Godot scenes

        Returns:
            list[tuple[int, int]]: A list of journey ids and exit ids
        """
        journeys = []
        for exit_area in scene.exit_areas:
            exit_id = self.sim.add_exit_stage(exit_area.exterior.coords[:-1])
            journey_id = self.sim.add_journey(jps.JourneyDescription([exit_id]))
            journeys.append((journey_id, exit_id))
        return journeys

    def _spawn_random_agent(self) -> bool:
        """Try to spawn one agent at a random entry with a random exit."""
        for _ in range(SPAWN_POSITION_ATTEMPTS):
            entry_area = random.choice(self._entry_areas)
            try:
                positions = jps.distributions.distribute_by_number(
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

            journey_id, exit_stage_id = random.choice(self._exit_journeys)
            desired_speed = max(
                0.1, float(normal(MEAN_DESIRED_SPEED, SPEED_STD_DEV))
            )
            try:
                self.sim.add_agent(
                    jps.AnticipationVelocityModelAgentParameters(
                        journey_id=journey_id,
                        stage_id=exit_stage_id,
                        position=positions[0],
                        desired_speed=desired_speed,
                    )
                )
                return True
            except RuntimeError:
                # The candidate can be too close to an agent already occupying
                # the entry. Try another random position instead.
                continue

        return False

    def step(self) -> None:
        if (
            self._agents_left_to_spawn > 0
            and self.sim.elapsed_time() >= self._next_spawn_time
        ):
            if self._spawn_random_agent():
                self._agents_left_to_spawn -= 1
                self._next_spawn_time = self.sim.elapsed_time() + random.uniform(
                    MIN_SPAWN_INTERVAL, MAX_SPAWN_INTERVAL
                )
        self.sim.iterate()
        
    def delta_time(self) -> float:
        return self.sim.delta_time()

    def agent_count(self) -> int:
        return self.sim.agent_count()

    def is_finished(self) -> bool:
        """True after every requested agent has spawned and reached an exit."""
        return self._agents_left_to_spawn == 0 and self.agent_count() == 0

    def snapshot(self) -> list[dict]:
        return [
            {"id": a.id, "x": a.position[0], "y": a.position[1]}
            for a in self.sim.agents()
        ]
