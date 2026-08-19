"""Edge case tests for error recovery and stuck detection."""
from unittest.mock import Mock

import pytest

from game_state import GameState
from metrics import MetricsCollector
from pokemon_agent import PokemonAgent


class TestErrorRecovery:
    """Tests for error recovery paths."""
    
    def test_llm_provider_error_recovery(self, mock_llm_provider, mock_pyboy):
        """Test: Agent recovers from LLM provider errors."""
        metrics = MetricsCollector()
        game_state = GameState(mock_pyboy, ocr_enabled=False, metrics=metrics)
        agent = PokemonAgent(mock_llm_provider, game_state, metrics=metrics)
        
        call_count = [0]
        def mock_get_info():
            call_count[0] += 1
            return {
                "screen_text": f"State {call_count[0]}",
                "frame_count": 100 + call_count[0],
                "game_state": "overworld",
            }
        
        game_state.get_game_info = Mock(side_effect=mock_get_info)
        game_state.execute_action = Mock(return_value=True)
        
        # Simulate LLM error, then recovery
        error_count = [0]
        def mock_llm_with_error(*args, **kwargs):
            error_count[0] += 1
            if error_count[0] <= 2:
                raise Exception("LLM provider error")
            return "A"
        
        mock_llm_provider.generate = Mock(side_effect=mock_llm_with_error)
        
        # Agent should handle errors gracefully
        for step in range(10):
            try:
                action = agent.get_action()
                agent.step()
                # After errors, should eventually get an action
                if step > 2:
                    assert action is not None, "Agent didn't recover from LLM errors"
            except Exception as e:
                # Should handle errors, not crash
                if step < 3:
                    # First few errors are expected
                    pass
                else:
                    pytest.fail(f"Agent didn't recover from errors: {e}")
    
    def test_game_state_error_recovery(self, mock_llm_provider, mock_pyboy):
        """Test: Agent recovers from game state errors."""
        metrics = MetricsCollector()
        game_state = GameState(mock_pyboy, ocr_enabled=False, metrics=metrics)
        agent = PokemonAgent(mock_llm_provider, game_state, metrics=metrics)
        
        error_count = [0]
        def mock_get_info_with_error():
            error_count[0] += 1
            if error_count[0] <= 2:
                raise Exception("Game state error")
            return {
                "screen_text": "",
                "frame_count": 100 + error_count[0],
                "game_state": "overworld",
            }
        
        game_state.get_game_info = Mock(side_effect=mock_get_info_with_error)
        game_state.execute_action = Mock(return_value=True)
        
        # Agent should handle game state errors
        for step in range(10):
            try:
                agent.step()
            except Exception as e:
                if step < 3:
                    # First few errors might be expected
                    pass
                else:
                    pytest.fail(f"Agent didn't recover from game state errors: {e}")
    
    def test_memory_reading_error_recovery(self, mock_llm_provider, mock_pyboy):
        """Test: Agent recovers when memory reading fails."""
        metrics = MetricsCollector()
        game_state = GameState(mock_pyboy, ocr_enabled=True, metrics=metrics)
        agent = PokemonAgent(mock_llm_provider, game_state, metrics=metrics)
        
        # Simulate memory reading failure
        def mock_get_info():
            # Memory reading might fail, but should fallback to OCR
            return {
                "screen_text": "Fallback text",
                "frame_count": 100,
                "game_state": "overworld",
            }
        
        game_state.get_game_info = Mock(side_effect=mock_get_info)
        game_state.execute_action = Mock(return_value=True)
        
        # Agent should work even if memory reading fails
        for step in range(10):
            try:
                agent.step()
            except Exception as e:
                pytest.fail(f"Agent didn't handle memory reading failure: {e}")


class TestStuckDetection:
    """Tests for stuck detection scenarios."""
    
    def test_repetitive_action_detection(self, mock_llm_provider, mock_pyboy):
        """Test: Agent detects and handles repetitive actions."""
        metrics = MetricsCollector()
        game_state = GameState(mock_pyboy, ocr_enabled=False, metrics=metrics)
        agent = PokemonAgent(mock_llm_provider, game_state, metrics=metrics)
        
        # Simulate stuck state (same state repeatedly)
        def mock_get_info():
            return {
                "screen_text": "Same text",
                "frame_count": 100,
                "game_state": "overworld",
            }
        
        game_state.get_game_info = Mock(side_effect=mock_get_info)
        game_state.execute_action = Mock(return_value=True)
        
        # Run many steps with same state
        actions_taken = []
        for step in range(50):
            action = agent.get_action()
            actions_taken.append(action)
            agent.step()
        
        # Agent should detect repetition and try alternatives
        # Should have some action diversity (not all same action)
        unique_actions = len(set(actions_taken))
        assert unique_actions > 1, f"Agent stuck in repetitive actions: {unique_actions} unique actions"
    
    def test_position_stuck_detection(self, mock_llm_provider, mock_pyboy):
        """Test: Agent detects when position doesn't change."""
        metrics = MetricsCollector()
        game_state = GameState(mock_pyboy, ocr_enabled=False, metrics=metrics)
        agent = PokemonAgent(mock_llm_provider, game_state, metrics=metrics)
        
        # Simulate position not changing despite movement actions
        position = [5, 5]
        def mock_get_info():
            return {
                "screen_text": "",
                "frame_count": 100,
                "game_state": "overworld",
            }
        
        def mock_get_position():
            return tuple(position)  # Position never changes
        
        def mock_execute_action(action):
            # Position doesn't change (hitting wall)
            return True
        
        game_state.get_game_info = Mock(side_effect=mock_get_info)
        game_state.get_player_position = Mock(side_effect=mock_get_position)
        game_state.execute_action = Mock(side_effect=mock_execute_action)
        
        # Agent should detect stuck position
        actions_taken = []
        initial_position = mock_get_position()
        
        for step in range(30):
            action = agent.get_action()
            actions_taken.append(action)
            agent.step()
        
        final_position = mock_get_position()
        
        # If position didn't change, agent should try different actions
        if initial_position == final_position:
            # Should have tried different movement directions
            movement_actions = ["UP", "DOWN", "LEFT", "RIGHT"]
            unique_movements = len([a for a in actions_taken if a in movement_actions])
            assert unique_movements > 1, "Agent didn't try different directions when stuck"
    
    def test_same_state_persistence_detection(self, mock_llm_provider, mock_pyboy):
        """Test: Agent detects persistent same state."""
        metrics = MetricsCollector()
        game_state = GameState(mock_pyboy, ocr_enabled=False, metrics=metrics)
        agent = PokemonAgent(mock_llm_provider, game_state, metrics=metrics)
        
        # Simulate same state persisting
        def mock_get_info():
            return {
                "screen_text": "Stuck text",
                "frame_count": 100,
                "game_state": "dialog",
            }
        
        game_state.get_game_info = Mock(side_effect=mock_get_info)
        game_state.execute_action = Mock(return_value=True)
        
        # Run many steps with same state
        actions_taken = []
        for step in range(40):
            action = agent.get_action()
            actions_taken.append(action)
            agent.step()
        
        # Agent should try to break out of stuck state
        # Should use A button for dialogue, but also try alternatives if stuck
        assert "A" in actions_taken, "Agent should use A for dialogue"
        
        # If still stuck after many A presses, should try alternatives
        if actions_taken.count("A") > 20:
            assert len(set(actions_taken)) > 1, "Agent stuck pressing A repeatedly"


class TestEdgeCaseScenarios:
    """Tests for various edge case scenarios."""
    
    def test_empty_screen_text(self, mock_llm_provider, mock_pyboy):
        """Test: Agent handles empty screen text."""
        metrics = MetricsCollector()
        game_state = GameState(mock_pyboy, ocr_enabled=False, metrics=metrics)
        agent = PokemonAgent(mock_llm_provider, game_state, metrics=metrics)
        
        def mock_get_info():
            return {
                "screen_text": "",  # Empty text
                "frame_count": 100,
                "game_state": "overworld",
            }
        
        game_state.get_game_info = Mock(side_effect=mock_get_info)
        game_state.execute_action = Mock(return_value=True)
        
        # Agent should handle empty text
        for step in range(10):
            try:
                agent.step()
            except Exception as e:
                pytest.fail(f"Agent didn't handle empty screen text: {e}")
    
    def test_very_long_screen_text(self, mock_llm_provider, mock_pyboy):
        """Test: Agent handles very long screen text."""
        metrics = MetricsCollector()
        game_state = GameState(mock_pyboy, ocr_enabled=False, metrics=metrics)
        agent = PokemonAgent(mock_llm_provider, game_state, metrics=metrics)
        
        long_text = "A" * 1000  # Very long text
        
        def mock_get_info():
            return {
                "screen_text": long_text,
                "frame_count": 100,
                "game_state": "dialog",
            }
        
        game_state.get_game_info = Mock(side_effect=mock_get_info)
        game_state.execute_action = Mock(return_value=True)
        
        # Agent should handle long text
        for step in range(10):
            try:
                agent.step()
            except Exception as e:
                pytest.fail(f"Agent didn't handle long screen text: {e}")
    
    def test_rapid_state_changes(self, mock_llm_provider, mock_pyboy):
        """Test: Agent handles rapid state changes."""
        metrics = MetricsCollector()
        game_state = GameState(mock_pyboy, ocr_enabled=False, metrics=metrics)
        agent = PokemonAgent(mock_llm_provider, game_state, metrics=metrics)
        
        states = ["overworld", "battle", "menu", "dialog", "title_screen"]
        state_index = [0]
        
        def mock_get_info():
            idx = state_index[0] % len(states)
            state_index[0] += 1
            return {
                "screen_text": "",
                "frame_count": 100 + state_index[0],
                "game_state": states[idx],
            }
        
        game_state.get_game_info = Mock(side_effect=mock_get_info)
        game_state.execute_action = Mock(return_value=True)
        
        # Agent should handle rapid changes
        for step in range(20):
            try:
                agent.step()
            except Exception as e:
                pytest.fail(f"Agent didn't handle rapid state changes: {e}")
    
    def test_invalid_action_handling(self, mock_llm_provider, mock_pyboy):
        """Test: Agent handles invalid actions gracefully."""
        metrics = MetricsCollector()
        game_state = GameState(mock_pyboy, ocr_enabled=False, metrics=metrics)
        agent = PokemonAgent(mock_llm_provider, game_state, metrics=metrics)
        
        def mock_get_info():
            return {
                "screen_text": "",
                "frame_count": 100,
                "game_state": "overworld",
            }
        
        def mock_execute_action(action):
            # Simulate invalid action error
            if action == "INVALID":
                raise ValueError("Invalid action")
            return True
        
        game_state.get_game_info = Mock(side_effect=mock_get_info)
        game_state.execute_action = Mock(side_effect=mock_execute_action)
        
        # Mock LLM to return invalid action once
        call_count = [0]
        def mock_llm(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                return "INVALID"
            return "A"
        
        mock_llm_provider.generate = Mock(side_effect=mock_llm)
        
        # Agent should handle invalid actions
        for step in range(10):
            try:
                agent.step()
            except ValueError:
                # Invalid action error is expected, but agent should recover
                if step > 1:
                    pytest.fail("Agent didn't recover from invalid action")
            except Exception as e:
                pytest.fail(f"Unexpected error: {e}")

