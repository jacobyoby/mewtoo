"""Unit tests for the multimodal stuck-time navigation advisor."""
from unittest.mock import Mock

import numpy as np

from vision import VisionAdvisor


def frame():
    return np.full((144, 160, 3), 128, dtype=np.uint8)


def advisor(reply="LEFT"):
    v = VisionAdvisor(cooldown_steps=10)
    v.client = Mock()
    v.client.chat = Mock(return_value={"message": {"content": reply}})
    return v


class TestDirectionParsing:
    def test_plain_direction(self):
        assert advisor("LEFT")._parse_direction("LEFT") == "LEFT"

    def test_direction_in_a_sentence(self):
        assert advisor()._parse_direction("The player should go UP.") == "UP"

    def test_lowercase_and_punctuation(self):
        assert advisor()._parse_direction("go right!") == "RIGHT"

    def test_no_direction_returns_none(self):
        assert advisor()._parse_direction("I cannot tell from this image.") is None

    def test_empty_reply(self):
        assert advisor()._parse_direction("") is None


class TestCooldown:
    def test_first_call_is_ready(self):
        assert advisor().is_ready(0) is True

    def test_blocked_during_cooldown(self):
        v = advisor()
        v.suggest_direction(frame(), step_count=100)
        assert v.is_ready(105) is False

    def test_ready_after_cooldown(self):
        v = advisor()
        v.suggest_direction(frame(), step_count=100)
        assert v.is_ready(110) is True

    def test_suggest_respects_cooldown(self):
        v = advisor()
        v.suggest_direction(frame(), step_count=100)
        assert v.suggest_direction(frame(), step_count=101) is None
        assert v.client.chat.call_count == 1


class TestFailureSafety:
    def test_model_error_returns_none(self):
        v = advisor()
        v.client.chat = Mock(side_effect=RuntimeError("ollama down"))
        assert v.suggest_direction(frame(), step_count=0) is None

    def test_missing_image_returns_none(self):
        assert advisor().suggest_direction(None, step_count=0) is None

    def test_unparseable_reply_returns_none(self):
        assert advisor("I'm not sure").suggest_direction(frame(), step_count=0) is None


class TestAgentIntegration:
    def _agent(self, mock_llm_provider, mock_pyboy, vision):
        from game_state import GameState
        from pokemon_agent import PokemonAgent
        gs = GameState(mock_pyboy, ocr_enabled=False)
        agent = PokemonAgent(mock_llm_provider, gs, vision=vision)
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

    def test_vision_consulted_when_stuck(self, mock_llm_provider, mock_pyboy):
        v = advisor("LEFT")
        agent = self._agent(mock_llm_provider, mock_pyboy, v)
        agent.stuck_count = 8
        assert agent.get_action() == "LEFT"

    def test_vision_not_consulted_when_moving_fine(self, mock_llm_provider, mock_pyboy):
        v = advisor("LEFT")
        agent = self._agent(mock_llm_provider, mock_pyboy, v)
        agent.stuck_count = 0
        agent.get_action()
        assert v.client.chat.call_count == 0  # too slow to run when unstuck

    def test_agent_runs_without_vision(self, mock_llm_provider, mock_pyboy):
        agent = self._agent(mock_llm_provider, mock_pyboy, None)
        agent.stuck_count = 8
        assert agent.get_action() is not None


class TestVisionOnForcedExploration:
    """step() short-circuits to random movement when stuck; vision must run there."""

    def _agent(self, mock_llm_provider, mock_pyboy, vision):
        from game_state import GameState
        from pokemon_agent import PokemonAgent
        gs = GameState(mock_pyboy, ocr_enabled=False)
        agent = PokemonAgent(mock_llm_provider, gs, vision=vision)
        gs.get_game_info = Mock(return_value={
            "screen_text": "", "frame_count": 100, "game_state": "overworld",
            "party": [], "player_position": (10, 1),
            "current_map": {"map_id": 0x00, "map_name": "Pallet Town"},
        })
        gs.execute_action = Mock(return_value=True)
        agent.new_game_started = True
        agent.character_creation_steps = 60
        agent.step_count = 300
        agent.stuck_count = 8  # forced-exploration territory
        return agent

    def test_vision_used_instead_of_random_movement(self, mock_llm_provider, mock_pyboy):
        v = advisor("RIGHT")
        agent = self._agent(mock_llm_provider, mock_pyboy, v)
        result = agent.step()
        assert v.client.chat.call_count == 1
        assert result["action"] == "RIGHT"

    def test_falls_back_to_random_when_vision_declines(self, mock_llm_provider, mock_pyboy):
        v = advisor("no idea")
        agent = self._agent(mock_llm_provider, mock_pyboy, v)
        result = agent.step()
        assert result["action"] in ("UP", "DOWN", "LEFT", "RIGHT")

    def test_no_vision_still_explores(self, mock_llm_provider, mock_pyboy):
        agent = self._agent(mock_llm_provider, mock_pyboy, None)
        result = agent.step()
        assert result["action"] in ("UP", "DOWN", "LEFT", "RIGHT")


class TestConstantAnswerGuard:
    """A VLM that answers the same direction every time is defaulting, not looking."""

    def test_retires_itself_after_repeated_identical_answers(self):
        v = advisor("RIGHT")
        v.cooldown_steps = 0
        results = [v.suggest_direction(frame(), step_count=i) for i in range(8)]
        assert results[0] == "RIGHT"
        assert v.disabled is True
        assert results[-1] is None

    def test_varied_answers_keep_vision_alive(self):
        v = advisor()
        v.cooldown_steps = 0
        replies = iter(["UP", "LEFT", "UP", "RIGHT", "DOWN", "LEFT"])
        v.client.chat = Mock(side_effect=lambda **kw: {"message": {"content": next(replies)}})
        for i in range(6):
            v.suggest_direction(frame(), step_count=i)
        assert v.disabled is False

    def test_disabled_advisor_stops_calling_the_model(self):
        v = advisor("DOWN")
        v.cooldown_steps = 0
        for i in range(8):
            v.suggest_direction(frame(), step_count=i)
        calls_before = v.client.chat.call_count
        v.suggest_direction(frame(), step_count=99)
        assert v.client.chat.call_count == calls_before
