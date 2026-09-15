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
    target_queue_indices: tuple[int, ...]

@dataclass(frozen=True)
class QueueDefinition:
    path: tuple[tuple[float, float], ...]
    release_interval_seconds: float = 5.0
    target_switch_ids: tuple[str, ...] = ()
    target_exit_indices: tuple[int, ...] = ()
    transition: str = "fixed"

class SceneGeometry:
    def __init__(self):
        self.walkable_area: Polygon | None = None
        self.entry_areas: list[Polygon] = []
        self.entry_start_switch_ids: list[str] = []
        self.exit_areas: list[Polygon] = []
        self.obstacles: list[Polygon] = []
        self.switches: dict[str, SwitchDefinition] = {}
        self.initial_switch_id: str | None = None
        self._routing_valid = False
        self.queues: list[QueueDefinition] = []

    def set_from_message(self, data: dict) -> None:
        self._routing_valid = False
        self.walkable_area = Polygon(data["walkable_area"])
        # Accept legacy polygon-only entries as well as per-entry routing.
        raw_entries = data["entry_areas"]
        fallback = str(data.get("initial_switch_id", "")).strip()
        self.entry_areas = [
            Polygon(entry["polygon"] if isinstance(entry, dict) else entry)
            for entry in raw_entries
        ]
        self.entry_start_switch_ids = [
            (str(entry.get("starting_switch_id", "")).strip() or fallback)
            if isinstance(entry, dict) else fallback
            for entry in raw_entries
        ]
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
    
        self.queues = [
            self._parse_queue(raw_queue) for raw_queue in data.get("queues", [])
        ]
        
        for i in range(len(self.queues)):
            if not self._queue_reaches_an_exit(i, frozenset()):
                raise ValueError(f"Queue #{i} has a cycle or a path without an exit")

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
            target_queue_indices=tuple(
                int(queue_index) for queue_index in data.get("target_queue_indices", [])
            ),
        )
    
    @staticmethod
    def _parse_queue(data: dict) -> QueueDefinition:
        raw_path = data.get("path", [])
        if len(raw_path) < 2:
            raise ValueError("A queue must have at least 2 points to define a path")

        return QueueDefinition(
            path=tuple((float(p[0]), float(p[1])) for p in raw_path),
            release_interval_seconds=float(data.get("release_interval_seconds", 10.0)),
            target_switch_ids=tuple(str(t).strip() for t in data.get("target_switch_ids", [])),
            target_exit_indices=tuple(int(i) for i in data.get("target_exit_indices", [])),
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
        if self.initial_switch_id is not None and self.initial_switch_id not in self.switches:
            raise ValueError(
                f"Initial switch '{self.initial_switch_id}' does not exist"
            )
        for i, switch_id in enumerate(self.entry_start_switch_ids):
            if switch_id not in self.switches:
                raise ValueError(
                    f"Entry #{i} starting switch '{switch_id}' does not exist; "
                    "assign a starting switch or an initial switch fallback"
                )
        
        valid_transitions = {"fixed", "least_targeted", "round_robin"}
        for i, queue in enumerate(self.queues):
            if not math.isfinite(queue.release_interval_seconds) or queue.release_interval_seconds <= 0:
                raise ValueError(f"Queue #{i} must have a positive release_interval_seconds")
            if queue.transition not in valid_transitions:
                raise ValueError(f"Queue #{i} has unknown transition '{queue.transition}'")
            unknown_targets = set(queue.target_switch_ids) - self.switches.keys()
            if unknown_targets:
                raise ValueError(f"Queue #{i} targets unknown switches: {sorted(unknown_targets)}")
            invalid_exit_indices = [j for j in queue.target_exit_indices if j < 0 or j >= len(self.exit_areas)]
            if invalid_exit_indices:
                raise ValueError(f"Queue #{i} targets invalid exit indices: {invalid_exit_indices}")
            target_count = len(queue.target_switch_ids) + len(queue.target_exit_indices)
            if target_count == 0:
                raise ValueError(f"Queue #{i} must target at least one switch or exit")
            if queue.transition == "fixed" and target_count != 1:
                raise ValueError(f"Fixed queue #{i} must have exactly one target")
        
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
            
            invalid_queue_indices = [
                index for index in switch.target_queue_indices
                if index < 0 or index >= len(self.queues)
            ]
            if invalid_queue_indices:
                raise ValueError(f"Switch '{switch.switch_id}' targets invalid queue indices: {invalid_queue_indices}")

            target_count = (
                len(switch.target_switch_ids)
                + len(switch.target_exit_indices)
                + len(switch.target_queue_indices)
            )
            if target_count == 0:
                raise ValueError(f"Switch '{switch.switch_id}' must target a switch, exit, or queue")
            if switch.transition == "fixed" and target_count != 1:
                raise ValueError(f"Fixed switch '{switch.switch_id}' must have exactly one target")

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
        if not (switch.target_exit_indices or switch.target_switch_ids or switch.target_queue_indices):
            return False
        return (
            all(self._all_paths_reach_an_exit(t, next_visiting) for t in switch.target_switch_ids)
            and all(self._queue_reaches_an_exit(i, next_visiting) for i in switch.target_queue_indices)
        )

    def _queue_reaches_an_exit(self, queue_index: int, visiting: frozenset[str]) -> bool:
        queue = self.queues[queue_index]
        has_any_target = bool(queue.target_exit_indices or queue.target_switch_ids)
        return has_any_target and all(
            self._all_paths_reach_an_exit(switch_id, visiting)
            for switch_id in queue.target_switch_ids
        )
