"""Has information on the polygon geometry received from Godot, as shapely Polygons"""
from shapely import Polygon

class SceneGeometry:
    def __init__(self):
        self.walkable_area: Polygon | None = None
        self.entry_areas: list[Polygon] = []
        self.exit_areas: list[Polygon] = []

    def set_from_message(self, data: dict) -> None:
        self.walkable_area = Polygon(data["walkable_area"])
        self.entry_areas = [Polygon(pts) for pts in data["entry_areas"]]
        self.exit_areas = [Polygon(pts) for pts in data["exit_areas"]]

    def is_ready(self) -> bool:
        """True once a walkable area and at least one entry/exit have arrived."""
        return self.walkable_area is not None and self.entry_areas and self.exit_areas