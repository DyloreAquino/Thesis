import shapely
import numpy as np

def compute_density(simulation, walkable_area) -> float:
    """Mean density over the walkable area, in agents/m²."""
    positions = np.array([agent.position for agent in simulation.agents()])
    if positions.size == 0:
        return 0.0
    points = shapely.points(positions[:, 0], positions[:, 1])
    inside = shapely.contains(walkable_area, points)
    return float(inside.sum()) / walkable_area.area