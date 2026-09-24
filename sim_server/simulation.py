"""Owns the JuPedSim Simulation, agent spawning and journey setup."""

import math
import pathlib
from time import perf_counter

import jupedsim as jps
from geometry import SceneGeometry

from queues import QueueController
import routing
import spawning
import sim_stats

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
        
        self.geometry = scene
        
        self._trajectory_writer = jps.SqliteTrajectoryWriter(
            output_file=pathlib.Path(trajectory_file)
        )
        self._closed = False
        model = jps.CollisionFreeSpeedModelV2()
        self._model_name = type(model).__name__
        self._run_statistics = sim_stats.RunStatistics(scene.walkable_area.area)
        self.sim = jps.Simulation(
            model=model,
            geometry=scene.walkable_area,
            trajectory_writer=self._trajectory_writer,
        )
        self._entry_areas = scene.entry_areas
        self._journey_starts, queue_stage_ids = routing.build_journeys(self.sim, scene)
        
        delta_time = self.sim.delta_time()
        self._queue_controllers = [
            QueueController(
                stage=self.sim.get_stage(stage_id),
                release_interval_seconds=queue_def.release_interval_seconds,
                delta_time=delta_time,
            )
            for stage_id, queue_def in zip(queue_stage_ids, scene.queues)
        ]
        
        self._agents_left_to_spawn = max(
            0, int(self.sim_parameters.get("agent_count", 20))
        )
        self._spawn_interval = 1.0 / entry_rate
        self._next_spawn_time = 0

    def step(self) -> None:
        compute_start = perf_counter()
        start_time = self.sim.elapsed_time()
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
        
        current_iteration = self.sim.iteration_count()
        for controller in self._queue_controllers:
            controller.update(current_iteration)
        
        before = {agent.id: agent.position for agent in self.sim.agents()}
        pre_step_seconds = perf_counter() - compute_start
        iterate_start = perf_counter()
        self.sim.iterate()
        compute_seconds = pre_step_seconds + perf_counter() - iterate_start
        after = {agent.id: agent.position for agent in self.sim.agents()}
        self._run_statistics.record_step(
            start_time, self.sim.elapsed_time(), before, after, compute_seconds
        )

    def print_run_summary(self) -> None:
        print(
            f"\n--- Simulation summary: {self._model_name} ---\n"
            f"Requested agents: {self.sim_parameters.get('agent_count', 20)} | "
            f"Entry rate: {self.sim_parameters.get('entry_rate', 1.0)} agents/s\n"
            f"Desired speed distribution: mean={spawning.MEAN_DESIRED_SPEED:.3f}, "
            f"std={spawning.SPEED_STD_DEV:.3f} m/s\n"
            f"{self._run_statistics.summary()}\n"
        )
        
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
            self._trajectory_writer.connection().close()
            self._closed = True

    def snapshot(self) -> list[dict]:
        return [
            {"id": a.id, "x": a.position[0], "y": a.position[1]}
            for a in self.sim.agents()
        ]
    
    def get_statistics(self) -> dict:
        return {
            "density": sim_stats.compute_density(self.sim, self.geometry.walkable_area)
        }
