"""Walkability grid and a one-step path toward a map coordinate.

Pokemon Red's visible map is a 9 by 10 grid of walkable blocks (each block is
a 2x2 tile). PyBoy's ``game_area_collision`` reports the 18 by 20 tile view;
``downsample_collision`` folds that into the 9 by 10 block grid the player
actually steps on. The player is not a global "this direction is a wall":
a fence can block UP on one column and be open on the next.

The pathfinder returns only the next button. Dialog, menus, and which
coordinate to head for stay with the policy chain and the strategy.
"""

from collections import deque

# Visible blocks. The camera keeps the player near (4, 4) on maps larger
# than the screen, matching the Claude / PyBoy collision overlay.
VIEW_ROWS = 9
VIEW_COLS = 10
CENTER_ROW = 4
CENTER_COL = 4

_DELTAS = (
    (-1, 0, "UP"),
    (1, 0, "DOWN"),
    (0, -1, "LEFT"),
    (0, 1, "RIGHT"),
)


def camera_origin(
    player_x: int,
    player_y: int,
    map_width: int,
    map_height: int,
) -> tuple[int, int]:
    """Top-left map block currently on screen."""
    max_x = max(0, map_width - VIEW_COLS)
    max_y = max(0, map_height - VIEW_ROWS)
    origin_x = min(max(player_x - CENTER_COL, 0), max_x)
    origin_y = min(max(player_y - CENTER_ROW, 0), max_y)
    return origin_x, origin_y


def downsample_collision(collision) -> list[list[int]] | None:
    """Fold an 18 by 20 tile collision map into a 9 by 10 block grid.

    A block is walkable when any of its four tiles is. Returns None when
    the value is not a numeric grid (a missing game wrapper, for example).
    """
    try:
        if len(collision) < VIEW_ROWS * 2 or len(collision[0]) < VIEW_COLS * 2:
            return None
        int(collision[0][0])
    except (TypeError, ValueError, IndexError):
        return None

    grid: list[list[int]] = []
    for row in range(VIEW_ROWS):
        blocks: list[int] = []
        for col in range(VIEW_COLS):
            tiles = (
                collision[row * 2][col * 2],
                collision[row * 2][col * 2 + 1],
                collision[row * 2 + 1][col * 2],
                collision[row * 2 + 1][col * 2 + 1],
            )
            blocks.append(1 if any(int(tile) != 0 for tile in tiles) else 0)
        grid.append(blocks)
    return grid


def next_step(
    walkable: list[list[int]],
    player: tuple[int, int],
    target: tuple[int, int],
    map_width: int,
    map_height: int,
) -> str | None:
    """Button that walks the player one block closer to ``target``.

    ``player`` and ``target`` are map coordinates ``(x, y)``. The search
    runs on the visible walkability grid. When the target is off-screen,
    the goal is the visible walkable block closest to it.
    """
    if map_width <= 0 or map_height <= 0 or not walkable:
        return None
    origin_x, origin_y = camera_origin(player[0], player[1], map_width, map_height)
    start = (player[1] - origin_y, player[0] - origin_x)
    if not _inside(walkable, start) or walkable[start[0]][start[1]] == 0:
        return None

    goal, came_from = _closest_reachable(
        walkable, start, origin_x, origin_y, target
    )
    if goal == start:
        return _step_offscreen(walkable, start, player, target, origin_x, origin_y)
    return _reconstruct(came_from, goal)[0]


def _world_distance(
    cell: tuple[int, int],
    origin_x: int,
    origin_y: int,
    target: tuple[int, int],
) -> int:
    world_x = cell[1] + origin_x
    world_y = cell[0] + origin_y
    return abs(world_x - target[0]) + abs(world_y - target[1])


def _closest_reachable(
    walkable: list[list[int]],
    start: tuple[int, int],
    origin_x: int,
    origin_y: int,
    target: tuple[int, int],
) -> tuple[tuple[int, int], dict[tuple[int, int], tuple[int, int]]]:
    """Reachable block nearest the target, and the BFS parent map.

    Breadth-first search makes the parent chain the shortest walk. A later
    block replaces the goal only when it is strictly closer to the target,
    so an equal-distance cell on the wrong side of a wall does not win.
    """
    best = start
    best_dist = _world_distance(start, origin_x, origin_y, target)
    came_from: dict[tuple[int, int], tuple[int, int]] = {}
    seen = {start}
    queue: deque[tuple[int, int]] = deque([start])
    while queue:
        current = queue.popleft()
        distance = _world_distance(current, origin_x, origin_y, target)
        if distance < best_dist:
            best_dist = distance
            best = current
        for d_row, d_col, _direction in _DELTAS:
            neighbor = (current[0] + d_row, current[1] + d_col)
            if neighbor in seen or not _inside(walkable, neighbor):
                continue
            if walkable[neighbor[0]][neighbor[1]] == 0:
                continue
            seen.add(neighbor)
            came_from[neighbor] = current
            queue.append(neighbor)
    return best, came_from


def _step_offscreen(
    walkable: list[list[int]],
    start: tuple[int, int],
    player: tuple[int, int],
    target: tuple[int, int],
    origin_x: int,
    origin_y: int,
) -> str | None:
    """Step off the visible grid toward a target past the edge.

    Refuses the step when the next visible block is a wall.
    """
    if (player[0], player[1]) == target:
        return None
    screen_target = (target[1] - origin_y, target[0] - origin_x)
    row_delta = screen_target[0] - start[0]
    col_delta = screen_target[1] - start[1]
    if row_delta == 0 and col_delta == 0:
        return None
    if abs(row_delta) >= abs(col_delta) and row_delta != 0:
        direction = "UP" if row_delta < 0 else "DOWN"
        d_row, d_col = (-1 if row_delta < 0 else 1), 0
    elif col_delta < 0:
        direction = "LEFT"
        d_row, d_col = 0, -1
    elif col_delta > 0:
        direction = "RIGHT"
        d_row, d_col = 0, 1
    else:
        return None
    neighbor = (start[0] + d_row, start[1] + d_col)
    if _inside(walkable, neighbor) and walkable[neighbor[0]][neighbor[1]] == 0:
        return None
    return direction


def _inside(walkable: list[list[int]], cell: tuple[int, int]) -> bool:
    row, col = cell
    return 0 <= row < len(walkable) and 0 <= col < len(walkable[0])


def _reconstruct(
    came_from: dict[tuple[int, int], tuple[int, int]],
    current: tuple[int, int],
) -> list[str]:
    steps: list[str] = []
    while current in came_from:
        previous = came_from[current]
        steps.append(_direction_between(previous, current))
        current = previous
    steps.reverse()
    return steps


def _direction_between(previous: tuple[int, int], current: tuple[int, int]) -> str:
    d_row = current[0] - previous[0]
    d_col = current[1] - previous[1]
    for row, col, direction in _DELTAS:
        if row == d_row and col == d_col:
            return direction
    return "UP"
