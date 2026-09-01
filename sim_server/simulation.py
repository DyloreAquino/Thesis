"""Owns the JuPedSim Simulation, agent spawning and journey setup."""

import pathlib
import random

import jupedsim as jps
from geometry import SceneGeometry
from numpy.random import normal
import spawning
import routing

MEAN_DESIRED_SPEED = 1.34   # m/s, standard pedestrian walking speed
SPEED_STD_DEV = 0.2
MIN_SPAWN_INTERVAL = 0.5     # simulated seconds
MAX_SPAWN_INTERVAL = 2.0
SPAWN_POSITION_ATTEMPTS = 20

class CrowdSimulation:
    def __init__(self, 
                 scene: SceneGeometry, 
                 trajectory_file: str = "output.sqlite",
                 sim_parameters: dict | None = None):
        
        self.sim_parameters = sim_parameters or {}
        
        if scene.walkable_area is None:
            raise ValueError("Geometry cannot be none")
        
        self._trajectory_writer = jps.SqliteTrajectoryWriter(
            output_file=pathlib.Path(trajectory_file)
        )
        self._closed = False
        self.sim = jps.Simulation(
            model=jps.AnticipationVelocityModel(),
            geometry=scene.walkable_area,
            trajectory_writer=self._trajectory_writer,
        )
        self._entry_areas = scene.entry_areas
        self._exit_journeys = routing.build_exit_journeys(self.sim, scene)
        self._agents_left_to_spawn = max(
            0, int(self.sim_parameters.get("agent_count", 20))
        )
        self._spawn_interval = float(self.sim_parameters.get("entry_rate", 1.0))
        self._next_spawn_time = 0

    def step(self) -> None:
        if (self._agents_left_to_spawn > 0 and self.sim.elapsed_time() >= self._next_spawn_time):
            if spawning.spawn_random_agent(self.sim, self._entry_areas, self._exit_journeys):
                self._agents_left_to_spawn -= 1
                self._next_spawn_time = self.sim.elapsed_time() + self._spawn_interval
        self.sim.iterate()
        
    def delta_time(self) -> float:
        return self.sim.delta_time()

    def agent_count(self) -> int:
        return self.sim.agent_count()

    def is_finished(self) -> bool:
        """True after every requested agent has spawned and reached an exit."""
        return self._agents_left_to_spawn == 0 and self.agent_count() == 0

    def close(self) -> None:
        """Flush and close the trajectory database."""
        if not self._closed:
            self._trajectory_writer.close()
            self._closed = True

    def snapshot(self) -> list[dict]:
        return [
            {"id": a.id, "x": a.position[0], "y": a.position[1]}
            for a in self.sim.agents()
        ]
