"""AI Agent for playing Pokemon Red.

Version: 0.0.5.1
"""
from typing import Optional, List, Dict, Tuple
from collections import deque, Counter
from llm_provider import LLMProvider
from game_state import GameState
from llm_optimizer import ActionCache, PromptOptimizer, RepetitionDetector
from agent_strategy import AgentStrategy, GameEvent
from config import get_config
from pyboy import PyBoy


class PokemonAgent:
    """AI agent that plays Pokemon Red using an LLM."""
    
    SYSTEM_PROMPT = """You play Pokemon Red. Respond with ONLY one action: UP, DOWN, LEFT, RIGHT, A, B, START, SELECT, or WAIT N.
No explanations. Just the action."""

    def __init__(self, llm_provider: LLMProvider, game_state: GameState, use_cache: bool = True,
                 use_strategy: bool = True, goal_check_interval: int = 5):
        """Initialize Pokemon Agent.
        
        Args:
            llm_provider: LLM provider instance
            game_state: GameState instance
            use_cache: Enable action caching (default: True, can be overridden by config)
            use_strategy: Enable goal-oriented strategy (default: True, can be overridden by config)
            goal_check_interval: Check goal completion every N steps (default: 5, higher = less frequent)
        """
        config = get_config()
        agent_config = config.get_agent_config()
        perf_config = config.get_performance_config()
        llm_config = config.get_llm_config()
        
        self.llm_provider = llm_provider
        self.game_state = game_state
        self.action_history: List[str] = []
        self.max_history = agent_config.get("max_history", 20)  # Increased to 20 for diversity checking
        self.action_cache = ActionCache(max_size=perf_config.get("cache_max_size", 100)) if use_cache else None
        self.prompt_optimizer = PromptOptimizer()
        self.repetition_detector = RepetitionDetector()
        
        # Get strategy config for AgentStrategy initialization
        strategy_config = config.get_strategy_config()
        exploration_rate = strategy_config.get("exploration_rate", 0.3)
        max_recent_events = strategy_config.get("max_recent_events", 10)
        
        self.strategy = AgentStrategy(
            exploration_rate=exploration_rate,
            max_recent_events=max_recent_events
        ) if use_strategy else None
        
        self.last_game_state = None
        self.last_position = None
        self.position_history = deque(maxlen=5)
        self.stuck_count = 0
        self.goal_check_interval = max(goal_check_interval, 1)
        self.step_count = 0
        self.max_tokens = llm_config.get("max_tokens", 10)
        
        # Movement validation tracking
        self.movement_failures = {'UP': 0, 'DOWN': 0, 'LEFT': 0, 'RIGHT': 0}
        self.blocked_directions = set()
    
    def get_prompt(self) -> str:
        """Build optimized prompt for the LLM with enhanced context."""
        game_info = self.game_state.get_game_info()
        screen_text = game_info['screen_text'] or ""
        step_count = len(self.action_history)
        recent_actions = self.action_history[-3:] if self.action_history else []
        game_state = game_info.get('game_state', 'unknown')
        
        # Update strategy phase
        if self.strategy:
            memory_data = {
                "player_position": game_info.get('player_position'),
                "current_map": game_info.get('current_map', {}),
                "party": game_info.get('party', []),
                "health": game_info.get('health', {}),
            }
            self.strategy.update_phase(game_state, memory_data)
        
        # Build game state summary
        game_state_summary = None
        if game_info.get('player_position') or game_info.get('party'):
            game_state_summary = {
                "player_position": game_info.get('player_position'),
                "current_map": game_info.get('current_map', {}),
                "party": game_info.get('party', []),
                "health": game_info.get('health', {}),
            }
        
        # Get recent events
        recent_events = None
        if self.strategy:
            recent_events = self.strategy.get_recent_events_summary(3)
        
        # Get strategy context
        strategy_context = None
        if self.strategy:
            memory_data = {
                "player_position": game_info.get('player_position'),
                "current_map": game_info.get('current_map', {}),
                "party": game_info.get('party', []),
                "health": game_info.get('health', {}),
            }
            strategy_context = self.strategy.get_strategy_context(game_state, memory_data)
        
        # Use enhanced prompt with all context
        return self.prompt_optimizer.optimize_prompt(
            screen_text, game_info['frame_count'], step_count, recent_actions, game_state,
            game_state_summary=game_state_summary,
            recent_events=recent_events,
            strategy_context=strategy_context
        )
    
    def get_action(self) -> str:
        """Get next action from the LLM."""
        game_info = self.game_state.get_game_info()
        screen_text = game_info['screen_text'] or ""
        step_count = len(self.action_history)
        game_state = game_info.get('game_state', 'unknown')
        
        # Detect if we're stuck pressing A repeatedly (even if not detected as dialogue)
        # This handles cases where OCR is garbled and dialogue isn't detected
        if len(self.action_history) >= 10:
            recent_actions = self.action_history[-10:]
            a_count = sum(1 for a in recent_actions if a == "A")
            # If 7+ out of last 10 actions are A, likely stuck in dialogue
            if a_count >= 7 and game_state != "battle":
                # Check if we have screen text (indicates dialogue might be present)
                if len(screen_text) > 0:
                    # Check if state has been stable OR if position hasn't changed
                    position = game_info.get('player_position', (0, 0))
                    current_state_key = f"{game_state}|{position}"
                    
                    # If state hasn't changed OR if we're pressing A but not moving, likely stuck
                    if hasattr(self, '_last_state_key'):
                        if self._last_state_key == current_state_key:
                            # Stuck pressing A in same state - save screenshot and try B to break out
                            if not hasattr(self, '_last_stuck_screenshot_step') or step_count - self._last_stuck_screenshot_step > 10:
                                try:
                                    screenshot_path = self.game_state.save_screenshot(
                                        filename=f"stuck_A_repetition_step{step_count}.png"
                                    )
                                    print(f"[STUCK] Saved screenshot: {screenshot_path}")
                                    self._last_stuck_screenshot_step = step_count
                                except Exception as e:
                                    print(f"[STUCK] Failed to save screenshot: {e}")
                            return "B"
                    else:
                        # No previous state, but pressing A repeatedly with text = likely dialogue
                        # Save screenshot and try B to break out
                        if not hasattr(self, '_last_stuck_screenshot_step') or step_count - self._last_stuck_screenshot_step > 10:
                            try:
                                screenshot_path = self.game_state.save_screenshot(
                                    filename=f"stuck_A_repetition_step{step_count}.png"
                                )
                                print(f"[STUCK] Saved screenshot: {screenshot_path}")
                                self._last_stuck_screenshot_step = step_count
                            except Exception as e:
                                print(f"[STUCK] Failed to save screenshot: {e}")
                        return "B"
        
        # First action fallback - use strategy or simple heuristics to avoid LLM call
        if step_count == 0:
            # Use strategy suggestion if available
            if self.strategy:
                current_goal = self.strategy.get_current_goal()
                if current_goal:
                    memory_data = {
                        "player_position": game_info.get('player_position'),
                        "current_map": game_info.get('current_map', {}),
                        "party": game_info.get('party', []),
                        "health": game_info.get('health', {}),
                    }
                    suggested_action = self.strategy.suggest_action_for_goal(
                        current_goal, game_state, memory_data
                    )
                    if suggested_action:
                        return suggested_action
            
            # Fallback to simple heuristics for first action
            if game_state == 'title_screen':
                return "START"
            elif game_state == 'dialog':
                return "A"
            elif game_state == 'menu':
                return "A"
            elif game_state == 'overworld':
                return "UP"  # Default exploration
            else:
                return "A"  # Safe default
        
        # Check for action diversity FIRST (before same-state optimization)
        # This prevents getting stuck in dialogues or repetitive patterns
        is_low_diversity, dominant_action = self.check_action_diversity(window=15, threshold=0.6)
        
        # If pressing A repeatedly and have screen text, likely in dialogue (even if not detected)
        if dominant_action == "A" and len(screen_text) > 0 and game_state == "overworld":
            # Force dialogue state if we're pressing A repeatedly with text
            if is_low_diversity:
                game_state = "dialog"  # Override state detection
        
        if is_low_diversity and dominant_action:
            # Handle dialogue/menu states differently
            if game_state in ['dialog', 'menu']:
                # If stuck pressing A in dialogue, try B or wait
                if dominant_action == "A":
                    # Track how long we've been in same dialogue state
                    state_key = f"{game_state}|{game_info.get('player_position', (0,0))}"
                    if hasattr(self, '_last_state_key') and self._last_state_key == state_key:
                        # Same dialogue state + too many A presses = try B
                        if len(self.action_history) >= 5:
                            # Count recent A presses
                            recent_as = sum(1 for a in self.action_history[-10:] if a == "A")
                            if recent_as >= 7:  # 7+ A presses in last 10 actions
                                # Save screenshot when stuck in dialogue
                                if not hasattr(self, '_last_stuck_screenshot_step') or step_count - self._last_stuck_screenshot_step > 10:
                                    try:
                                        screenshot_path = self.game_state.save_screenshot(
                                            filename=f"stuck_dialog_A_step{step_count}.png"
                                        )
                                        print(f"[STUCK] Saved screenshot: {screenshot_path}")
                                        self._last_stuck_screenshot_step = step_count
                                    except Exception as e:
                                        print(f"[STUCK] Failed to save screenshot: {e}")
                                return "B"
                    # Save screenshot when stuck in dialogue
                    if not hasattr(self, '_last_stuck_screenshot_step') or step_count - self._last_stuck_screenshot_step > 10:
                        try:
                            screenshot_path = self.game_state.save_screenshot(
                                filename=f"stuck_dialog_A_step{step_count}.png"
                            )
                            print(f"[STUCK] Saved screenshot: {screenshot_path}")
                            self._last_stuck_screenshot_step = step_count
                        except Exception as e:
                            print(f"[STUCK] Failed to save screenshot: {e}")
                    return "B"  # Try B to break out of dialogue
                elif dominant_action == "B":
                    # Too many B presses, try A
                    return "A"
            else:
                # For movement actions, force exploration
                # Save screenshot when stuck in repetitive movement
                if not hasattr(self, '_last_stuck_screenshot_step') or step_count - self._last_stuck_screenshot_step > 10:
                    try:
                        screenshot_path = self.game_state.save_screenshot(
                            filename=f"stuck_movement_{dominant_action}_step{step_count}.png"
                        )
                        print(f"[STUCK] Saved screenshot (repetitive {dominant_action}): {screenshot_path}")
                        self._last_stuck_screenshot_step = step_count
                    except Exception as e:
                        print(f"[STUCK] Failed to save screenshot: {e}")
                
                import random
                movement_actions = ['UP', 'DOWN', 'LEFT', 'RIGHT']
                # Exclude the dominant action and blocked directions
                alternative_actions = [
                    a for a in movement_actions 
                    if a != dominant_action and a not in self.blocked_directions
                ]
                if not alternative_actions:
                    # If all alternatives are blocked, try any non-dominant action
                    alternative_actions = [a for a in movement_actions if a != dominant_action]
                if alternative_actions:
                    alt_action = random.choice(alternative_actions)
                    if self.action_cache:
                        cache_key_text = f"{game_state}:{screen_text[:30]}"
                        self.action_cache.set(
                            cache_key_text, game_info['frame_count'], self.action_history, alt_action
                        )
                    return alt_action
        
        # Performance optimization: Skip LLM call if state hasn't changed significantly
        # Use game state + position as key for better caching
        state_key = f"{game_state}|{game_info.get('player_position', (0,0))}"
        
        # Track how long we've been in the same dialogue state
        if hasattr(self, '_last_state_key') and self._last_state_key == state_key:
            # Same state, check if we can reuse last action or use a simple action
            if len(self.action_history) > 0:
                last_action = self.action_history[-1]
                # For dialog/menu states, check if we're stuck
                if game_state in ['dialog', 'menu']:
                    # Count how many times we've been in this same state
                    if not hasattr(self, '_same_state_count'):
                        self._same_state_count = 0
                    self._same_state_count += 1
                    
                    # If stuck in same dialogue for too long, try alternating more aggressively
                    if self._same_state_count > 10:
                        # After 10+ steps in same dialogue, save screenshot and try B if we've been pressing A
                        if last_action == "A":
                            # Save screenshot when stuck in same dialogue for too long
                            if not hasattr(self, '_last_stuck_screenshot_step') or step_count - self._last_stuck_screenshot_step > 10:
                                try:
                                    screenshot_path = self.game_state.save_screenshot(
                                        filename=f"stuck_same_state_step{step_count}.png"
                                    )
                                    print(f"[STUCK] Saved screenshot (same state {self._same_state_count} steps): {screenshot_path}")
                                    self._last_stuck_screenshot_step = step_count
                                except Exception as e:
                                    print(f"[STUCK] Failed to save screenshot: {e}")
                            return "B"
                        else:
                            return "A"
                    
                    # Normal alternation
                    return "A" if last_action != "B" else "B"
                # For overworld, continue movement
                elif game_state == 'overworld' and last_action in ['UP', 'DOWN', 'LEFT', 'RIGHT']:
                    return last_action
        else:
            # State changed, reset counter
            self._same_state_count = 0
        
        self._last_state_key = state_key
        
        # Check cache first (with improved key including game state)
        if self.action_cache:
            # Create a more stable cache key using game state
            cache_key_text = f"{game_state}:{screen_text[:30]}"
            cached_action = self.action_cache.get(
                cache_key_text, game_info['frame_count'], self.action_history
            )
            if cached_action:
                return cached_action
        
        # Check for repetition (before expensive LLM call)
        if len(self.action_history) >= 3:
            is_repeating, alt_action = self.repetition_detector.check(self.action_history[-1])
            if is_repeating and alt_action:
                # Use alternative action instead of calling LLM
                if self.action_cache:
                    cache_key_text = f"{game_state}:{screen_text[:30]}"
                    self.action_cache.set(
                        cache_key_text, game_info['frame_count'], self.action_history, alt_action
                    )
                return alt_action
        
        # Performance optimization: Skip LLM for common predictable states
        if game_state == 'dialog':
            action = "A"  # Always press A to advance dialog
            if self.action_cache:
                cache_key_text = f"{game_state}:{screen_text[:30]}"
                self.action_cache.set(
                    cache_key_text, game_info['frame_count'], self.action_history, action
                )
            return action
        
        # Generate prompt (only if we need to call LLM)
        try:
            prompt = self.get_prompt()
            
            # Call LLM with limited tokens for faster response
            response = self.llm_provider.generate(
                prompt=prompt,
                system_prompt=self.prompt_optimizer.optimize_system_prompt(),
                max_tokens=self.max_tokens  # Configurable token limit
            )
        except Exception as e:
            # If LLM call fails, use fallback action
            print(f"Warning: LLM call failed: {e}")
            print("Using fallback action based on game state")
            
            # Fallback to strategy or simple heuristics
            if self.strategy:
                current_goal = self.strategy.get_current_goal()
                if current_goal:
                    memory_data = {
                        "player_position": game_info.get('player_position'),
                        "current_map": game_info.get('current_map', {}),
                        "party": game_info.get('party', []),
                        "health": game_info.get('health', {}),
                    }
                    suggested_action = self.strategy.suggest_action_for_goal(
                        current_goal, game_state, memory_data
                    )
                    if suggested_action:
                        return suggested_action
            
            # Simple fallback based on game state
            if game_state == 'dialog':
                return "A"
            elif game_state == 'menu':
                return "A"
            elif game_state == 'title_screen':
                return "START"
            elif game_state == 'overworld':
                return "UP"
            else:
                return "A"  # Safe default
        
        # Extract action from response - optimized for short responses
        response_clean = response.strip().upper()
        
        # Direct match for common actions
        valid_buttons = ["UP", "DOWN", "LEFT", "RIGHT", "A", "B", "SELECT", "START"]
        
        # Check for direct match first (most common case)
        for button in valid_buttons:
            if button in response_clean:
                # Extract the button
                if ',' in response_clean:
                    # Handle comma-separated
                    parts = [p.strip() for p in response_clean.split(',')]
                    valid_parts = [p for p in parts if p in valid_buttons]
                    if valid_parts:
                        action = ', '.join(valid_parts[:2])  # Max 2 actions
                    else:
                        action = button
                else:
                    action = button
                
                # Cache and return (with improved cache key)
                if self.action_cache:
                    cache_key_text = f"{game_state}:{screen_text[:30]}"
                    self.action_cache.set(
                        cache_key_text, game_info['frame_count'], self.action_history, action
                    )
                return action
        
        # Check for WAIT command
        if "WAIT" in response_clean:
            parts = response_clean.split()
            if len(parts) >= 2:
                try:
                    wait_frames = int(parts[1])
                    action = f"WAIT {wait_frames}"
                except:
                    action = "WAIT 10"
            else:
                action = "WAIT 10"
            
            # Cache and return (with improved cache key)
            if self.action_cache:
                cache_key_text = f"{game_state}:{screen_text[:30]}"
                self.action_cache.set(
                    cache_key_text, game_info['frame_count'], self.action_history, action
                )
            return action
        
        # Fallback logic
        if len(self.action_history) < 5:
            action = "START"
        else:
            action = "A"
        
        # Cache the action (with improved cache key)
        if self.action_cache:
            cache_key_text = f"{game_state}:{screen_text[:30]}"
            self.action_cache.set(
                cache_key_text, game_info['frame_count'], self.action_history, action
            )
        
        return action
    
    def step(self) -> Dict:
        """Execute one step of the agent.
        
        Returns:
            Dictionary with step information
        """
        # Get current game state before action
        pre_state = self.game_state.get_game_info()
        pre_frame = pre_state['frame_count']
        pre_text = pre_state.get('screen_text', '')
        pre_game_state = pre_state.get('game_state', 'unknown')
        
        # Check if strategy suggests an action
        action = None
        if self.strategy:
            current_goal = self.strategy.get_current_goal()
            if current_goal:
                memory_data = {
                    "player_position": pre_state.get('player_position'),
                    "current_map": pre_state.get('current_map', {}),
                    "party": pre_state.get('party', []),
                    "health": pre_state.get('health', {}),
                }
                suggested_action = self.strategy.suggest_action_for_goal(
                    current_goal, pre_game_state, memory_data
                )
                # Use strategy suggestion if available and not in pure exploration mode
                # Calculate action diversity for adaptive exploration
                action_diversity = self.calculate_action_entropy(window=15) / 3.0  # Normalize to 0-1 range
                if suggested_action and not self.strategy.should_explore(self.stuck_count, action_diversity):
                    action = suggested_action
        
        # Force exploration when stuck (before getting action)
        if self.stuck_count > 5:
            import random
            movement_actions = ['UP', 'DOWN', 'LEFT', 'RIGHT']
            # Exclude blocked directions
            available_actions = [a for a in movement_actions if a not in self.blocked_directions]
            if available_actions:
                action = random.choice(available_actions)
            else:
                # All directions blocked, try any direction
                action = random.choice(movement_actions)
        # Get action from LLM if not suggested by strategy
        elif not action:
            action = self.get_action()
        
        # Execute action
        success = self.game_state.execute_action(action)
        
        # Get updated game state after action
        post_state = self.game_state.get_game_info()
        post_frame = post_state['frame_count']
        post_text = post_state.get('screen_text', '')
        post_game_state = post_state.get('game_state', 'unknown')
        
        # Validate if action had effect (calculate before using)
        state_changed = (
            post_frame != pre_frame or
            post_text != pre_text or
            post_game_state != pre_game_state
        )
        
        # Record event in strategy
        if self.strategy:
            event = GameEvent(
                event_type=post_game_state,
                description=f"Action: {action}, State: {post_game_state}",
                frame_count=post_frame,
                game_state=post_game_state,
                action_taken=action
            )
            self.strategy.add_event(event)
            
            # Check for goal completion (less frequently)
            should_check_goals = (
                self.step_count % self.goal_check_interval == 0 or
                state_changed  # Always check when state changes significantly
            )
            
            if should_check_goals:
                memory_data = {
                    "player_position": post_state.get('player_position'),
                    "current_map": post_state.get('current_map', {}),
                    "party": post_state.get('party', []),
                    "health": post_state.get('health', {}),
                }
                self.strategy.check_goal_completion(memory_data, post_game_state)
        
        # Update step count
        self.step_count += 1
        
        # Multi-modal stuck detection
        current_state_key = f"{post_game_state}|{post_text[:20]}"
        pre_position = pre_state.get('player_position')
        post_position = post_state.get('player_position')
        
        # Track position history
        if post_position:
            self.position_history.append(post_position)
        
        # Check multiple signals for stuck detection
        stuck_signals = {
            'state_key_same': current_state_key == self.last_game_state,
            'position_unchanged': (
                pre_position == post_position 
                and action in ['UP', 'DOWN', 'LEFT', 'RIGHT']
                and pre_position is not None
                and post_position is not None
            ),
            'action_repetition': self._check_action_repetition(action, window=10)
        }
        
        # Require 2+ signals to trigger stuck state
        is_stuck = sum(stuck_signals.values()) >= 2
        
        if is_stuck:
            self.stuck_count += 1
        else:
            self.stuck_count = 0
            self.last_game_state = current_state_key
            self.last_position = post_position
        
        # Validate movement
        if action in ['UP', 'DOWN', 'LEFT', 'RIGHT']:
            movement_valid, alt_action = self.validate_movement(action, pre_position, post_position)
            if not movement_valid and alt_action:
                # Movement failed, but we already executed the action
                # Store this info for next step
                pass
        
        # Update history
        self.action_history.append(action)
        if len(self.action_history) > self.max_history:
            self.action_history.pop(0)
        
        # Update step count in game_state for memory checking
        self.game_state._step_count = self.step_count
        
        # Get progress summary
        progress_summary = None
        if self.strategy:
            progress_summary = self.strategy.get_progress_summary()
        
        return {
            "action": action,
            "success": success,
            "game_info": post_state,
            "state_changed": state_changed,
            "stuck_count": self.stuck_count,
            "progress": progress_summary,
        }
    
    def _check_action_repetition(self, action: str, window: int = 10) -> bool:
        """Check if action is being repeated too frequently.
        
        Args:
            action: Current action
            window: Number of recent actions to check
            
        Returns:
            True if action repetition detected
        """
        if len(self.action_history) < window:
            return False
        
        recent = list(self.action_history[-window:])
        action_counts = Counter(recent)
        most_common_count = action_counts.most_common(1)[0][1]
        
        # If same action appears > 60% of the time, consider it repetitive
        return most_common_count / len(recent) > 0.6
    
    def check_action_diversity(self, window: int = 15, threshold: float = 0.6) -> Tuple[bool, Optional[str]]:
        """Check if action diversity is too low.
        
        Args:
            window: Number of recent actions to analyze
            threshold: Ratio threshold (0.0 to 1.0) - if one action exceeds this, diversity is low
            
        Returns:
            (is_low_diversity, most_common_action) tuple
        """
        if len(self.action_history) < window:
            return False, None
        
        recent = list(self.action_history[-window:])
        action_counts = Counter(recent)
        most_common_ratio = action_counts.most_common(1)[0][1] / len(recent)
        
        if most_common_ratio > threshold:
            return True, action_counts.most_common(1)[0][0]
        return False, None
    
    def validate_movement(self, action: str, pre_position: Optional[tuple], 
                          post_position: Optional[tuple], threshold: int = 3) -> Tuple[bool, Optional[str]]:
        """Validate that movement action actually moved the player.
        
        Args:
            action: Movement action taken
            pre_position: Position before action
            post_position: Position after action
            threshold: Number of failures before considering direction blocked
            
        Returns:
            (is_valid, alternative_action) tuple
        """
        if action not in ['UP', 'DOWN', 'LEFT', 'RIGHT']:
            return True, None
        
        if pre_position is None or post_position is None:
            return True, None  # Can't validate without position data
        
        if pre_position == post_position:
            # Movement didn't occur - likely hitting wall
            self.movement_failures[action] += 1
            if self.movement_failures[action] >= threshold:
                self.blocked_directions.add(action)
                # Try perpendicular direction
                perpendicular = {
                    'UP': ['LEFT', 'RIGHT'],
                    'DOWN': ['LEFT', 'RIGHT'],
                    'LEFT': ['UP', 'DOWN'],
                    'RIGHT': ['UP', 'DOWN']
                }
                import random
                alt_direction = random.choice(perpendicular[action])
                return False, alt_direction
        else:
            # Movement succeeded, reset counter
            self.movement_failures[action] = 0
            if action in self.blocked_directions:
                self.blocked_directions.remove(action)
        
        return True, None
    
    def calculate_action_entropy(self, window: int = 15) -> float:
        """Calculate entropy of action distribution.
        
        Args:
            window: Number of recent actions to analyze
            
        Returns:
            Entropy value (higher = more diverse)
        """
        if len(self.action_history) < window:
            return 0.0
        
        from math import log2
        
        recent = list(self.action_history[-window:])
        action_counts = Counter(recent)
        total = len(recent)
        
        entropy = 0.0
        for count in action_counts.values():
            p = count / total
            if p > 0:
                entropy -= p * log2(p)
        
        return entropy

