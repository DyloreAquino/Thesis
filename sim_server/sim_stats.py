import shapely
import numpy as np


class RunStatistics:
    """Collect per-step measurements, independently of network snapshot timing."""

    def __init__(self, area: float):
        self.area = area
        self.entry_times: dict[int, float] = {}
        self.travel_times: list[float] = []
        self.duration = 0.0
        self.density_integral = 0.0
        self.peak_density = 0.0
        self.distance = 0.0
        self.observed_agent_seconds = 0.0
        self.compute_seconds = 0.0
        self.active_count = 0

    def record_step(self, start: float, end: float, before: dict, after: dict,
                    compute_seconds: float) -> None:
        dt = end - start
        for agent_id in before:
            self.entry_times.setdefault(agent_id, start)
        for agent_id in before.keys() - after.keys():
            self.travel_times.append(end - self.entry_times.pop(agent_id))

        # Occupancy at the start of each integration interval, after spawning.
        density = len(before) / self.area
        self.density_integral += density * dt
        self.peak_density = max(self.peak_density, density)
        self.duration += dt
        self.compute_seconds += compute_seconds
        self.active_count = len(after)
        for agent_id in before.keys() & after.keys():
            x0, y0 = before[agent_id]
            x1, y1 = after[agent_id]
            self.distance += float(np.hypot(x1 - x0, y1 - y0))
            self.observed_agent_seconds += dt

    def summary(self) -> str:
        def number(value):
            return "N/A" if value is None else f"{value:.3f}"

        mean_density = self.density_integral / self.duration if self.duration else None
        throughput = len(self.travel_times) / self.duration if self.duration else None
        speed = (self.distance / self.observed_agent_seconds
                 if self.observed_agent_seconds else None)
        mean_tt = float(np.mean(self.travel_times)) if self.travel_times else None
        p95_tt = float(np.percentile(self.travel_times, 95)) if self.travel_times else None
        return (
            f"Simulated duration: {self.duration:.3f} s\n"
            f"Completed: {len(self.travel_times)} | Still active: {self.active_count}\n"
            f"Whole-area density (time mean / peak): "
            f"{number(mean_density)} / {self.peak_density:.3f} agents/m^2\n"
            f"Observed mean speed (includes waiting): {number(speed)} m/s\n"
            f"Travel time, spawn to removal (mean / P95): "
            f"{number(mean_tt)} / {number(p95_tt)} s\n"
            f"Exit throughput (completed / full duration): {number(throughput)} agents/s\n"
            f"Step computation time (spawn + queues + engine; excludes network/sleep): "
            f"{self.compute_seconds:.3f} s\n"
            "Accuracy vs real observations: N/A (reference data required)\n"
            "Notes: density is global, not local congestion; speed excludes removal steps."
        )

def compute_density(simulation, walkable_area) -> float:
    """Mean density over the walkable area, in agents/m²."""
    positions = np.array([agent.position for agent in simulation.agents()])
    if positions.size == 0:
        return 0.0
    points = shapely.points(positions[:, 0], positions[:, 1])
    inside = shapely.contains(walkable_area, points)
    return float(inside.sum()) / walkable_area.area
