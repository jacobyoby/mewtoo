"""AI Agent for playing Pokemon Red.

Version: 0.0.7
"""
import logging
import random
import time
from collections import Counter, deque
from dataclasses import dataclass

from agent_strategy import AgentStrategy, GameEvent
from config import get_config
from early_game import EarlyGameHandler
from game_state import GameState
from llm_optimizer import ActionCache, PromptOptimizer, RepetitionDetector
from llm_provider import LLMProvider
from metrics import MetricsCollector

logger = logging.getLogger(__name__)



@dataclass
class Observation:
    """One snapshot of game state consumed by the policy chain.

    game_state is mutable on purpose: the diversity policy reclassifies an
    undetected dialogue (A spam + screen text) so later policies see the
    corrected state.
    """
    game_info: dict
    screen_text: str
    game_state: str
    step_count: int
    is_character_creation: bool = False


class PokemonAgent:
    """AI agent that plays Pokemon Red using an LLM."""
    
    SYSTEM_PROMPT = """You play Pokemon Red. Respond with ONLY one action: UP, DOWN, LEFT, RIGHT, A, B, START, SELECT, or WAIT N.
No explanations. Just the action."""

    def __init__(self, llm_provider: LLMProvider, game_state: GameState, use_cache: bool = True,
                 use_strategy: bool = True, goal_check_interval: int = 5, metrics: MetricsCollector | None = None,
                 planner=None, vision=None):
        """Initialize Pokemon Agent.

        Args:
            llm_provider: LLM provider instance
            game_state: GameState instance
            use_cache: Enable action caching (default: True, can be overridden by config)
            use_strategy: Enable goal-oriented strategy (default: True, can be overridden by config)
            goal_check_interval: Check goal completion every N steps (default: 5, higher = less frequent)
            metrics: Optional metrics collector instance
            planner: Optional PlannerAgent — a slower, bigger model that
                periodically produces a strategy directive injected into
                this (fast) agent's prompts
            vision: Optional VisionAdvisor — a multimodal model consulted
                when the agent is stuck, to see which way is open
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
        self.planner = planner  # Optional slow-cadence strategy planner
        self.vision = vision  # Optional multimodal stuck-time advisor
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
        
        # Same-state tracking (used by several policies)
        self._last_state_key: str | None = None
        self._same_state_count = 0
        self._menu_steps = 0  # Consecutive steps observed in a menu
        self._creation_over = False  # Latched on first real overworld sighting
        self._phantom_menu = False  # Menu state that B presses cannot close
        self._dialog_loop_steps = 0  # Consecutive dialog steps at one tile
        self._edge_scan_steps = 0  # Lateral sweep progress along a blocking wall
        self._dialog_loop_pos = None
        self._edge_scan_steps = 0  # Lateral sweep progress along a blocking wall

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
        step_count = self.step_count
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

        # Inject the planner's latest directive so the fast model inherits
        # long-horizon direction without paying for it per step
        if self.planner and self.planner.current_plan:
            if strategy_context is None:
                strategy_context = {}
            strategy_context["plan"] = self.planner.current_plan

        # Use enhanced prompt with all context
        return self.prompt_optimizer.optimize_prompt(
            screen_text, game_info['frame_count'], step_count, recent_actions, game_state,
            game_state_summary=game_state_summary,
            recent_events=recent_events,
            strategy_context=strategy_context
        )
    
    def get_action(self) -> str:
        """Get the next action by running the policy chain.

        Policies run in priority order; the first one to return an action
        wins. Earlier policies handle situations where consulting the LLM
        would be wrong or wasteful (blank screens, scripted naming sequences,
        stuck-breaking, caching); the LLM policy at the end always returns.
        """
        obs = self._observe()

        for policy in (
            self._blank_screen_policy,
            self._track_character_creation,
            self._early_game_policy,
            self._loading_policy,
            self._a_spam_policy,
            self._menu_escape_policy,
            self._dialog_loop_policy,
            self._vision_policy,
            self._route_policy,
            self._first_action_policy,
            self._diversity_policy,
            self._same_state_policy,
            self._cache_lookup_policy,
            self._repetition_policy,
            self._dialog_shortcut_policy,
        ):
            action = policy(obs)
            if action is not None:
                return action

        return self._llm_policy(obs)

    def _observe(self) -> "Observation":
        """Snapshot the game state the policy chain decides from."""
        game_info = self.game_state.get_game_info()
        return Observation(
            game_info=game_info,
            screen_text=game_info['screen_text'] or "",
            game_state=game_info.get('game_state', 'unknown'),
            step_count=self.step_count,
        )

    def _in_creation_window(self) -> bool:
        """True while B presses must be blocked (they cancel the new game).

        Closed for good once the starter is in the party -- without that
        latch, the creation-steps counter resets to 0 when naming text
        disappears and `0 < 50` re-opens the block for the rest of the run
        (the reason agents camped in the START menu: B was never allowed).
        """
        if self.early_game_handler.is_done or self._creation_over:
            return False
        return self.new_game_started and self.character_creation_steps < 50

    def _text_box_open(self) -> bool:
        """True when a Gen 1 text box is on screen (pixel check, no memory)."""
        try:
            return self.game_state.detect_text_box()
        except Exception:
            return False

    def _cache_action(self, obs: "Observation", action: str) -> str:
        """Store an action in the cache under the observation's key."""
        if self.action_cache:
            cache_key_text = f"{obs.game_state}:{obs.screen_text[:30]}"
            self.action_cache.set(
                cache_key_text, obs.game_info['frame_count'], self.action_history, action
            )
        return action

    def _blank_screen_policy(self, obs: "Observation") -> str | None:
        """Progress through blank transition screens before anything else."""
        screen_image = self.game_state.get_screen_image()
        blank_info = self.game_state.detect_blank_screen(screen_image)

        if not blank_info['is_blank']:
            # Screen has content - reset blank screen counter
            if self.blank_screen_steps > 0:
                self.blank_screen_steps = 0
            return None

        self.blank_screen_steps += 1
        # Blank screens during gameplay usually need A presses to progress
        if self.blank_screen_steps > 20:
            # Stuck on blank screen for too long - try aggressive actions
            actions_to_try = ['A', 'START', 'A', 'A']  # More A presses
            action_idx = (self.blank_screen_steps - 21) % len(actions_to_try)
            logger.info(f"[BLANK_SCREEN] Step {obs.step_count}: Blank screen for {self.blank_screen_steps} steps, trying {actions_to_try[action_idx]}")
            return actions_to_try[action_idx]
        elif self.blank_screen_steps > 10:
            logger.info(f"[BLANK_SCREEN] Step {obs.step_count}: Blank screen for {self.blank_screen_steps} steps, pressing A")
            return 'A'
        elif self.blank_screen_steps > 3:
            # After 3 steps, start pressing A to progress through transition
            return 'A'
        else:
            # Early blank screen - wait briefly then press A
            return 'WAIT 1' if self.blank_screen_steps == 1 else 'A'

    def _track_character_creation(self, obs: "Observation") -> None:
        """Side-effect stage: detect naming screens and track persistence.

        Never returns an action; it sets obs.is_character_creation and keeps
        new_game_started / character_creation_steps current for later
        policies (B presses during creation cancel the new game).
        """
        screen_text_upper = obs.screen_text.upper()
        obs.is_character_creation = (
            any(word in screen_text_upper for word in ["NAME", "WHAT", "BOY", "GIRL", "ARE YOU A BOY", "ARE YOU A GIRL"]) or
            (obs.game_state == 'menu' and obs.step_count < 50)  # Early menu after title screen is likely character creation
        )

        # Track if we've started a new game
        if not self.new_game_started:
            # Moved past title screen with creation-like screens = new game
            if obs.game_state != 'title_screen' and obs.step_count > 5:
                if obs.is_character_creation or obs.game_state in ['menu', 'dialog']:
                    self.new_game_started = True
                    self.character_creation_steps = 0

        # Track character creation persistence
        if obs.is_character_creation or self._in_creation_window():
            self.character_creation_steps += 1
        elif self.character_creation_steps > 0:
            self.character_creation_steps = 0

        # Once the player is in the overworld on a known map, the naming
        # sequence is permanently behind us -- close the B-block for good
        # (it cannot re-open; `0 < 50` used to re-arm it forever)
        if (not self._creation_over and self.new_game_started
                and obs.game_state == 'overworld'
                and (obs.game_info.get('current_map') or {}).get('map_id') is not None):
            self._creation_over = True
        return None

    def _early_game_policy(self, obs: "Observation") -> str | None:
        """Scripted naming-screen handling.

        The NAME? menu and letter grid cannot be completed by the generic
        "always press A" policy (A on NEW NAME enters the grid, where A just
        types letters forever) -- the reason get_starter validated at 0%.
        The handler recognizes those screens from OCR text, returns short
        deterministic sequences (DOWN,A to pick a preset name; A,START,A to
        finish a grid entry), and latches off once the party is non-empty.
        """
        party_size = len(obs.game_info.get('party', []) or [])
        early_action = self.early_game_handler.next_action(
            obs.screen_text, obs.game_state, party_size
        )
        if early_action is not None:
            logger.info(f"[EARLY_GAME] Step {obs.step_count}: scripted {early_action} "
                        f"for naming/confirm screen")
        return early_action

    def _loading_policy(self, obs: "Observation") -> str | None:
        """Wait out (or A through) loading-state screens."""
        if obs.game_state != 'loading':
            self.loading_state_steps = 0
            return None
        self.loading_state_steps += 1

        screen_image = self.game_state.get_screen_image()
        blank_info = self.game_state.detect_blank_screen(screen_image)

        if blank_info['is_blank']:
            # Screen is blank - need to wait or progress through transition
            if self.loading_state_steps > 30:
                # Stuck on blank screen for too long - try aggressive actions
                actions_to_try = ['A', 'START', 'A', 'A']  # More A presses for dialog transitions
                action_idx = (self.loading_state_steps - 31) % len(actions_to_try)
                return actions_to_try[action_idx]
            elif self.loading_state_steps > 15:
                return 'A'
            elif self.loading_state_steps > 5:
                return 'A'
            else:
                # Early in loading - wait a bit for screen to load
                return 'WAIT 2'
        else:
            # Screen has content but state is "loading" - might be transitioning
            return 'A' if self.loading_state_steps > 10 else 'WAIT 1'

    def _a_spam_policy(self, obs: "Observation") -> str | None:
        """Break out of undetected dialogue by pressing B after heavy A spam.

        Handles cases where OCR is garbled and dialogue isn't detected.
        Skipped during character creation - B would cancel the new game.
        """
        if len(self.action_history) < 10 or self._in_creation_window():
            return None
        recent_actions = self.action_history[-10:]
        a_count = sum(1 for a in recent_actions if a == "A")
        # If 7+ out of last 10 actions are A, likely stuck in dialogue
        if a_count < 7 or obs.game_state == "battle" or len(obs.screen_text) == 0:
            return None

        position = obs.game_info.get('player_position', (0, 0))
        current_state_key = f"{obs.game_state}|{position}"

        if self._last_state_key is not None:
            if self._last_state_key == current_state_key:
                # Stuck pressing A in same state - try B to break out
                self._save_stuck_screenshot(
                    step_count=obs.step_count,
                    reason="A_repetition_same_state",
                    details={
                        'action': 'A',
                        'state_key': current_state_key,
                        'screen_text': obs.screen_text[:50]
                    }
                )
                return "B"
            return None
        # No previous state, but pressing A repeatedly with text = likely dialogue
        self._save_stuck_screenshot(
            step_count=obs.step_count,
            reason="A_repetition_no_state",
            details={
                'action': 'A',
                'screen_text': obs.screen_text[:50],
                'game_state': obs.game_state
            }
        )
        return "B"

    def _menu_escape_policy(self, obs: "Observation") -> str | None:
        """Close a lingering START menu with B.

        Live validation runs repeatedly ended with the agent parked in the
        START menu: it opens the menu in the overworld and then dithers
        (800-step runs finishing in state 'start_menu'). No early-game goal
        needs that menu, so after a few consecutive menu observations press
        B to close it. Guards:
        - never during character creation (B cancels the new game; the
          naming menu is also handled earlier in the chain by the scripted
          early-game policy)
        - never on YES/NO choice menus (B would pick NO implicitly)
        """
        if 'menu' not in obs.game_state:
            self._menu_steps = 0
            self._phantom_menu = False
            return None
        if self._phantom_menu:
            # Stale menu bytes: Gen 1 never zeroes its menu RAM after a menu
            # closes, so memory can report "pokemon_menu" indefinitely. Trust
            # pixels instead: a solid white bottom panel means a text box is
            # open (press A), otherwise it is plain overworld.
            obs.game_state = 'dialog' if self._text_box_open() else 'overworld'
            return None
        self._menu_steps += 1

        if self._menu_steps >= 10:
            # ~7 B presses without the state changing: no real menu closes
            # that slowly -- this is leftover menu RAM, not an open menu
            logger.info(f"[MENU_ESCAPE] Step {obs.step_count}: menu state for "
                        f"{self._menu_steps} steps despite B presses -- "
                        f"treating as phantom (stale memory), trusting pixels")
            self._phantom_menu = True
            obs.game_state = 'dialog' if self._text_box_open() else 'overworld'
            return None

        if self._in_creation_window() or obs.is_character_creation:
            return None
        if "YES" in obs.screen_text.upper():
            return None
        if self._menu_steps >= 3:
            logger.info(f"[MENU_ESCAPE] Step {obs.step_count}: in menu for "
                        f"{self._menu_steps} steps, pressing B to close")
            return "B"
        return None

    def _dialog_loop_policy(self, obs: "Observation") -> str | None:
        """Break out of re-triggering scenery dialog (TV, PC, sign).

        Pressing A while facing an interactable re-opens its text box the
        instant the last one closes, so "dialog -> press A" loops forever
        without the player ever moving. Observed live: 330+ consecutive
        dialog steps parked at one tile in front of the bedroom TV. After a
        long same-position dialog run, close the box and step away.
        """
        pos = tuple(obs.game_info.get('player_position') or ())
        if obs.game_state != 'dialog':
            self._dialog_loop_steps = 0
            self._dialog_loop_pos = None
            return None

        if pos and pos == self._dialog_loop_pos:
            self._dialog_loop_steps += 1
        else:
            self._dialog_loop_pos = pos
            self._dialog_loop_steps = 1

        if self._dialog_loop_steps < 25:
            return None

        # Alternate: close the box, then walk off the tile that triggers it
        phase = (self._dialog_loop_steps - 25) % 2
        if phase == 0:
            logger.info(f"[DIALOG_LOOP] Step {obs.step_count}: {self._dialog_loop_steps} "
                        f"dialog steps at {pos} -- closing box to walk away")
            return "B"
        escape = random.choice(["DOWN", "LEFT", "RIGHT", "UP"])
        logger.info(f"[DIALOG_LOOP] Step {obs.step_count}: stepping {escape} "
                    f"away from the re-triggering tile")
        return escape

    def _vision_policy(self, obs: "Observation") -> str | None:
        """When stuck in the overworld, look at the screen and go that way.

        Every other sensor is indirect (RAM, OCR, pixel stats) and the
        navigation heuristics have no way to find, say, the single column
        of Pallet Town's fence that opens onto Route 1. A multimodal model
        can see the gap. Too slow for per-step use (~7s), so it runs only
        on a genuine stall, rate-limited by its own cooldown.
        """
        if not self.vision or obs.game_state != 'overworld':
            return None
        if self.stuck_count < 6:
            return None
        if not self.vision.is_ready(obs.step_count):
            return None
        direction = self.vision.suggest_direction(
            self.game_state.get_screen_image(), obs.step_count
        )
        if direction and direction not in self.blocked_directions:
            return direction
        return None

    def _route_policy(self, obs: "Observation") -> str | None:
        """Follow the encoded walkthrough route on known maps.

        The strategy's direction used to be one suggestion among many,
        competing with random exploration and the LLM -- so runs still
        wandered into Oak's Lab and stalled. On a known map, with a live
        goal and nothing blocking, the route wins outright. It yields when
        the agent is genuinely stuck (so the stuck breakers can work) or
        when the route direction is a known wall.
        """
        if not self.strategy or obs.game_state != 'overworld':
            return None
        if self.stuck_count >= 5:
            return None  # let the stuck breakers take over
        map_id = (obs.game_info.get('current_map') or {}).get('map_id')
        if map_id is None:
            return None
        goal = self.strategy.get_current_goal()
        if goal is None:
            return None
        action = self.strategy.suggest_action_for_goal(
            goal, obs.game_state, self._memory_data(obs.game_info)
        )
        if not action:
            return None
        if action in self.blocked_directions:
            # The route direction is a known wall. Rather than surrendering
            # to random exploration, sweep along the wall: Pallet Town's
            # Route 1 exit is one specific column in the north fence, so
            # runs reached the top row (y=1) and stalled there. Alternating
            # lateral steps scan for the gap, then the route resumes.
            perpendicular = {
                'UP': ('LEFT', 'RIGHT'), 'DOWN': ('LEFT', 'RIGHT'),
                'LEFT': ('UP', 'DOWN'), 'RIGHT': ('UP', 'DOWN'),
            }.get(action)
            if not perpendicular:
                return None
            options = [d for d in perpendicular if d not in self.blocked_directions]
            if not options:
                return None
            self._edge_scan_steps += 1
            # blocked_directions is global, not per-tile: once UP is marked
            # blocked at one fence tile it stays blocked at every column, so
            # the actual gap would never be tried. Retry the route direction
            # every third step of the sweep.
            if self._edge_scan_steps % 3 == 0:
                logger.info(f"[ROUTE] Step {obs.step_count}: retrying {action} "
                            f"after {self._edge_scan_steps} scan steps")
                return action
            scan = options[(self._edge_scan_steps // 6) % len(options)]
            logger.info(f"[ROUTE] Step {obs.step_count}: {action} blocked -- "
                        f"scanning {scan} along the wall for an opening")
            return scan
        self._edge_scan_steps = 0
        return action

    def _first_action_policy(self, obs: "Observation") -> str | None:
        """Cheap heuristics for the very first action (avoids an LLM call)."""
        if obs.step_count != 0 or self.action_history:
            return None
        # Use strategy suggestion if available
        if self.strategy:
            current_goal = self.strategy.get_current_goal()
            if current_goal:
                suggested_action = self.strategy.suggest_action_for_goal(
                    current_goal, obs.game_state, self._memory_data(obs.game_info)
                )
                if suggested_action:
                    return suggested_action

        # Fallback to simple heuristics for first action
        if obs.game_state == 'title_screen':
            return "START"
        elif obs.game_state == 'overworld':
            return "UP"  # Default exploration
        elif obs.game_state == 'loading':
            return "WAIT 1"  # Wait for loading to complete
        # dialog, menu, and anything else: A is the safe default, and during
        # character creation A is the only safe button anyway
        return "A"

    def _diversity_policy(self, obs: "Observation") -> str | None:
        """React to low action diversity (dialogue loops, wall-walking).

        May reclassify obs.game_state to 'dialog' when A spam plus screen
        text indicates an undetected dialogue - later policies see the
        corrected state.
        """
        is_low_diversity, dominant_action = self.check_action_diversity(window=15, threshold=0.6)

        # If pressing A repeatedly and have screen text, likely in dialogue (even if not detected)
        if dominant_action == "A" and len(obs.screen_text) > 0 and obs.game_state == "overworld":
            if is_low_diversity:
                obs.game_state = "dialog"  # Override state detection

        if not (is_low_diversity and dominant_action):
            return None

        if obs.game_state in ['dialog', 'menu']:
            # CRITICAL: Don't press B during character creation - it will cancel new game!
            if self._in_creation_window():
                # In character creation - only press A, never B
                return "A"

            # If stuck pressing A in dialogue, try B or wait (but not during character creation)
            if dominant_action == "A":
                # Track how long we've been in same dialogue state
                state_key = f"{obs.game_state}|{obs.game_info.get('player_position', (0, 0))}"
                if self._last_state_key == state_key and len(self.action_history) >= 5:
                    recent_as = sum(1 for a in self.action_history[-10:] if a == "A")
                    if recent_as >= 7:  # 7+ A presses in last 10 actions
                        self._save_stuck_screenshot(
                            step_count=obs.step_count,
                            reason="dialog_A_repetition",
                            details={
                                'action': 'A',
                                'recent_as': recent_as,
                                'state_key': state_key,
                                'game_state': obs.game_state
                            }
                        )
                        return "B"
                self._save_stuck_screenshot(
                    step_count=obs.step_count,
                    reason="dialog_stuck",
                    details={
                        'action': 'A',
                        'game_state': obs.game_state,
                        'screen_text': obs.screen_text[:50]
                    }
                )
                return "B"  # Try B to break out of dialogue
            elif dominant_action == "B":
                # Too many B presses, try A
                return "A"
            return None

        # For movement actions, force exploration
        self._save_stuck_screenshot(
            step_count=obs.step_count,
            reason="repetitive_movement",
            details={
                'dominant_action': dominant_action,
                'game_state': obs.game_state,
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
            return self._cache_action(obs, random.choice(alternative_actions))
        return None

    def _same_state_policy(self, obs: "Observation") -> str | None:
        """Skip the LLM when the state hasn't changed since last step."""
        state_key = f"{obs.game_state}|{obs.game_info.get('player_position', (0, 0))}"

        if self._last_state_key is not None and self._last_state_key == state_key:
            if len(self.action_history) > 0:
                last_action = self.action_history[-1]
                if obs.game_state in ['dialog', 'menu']:
                    self._same_state_count += 1
                    # If stuck in same dialogue for too long, alternate aggressively
                    if self._same_state_count > 10:
                        if last_action == "A":
                            self._save_stuck_screenshot(
                                step_count=obs.step_count,
                                reason="same_state_persistent",
                                details={
                                    'same_state_count': self._same_state_count,
                                    'state_key': state_key,
                                    'game_state': obs.game_state,
                                    'screen_text': obs.screen_text[:50]
                                }
                            )
                            return "B"
                        return "A"
                    # Normal alternation
                    return "A" if last_action != "B" else "B"
                # For overworld, continue movement
                elif obs.game_state == 'overworld' and last_action in ['UP', 'DOWN', 'LEFT', 'RIGHT']:
                    return last_action
        else:
            # State changed, reset counter
            self._same_state_count = 0

        self._last_state_key = state_key
        return None

    def _cache_lookup_policy(self, obs: "Observation") -> str | None:
        """Reuse a cached action for a previously seen state."""
        if not self.action_cache:
            return None
        cache_key_text = f"{obs.game_state}:{obs.screen_text[:30]}"
        cached_action = self.action_cache.get(
            cache_key_text, obs.game_info['frame_count'], self.action_history
        )
        if self.metrics:
            if cached_action:
                self.metrics.cache.record_hit()
            else:
                self.metrics.cache.record_miss()
            self.metrics.cache.update_size(
                len(self.action_cache.cache),
                self.action_cache.max_size
            )
        return cached_action

    def _repetition_policy(self, obs: "Observation") -> str | None:
        """Divert to an alternative action when repetition is detected."""
        if len(self.action_history) < 3:
            return None
        is_repeating, alt_action = self.repetition_detector.check(self.action_history[-1])
        if is_repeating and alt_action:
            # Use alternative action instead of calling LLM
            return self._cache_action(obs, alt_action)
        return None

    def _dialog_shortcut_policy(self, obs: "Observation") -> str | None:
        """Skip the LLM for dialog: A always advances it."""
        if obs.game_state == 'dialog':
            return self._cache_action(obs, "A")
        return None

    def _llm_policy(self, obs: "Observation") -> str:
        """Ask the LLM for an action; falls back to heuristics on failure."""
        llm_start_time = None
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
                self.metrics.llm.record_call(llm_duration)
        except Exception as e:
            llm_duration = time.time() - llm_start_time if llm_start_time is not None else 0.0
            if self.metrics:
                self.metrics.llm.record_call(llm_duration, error=True)
            logger.warning(f"LLM call failed: {e}")
            logger.warning("Using fallback action based on game state")
            return self._llm_fallback(obs)

        return self._parse_llm_response(obs, response)

    def _llm_fallback(self, obs: "Observation") -> str:
        """Heuristic action when the LLM is unavailable."""
        if self.strategy:
            current_goal = self.strategy.get_current_goal()
            if current_goal:
                suggested_action = self.strategy.suggest_action_for_goal(
                    current_goal, obs.game_state, self._memory_data(obs.game_info)
                )
                if suggested_action:
                    return suggested_action

        # Simple fallback based on game state
        if obs.game_state == 'title_screen':
            return "START"
        elif obs.game_state == 'overworld':
            return "UP"
        # dialog, menu, and anything else: A (also the only safe button
        # during character creation)
        return "A"

    def _parse_llm_response(self, obs: "Observation", response: str) -> str:
        """Extract a valid button action from the LLM's raw response."""
        response_clean = response.strip().upper()

        # CRITICAL: Final check - prevent B during character creation
        if self._in_creation_window():
            if response_clean == "B" or response_clean.startswith("B"):
                logger.info(f"[CHARACTER_CREATION] Blocked B press from LLM, using A instead (step {obs.step_count})")
                response_clean = "A"

        valid_buttons = ["UP", "DOWN", "LEFT", "RIGHT", "A", "B", "SELECT", "START"]

        # Check for direct match first (most common case)
        for button in valid_buttons:
            if button in response_clean:
                # CRITICAL: Block B during character creation even if found in response
                if button == "B" and self._in_creation_window():
                    logger.info(f"[CHARACTER_CREATION] Blocked B button, using A instead (step {obs.step_count})")
                    return self._cache_action(obs, "A")
                # Extract the button
                if ',' in response_clean:
                    # Handle comma-separated
                    parts = [p.strip() for p in response_clean.split(',')]
                    valid_parts = [p for p in parts if p in valid_buttons]
                    action = ', '.join(valid_parts[:2]) if valid_parts else button  # Max 2 actions
                else:
                    action = button
                return self._cache_action(obs, action)

        # Check for WAIT command
        if "WAIT" in response_clean:
            parts = response_clean.split()
            action = "WAIT 10"
            if len(parts) >= 2:
                try:
                    action = f"WAIT {int(parts[1])}"
                except ValueError:
                    pass
            return self._cache_action(obs, action)

        # Fallback: START while still orienting, A afterwards
        action = "START" if len(self.action_history) < 5 else "A"
        return self._cache_action(obs, action)

    def _memory_data(self, game_info: dict) -> dict:
        """Memory-derived context passed to the strategy system."""
        return {
            "player_position": game_info.get('player_position'),
            "current_map": game_info.get('current_map', {}),
            "party": game_info.get('party', []),
            "health": game_info.get('health', {}),
        }

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

        # Keep strategy map/phase tracking current on EVERY step. It used to
        # run only inside get_prompt(), i.e. only when the chain fell through
        # to the LLM -- so once the route policy started short-circuiting,
        # map transitions went unseen and the door-exit maneuver never fired.
        if self.strategy:
            self.strategy.update_phase(pre_game_state, self._memory_data(pre_state))

        # Consult the slow-lane planner (no-op unless a plan is due)
        if self.planner:
            completed = len(self.strategy.completed_goals) if self.strategy else 0
            summary = ""
            if self.strategy:
                goal = self.strategy.get_current_goal()
                if goal:
                    summary = f"Current goal: {goal.description}"
            self.planner.maybe_plan(
                step_count=self.step_count,
                game_info=pre_state,
                stuck_count=self.stuck_count,
                strategy_summary=summary,
                completed_goals=completed,
            )
        
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
        
        # Force exploration when stuck (before getting action).
        # Overworld only: random arrows inside a menu, dialog, or transition
        # just wiggle the cursor -- the policy chain owns those states.
        if self.stuck_count > 5 and pre_game_state == 'overworld':
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

