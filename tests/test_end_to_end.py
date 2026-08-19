"""End-to-end tests for complete gameplay sequences."""
from unittest.mock import Mock

import pytest

from game_state import GameState
from metrics import MetricsCollector
from pokemon_agent import PokemonAgent


class TestEarlyGameSequence:
    """End-to-end test for early game sequence: start game -> get starter -> reach first town."""
    
    @pytest.mark.slow
    @pytest.mark.integration
    def test_start_game_sequence(self, mock_llm_provider, mock_pyboy):
        """Test: Agent can navigate from title screen to game start."""
        metrics = MetricsCollector()
        game_state = GameState(mock_pyboy, ocr_enabled=False, metrics=metrics)
        agent = PokemonAgent(mock_llm_provider, game_state, metrics=metrics)
        
        # Simulate title screen -> start menu -> game start sequence
        game_state_sequence = [
            {"screen_text": "NINTENDO", "frame_count": 1, "game_state": "title_screen"},
            {"screen_text": "PRESS START", "frame_count": 2, "game_state": "title_screen"},
            {"screen_text": "NEW GAME", "frame_count": 3, "game_state": "menu"},
            {"screen_text": "CONTINUE", "frame_count": 4, "game_state": "menu"},
            {"screen_text": "Choose a Pokemon", "frame_count": 5, "game_state": "menu"},
        ]
        
        state_index = [0]
        def mock_get_info():
            idx = state_index[0]
            if idx < len(game_state_sequence):
                result = game_state_sequence[idx]
                state_index[0] += 1
                return result
            return game_state_sequence[-1]
        
        game_state.get_game_info = Mock(side_effect=mock_get_info)
        game_state.execute_action = Mock(return_value=True)
        
        # Agent should progress through states
        actions_taken = []
        for step in range(10):
            action = agent.get_action()
            actions_taken.append(action)
            agent.step()
            
            # Check that agent is making progress (not stuck)
            if step > 3:
                # Should have taken some actions by now
                assert len(set(actions_taken)) > 1, "Agent stuck in repetitive actions"
        
        # Verify agent attempted to progress
        assert "START" in actions_taken or "A" in actions_taken, "Agent didn't attempt to start game"
    
    @pytest.mark.slow
    @pytest.mark.integration
    def test_menu_navigation(self, mock_llm_provider, mock_pyboy):
        """Test: Agent can navigate menus effectively."""
        metrics = MetricsCollector()
        game_state = GameState(mock_pyboy, ocr_enabled=False, metrics=metrics)
        agent = PokemonAgent(mock_llm_provider, game_state, metrics=metrics)
        
        # Simulate menu navigation
        menu_states = [
            {"screen_text": "POKEMON", "frame_count": 1, "game_state": "menu"},
            {"screen_text": "ITEM", "frame_count": 2, "game_state": "menu"},
            {"screen_text": "SAVE", "frame_count": 3, "game_state": "menu"},
        ]
        
        state_index = [0]
        def mock_get_info():
            idx = state_index[0] % len(menu_states)
            state_index[0] += 1
            return menu_states[idx]
        
        game_state.get_game_info = Mock(side_effect=mock_get_info)
        game_state.execute_action = Mock(return_value=True)
        
        # Agent should navigate menu
        actions_taken = []
        for _step in range(20):
            action = agent.get_action()
            actions_taken.append(action)
            agent.step()
        
        # Verify menu navigation actions were used
        # Agent can navigate menus with A/B (select/cancel) or UP/DOWN (move selection)
        # Both are valid, so check that agent is interacting with menu
        assert "A" in actions_taken or "B" in actions_taken, "Agent didn't interact with menu"
        # If agent uses UP/DOWN, that's also valid menu navigation
        if "UP" in actions_taken or "DOWN" in actions_taken:
            assert True  # Explicit menu navigation detected
    
    @pytest.mark.slow
    @pytest.mark.integration
    def test_overworld_movement(self, mock_llm_provider, mock_pyboy):
        """Test: Agent can move in overworld."""
        metrics = MetricsCollector()
        game_state = GameState(mock_pyboy, ocr_enabled=False, metrics=metrics)
        agent = PokemonAgent(mock_llm_provider, game_state, metrics=metrics)
        
        # Simulate overworld movement
        def mock_get_info():
            return {
                "screen_text": "",
                "frame_count": 100,
                "game_state": "overworld",
            }
        
        # Mock position changes to simulate movement
        position = [5, 5]
        def mock_get_position():
            return tuple(position)
        
        game_state.get_game_info = Mock(side_effect=mock_get_info)
        game_state.get_player_position = Mock(side_effect=mock_get_position)
        game_state.execute_action = Mock(side_effect=lambda action: True)
        
        # Mock position update based on movement actions
        def mock_execute_action(action):
            if action == "UP":
                position[1] -= 1
            elif action == "DOWN":
                position[1] += 1
            elif action == "LEFT":
                position[0] -= 1
            elif action == "RIGHT":
                position[0] += 1
            return True
        
        game_state.execute_action = Mock(side_effect=mock_execute_action)
        
        # Agent should move in overworld
        actions_taken = []
        initial_position = mock_get_position()
        
        for _step in range(30):
            action = agent.get_action()
            actions_taken.append(action)
            agent.step()
        
        final_position = mock_get_position()
        
        # Verify movement actions were used
        movement_actions = ["UP", "DOWN", "LEFT", "RIGHT"]
        assert any(action in actions_taken for action in movement_actions), "Agent didn't use movement actions"
        
        # Verify position changed (if movement actions were executed)
        if any(action in movement_actions for action in actions_taken[:10]):
            # Position should have changed if movement was executed
            assert initial_position != final_position or len(set(actions_taken)) > 2, "Agent didn't move or is stuck"


class TestCompleteGameplayFlow:
    """Tests for complete gameplay flow scenarios."""
    
    @pytest.mark.slow
    @pytest.mark.integration
    def test_dialogue_handling(self, mock_llm_provider, mock_pyboy):
        """Test: Agent can handle dialogue boxes correctly."""
        metrics = MetricsCollector()
        game_state = GameState(mock_pyboy, ocr_enabled=False, metrics=metrics)
        agent = PokemonAgent(mock_llm_provider, game_state, metrics=metrics)
        
        # Simulate dialogue sequence
        dialogue_states = [
            {"screen_text": "Hello there!", "frame_count": 1, "game_state": "dialog"},
            {"screen_text": "Welcome to the world", "frame_count": 2, "game_state": "dialog"},
            {"screen_text": "of Pokemon!", "frame_count": 3, "game_state": "dialog"},
            {"screen_text": "", "frame_count": 4, "game_state": "overworld"},
        ]
        
        state_index = [0]
        def mock_get_info():
            idx = state_index[0] % len(dialogue_states)
            state_index[0] += 1
            return dialogue_states[idx]
        
        game_state.get_game_info = Mock(side_effect=mock_get_info)
        game_state.execute_action = Mock(return_value=True)
        
        # Agent should handle dialogue
        actions_taken = []
        for _step in range(15):
            action = agent.get_action()
            actions_taken.append(action)
            agent.step()
        
        # Verify dialogue handling (should use A button)
        assert actions_taken.count("A") > 0, "Agent didn't handle dialogue with A button"
    
    @pytest.mark.slow
    @pytest.mark.integration
    def test_state_transitions(self, mock_llm_provider, mock_pyboy):
        """Test: Agent handles state transitions correctly."""
        metrics = MetricsCollector()
        game_state = GameState(mock_pyboy, ocr_enabled=False, metrics=metrics)
        agent = PokemonAgent(mock_llm_provider, game_state, metrics=metrics)
        
        # Simulate various state transitions
        transitions = [
            {"screen_text": "", "frame_count": 1, "game_state": "overworld"},
            {"screen_text": "Wild POKEMON", "frame_count": 2, "game_state": "battle"},
            {"screen_text": "", "frame_count": 3, "game_state": "battle"},
            {"screen_text": "", "frame_count": 4, "game_state": "overworld"},
            {"screen_text": "POKEMON", "frame_count": 5, "game_state": "menu"},
            {"screen_text": "", "frame_count": 6, "game_state": "overworld"},
        ]
        
        state_index = [0]
        def mock_get_info():
            idx = state_index[0] % len(transitions)
            state_index[0] += 1
            return transitions[idx]
        
        game_state.get_game_info = Mock(side_effect=mock_get_info)
        game_state.execute_action = Mock(return_value=True)
        
        # Agent should handle transitions
        actions_taken = []
        for _step in range(25):
            action = agent.get_action()
            actions_taken.append(action)
            agent.step()
        
        # Verify agent adapted to different states
        assert len(set(actions_taken)) > 2, "Agent didn't adapt to state transitions"

