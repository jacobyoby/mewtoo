"""LLM call optimizations for Pokemon agent."""
import hashlib
from collections import Counter


class ActionCache:
    """Cache actions for similar game states with LRU eviction."""
    
    def __init__(self, max_size: int = 100):
        """Initialize action cache.
        
        Args:
            max_size: Maximum number of cached entries
        """
        self.cache: dict[str, str] = {}
        self.access_order: list[str] = []  # Track access order for LRU
        self.max_size = max_size
        self.hits = 0
        self.misses = 0
        self.evictions = 0
    
    def _get_key(self, screen_text: str, frame_count: int, recent_actions: list) -> str:
        """Generate cache key from game state."""
        # Normalize screen text (remove whitespace, lowercase)
        normalized_text = screen_text.lower().strip()[:50]  # First 50 chars
        
        # Create key from normalized state
        state_str = f"{normalized_text}|{frame_count // 100}|{','.join(recent_actions[-3:])}"
        return hashlib.md5(state_str.encode()).hexdigest()
    
    def get(self, screen_text: str, frame_count: int, recent_actions: list) -> str | None:
        """Get cached action if available.
        
        Returns:
            Cached action or None
        """
        key = self._get_key(screen_text, frame_count, recent_actions)
        if key in self.cache:
            self.hits += 1
            # Update access order (move to end = most recently used)
            if key in self.access_order:
                self.access_order.remove(key)
            self.access_order.append(key)
            return self.cache[key]
        self.misses += 1
        return None
    
    def set(self, screen_text: str, frame_count: int, recent_actions: list, action: str):
        """Cache an action.
        
        Args:
            screen_text: Screen text
            frame_count: Frame count
            recent_actions: Recent actions
            action: Action to cache
        """
        key = self._get_key(screen_text, frame_count, recent_actions)
        
        # Evict least recently used if cache is full
        if len(self.cache) >= self.max_size and key not in self.cache:
            # Remove least recently used (first in access_order)
            if self.access_order:
                lru_key = self.access_order.pop(0)
                del self.cache[lru_key]
                self.evictions += 1
        
        self.cache[key] = action
        # Update access order
        if key in self.access_order:
            self.access_order.remove(key)
        self.access_order.append(key)
    
    def get_stats(self) -> dict:
        """Get cache statistics."""
        total = self.hits + self.misses
        hit_rate = (self.hits / total * 100) if total > 0 else 0
        return {
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": hit_rate,
            "size": len(self.cache),
            "max_size": self.max_size,
            "evictions": self.evictions
        }


class PromptOptimizer:
    """Optimize prompts for faster LLM responses with enhanced context."""
    
    @staticmethod
    def optimize_prompt(screen_text: str, frame_count: int, step_count: int, recent_actions: list, 
                       game_state: str = "unknown", game_state_summary: dict | None = None,
                       recent_events: str | None = None, strategy_context: dict | None = None) -> str:
        """Create optimized, concise prompt with better context.
        
        Args:
            screen_text: Screen text
            frame_count: Frame count
            step_count: Step count
            recent_actions: Recent actions
            game_state: Detected game state (title_screen, menu, battle, dialog, overworld)
            game_state_summary: Optional game state summary with memory data
            recent_events: Optional recent events summary
            strategy_context: Optional strategy context (goals, phase, etc.)
        
        Returns:
            Optimized prompt
        """
        # Truncate screen text but keep important parts
        if screen_text:
            # Keep first 80 chars, prioritize lines with more text
            lines = screen_text.split('\n')
            important_lines = [line for line in lines if len(line.strip()) > 3]
            if important_lines:
                screen_text_short = ' '.join(important_lines[:2])[:80]
            else:
                screen_text_short = screen_text[:60]
        else:
            screen_text_short = "(no text detected)"
        
        # Only include last 3 actions
        recent = recent_actions[-3:] if recent_actions else []
        
        # Build game state summary
        state_summary_parts = []
        if game_state_summary:
            if "player_position" in game_state_summary:
                pos = game_state_summary["player_position"]
                if pos and pos != (0, 0):
                    state_summary_parts.append(f"Position: ({pos[0]}, {pos[1]})")
            
            if "current_map" in game_state_summary:
                map_name = game_state_summary["current_map"].get("map_name", "Unknown")
                if map_name != "Unknown":
                    state_summary_parts.append(f"Location: {map_name}")
            
            if "party" in game_state_summary:
                party = game_state_summary["party"]
                if party:
                    state_summary_parts.append(f"Party: {len(party)} Pokemon")
                    # Show first Pokemon info
                    first_pokemon = party[0]
                    state_summary_parts.append(
                        f"  - Level {first_pokemon.get('level', '?')}, "
                        f"HP {first_pokemon.get('hp_current', 0)}/{first_pokemon.get('hp_max', 0)}"
                    )
            
            if "health" in game_state_summary:
                health = game_state_summary["health"]
                hp_percent = health.get("total_hp_percent", 0)
                if hp_percent > 0:
                    state_summary_parts.append(f"Party Health: {hp_percent:.0f}%")
        
        state_summary = "\n".join(state_summary_parts) if state_summary_parts else "No state data"
        
        # Build strategy context
        strategy_info = ""
        if strategy_context:
            strategy_parts = []
            if "current_goal" in strategy_context and strategy_context["current_goal"] != "none":
                strategy_parts.append(f"Goal: {strategy_context.get('goal_description', 'Unknown')}")
            if "phase" in strategy_context:
                strategy_parts.append(f"Phase: {strategy_context['phase']}")
            if "completed_goals" in strategy_context and strategy_context["completed_goals"]:
                strategy_parts.append(f"Completed: {', '.join(strategy_context['completed_goals'][-3:])}")
            
            strategy_info = "\n".join(strategy_parts) if strategy_parts else ""
        
        # Context-aware hints based on game state
        hint = PromptOptimizer._get_context_hint(game_state, step_count, recent_actions, strategy_context)
        
        # Action explanations
        action_explanations = PromptOptimizer._get_action_explanations(game_state, strategy_context, step_count)
        
        # Build prompt
        prompt_parts = [
            f"Game State: {game_state}",
            f"Screen: {screen_text_short}",
            f"Step: {step_count} | Frame: {frame_count} | Recent Actions: {','.join(recent) if recent else 'none'}",
        ]
        
        # Add game state summary
        if state_summary != "No state data":
            prompt_parts.append(f"\nGame State Summary:\n{state_summary}")
        
        # Add strategy context
        if strategy_info:
            prompt_parts.append(f"\nStrategy:\n{strategy_info}")
        
        # Add recent events
        if recent_events:
            prompt_parts.append(f"\nRecent Events:\n{recent_events}")
        
        # Add hints and explanations
        prompt_parts.append(f"\nHint: {hint}")
        if action_explanations:
            prompt_parts.append(f"\nAction Explanations:\n{action_explanations}")
        
        prompt_parts.append("\nWhat action should you take? (UP, DOWN, LEFT, RIGHT, A, B, START, SELECT, or WAIT N)")
        
        return "\n".join(prompt_parts)
    
    @staticmethod
    def _get_context_hint(game_state: str, step_count: int, recent_actions: list, 
                         strategy_context: dict | None = None) -> str:
        """Get context-aware hint based on game state."""
        if game_state == "title_screen":
            return "Title screen - press START to begin new game"
        elif game_state == "menu":
            # Check if we're in character creation (early menu after title screen)
            # Don't suggest B during character creation as it cancels new game
            if step_count < 50:
                return "In menu/character creation - use UP/DOWN to navigate, A to select (DO NOT press B - it will cancel new game)"
            return "In menu - use UP/DOWN to navigate, A to select, B to cancel"
        elif game_state == "battle":
            return "In battle - choose actions carefully. A to attack, B to use items, UP/DOWN to select"
        elif game_state == "dialog":
            return "Reading dialog - press A to continue, B to cancel"
        elif game_state == "overworld":
            if strategy_context and strategy_context.get("current_goal") == "reach_viridian":
                return "Exploring - move UP/NORTH to reach Route 1 and Viridian City"
            elif strategy_context and strategy_context.get("current_goal") == "get_starter":
                return "Navigating to get starter Pokemon - follow dialog prompts"
            else:
                return "Exploring - move with arrows, A to interact with objects/NPCs"
        elif step_count < 5:
            return "Starting game - navigate menus to begin"
        else:
            return "Playing - explore and progress through the game"
    
    @staticmethod
    def _get_action_explanations(game_state: str, strategy_context: dict | None = None, step_count: int = 0) -> str:
        """Get explanations for available actions."""
        explanations = []
        
        if game_state == "title_screen":
            explanations.append("START - Begin new game")
        elif game_state == "menu":
            explanations.append("UP/DOWN - Navigate menu options")
            explanations.append("A - Select current option")
            # Don't suggest B during early game (character creation)
            # B during character creation cancels new game!
            if step_count >= 50:  # Only suggest B after character creation is done
                explanations.append("B - Go back/cancel")
            else:
                explanations.append("WARNING: DO NOT press B - you are creating a new character, B will cancel!")
        elif game_state == "battle":
            explanations.append("A - Confirm selection (attack, item, etc.)")
            explanations.append("UP/DOWN - Navigate battle menu")
            explanations.append("B - Cancel/go back")
        elif game_state == "dialog":
            explanations.append("A - Continue dialog")
            explanations.append("B - Cancel/skip dialog (if possible)")
        elif game_state == "overworld":
            explanations.append("UP/DOWN/LEFT/RIGHT - Move player")
            explanations.append("A - Interact (talk, check, use)")
            explanations.append("B - Run (in battle) or cancel")
            if strategy_context and strategy_context.get("current_goal") == "reach_viridian":
                explanations.append("-> Move UP/NORTH to progress toward Viridian City")
        
        return "\n".join(explanations) if explanations else ""
    
    @staticmethod
    def optimize_system_prompt() -> str:
        """Create optimized system prompt."""
        return """You are playing Pokemon Red. Your goal is to progress through the game efficiently.
Respond with ONLY one action: UP, DOWN, LEFT, RIGHT, A, B, START, SELECT, or WAIT N.
Consider the game state, your current goal, and recent events when choosing actions.
No explanations. Just the action."""


class RepetitionDetector:
    """Detect and handle action repetition and patterns."""
    
    def __init__(self, threshold: int = 3, pattern_threshold: int = 2):
        """Initialize repetition detector.
        
        Args:
            threshold: Number of repeated actions before triggering
            pattern_threshold: Number of pattern repetitions before triggering
        """
        self.threshold = threshold
        self.pattern_threshold = pattern_threshold
        self.last_action = None
        self.repeat_count = 0
        self.action_history: list[str] = []
        self.max_history = 10
    
    def check(self, action: str) -> tuple[bool, str | None]:
        """Check if action is repeating or stuck in a pattern.
        
        Returns:
            (is_repeating, suggested_action)
        """
        # Add to history
        self.action_history.append(action)
        if len(self.action_history) > self.max_history:
            self.action_history.pop(0)
        
        # Check for simple repetition (same action N times)
        if action == self.last_action:
            self.repeat_count += 1
            if self.repeat_count >= self.threshold:
                return self._suggest_alternative(action, "repetition")
        else:
            self.last_action = action
            self.repeat_count = 1
        
        # Check for statistical patterns (e.g., mostly UP)
        stat_pattern, stat_action, stat_ratio = self.detect_statistical_pattern()
        if stat_pattern:
            return self._suggest_alternative(stat_action, f"Statistical pattern: {stat_ratio:.0%} {stat_action}")
        
        # Check for patterns (e.g., A-A-SELECT repeating)
        if len(self.action_history) >= 6:
            # Check for common stuck patterns
            patterns = [
                (["A", "A", "SELECT"], "A-A-SELECT pattern detected"),
                (["SELECT", "A", "A"], "SELECT-A-A pattern detected"),
                (["A", "SELECT", "A"], "A-SELECT-A pattern detected"),
                (["START", "A", "START"], "START-A-START pattern detected"),
            ]
            
            for pattern, description in patterns:
                if self._pattern_matches(pattern):
                    return self._suggest_alternative(action, description)
        
        return False, None
    
    def _pattern_matches(self, pattern: list[str]) -> bool:
        """Check if recent history matches a pattern."""
        if len(self.action_history) < len(pattern) * self.pattern_threshold:
            return False
        
        # Check last N occurrences of pattern
        recent = self.action_history[-len(pattern) * self.pattern_threshold:]
        
        # Check if pattern repeats
        for i in range(self.pattern_threshold):
            start_idx = i * len(pattern)
            end_idx = start_idx + len(pattern)
            if recent[start_idx:end_idx] != pattern:
                return False
        
        return True
    
    def _suggest_alternative(self, current_action: str, reason: str) -> tuple[bool, str | None]:
        """Suggest an alternative action based on current action and reason."""
        # Smart alternatives based on action type
        alternatives = {
            "START": ["A", "WAIT 10"],
            "A": ["B", "WAIT 10", "UP"],
            "SELECT": ["A", "B", "WAIT 10"],
            "B": ["A", "START"],
            "UP": ["DOWN", "A", "RIGHT"],
            "DOWN": ["UP", "A", "LEFT"],
            "LEFT": ["RIGHT", "A", "UP"],
            "RIGHT": ["LEFT", "A", "DOWN"],
        }
        
        # Get alternatives for current action
        if current_action in alternatives:
            # Try first alternative
            alt = alternatives[current_action][0]
        else:
            # Default: wait or try different button
            alt = "WAIT 10"
        
        return True, alt
    
    def detect_statistical_pattern(self, window: int = 15, threshold: float = 0.6) -> tuple[bool, str | None, float]:
        """Detect statistical patterns (e.g., mostly UP).
        
        Args:
            window: Number of recent actions to analyze
            threshold: Ratio threshold (0.0 to 1.0) - if one action exceeds this, pattern detected
            
        Returns:
            (is_pattern, dominant_action, ratio) tuple
        """
        if len(self.action_history) < window:
            return False, None, 0.0
        
        recent = list(self.action_history[-window:])
        action_counts = Counter(recent)
        
        total = len(recent)
        for action, count in action_counts.items():
            ratio = count / total
            if ratio > threshold:
                return True, action, ratio
        
        return False, None, 0.0

