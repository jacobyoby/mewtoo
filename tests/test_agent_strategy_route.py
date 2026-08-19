"""Route-to-Oak direction tests for the get_starter goal."""
from agent_strategy import AgentStrategy


def suggest(map_id, pos, visited=()):
    s = AgentStrategy()
    s.visited_maps.update(visited)
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
    # Only after Route 1 (0x0B) has been seen — that is when Oak's cutscene
    # has fired and the balls become takeable.
    r1 = (0x0B,)
    assert suggest(0x28, (4, 11), r1) == "UP"    # deep in the lab: go up
    assert suggest(0x28, (4, 4), r1) == "RIGHT"  # at table row: go right
    assert suggest(0x28, (7, 4), r1) == "A"      # at the table: interact


def test_lab_is_a_dead_end_before_the_oak_cutscene():
    """Entering Oak's Lab before triggering Oak on Route 1 -> leave."""
    s = AgentStrategy()
    goal = next(g for g in s.goals if g.name == "get_starter")
    md = {"current_map": {"map_id": 0x28}, "player_position": (5, 3), "party": []}
    assert s.suggest_action_for_goal(goal, "overworld", md) == "DOWN"


def test_lab_approaches_table_after_route_1_seen():
    s = AgentStrategy()
    s.visited_maps.add(0x0B)  # Route 1 visited -> Oak cutscene has fired
    goal = next(g for g in s.goals if g.name == "get_starter")
    md = {"current_map": {"map_id": 0x28}, "player_position": (4, 11), "party": []}
    assert s.suggest_action_for_goal(goal, "overworld", md) == "UP"


def test_visited_maps_tracked_from_memory():
    s = AgentStrategy()
    s.update_phase("overworld", {"current_map": {"map_id": 0x0B}, "party": []})
    assert 0x0B in s.visited_maps
