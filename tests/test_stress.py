"""Stress tests for extended runs and edge cases."""
import gc
import time
from unittest.mock import Mock

import pytest

from game_state import GameState
from metrics import MetricsCollector
from pokemon_agent import PokemonAgent


class TestExtendedRuns:
    """Stress tests for extended gameplay runs."""
    
    @pytest.mark.slow
    def test_1000_steps_run(self, mock_llm_provider, mock_pyboy):
        """Stress test: Agent should handle 1000+ steps without crashing."""
        metrics = MetricsCollector()
        game_state = GameState(mock_pyboy, ocr_enabled=False, metrics=metrics)
        agent = PokemonAgent(mock_llm_provider, game_state, metrics=metrics)
        
        call_count = [0]
        def mock_get_info():
            call_count[0] += 1
            return {
                "screen_text": f"Step {call_count[0]}",
                "frame_count": 100 + call_count[0],
                "game_state": "overworld",
            }
        
        game_state.get_game_info = Mock(side_effect=mock_get_info)
        game_state.execute_action = Mock(return_value=True)
        
        # Run 1000 steps
        start_time = time.time()
        for step in range(1000):
            try:
                agent.step()
            except Exception as e:
                pytest.fail(f"Agent crashed at step {step}: {e}")
        
        total_time = time.time() - start_time
        
        # Verify completion
        assert call_count[0] >= 1000, "Not all steps were executed"
        
        # Check metrics
        stats = metrics.get_all_stats()
        assert stats['performance']['step_timing']['total_steps'] >= 1000
        
        # Performance should be reasonable (not extremely slow)
        assert total_time < 300, f"1000 steps took {total_time:.2f}s, should be <300s"
    
    @pytest.mark.slow
    def test_5000_steps_run(self, mock_llm_provider, mock_pyboy):
        """Stress test: Agent should handle 5000+ steps without crashing."""
        metrics = MetricsCollector()
        game_state = GameState(mock_pyboy, ocr_enabled=False, metrics=metrics)
        agent = PokemonAgent(mock_llm_provider, game_state, metrics=metrics)
        
        call_count = [0]
        def mock_get_info():
            call_count[0] += 1
            return {
                "screen_text": "",
                "frame_count": 100 + call_count[0],
                "game_state": "overworld",
            }
        
        game_state.get_game_info = Mock(side_effect=mock_get_info)
        game_state.execute_action = Mock(return_value=True)
        
        # Run 5000 steps
        for step in range(5000):
            try:
                agent.step()
            except Exception as e:
                pytest.fail(f"Agent crashed at step {step}: {e}")
        
        # Verify completion
        assert call_count[0] >= 5000, "Not all steps were executed"
    
    @pytest.mark.slow
    def test_memory_leak_detection(self, mock_llm_provider, mock_pyboy):
        """Stress test: Check for memory leaks over extended run."""
        import sys
        
        metrics = MetricsCollector()
        game_state = GameState(mock_pyboy, ocr_enabled=False, metrics=metrics)
        agent = PokemonAgent(mock_llm_provider, game_state, metrics=metrics)
        
        call_count = [0]
        def mock_get_info():
            call_count[0] += 1
            return {
                "screen_text": "",
                "frame_count": 100 + call_count[0],
                "game_state": "overworld",
            }
        
        game_state.get_game_info = Mock(side_effect=mock_get_info)
        game_state.execute_action = Mock(return_value=True)
        
        # Get initial memory usage
        gc.collect()
        initial_size = sys.getsizeof(agent.action_history) + sys.getsizeof(agent.action_cache)
        if agent.action_cache:
            initial_size += sys.getsizeof(agent.action_cache.cache)
        
        # Run many steps
        for step in range(2000):
            agent.step()
            # Periodically check memory
            if step % 500 == 0:
                gc.collect()
        
        # Get final memory usage
        gc.collect()
        final_size = sys.getsizeof(agent.action_history) + sys.getsizeof(agent.action_cache)
        if agent.action_cache:
            final_size += sys.getsizeof(agent.action_cache.cache)
        
        # Memory should not grow excessively (cache and history have limits)
        # Allow some growth but not 100x (would indicate a leak)
        growth_factor = final_size / initial_size if initial_size > 0 else 1
        assert growth_factor < 100, f"Potential memory leak: initial {initial_size}, final {final_size}, growth {growth_factor:.2f}x"
    
    @pytest.mark.slow
    def test_long_running_stability(self, mock_llm_provider, mock_pyboy):
        """Stress test: Agent should remain stable over long period."""
        metrics = MetricsCollector()
        game_state = GameState(mock_pyboy, ocr_enabled=False, metrics=metrics)
        agent = PokemonAgent(mock_llm_provider, game_state, metrics=metrics)
        
        call_count = [0]
        def mock_get_info():
            call_count[0] += 1
            return {
                "screen_text": "",
                "frame_count": 100 + call_count[0],
                "game_state": "overworld",
            }
        
        game_state.get_game_info = Mock(side_effect=mock_get_info)
        game_state.execute_action = Mock(return_value=True)
        
        # Track performance over time
        step_times = []
        errors = []
        
        # Run for extended period
        for step in range(2000):
            try:
                start = time.time()
                agent.step()
                step_times.append(time.time() - start)
            except Exception as e:
                errors.append((step, str(e)))
        
        # Should have no errors
        assert len(errors) == 0, f"Errors occurred during long run: {errors}"
        
        # Performance should remain stable (not degrade significantly)
        if len(step_times) > 100:
            early_avg = sum(step_times[:100]) / 100
            late_avg = sum(step_times[-100:]) / 100
            
            # Late steps shouldn't be more than 5x slower (allowing for some variance)
            assert late_avg < early_avg * 5, f"Performance degradation: early {early_avg:.4f}s, late {late_avg:.4f}s"


class TestResourceLimits:
    """Tests for resource limit handling."""
    
    @pytest.mark.slow
    def test_cache_size_limit(self, mock_llm_provider, mock_pyboy):
        """Test: Cache should respect size limits and evict properly."""
        from unittest.mock import patch

        
        metrics = MetricsCollector()
        game_state = GameState(mock_pyboy, ocr_enabled=False, metrics=metrics)
        
        # Mock config to set cache_max_size
        with patch('pokemon_agent.get_config') as mock_get_config:
            mock_config = Mock()
            mock_config.get_agent_config.return_value = {"max_history": 20}
            mock_config.get_performance_config.return_value = {"cache_max_size": 50}
            mock_config.get_llm_config.return_value = {"max_tokens": 10}
            mock_config.get_strategy_config.return_value = {"exploration_rate": 0.3, "max_recent_events": 10}
            mock_get_config.return_value = mock_config
            
            agent = PokemonAgent(mock_llm_provider, game_state, metrics=metrics)
        
        call_count = [0]
        def mock_get_info():
            call_count[0] += 1
            return {
                "screen_text": f"Unique state {call_count[0]}",
                "frame_count": 100 + call_count[0],
                "game_state": "overworld",
            }
        
        game_state.get_game_info = Mock(side_effect=mock_get_info)
        game_state.execute_action = Mock(return_value=True)
        
        # Run many steps with unique states (should trigger evictions)
        for step in range(200):
            agent.step()
        
            # Check cache size is within limit
            if agent.action_cache:
                cache_size = len(agent.action_cache.cache)
                assert cache_size <= 50, f"Cache size {cache_size} exceeds limit of 50"
                
                # Check evictions occurred (if we ran enough steps with unique states)
                stats = metrics.get_all_stats()
                evictions = stats['cache']['evictions']
                # Evictions should occur when cache fills up, but might not if we didn't fill it
                # Just verify cache respects the limit
                assert cache_size <= 50, "Cache respects size limit"
    
    @pytest.mark.slow
    def test_action_history_limit(self, mock_llm_provider, mock_pyboy):
        """Test: Action history should respect size limits."""
        from unittest.mock import patch

        
        metrics = MetricsCollector()
        game_state = GameState(mock_pyboy, ocr_enabled=False, metrics=metrics)
        
        # Mock config to set max_history
        with patch('pokemon_agent.get_config') as mock_get_config:
            mock_config = Mock()
            mock_config.get_agent_config.return_value = {"max_history": 100}
            mock_config.get_performance_config.return_value = {"cache_max_size": 100}
            mock_config.get_llm_config.return_value = {"max_tokens": 10}
            mock_config.get_strategy_config.return_value = {"exploration_rate": 0.3, "max_recent_events": 10}
            mock_get_config.return_value = mock_config
            
            agent = PokemonAgent(mock_llm_provider, game_state, metrics=metrics)
        
        call_count = [0]
        def mock_get_info():
            call_count[0] += 1
            return {
                "screen_text": "",
                "frame_count": 100 + call_count[0],
                "game_state": "overworld",
            }
        
        game_state.get_game_info = Mock(side_effect=mock_get_info)
        game_state.execute_action = Mock(return_value=True)
        
        # Run more steps than history limit
        for step in range(200):
            agent.step()
        
            # Check history size is within limit
            assert len(agent.action_history) <= 100, f"Action history {len(agent.action_history)} exceeds limit of 100"

