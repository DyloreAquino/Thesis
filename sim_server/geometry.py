"""Has information on the polygon geometry received from Godot, as shapely Polygons"""
from shapely import Polygon

class SceneGeometry:
    def __init__(self):
        self.walkable_area: Polygon | None = None
        self.entry_areas: list[Polygon] = []
        self.exit_areas: list[Polygon] = []
        self.obstacles: list[Polygon] = []
        self.switches: list[tuple[float, float]] = []

    def set_from_message(self, data: dict) -> None:
        self.walkable_area = Polygon(data["walkable_area"])
        self.entry_areas = [Polygon(pts) for pts in data["entry_areas"]]
        self.exit_areas = [Polygon(pts) for pts in data["exit_areas"]]
        self.obstacles = [Polygon(pts) for pts in data["obstacles"]]
        self.switch_positions = [(float(position[0]), float(position[1])) for position in data["switches"]]
        self._build_obstacles(data)

    def is_ready(self) -> bool:
        """True once a walkable area and at least one entry/exit have arrived."""
        return self.walkable_area is not None and self.entry_areas and self.exit_areas # type: ignore
    
    def _build_obstacles(self, data: dict) -> None:
        for obstacle in self.obstacles:
            self.walkable_area = self.walkable_area.difference(obstacle) # type: ignore