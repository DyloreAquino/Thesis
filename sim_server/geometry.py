"""Convert Godot geometry and routing definitions into simulation data."""

import math
from dataclasses import dataclass

from shapely import Point, Polygon


@dataclass(frozen=True)
class SwitchDefinition:
    """A Godot-authored waypoint and its outgoing routing connections."""

    switch_id: str
    position: tuple[float, float]
    radius: float
    target_switch_ids: tuple[str, ...]
    target_exit_indices: tuple[int, ...]
    transition: str


class SceneGeometry:
    def __init__(self):
        self.walkable_area: Polygon | None = None
        self.entry_areas: list[Polygon] = []
        self.exit_areas: list[Polygon] = []
        self.obstacles: list[Polygon] = []
        self.switches: dict[str, SwitchDefinition] = {}
        self.initial_switch_id: str | None = None
        self._routing_valid = False

    def set_from_message(self, data: dict) -> None:
        self._routing_valid = False
        self.walkable_area = Polygon(data["walkable_area"])
        self.entry_areas = [Polygon(pts) for pts in data["entry_areas"]]
        self.exit_areas = [Polygon(pts) for pts in data["exit_areas"]]
        self.obstacles = [Polygon(pts) for pts in data["obstacles"]]
        self._build_obstacles()

        switch_definitions = [
            self._parse_switch(raw_switch)
            for raw_switch in data.get("switches", [])
        ]
        self.switches = {
            switch.switch_id: switch for switch in switch_definitions
        }
        if len(self.switches) != len(switch_definitions):
            raise ValueError("Every journey switch must have a unique id")

        initial_switch_id = str(data.get("initial_switch_id", "")).strip()
        self.initial_switch_id = initial_switch_id or None
        self._validate_routing()
        self._routing_valid = True

    def is_ready(self) -> bool:
        """True when geometry and a valid routing graph have arrived."""
        return bool(
            self.walkable_area is not None
            and self.entry_areas
            and self.exit_areas
            and self.switches
            and self.initial_switch_id
            and self._routing_valid
        )

    # convert json switch to a switch struct that is parasable in python
    @staticmethod
    def _parse_switch(data: dict) -> SwitchDefinition:
        switch_id = str(data.get("id", "")).strip()
        position = data.get("position", [])
        if len(position) != 2:
            raise ValueError(f"Switch '{switch_id}' must contain an [x, y] position")

        return SwitchDefinition(
            switch_id=switch_id,
            position=(float(position[0]), float(position[1])),
            radius=float(data.get("radius", 0)),
            target_switch_ids=tuple(
                str(target_id).strip()
                for target_id in data.get("target_switch_ids", [])
            ),
            target_exit_indices=tuple(
                int(exit_index)
                for exit_index in data.get("target_exit_indices", [])
            ),
            transition=str(data.get("transition", "fixed")),
        )

    def _build_obstacles(self) -> None:
        for obstacle in self.obstacles:
            self.walkable_area = self.walkable_area.difference(obstacle)  # type: ignore[union-attr]

    # check current shapes and attribs, especially switch attribs to adhere to their godot scripts counterparts
    def _validate_routing(self) -> None:
        if self.walkable_area is None:
            raise ValueError("Walkable geometry is required")
        if not self.switches:
            raise ValueError("At least one journey switch is required")
        if self.initial_switch_id not in self.switches:
            raise ValueError(
                f"Initial switch '{self.initial_switch_id}' does not exist"
            )

        valid_transitions = {"fixed", "least_targeted", "round_robin"}
        for switch in self.switches.values():
            if not switch.switch_id:
                raise ValueError("Every journey switch must have a non-empty id")
            if not all(math.isfinite(value) for value in switch.position):
                raise ValueError(
                    f"Switch '{switch.switch_id}' has a non-finite position"
                )
            if not Point(switch.position).within(self.walkable_area):
                raise ValueError(
                    f"Switch '{switch.switch_id}' at {switch.position} "
                    "is outside the walkable area"
                )
            if not math.isfinite(switch.radius) or switch.radius <= 0:
                raise ValueError(
                    f"Switch '{switch.switch_id}' must have a positive radius"
                )
            if switch.transition not in valid_transitions:
                raise ValueError(
                    f"Switch '{switch.switch_id}' has unknown transition "
                    f"'{switch.transition}'"
                )

            unknown_targets = set(switch.target_switch_ids) - self.switches.keys()
            if unknown_targets:
                raise ValueError(
                    f"Switch '{switch.switch_id}' targets unknown switches: "
                    f"{sorted(unknown_targets)}"
                )
            invalid_exit_indices = [
                index
                for index in switch.target_exit_indices
                if index < 0 or index >= len(self.exit_areas)
            ]
            if invalid_exit_indices:
                raise ValueError(
                    f"Switch '{switch.switch_id}' targets invalid exit indices: "
                    f"{invalid_exit_indices}"
                )

            target_count = (
                len(switch.target_switch_ids)
                + len(switch.target_exit_indices)
            )
            if target_count == 0:
                raise ValueError(
                    f"Switch '{switch.switch_id}' must target a switch or exit"
                )
            if switch.transition == "fixed" and target_count != 1:
                raise ValueError(
                    f"Fixed switch '{switch.switch_id}' must have exactly one target"
                )

        for switch_id in self.switches:
            if not self._all_paths_reach_an_exit(switch_id, frozenset()):
                raise ValueError(
                    f"Switch '{switch_id}' has a cycle or a path without an exit"
                )

    def _all_paths_reach_an_exit(self, switch_id: str, visiting: frozenset[str]) -> bool:
        if switch_id in visiting:
            return False

        switch = self.switches[switch_id]
        next_visiting = visiting | {switch_id}
        return bool(switch.target_exit_indices or switch.target_switch_ids) and all(
            self._all_paths_reach_an_exit(target_id, next_visiting)
            for target_id in switch.target_switch_ids
        )
