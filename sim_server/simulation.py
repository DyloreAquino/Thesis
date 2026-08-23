"""Owns the JuPedSim Simulation, agent spawning and journey setup."""

import pathlib
import random
import jupedsim as jps
from numpy.random import normal
from geometry import SceneGeometry

AGENTS_PER_ENTRY = 20
MEAN_DESIRED_SPEED = 1.34   # m/s, standard pedestrian walking speed
SPEED_STD_DEV = 0.2

class CrowdSimulation:
    def __init__(self, scene: SceneGeometry, trajectory_file: str = "output.sqlite"):
        self.sim = jps.Simulation(
            model=jps.AnticipationVelocityModel(),
            geometry=scene.walkable_area,
            trajectory_writer=jps.SqliteTrajectoryWriter(
                output_file=pathlib.Path(trajectory_file)
            ),
        )
        self._exit_journeys = self._build_exit_journeys(scene)  # list of (journey_id, stage_id)
        self._spawn_agents(scene)

    def _build_exit_journeys(self, scene: SceneGeometry) -> list[tuple[int, int]]:
        journeys = []
        for exit_area in scene.exit_areas:
            exit_id = self.sim.add_exit_stage(exit_area.exterior.coords[:-1])
            journey_id = self.sim.add_journey(jps.JourneyDescription([exit_id]))
            journeys.append((journey_id, exit_id))
        return journeys

    def _spawn_agents(self, scene: SceneGeometry) -> None:
        for entry_area in scene.entry_areas:
            positions = jps.distributions.distribute_by_number(
                polygon=entry_area,
                number_of_agents=AGENTS_PER_ENTRY,
                distance_to_agents=1.0,
                distance_to_polygon=0.2,
                seed=None,
            )
            speeds = normal(MEAN_DESIRED_SPEED, SPEED_STD_DEV, len(positions))
            for pos, speed in zip(positions, speeds):
                journey_id, stage_id = random.choice(self._exit_journeys)
                self.sim.add_agent(
                    jps.AnticipationVelocityModelAgentParameters(
                        journey_id=journey_id,
                        stage_id=stage_id,
                        position=pos,
                        desired_speed=speed,
                    )
                )

    def step(self) -> None:
        self.sim.iterate()
        
    def delta_time(self) -> float:
        return self.sim.delta_time()

    def agent_count(self) -> int:
        return self.sim.agent_count()

    def snapshot(self) -> list[dict]:
        return [{"id": a.id, "x": a.position[0], "y": a.position[1]} for a in self.sim.agents()]