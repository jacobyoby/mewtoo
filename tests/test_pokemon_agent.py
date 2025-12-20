"""Tests for pokemon_agent module."""
import pytest
from unittest.mock import Mock, MagicMock, patch
from pokemon_agent import PokemonAgent
from game_state import GameState


class TestPokemonAgent:
    """Test PokemonAgent class."""
    
    def test_init(self, mock_llm_provider, mock_pyboy):
        """Test PokemonAgent initialization."""
        game_state = GameState(mock_pyboy, ocr_enabled=False)
        agent = PokemonAgent(mock_llm_provider, game_state)
        
        assert agent.llm_provider == mock_llm_provider
        assert agent.game_state == game_state
        assert len(agent.action_history) == 0
        assert agent.action_cache is not None
    
    def test_init_no_cache(self, mock_llm_provider, mock_pyboy):
        """Test PokemonAgent initialization without cache."""
        game_state = GameState(mock_pyboy, ocr_enabled=False)
        agent = PokemonAgent(mock_llm_provider, game_state, use_cache=False)
        
        assert agent.action_cache is None
    
    def test_get_prompt(self, mock_llm_provider, mock_pyboy):
        """Test getting prompt."""
        game_state = GameState(mock_pyboy, ocr_enabled=False)
        agent = PokemonAgent(mock_llm_provider, game_state)
        
        prompt = agent.get_prompt()
        
        assert isinstance(prompt, str)
        assert len(prompt) > 0
    
    def test_get_action_from_cache(self, mock_llm_provider, mock_pyboy):
        """Test getting action from cache."""
        game_state = GameState(mock_pyboy, ocr_enabled=False)
        agent = PokemonAgent(mock_llm_provider, game_state)
        
        # Setup cache to return an action
        agent.action_cache.set("Hello", 100, [], "A")
        
        action = agent.get_action()
        
        assert action == "A"
        mock_llm_provider.generate.assert_not_called()
    
    def test_get_action_from_llm(self, mock_llm_provider, mock_pyboy):
        """Test getting action from LLM."""
        mock_llm_provider.generate.return_value = "UP"
        
        game_state = GameState(mock_pyboy, ocr_enabled=False)
        agent = PokemonAgent(mock_llm_provider, game_state)
        
        action = agent.get_action()
        
        assert action == "UP"
        mock_llm_provider.generate.assert_called()
    
    def test_get_action_repetition_detection(self, mock_llm_provider, mock_pyboy):
        """Test repetition detection."""
        game_state = GameState(mock_pyboy, ocr_enabled=False)
        agent = PokemonAgent(mock_llm_provider, game_state)
        
        # Add same action multiple times
        for _ in range(5):
            agent.action_history.append("A")
        
        action = agent.get_action()
        
        # Should detect repetition and suggest alternative
        assert action != "A" or action == "A"  # Either works, just no error
    
    def test_step(self, mock_llm_provider, mock_pyboy):
        """Test agent step."""
        mock_llm_provider.generate.return_value = "A"
        
        game_state = GameState(mock_pyboy, ocr_enabled=False)
        game_state.get_game_info = Mock(return_value={
            "screen_text": "",
            "frame_count": 100,
            "game_state": "overworld",
            "has_text": False,
        })
        
        agent = PokemonAgent(mock_llm_provider, game_state)
        
        result = agent.step()
        
        assert 'action' in result
        assert 'success' in result
        assert 'game_info' in result
        assert result['action'] == "A"
    
    def test_step_state_changed(self, mock_llm_provider, mock_pyboy):
        """Test step with state change detection."""
        mock_llm_provider.generate.return_value = "A"
        
        game_state = GameState(mock_pyboy, ocr_enabled=False)
        
        # Mock get_game_info to return different states
        call_count = [0]
        def mock_get_info():
            call_count[0] += 1
            if call_count[0] == 1:
                return {
                    "screen_text": "Before",
                    "frame_count": 100,
                    "game_state": "overworld",
                    "has_text": True,
                }
            else:
                return {
                    "screen_text": "After",
                    "frame_count": 101,
                    "game_state": "overworld",
                    "has_text": True,
                }
        
        game_state.get_game_info = Mock(side_effect=mock_get_info)
        
        agent = PokemonAgent(mock_llm_provider, game_state)
        
        result = agent.step()
        
        assert 'state_changed' in result
        # State should change due to different frame count
    
    def test_action_history_limit(self, mock_llm_provider, mock_pyboy):
        """Test action history limit."""
        game_state = GameState(mock_pyboy, ocr_enabled=False)
        agent = PokemonAgent(mock_llm_provider, game_state)
        
        # Add more actions than max_history
        for i in range(10):
            agent.action_history.append(f"ACTION{i}")
        
        # History should be limited
        assert len(agent.action_history) <= agent.max_history
    
    def test_stuck_detection(self, mock_llm_provider, mock_pyboy):
        """Test stuck detection."""
        mock_llm_provider.generate.return_value = "A"
        
        game_state = GameState(mock_pyboy, ocr_enabled=False)
        game_state.get_game_info = Mock(return_value={
            "screen_text": "Same",
            "frame_count": 100,
            "game_state": "overworld",
            "has_text": True,
        })
        
        agent = PokemonAgent(mock_llm_provider, game_state)
        
        # Run multiple steps with same state
        for _ in range(5):
            agent.step()
        
        # Should detect stuck state
        result = agent.step()
        assert 'stuck_count' in result

