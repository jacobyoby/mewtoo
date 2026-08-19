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


class TestRoutePolicyWins:
    """The encoded route beats exploration/LLM on known maps."""

    def _agent(self, mock_llm_provider, mock_pyboy, map_id, pos):
        from unittest.mock import Mock

        from game_state import GameState
        from pokemon_agent import PokemonAgent
        gs = GameState(mock_pyboy, ocr_enabled=False)
        agent = PokemonAgent(mock_llm_provider, gs)
        gs.get_game_info = Mock(return_value={
            "screen_text": "", "frame_count": 100, "game_state": "overworld",
            "party": [], "player_position": pos,
            "current_map": {"map_id": map_id, "map_name": "test"},
        })
        agent.new_game_started = True
        agent.character_creation_steps = 60
        agent.step_count = 300
        # Real runs mark this on the first goal check; without it the
        # higher-priority start_game goal answers instead of get_starter
        agent.strategy.mark_goal_complete("start_game")
        return agent

    def test_pallet_town_goes_north(self, mock_llm_provider, mock_pyboy):
        agent = self._agent(mock_llm_provider, mock_pyboy, 0x00, (10, 10))
        assert agent.get_action() == "UP"

    def test_lab_before_cutscene_exits(self, mock_llm_provider, mock_pyboy):
        agent = self._agent(mock_llm_provider, mock_pyboy, 0x28, (5, 3))
        assert agent.get_action() == "DOWN"

    def test_yields_when_stuck(self, mock_llm_provider, mock_pyboy):
        agent = self._agent(mock_llm_provider, mock_pyboy, 0x00, (10, 10))
        agent.stuck_count = 9
        # Route steps aside so stuck-breaking logic can run
        assert agent._route_policy(agent._observe()) is None

    def test_scans_along_the_wall_when_route_direction_is_blocked(self, mock_llm_provider, mock_pyboy):
        # Superseded "yield when blocked": giving up handed control to random
        # exploration and runs stalled at Pallet Town's north fence. The route
        # now sweeps sideways looking for the gap.
        agent = self._agent(mock_llm_provider, mock_pyboy, 0x00, (10, 10))
        agent.blocked_directions.add("UP")
        assert agent._route_policy(agent._observe()) in ("LEFT", "RIGHT")


class TestDoorExitManeuver:
    """Leaving a building must not walk straight back in."""

    def _strategy_after_exit(self):
        s = AgentStrategy()
        s.update_phase("overworld", {"current_map": {"map_id": 0x25}, "party": []})  # inside
        s.update_phase("overworld", {"current_map": {"map_id": 0x00}, "party": []})  # stepped out
        return s

    def test_sidesteps_before_heading_north(self):
        s = self._strategy_after_exit()
        goal = next(g for g in s.goals if g.name == "get_starter")
        md = {"current_map": {"map_id": 0x00}, "player_position": (5, 6), "party": []}
        seq = [s.suggest_action_for_goal(goal, "overworld", md) for _ in range(5)]
        assert seq[0] == "DOWN"          # step away from the doorway
        assert "LEFT" in seq[1:3]        # move to a different column
        # Then resume routing toward the Oak trigger tile (10, 1); from
        # x=5 that means heading right, not straight north.
        assert seq[-1] == "RIGHT"

    def test_no_maneuver_when_not_leaving_a_building(self):
        s = AgentStrategy()
        s.update_phase("overworld", {"current_map": {"map_id": 0x00}, "party": []})
        goal = next(g for g in s.goals if g.name == "get_starter")
        md = {"current_map": {"map_id": 0x00}, "player_position": (5, 6), "party": []}
        # No maneuver queued -> routes straight toward the trigger column
        assert s.suggest_action_for_goal(goal, "overworld", md) == "RIGHT"


def test_step_updates_map_tracking(mock_llm_provider, mock_pyboy):
    """Map transitions must register even when the route policy short-circuits."""
    from unittest.mock import Mock

    from game_state import GameState
    from pokemon_agent import PokemonAgent

    gs = GameState(mock_pyboy, ocr_enabled=False)
    agent = PokemonAgent(mock_llm_provider, gs)
    gs.get_game_info = Mock(return_value={
        "screen_text": "", "frame_count": 100, "game_state": "overworld",
        "party": [], "player_position": (5, 6),
        "current_map": {"map_id": 0x0B, "map_name": "Route 1"},
    })
    gs.execute_action = Mock(return_value=True)
    agent.step()
    assert 0x0B in agent.strategy.visited_maps


class TestEdgeScan:
    """A blocked route direction sweeps along the wall instead of giving up."""

    def _agent(self, mock_llm_provider, mock_pyboy):
        from unittest.mock import Mock

        from game_state import GameState
        from pokemon_agent import PokemonAgent
        gs = GameState(mock_pyboy, ocr_enabled=False)
        agent = PokemonAgent(mock_llm_provider, gs)
        gs.get_game_info = Mock(return_value={
            "screen_text": "", "frame_count": 100, "game_state": "overworld",
            "party": [], "player_position": (10, 1),
            "current_map": {"map_id": 0x00, "map_name": "Pallet Town"},
        })
        agent.new_game_started = True
        agent.character_creation_steps = 60
        agent.step_count = 300
        agent.strategy.mark_goal_complete("start_game")
        return agent

    def test_blocked_north_scans_laterally(self, mock_llm_provider, mock_pyboy):
        agent = self._agent(mock_llm_provider, mock_pyboy)
        agent.blocked_directions.add("UP")
        actions = [agent.get_action() for _ in range(6)]
        # Mostly lateral sweeping, with periodic retries of the blocked
        # direction (blocked_directions is global, so the gap column must
        # still get tried)
        assert any(a in ("LEFT", "RIGHT") for a in actions)
        assert all(a in ("LEFT", "RIGHT", "UP") for a in actions)

    def test_scan_alternates_direction_over_time(self, mock_llm_provider, mock_pyboy):
        agent = self._agent(mock_llm_provider, mock_pyboy)
        agent.blocked_directions.add("UP")
        actions = [agent.get_action() for _ in range(24)]
        lateral = [a for a in actions if a in ("LEFT", "RIGHT")]
        assert set(lateral) == {"LEFT", "RIGHT"}  # sweeps both ways

    def test_unblocked_route_resumes_and_resets_scan(self, mock_llm_provider, mock_pyboy):
        agent = self._agent(mock_llm_provider, mock_pyboy)
        agent.blocked_directions.add("UP")
        agent.get_action()
        agent.blocked_directions.discard("UP")
        assert agent.get_action() == "UP"
        assert agent._edge_scan_steps == 0


def test_edge_scan_retries_the_blocked_direction(mock_llm_provider, mock_pyboy):
    """blocked_directions is global, so the gap column must still be retried."""
    from unittest.mock import Mock

    from game_state import GameState
    from pokemon_agent import PokemonAgent

    gs = GameState(mock_pyboy, ocr_enabled=False)
    agent = PokemonAgent(mock_llm_provider, gs)
    gs.get_game_info = Mock(return_value={
        "screen_text": "", "frame_count": 100, "game_state": "overworld",
        "party": [], "player_position": (10, 1),
        "current_map": {"map_id": 0x00, "map_name": "Pallet Town"},
    })
    agent.new_game_started = True
    agent.character_creation_steps = 60
    agent.step_count = 300
    agent.strategy.mark_goal_complete("start_game")
    agent.blocked_directions.add("UP")
    actions = [agent.get_action() for _ in range(9)]
    assert actions.count("UP") >= 2  # retried while sweeping
    assert any(a in ("LEFT", "RIGHT") for a in actions)


class TestOakTriggerTile:
    """Pallet Town routing aims at the measured cutscene tile (10, 1)."""

    def _suggest(self, pos):
        s = AgentStrategy()
        goal = next(g for g in s.goals if g.name == "get_starter")
        return s.suggest_action_for_goal(goal, "overworld", {
            "current_map": {"map_id": 0x00}, "player_position": pos, "party": [],
        })

    def test_walks_right_toward_the_trigger_column(self):
        assert self._suggest((3, 6)) == "RIGHT"

    def test_walks_left_when_past_the_trigger_column(self):
        assert self._suggest((14, 4)) == "LEFT"

    def test_pushes_north_once_on_the_column(self):
        assert self._suggest((10, 6)) == "UP"
        assert self._suggest((10, 1)) == "UP"
