"""Unit tests for the two-tier planner."""
from unittest.mock import Mock

from planner import PlannerAgent


def make_planner(response="Head north to Viridian City. Avoid pressing B in menus.",
                 interval=25, min_gap=10):
    provider = Mock()
    provider.generate = Mock(return_value=response)
    return PlannerAgent(provider, interval=interval, min_gap=min_gap), provider


def info(map_id=0, game_state="overworld", **kw):
    base = {
        "game_state": game_state,
        "current_map": {"map_id": map_id, "map_name": "Pallet Town"},
        "player_position": (5, 5),
        "party": [],
        "screen_text": "",
    }
    base.update(kw)
    return base


class TestTriggers:
    def test_plans_immediately_on_first_call(self):
        planner, provider = make_planner()
        plan = planner.maybe_plan(step_count=0, game_info=info())
        assert plan is not None
        assert provider.generate.call_count == 1

    def test_no_replan_within_min_gap(self):
        planner, provider = make_planner(min_gap=10)
        planner.maybe_plan(step_count=0, game_info=info())
        # Even a map change within the gap is suppressed
        planner.maybe_plan(step_count=5, game_info=info(map_id=1))
        assert provider.generate.call_count == 1

    def test_replans_on_interval(self):
        planner, provider = make_planner(interval=25)
        planner.maybe_plan(step_count=0, game_info=info())
        planner.maybe_plan(step_count=24, game_info=info())
        assert provider.generate.call_count == 1
        planner.maybe_plan(step_count=25, game_info=info())
        assert provider.generate.call_count == 2

    def test_replans_on_map_change_after_gap(self):
        planner, provider = make_planner(interval=100, min_gap=10)
        planner.maybe_plan(step_count=0, game_info=info(map_id=0))
        planner.maybe_plan(step_count=12, game_info=info(map_id=1))
        assert provider.generate.call_count == 2

    def test_replans_on_stuck_streak(self):
        planner, provider = make_planner(interval=100, min_gap=10)
        planner.maybe_plan(step_count=0, game_info=info())
        planner.maybe_plan(step_count=15, game_info=info(), stuck_count=9)
        assert provider.generate.call_count == 2

    def test_replans_on_goal_completion(self):
        planner, provider = make_planner(interval=100, min_gap=10)
        planner.maybe_plan(step_count=0, game_info=info(), completed_goals=0)
        planner.maybe_plan(step_count=15, game_info=info(), completed_goals=1)
        assert provider.generate.call_count == 2

    def test_quiet_steps_do_not_plan(self):
        planner, provider = make_planner(interval=100, min_gap=10)
        planner.maybe_plan(step_count=0, game_info=info())
        for step in range(11, 50):
            planner.maybe_plan(step_count=step, game_info=info())
        assert provider.generate.call_count == 1


class TestOutputCleaning:
    def test_strips_think_block(self):
        planner, _ = make_planner(
            response="<think>The player has no starter yet, so...</think>Go to Oak's lab."
        )
        plan = planner.maybe_plan(step_count=0, game_info=info())
        assert plan == "Go to Oak's lab."

    def test_strips_unterminated_think_block(self):
        # Token limit can cut generation off mid-thought
        planner, _ = make_planner(response="<think>Endless reasoning that never closes")
        plan = planner.maybe_plan(step_count=0, game_info=info())
        # Whole output was reasoning: no usable plan
        assert plan is None

    def test_empty_response_keeps_previous_plan(self):
        planner, provider = make_planner(interval=1, min_gap=1)
        planner.maybe_plan(step_count=0, game_info=info())
        first = planner.current_plan
        provider.generate = Mock(return_value="   ")
        plan = planner.maybe_plan(step_count=5, game_info=info())
        assert plan == first


class TestFailureSafety:
    def test_provider_error_keeps_previous_plan(self):
        planner, provider = make_planner(interval=1, min_gap=1)
        planner.maybe_plan(step_count=0, game_info=info())
        first = planner.current_plan
        provider.generate = Mock(side_effect=ValueError("ollama down"))
        plan = planner.maybe_plan(step_count=5, game_info=info())
        assert plan == first  # no raise, plan preserved

    def test_error_does_not_retry_every_step(self):
        planner, provider = make_planner(interval=25, min_gap=10)
        provider.generate = Mock(side_effect=ValueError("ollama down"))
        planner.maybe_plan(step_count=0, game_info=info())
        planner.maybe_plan(step_count=1, game_info=info())
        planner.maybe_plan(step_count=2, game_info=info())
        # Failed attempt still consumes the slot; retries wait for the gap
        assert provider.generate.call_count == 1


class TestAgentIntegration:
    def test_plan_injected_into_prompt(self, mock_llm_provider, mock_pyboy):
        from unittest.mock import Mock as M

        from game_state import GameState
        from pokemon_agent import PokemonAgent

        planner, _ = make_planner(response="Head north to Route 1.")
        game_state = GameState(mock_pyboy, ocr_enabled=False)
        agent = PokemonAgent(mock_llm_provider, game_state, planner=planner)

        game_state.get_game_info = M(return_value={
            "screen_text": "PALLET TOWN",
            "frame_count": 100,
            "game_state": "overworld",
            "party": [],
            "player_position": (5, 5),
            "current_map": {"map_id": 0, "map_name": "Pallet Town"},
        })

        planner.maybe_plan(step_count=0, game_info=game_state.get_game_info())
        prompt = agent.get_prompt()
        assert "Head north to Route 1." in prompt

    def test_agent_without_planner_unchanged(self, mock_llm_provider, mock_pyboy):
        from unittest.mock import Mock as M

        from game_state import GameState
        from pokemon_agent import PokemonAgent

        game_state = GameState(mock_pyboy, ocr_enabled=False)
        agent = PokemonAgent(mock_llm_provider, game_state)
        game_state.get_game_info = M(return_value={
            "screen_text": "",
            "frame_count": 100,
            "game_state": "overworld",
            "party": [],
        })
        # No planner: step() must run without error
        result = agent.step()
        assert result["action"] is not None
