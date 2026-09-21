"""Walkability grid and path step."""

from unittest.mock import Mock

from agent_strategy import AgentStrategy
from navigation import camera_origin, downsample_collision, next_step


def _open_grid() -> list[list[int]]:
    return [[1 for _ in range(10)] for _ in range(9)]


def _fence_with_gap(gap_col: int) -> list[list[int]]:
    """A wall across row 3, open only at ``gap_col``."""
    grid = _open_grid()
    for col in range(10):
        grid[3][col] = 0
    grid[3][gap_col] = 1
    return grid


def test_camera_stays_at_origin_on_a_screen_sized_map():
    assert camera_origin(5, 6, 10, 9) == (0, 0)


def test_camera_centers_the_player_on_a_large_map():
    assert camera_origin(20, 15, 40, 30) == (16, 11)


def test_downsample_collision_folds_tiles_into_blocks():
    tiles = [[0 for _ in range(20)] for _ in range(18)]
    # One walkable 2x2 block at block (1, 2) -> tiles rows 4-5, cols 2-3
    tiles[4][2] = 1
    tiles[4][3] = 1
    tiles[5][2] = 1
    tiles[5][3] = 1
    grid = downsample_collision(tiles)
    assert grid is not None
    assert len(grid) == 9 and len(grid[0]) == 10
    assert grid[2][1] == 1
    assert grid[0][0] == 0


def test_downsample_rejects_a_non_grid():
    assert downsample_collision(Mock()) is None


def test_open_column_steps_toward_the_target():
    step = next_step(_open_grid(), (2, 4), (2, 1), 10, 9)
    assert step == "UP"


def test_fence_gap_is_used_instead_of_the_blocked_column():
    # Straight UP from x=2 hits the wall. The only opening is column 6,
    # and the target sits on the far side of that opening.
    step = next_step(_fence_with_gap(6), (2, 4), (2, 1), 10, 9)
    assert step == "RIGHT"


def test_does_not_step_into_a_wall_when_already_beside_it():
    grid = _fence_with_gap(6)
    # Standing just south of the wall, off the gap column, with the
    # target one step north through the wall. Nothing on this column is
    # closer, and UP is a wall, so there is no legal step.
    assert next_step(grid, (2, 4), (2, 3), 10, 9) is None


def test_already_on_the_target_does_not_move():
    assert next_step(_open_grid(), (4, 4), (4, 4), 10, 9) is None


def test_movement_target_is_the_oak_tile_on_pallet():
    strategy = AgentStrategy()
    strategy.mark_goal_complete("start_game")
    goal = strategy.get_current_goal()
    target = strategy.movement_target(
        goal,
        "overworld",
        {"current_map": {"map_id": 0x00}, "player_position": (3, 6)},
    )
    assert target == AgentStrategy.OAK_TRIGGER


def test_movement_target_skips_dialog_and_the_doorway_clear():
    strategy = AgentStrategy()
    strategy.mark_goal_complete("start_game")
    goal = strategy.get_current_goal()
    memory = {"current_map": {"map_id": 0x00}, "player_position": (3, 6)}
    assert strategy.movement_target(goal, "dialog", memory) is None
    strategy._exit_maneuver_steps = 2
    assert strategy.movement_target(goal, "overworld", memory) is None
