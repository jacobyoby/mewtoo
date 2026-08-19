"""Route-to-Oak direction tests for the get_starter goal."""
from agent_strategy import AgentStrategy


def suggest(map_id, pos):
    s = AgentStrategy()
    goal = next(g for g in s.goals if g.name == "get_starter")
    return s.suggest_action_for_goal(goal, "overworld", {
        "current_map": {"map_id": map_id},
        "player_position": pos,
        "party": [],
    })


def test_bedroom_heads_for_stairs_top_right():
    assert suggest(0x26, (3, 6)) == "RIGHT"
    assert suggest(0x26, (7, 5)) == "UP"


def test_house_1f_heads_for_door_at_bottom():
    assert suggest(0x25, (4, 3)) == "DOWN"


def test_pallet_town_heads_north():
    assert suggest(0x00, (10, 10)) == "UP"


def test_oaks_lab_heads_to_ball_table_then_interacts():
    assert suggest(0x28, (4, 11)) == "UP"    # deep in the lab: go up
    assert suggest(0x28, (4, 4)) == "RIGHT"  # at table row: go right
    assert suggest(0x28, (7, 4)) == "A"      # at the table: interact
