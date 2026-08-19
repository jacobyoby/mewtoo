"""AI Agent for playing Pokemon Red.

Version: 0.0.7
"""
import logging
import random
import time
from collections import Counter, deque

from agent_strategy import AgentStrategy, GameEvent
from config import get_config
from early_game import EarlyGameHandler
from game_state import GameState
from llm_optimizer import ActionCache, PromptOptimizer, RepetitionDetector
from llm_provider import LLMProvider
from metrics import MetricsCollector

logger = logging.getLogger(__name__)


class PokemonAgent:
    """AI agent that plays Pokemon Red using an LLM."""
    
    SYSTEM_PROMPT = """You play Pokemon Red. Respond with ONLY one action: UP, DOWN, LEFT, RIGHT, A, B, START, SELECT, or WAIT N.
No explanations. Just the action."""

    def __init__(self, llm_provider: LLMProvider, game_state: GameState, use_cache: bool = True,
                 use_strategy: bool = True, goal_check_interval: int = 5, metrics: MetricsCollector | None = None):
        """Initialize Pokemon Agent.
        
        Args:
            llm_provider: LLM provider instance
            game_state: GameState instance
            use_cache: Enable action caching (default: True, can be overridden by config)
            use_strategy: Enable goal-oriented strategy (default: True, can be overridden by config)
            goal_check_interval: Check goal completion every N steps (default: 5, higher = less frequent)
            metrics: Optional metrics collector instance
        """
        config = get_config()
        agent_config = config.get_agent_config()
        perf_config = config.get_performance_config()
        llm_config = config.get_llm_config()
        
        self.llm_provider = llm_provider
        self.game_state = game_state
        self.action_history: list[str] = []
        self.max_history = agent_config.get("max_history", 20)  # Increased to 20 for diversity checking
        self.action_cache = ActionCache(max_size=perf_config.get("cache_max_size", 100)) if use_cache else None
        self.loading_state_steps = 0  # Track consecutive steps in loading state
        self.blank_screen_steps = 0  # Track consecutive steps with blank screen (regardless of state)
        self.new_game_started = False  # Track if we've started a new game (prevent backing out)
        self.character_creation_steps = 0  # Track steps in character creation
        self.early_game_handler = EarlyGameHandler()  # Scripted naming-screen sequences
        self.prompt_optimizer = PromptOptimizer()
        self.repetition_detector = RepetitionDetector()
        self.metrics = metrics  # Store metrics collector
        
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
    
    def _save_stuck_screenshot(self, step_count: int, reason: str, details: dict | None = None):
        """Save screenshot when agent is stuck.
        
        Args:
            step_count: Current step count
            reason: Reason for being stuck (e.g., 'multi_modal_stuck', 'repetitive_action', etc.)
            details: Optional dictionary with additional details about the stuck state
        """
        try:
            # Check if screen is blank before saving screenshot
            screen_image = self.game_state.get_screen_image()
            blank_info = self.game_state.detect_blank_screen(screen_image)
            
            if blank_info['is_blank']:
                # Screen is blank - don't save screenshot, but log the issue
                logger.debug(f"[STUCK] Skipping screenshot - screen is blank ({blank_info['blank_type']}, {blank_info['white_percentage']:.1%} white, {blank_info['black_percentage']:.1%} black)")
                logger.info(f"[STUCK] Stuck reason: {reason}, Step: {step_count}")
                if details:
                    logger.debug(f"[STUCK] Details: {details}")
                return
            
            # Screen has content - save screenshot
            # Create descriptive filename
            filename = f"stuck_{reason}_step{step_count}"
            if details:
                # Add key details to filename
                if 'action' in details:
                    filename += f"_{details['action']}"
                if 'stuck_count' in details:
                    filename += f"_count{details['stuck_count']}"
            filename += ".png"
            
            screenshot_path = self.game_state.save_screenshot(filename=filename)
            logger.info(f"[STUCK] Saved screenshot ({reason}): {screenshot_path}")
            if details:
                logger.debug(f"[STUCK] Details: {details}")
        except Exception as e:
            logger.warning(f"[STUCK] Failed to save screenshot: {e}")
    
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
        
        # CRITICAL: Check for blank screen FIRST, before other logic
        # Blank screens often indicate transitions that need A presses
        screen_image = self.game_state.get_screen_image()
        blank_info = self.game_state.detect_blank_screen(screen_image)
        
        if blank_info['is_blank']:
            self.blank_screen_steps += 1
            # Blank screen detected - handle it aggressively
            # Blank screens during gameplay usually need A presses to progress
            if self.blank_screen_steps > 20:
                # Stuck on blank screen for too long - try aggressive actions
                actions_to_try = ['A', 'START', 'A', 'A']  # More A presses
                action_idx = (self.blank_screen_steps - 21) % len(actions_to_try)
                logger.info(f"[BLANK_SCREEN] Step {step_count}: Blank screen for {self.blank_screen_steps} steps, trying {actions_to_try[action_idx]}")
                return actions_to_try[action_idx]
            elif self.blank_screen_steps > 10:
                # After 10 steps on blank screen, press A more aggressively
                logger.info(f"[BLANK_SCREEN] Step {step_count}: Blank screen for {self.blank_screen_steps} steps, pressing A")
                return 'A'
            elif self.blank_screen_steps > 3:
                # After 3 steps, start pressing A to progress through transition
                return 'A'
            else:
                # Early blank screen - wait briefly then press A
                return 'WAIT 1' if self.blank_screen_steps == 1 else 'A'
        else:
            # Screen has content - reset blank screen counter
            if self.blank_screen_steps > 0:
                self.blank_screen_steps = 0
        
        # Detect if we're in character creation/naming screens
        # These screens appear after selecting "New Game"
        screen_text_upper = screen_text.upper()
        is_character_creation = (
            any(word in screen_text_upper for word in ["NAME", "WHAT", "BOY", "GIRL", "ARE YOU A BOY", "ARE YOU A GIRL"]) or
            (game_state == 'menu' and step_count < 50)  # Early menu after title screen is likely character creation
        )
        
        # Track if we've started a new game
        if not self.new_game_started:
            # Check if we've moved past title screen (indicates new game started)
            if game_state != 'title_screen' and step_count > 5:
                # Check if we're in character creation or early game
                if is_character_creation or game_state in ['menu', 'dialog']:
                    self.new_game_started = True
                    self.character_creation_steps = 0
        
        # Track character creation persistence
        if is_character_creation or (self.new_game_started and self.character_creation_steps < 50):
            self.character_creation_steps += 1
        else:
            if self.character_creation_steps > 0:
                self.character_creation_steps = 0
        
        # Scripted naming-screen handling. The NAME? menu and letter grid
        # cannot be completed by the generic "always press A" policy (A on
        # NEW NAME enters the grid, where A just types letters forever) -- the
        # reason get_starter validated at 0%. The handler recognizes those
        # screens from OCR text, returns short deterministic sequences
        # (DOWN,A to pick a preset name; A,START,A to finish a grid entry),
        # and latches off permanently once the party is non-empty.
        party_size = len(game_info.get('party', []) or [])
        early_action = self.early_game_handler.next_action(
            screen_text, game_state, party_size
        )
        if early_action is not None:
            logger.info(f"[EARLY_GAME] Step {step_count}: scripted {early_action} "
                  f"for naming/confirm screen")
            return early_action

        # Track loading state persistence
        if game_state == 'loading':
            self.loading_state_steps += 1
        else:
            self.loading_state_steps = 0
        
        # Handle loading state - blank screens need special handling
        if game_state == 'loading':
            # Check if screen is actually blank
            screen_image = self.game_state.get_screen_image()
            blank_info = self.game_state.detect_blank_screen(screen_image)
            
            if blank_info['is_blank']:
                # Screen is blank - need to wait or progress through transition
                if self.loading_state_steps > 30:
                    # Stuck on blank screen for too long - try aggressive actions
                    # Cycle through A, START, B to try to progress
                    actions_to_try = ['A', 'START', 'A', 'A']  # More A presses for dialog transitions
                    action_idx = (self.loading_state_steps - 31) % len(actions_to_try)
                    return actions_to_try[action_idx]
                elif self.loading_state_steps > 15:
                    # After 15 steps on blank screen, start pressing A more aggressively
                    # Blank screens often indicate transitions that need A presses
                    return 'A'
                elif self.loading_state_steps > 5:
                    # After 5 steps, try pressing A to progress through transition
                    return 'A'
                else:
                    # Early in loading - wait a bit for screen to load
                    return 'WAIT 2'  # Wait slightly longer
            else:
                # Screen has content but state is "loading" - might be transitioning
                # Try pressing A to progress
                if self.loading_state_steps > 10:
                    return 'A'
                else:
                    return 'WAIT 1'
        
        # Detect if we're stuck pressing A repeatedly (even if not detected as dialogue)
        # This handles cases where OCR is garbled and dialogue isn't detected
        # BUT: Don't press B during character creation - it will cancel new game!
        if len(self.action_history) >= 10 and not (self.new_game_started and self.character_creation_steps < 50):
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
                            self._save_stuck_screenshot(
                                step_count=step_count,
                                reason="A_repetition_same_state",
                                details={
                                    'action': 'A',
                                    'state_key': current_state_key,
                                    'screen_text': screen_text[:50]
                                }
                            )
                            return "B"
                    else:
                        # No previous state, but pressing A repeatedly with text = likely dialogue
                        # Save screenshot and try B to break out
                        self._save_stuck_screenshot(
                            step_count=step_count,
                            reason="A_repetition_no_state",
                            details={
                                'action': 'A',
                                'screen_text': screen_text[:50],
                                'game_state': game_state
                            }
                        )
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
                # During character creation, always press A (never B)
                if is_character_creation or (self.new_game_started and self.character_creation_steps < 50):
                    return "A"
                return "A"
            elif game_state == 'loading':
                return "WAIT 1"  # Wait for loading to complete
            elif game_state == 'overworld':
                return "UP"  # Default exploration
            else:
                # During character creation, always press A
                if is_character_creation or (self.new_game_started and self.character_creation_steps < 50):
                    return "A"
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
                # CRITICAL: Don't press B during character creation - it will cancel new game!
                if self.new_game_started and self.character_creation_steps < 50:
                    # In character creation - only press A, never B
                    if dominant_action == "A" and len(self.action_history) >= 3:
                        # Even if pressing A repeatedly, continue - character creation needs multiple A presses
                        return "A"
                    else:
                        return "A"  # Always A during character creation
                
                # If stuck pressing A in dialogue, try B or wait (but not during character creation)
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
                                self._save_stuck_screenshot(
                                    step_count=step_count,
                                    reason="dialog_A_repetition",
                                    details={
                                        'action': 'A',
                                        'recent_as': recent_as,
                                        'state_key': state_key,
                                        'game_state': game_state
                                    }
                                )
                                return "B"
                    # Save screenshot when stuck in dialogue
                    self._save_stuck_screenshot(
                        step_count=step_count,
                        reason="dialog_stuck",
                        details={
                            'action': 'A',
                            'game_state': game_state,
                            'screen_text': screen_text[:50]
                        }
                    )
                    return "B"  # Try B to break out of dialogue
                elif dominant_action == "B":
                    # Too many B presses, try A
                    return "A"
            else:
                # For movement actions, force exploration
                # Save screenshot when stuck in repetitive movement
                self._save_stuck_screenshot(
                    step_count=step_count,
                    reason="repetitive_movement",
                    details={
                        'dominant_action': dominant_action,
                        'game_state': game_state,
                        'is_low_diversity': is_low_diversity
                    }
                )
                
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
                            self._save_stuck_screenshot(
                                step_count=step_count,
                                reason="same_state_persistent",
                                details={
                                    'same_state_count': self._same_state_count,
                                    'state_key': state_key,
                                    'game_state': game_state,
                                    'screen_text': screen_text[:50]
                                }
                            )
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
                # Update metrics for cache hit
                if self.metrics:
                    self.metrics.cache.record_hit()
                    self.metrics.cache.update_size(
                        len(self.action_cache.cache),
                        self.action_cache.max_size
                    )
                return cached_action
            # Update metrics for cache miss
            if self.metrics:
                self.metrics.cache.record_miss()
                self.metrics.cache.update_size(
                    len(self.action_cache.cache),
                    self.action_cache.max_size
                )
        
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
            llm_start_time = time.time()
            response = self.llm_provider.generate(
                prompt=prompt,
                system_prompt=self.prompt_optimizer.optimize_system_prompt(),
                max_tokens=self.max_tokens  # Configurable token limit
            )
            llm_duration = time.time() - llm_start_time
            
            # Record LLM metrics
            if self.metrics:
                self.metrics.performance.record_llm_time(llm_duration)
                # LLM provider should have recorded detailed metrics, but we track timing here too
                self.metrics.llm.record_call(llm_duration)
        except Exception as e:
            # If LLM call fails, use fallback action
            llm_duration = time.time() - llm_start_time if 'llm_start_time' in locals() else 0.0
            if self.metrics:
                self.metrics.llm.record_call(llm_duration, error=True)
            logger.warning(f"LLM call failed: {e}")
            logger.warning("Using fallback action based on game state")
            
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
                # During character creation, always press A (never B)
                if self.new_game_started and self.character_creation_steps < 50:
                    return "A"
                return "A"
            elif game_state == 'title_screen':
                return "START"
            elif game_state == 'overworld':
                return "UP"
            else:
                return "A"  # Safe default
        
        # Extract action from response - optimized for short responses
        response_clean = response.strip().upper()
        
        # CRITICAL: Final check - prevent B during character creation
        # This catches any B that might have slipped through from LLM
        if self.new_game_started and self.character_creation_steps < 50:
            if response_clean == "B" or response_clean.startswith("B"):
                logger.info(f"[CHARACTER_CREATION] Blocked B press from LLM, using A instead (step {step_count})")
                response_clean = "A"
        
        # Direct match for common actions
        valid_buttons = ["UP", "DOWN", "LEFT", "RIGHT", "A", "B", "SELECT", "START"]
        
        # Check for direct match first (most common case)
        for button in valid_buttons:
            if button in response_clean:
                # CRITICAL: Block B during character creation even if found in response
                if button == "B" and self.new_game_started and self.character_creation_steps < 50:
                    logger.info(f"[CHARACTER_CREATION] Blocked B button, using A instead (step {step_count})")
                    action = "A"
                    break
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
    
    def step(self) -> dict:
        """Execute one step of the agent.
        
        Returns:
            Dictionary with step information
        """
        step_start_time = time.time()
        
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
            # Only save screenshot if screen is not blank
            screen_image = self.game_state.get_screen_image()
            blank_info = self.game_state.detect_blank_screen(screen_image)
            if not blank_info['is_blank']:
                # Save screenshot when forcing exploration due to high stuck count
                self._save_stuck_screenshot(
                    step_count=self.step_count,
                    reason="forced_exploration",
                    details={
                        'stuck_count': self.stuck_count,
                        'blocked_directions': list(self.blocked_directions),
                        'pre_game_state': pre_game_state
                    }
                )
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
            # Save screenshot when stuck
            self._save_stuck_screenshot(
                step_count=self.step_count,
                reason="multi_modal_stuck",
                details={
                    'stuck_signals': stuck_signals,
                    'stuck_count': self.stuck_count,
                    'action': action,
                    'game_state': post_game_state,
                    'position': post_position
                }
            )
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
        
        # Record step timing
        step_duration = time.time() - step_start_time
        if self.metrics:
            self.metrics.performance.record_step_time(step_duration)
        
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
    
    def check_action_diversity(self, window: int = 15, threshold: float = 0.6) -> tuple[bool, str | None]:
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
    
    def validate_movement(self, action: str, pre_position: tuple | None, 
                          post_position: tuple | None, threshold: int = 3) -> tuple[bool, str | None]:
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

