"""Tests for llm_optimizer module."""
import pytest
from llm_optimizer import ActionCache, PromptOptimizer, RepetitionDetector


class TestActionCache:
    """Test ActionCache class."""
    
    def test_init(self):
        """Test ActionCache initialization."""
        cache = ActionCache(max_size=50)
        assert cache.max_size == 50
        assert cache.hits == 0
        assert cache.misses == 0
        assert len(cache.cache) == 0
    
    def test_get_key(self):
        """Test cache key generation."""
        cache = ActionCache()
        key1 = cache._get_key("Hello", 100, ["A", "B"])
        key2 = cache._get_key("Hello", 100, ["A", "B"])
        key3 = cache._get_key("World", 100, ["A", "B"])
        
        # Same inputs should produce same key
        assert key1 == key2
        # Different inputs should produce different key
        assert key1 != key3
    
    def test_get_miss(self):
        """Test cache miss."""
        cache = ActionCache()
        result = cache.get("Hello", 100, ["A"])
        
        assert result is None
        assert cache.misses == 1
        assert cache.hits == 0
    
    def test_set_and_get(self):
        """Test setting and getting from cache."""
        cache = ActionCache()
        
        # Set a value
        cache.set("Hello", 100, ["A"], "B")
        
        # Get it back
        result = cache.get("Hello", 100, ["A"])
        
        assert result == "B"
        assert cache.hits == 1
        assert cache.misses == 0
    
    def test_max_size(self):
        """Test cache size limit."""
        cache = ActionCache(max_size=2)
        
        # Add 3 items
        cache.set("Text1", 100, ["A"], "B1")
        cache.set("Text2", 200, ["B"], "B2")
        cache.set("Text3", 300, ["C"], "B3")
        
        # First item should be evicted
        result1 = cache.get("Text1", 100, ["A"])
        assert result1 is None
        
        # Last two should still be there
        result2 = cache.get("Text2", 200, ["B"])
        result3 = cache.get("Text3", 300, ["C"])
        assert result2 == "B2"
        assert result3 == "B3"


class TestPromptOptimizer:
    """Test PromptOptimizer class."""
    
    def test_init(self):
        """Test PromptOptimizer initialization."""
        optimizer = PromptOptimizer()
        assert optimizer is not None
    
    def test_optimize_prompt(self):
        """Test prompt optimization."""
        optimizer = PromptOptimizer()
        
        prompt = optimizer.optimize_prompt(
            screen_text="Hello",
            frame_count=100,
            step_count=5,
            recent_actions=["A", "B"],
            game_state="overworld"
        )
        
        assert isinstance(prompt, str)
        assert len(prompt) > 0
        assert "Hello" in prompt or "overworld" in prompt
    
    def test_optimize_system_prompt(self):
        """Test system prompt optimization."""
        optimizer = PromptOptimizer()
        system_prompt = optimizer.optimize_system_prompt()
        
        assert isinstance(system_prompt, str)
        assert len(system_prompt) > 0


class TestRepetitionDetector:
    """Test RepetitionDetector class."""
    
    def test_init(self):
        """Test RepetitionDetector initialization."""
        detector = RepetitionDetector()
        assert detector.pattern_threshold == 2  # Default is 2, not 3
        assert len(detector.action_history) == 0
    
    def test_check_adds_to_history(self):
        """Test that check() adds actions to history."""
        detector = RepetitionDetector()
        detector.check("A")
        detector.check("B")
        
        assert len(detector.action_history) == 2
        assert detector.action_history[0] == "A"
        assert detector.action_history[1] == "B"
    
    def test_check_no_repetition(self):
        """Test checking for repetition when none exists."""
        detector = RepetitionDetector()
        detector.check("A")
        detector.check("B")
        detector.check("C")
        
        is_repeating, alt = detector.check("D")
        
        assert not is_repeating
        assert alt is None
    
    def test_check_repetition(self):
        """Test detecting repetition."""
        detector = RepetitionDetector()
        
        # Check same action multiple times (threshold is 3)
        for _ in range(3):
            is_repeating, alt = detector.check("A")
            if _ < 2:  # First two times should not trigger
                assert not is_repeating
        
        # Third time should trigger repetition
        is_repeating, alt = detector.check("A")
        assert is_repeating
        assert alt is not None
        assert alt != "A"
    
    def test_pattern_matches(self):
        """Test pattern matching."""
        detector = RepetitionDetector(pattern_threshold=2)
        
        # Add pattern multiple times (need at least pattern_threshold * len(pattern) actions)
        pattern = ["A", "B"]
        for _ in range(4):  # 2 * 2 = 4 actions needed
            detector.check("A")
            detector.check("B")
        
        matches = detector._pattern_matches(pattern)
        assert matches
    
    def test_suggest_alternative(self):
        """Test suggesting alternative action."""
        detector = RepetitionDetector()
        
        is_repeating, alt = detector._suggest_alternative("A", "repetitive")
        
        assert is_repeating is True
        assert alt is not None
        assert alt != "A"
        # Should return a tuple (bool, str)
        assert isinstance(alt, str)
        assert alt in ["B", "WAIT 10", "UP"]  # First alternative for "A"

