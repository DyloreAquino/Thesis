# Turns a raw path (points from a Godot Line2D) into
# evenly-spaced JuPedSim queue waiting positions.
import math

class QueueController:
    """Owns release timing for one queue stage: releases one agent from the
    front every `release_interval_seconds`, but only starts the clock once
    someone is actually waiting in it.
    """
    def __init__(self, stage, release_interval_seconds: float, delta_time: float):
        self._stage = stage
        self._release_every_n_iterations = max(1, round(release_interval_seconds / delta_time))
        self._is_active = False
        self._started_at_iteration = 0

    def update(self, current_iteration: int) -> None:
        if self._stage.count_enqueued() == 0:
            self._is_active = False
            return

        if not self._is_active:
            self._is_active = True
            self._started_at_iteration = current_iteration
            return

        elapsed = current_iteration - self._started_at_iteration
        if elapsed % self._release_every_n_iterations == 0:
            self._stage.pop(1)

def resample_path(points: list[tuple[float, float]], spacing: float) -> list[tuple[float, float]]:
    if len(points) < 2:
        return points

    resampled = [points[0]]
    leftover = 0.0  # distance carried over from the previous segment

    for start, end in zip(points, points[1:]):
        seg_vec = (end[0] - start[0], end[1] - start[1])
        seg_len = math.hypot(*seg_vec)
        if seg_len == 0:
            continue
        direction = (seg_vec[0] / seg_len, seg_vec[1] / seg_len)
        traveled = 0.0

        while leftover + (seg_len - traveled) >= spacing:
            traveled += spacing - leftover
            resampled.append((start[0] + direction[0] * traveled, start[1] + direction[1] * traveled))
            leftover = 0.0

        leftover += seg_len - traveled

    return resampled
