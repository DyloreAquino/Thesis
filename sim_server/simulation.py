"""Owns the JuPedSim Simulation, agent spawning and journey setup."""

import math
import pathlib

import jupedsim as jps
from geometry import SceneGeometry
import routing
import spawning

class CrowdSimulation:
    def __init__(self, 
                 scene: SceneGeometry, 
                 trajectory_file: str = "output.sqlite",
                 sim_parameters: dict | None = None):
        
        self.sim_parameters = sim_parameters or {}

        entry_rate = float(self.sim_parameters.get("entry_rate", 1.0))
        if not math.isfinite(entry_rate) or entry_rate <= 0:
            raise ValueError("entry_rate must be greater than 0 agents per second")
        
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
        # # temp remove after
        # temporary_switch = scene.walkable_area.representative_point()
        # temp_pos = (
        #     temporary_switch.x,
        #     temporary_switch.y
        # )
        
        self._journey_starts = routing.build_journeys(self.sim,
                                                      scene,
                                                      switch_position=scene.switch_positions[0],
                                                      switch_radius=1.5)
        self._agents_left_to_spawn = max(
            0, int(self.sim_parameters.get("agent_count", 20))
        )
        self._spawn_interval = 1.0 / entry_rate
        self._next_spawn_time = 0

    def step(self) -> None:
        while (
            self._agents_left_to_spawn > 0
            and self.sim.elapsed_time() >= self._next_spawn_time
        ):
            if not spawning.spawn_random_agent(
                self.sim, self._entry_areas, self._journey_starts
            ):
                break
            self._agents_left_to_spawn -= 1
            self._next_spawn_time += self._spawn_interval
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
