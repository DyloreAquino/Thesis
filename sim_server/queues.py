# Turns a raw path (points from a Godot Line2D) into
# evenly-spaced JuPedSim queue waiting positions.
import math

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