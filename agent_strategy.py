"""Goal-oriented agent strategy with state machine and exploration/exploitation balance."""
from enum import Enum
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from collections import deque


class GamePhase(Enum):
    """Different phases of the game."""
    TITLE_SCREEN = "title_screen"
    CHARACTER_CREATION = "character_creation"
    EARLY_GAME = "early_game"  # Getting starter, learning controls
    EXPLORATION = "exploration"  # Exploring routes, catching Pokemon
    BATTLE = "battle"  # In battle
    MENU_NAVIGATION = "menu_navigation"
    DIALOG = "dialog"  # Reading dialog
    UNKNOWN = "unknown"


@dataclass
class Goal:
    """Represents a game goal."""
    name: str
    description: str
    priority: int  # Higher = more important
    completed: bool = False
    progress: float = 0.0  # 0.0 to 1.0
    required_actions: List[str] = field(default_factory=list)
    completion_condition: Optional[object] = None  # callable type


@dataclass
class GameEvent:
    """Represents a game event."""
    event_type: str
    description: str
    frame_count: int
    game_state: str
    action_taken: str


class AgentStrategy:
    """Goal-oriented strategy system for Pokemon agent."""
    
    def __init__(self, exploration_rate: float = 0.3, max_recent_events: int = 10):
        """Initialize agent strategy.
        
        Args:
            exploration_rate: Exploration rate (0.0 to 1.0). 0.0 = always follow goals, 1.0 = always explore.
            max_recent_events: Maximum number of recent events to track.
        """
        self.current_phase = GamePhase.UNKNOWN
        self.goals: List[Goal] = []
        self.completed_goals: List[str] = []
        self.recent_events: deque = deque(maxlen=max_recent_events)
        self.exploration_rate = max(0.0, min(1.0, exploration_rate))  # Clamp between 0 and 1
        self.step_count = 0
        
        # Initialize default goals
        self._initialize_default_goals()
    
    def _initialize_default_goals(self):
        """Initialize default game goals."""
        self.goals = [
            Goal(
                name="start_game",
                description="Navigate title screen and start new game",
                priority=10,
                required_actions=["START", "A"]
            ),
            Goal(
                name="get_starter",
                description="Get starter Pokemon (Bulbasaur, Charmander, or Squirtle)",
                priority=9,
                required_actions=["A", "A", "A"]  # Navigate to starter selection
            ),
            Goal(
                name="reach_viridian",
                description="Reach Viridian City from Pallet Town",
                priority=8,
            ),
            Goal(
                name="catch_pokemon",
                description="Catch a wild Pokemon",
                priority=7,
            ),
            Goal(
                name="level_up",
                description="Level up Pokemon through battles",
                priority=6,
            ),
            Goal(
                name="reach_pewter",
                description="Reach Pewter City (first gym city)",
                priority=7,
            ),
            Goal(
                name="defeat_brock",
                description="Defeat Brock (first gym leader)",
                priority=6,
            ),
            Goal(
                name="get_pokedex",
                description="Get Pokedex from Professor Oak",
                priority=8,
            ),
            Goal(
                name="explore_route_1",
                description="Explore Route 1 between Pallet and Viridian",
                priority=5,
            ),
            Goal(
                name="train_pokemon",
                description="Train Pokemon to level 10+",
                priority=5,
            ),
        ]
    
    def update_phase(self, game_state: str, memory_data: Optional[Dict] = None):
        """Update current game phase based on game state.
        
        Args:
            game_state: Current game state string
            memory_data: Optional memory data for more accurate phase detection
        """
        if game_state == "title_screen":
            self.current_phase = GamePhase.TITLE_SCREEN
        elif game_state == "battle":
            self.current_phase = GamePhase.BATTLE
        elif game_state == "menu":
            self.current_phase = GamePhase.MENU_NAVIGATION
        elif game_state == "dialog":
            self.current_phase = GamePhase.DIALOG
        elif game_state == "overworld":
            # Determine overworld phase based on progress
            if memory_data:
                party = memory_data.get("party", [])
                map_info = memory_data.get("current_map", {})
                map_id = map_info.get("map_id", 0)
                
                if len(party) == 0:
                    self.current_phase = GamePhase.EARLY_GAME
                elif map_id == 0x00:  # Pallet Town
                    self.current_phase = GamePhase.EARLY_GAME
                else:
                    self.current_phase = GamePhase.EXPLORATION
            else:
                self.current_phase = GamePhase.EXPLORATION
        else:
            self.current_phase = GamePhase.UNKNOWN
    
    def get_current_goal(self) -> Optional[Goal]:
        """Get the highest priority incomplete goal.
        
        Returns:
            Current goal or None
        """
        incomplete_goals = [g for g in self.goals if not g.completed]
        if not incomplete_goals:
            return None
        
        # Sort by priority (highest first)
        incomplete_goals.sort(key=lambda g: g.priority, reverse=True)
        return incomplete_goals[0]
    
    def suggest_action_for_goal(self, goal: Goal, game_state: str, 
                               memory_data: Optional[Dict] = None) -> Optional[str]:
        """Suggest an action to progress toward a goal.
        
        Args:
            goal: Current goal
            game_state: Current game state
            memory_data: Optional memory data
            
        Returns:
            Suggested action or None
        """
        if goal.name == "start_game":
            if game_state == "title_screen":
                return "START"
            elif game_state == "menu":
                return "A"
        
        elif goal.name == "get_starter":
            if game_state == "dialog":
                return "A"  # Continue dialog
            elif game_state == "menu":
                # Navigate to starter selection
                return "DOWN"  # Usually need to go down to select starter
        
        elif goal.name == "reach_viridian":
            if game_state == "overworld":
                if memory_data:
                    pos = memory_data.get("player_position", (0, 0))
                    map_info = memory_data.get("current_map", {})
                    map_id = map_info.get("map_id", 0)
                    
                    # Use map knowledge and position data
                    if map_id == 0x00:  # Pallet Town
                        # Need to go north, but check if at boundary
                        if pos and len(pos) >= 2:
                            if self.is_at_boundary(pos, 'UP', map_id):
                                return "RIGHT"  # Try different direction
                            return "UP"
                        return "UP"
                    elif map_id == 0x0B:  # Route 1
                        # Continue north toward Viridian
                        if pos and len(pos) >= 2:
                            if self.is_at_boundary(pos, 'UP', map_id):
                                # At north boundary, try other directions
                                return "LEFT"  # Try exploring left
                            return "UP"
                        return "UP"
                    else:
                        # Default: move up/north, but check boundaries
                        if pos and len(pos) >= 2:
                            if self.is_at_boundary(pos, 'UP', map_id):
                                return "RIGHT"
                        return "UP"
                return "UP"
            elif game_state == "dialog":
                return "A"
        
        elif goal.name == "catch_pokemon":
            if game_state == "battle":
                # In battle, try to catch
                return "A"  # Select catch option
            elif game_state == "overworld":
                # Move around to encounter wild Pokemon
                return "UP"  # Explore
        
        elif goal.name == "level_up":
            if game_state == "battle":
                return "A"  # Attack
            elif game_state == "overworld":
                return "UP"  # Find trainers/wild Pokemon
        
        # Default: continue dialog or explore
        if game_state == "dialog":
            return "A"
        elif game_state == "overworld":
            return "UP"
        
        return None
    
    def add_event(self, event: GameEvent):
        """Add a game event to history.
        
        Args:
            event: Game event
        """
        self.recent_events.append(event)
        self.step_count += 1
    
    def get_recent_events_summary(self, count: int = 5) -> str:
        """Get summary of recent events.
        
        Args:
            count: Number of recent events to include
            
        Returns:
            Summary string
        """
        if not self.recent_events:
            return "No recent events"
        
        events = list(self.recent_events)[-count:]
        summary_parts = []
        
        for event in events:
            summary_parts.append(f"- {event.description} ({event.event_type})")
        
        return "\n".join(summary_parts)
    
    def should_explore(self, stuck_count: int = 0, action_diversity: float = 1.0) -> bool:
        """Determine if agent should explore (vs exploit).
        
        Args:
            stuck_count: Current stuck count (higher = more likely to explore)
            action_diversity: Action diversity metric (0.0 to 1.0, higher = more diverse)
            
        Returns:
            True if should explore, False if should exploit
        """
        adaptive_rate = self.get_adaptive_exploration_rate(
            self.exploration_rate, stuck_count, action_diversity
        )
        import random
        return random.random() < adaptive_rate
    
    def get_adaptive_exploration_rate(self, base_rate: float, stuck_count: int, 
                                     action_diversity: float) -> float:
        """Adaptively adjust exploration rate based on stuck state.
        
        Args:
            base_rate: Base exploration rate (0.0 to 1.0)
            stuck_count: Current stuck count
            action_diversity: Action diversity metric (0.0 to 1.0)
            
        Returns:
            Adjusted exploration rate
        """
        rate = base_rate
        
        # Increase exploration when stuck
        if stuck_count > 5:
            rate = min(0.8, rate + 0.3)
        
        # Increase exploration when action diversity is low
        if action_diversity < 0.3:
            rate = min(0.7, rate + 0.2)
        
        return rate
    
    def get_strategy_context(self, game_state: str, memory_data: Optional[Dict] = None) -> Dict:
        """Get strategy context for prompt generation.
        
        Args:
            game_state: Current game state
            memory_data: Optional memory data
            
        Returns:
            Strategy context dictionary
        """
        current_goal = self.get_current_goal()
        
        context = {
            "phase": self.current_phase.value,
            "current_goal": current_goal.name if current_goal else "none",
            "goal_description": current_goal.description if current_goal else "No active goal",
            "completed_goals": self.completed_goals,
            "recent_events": self.get_recent_events_summary(3),
            "exploration_mode": self.should_explore(0, 1.0),  # Default values when called without context
        }
        
        # Add memory-based context if available
        if memory_data:
            context["player_position"] = memory_data.get("player_position")
            context["current_map"] = memory_data.get("current_map", {}).get("map_name", "Unknown")
            context["party_size"] = len(memory_data.get("party", []))
            context["health"] = memory_data.get("health", {})
        
        return context
    
    def mark_goal_complete(self, goal_name: str):
        """Mark a goal as completed.
        
        Args:
            goal_name: Name of completed goal
        """
        for goal in self.goals:
            if goal.name == goal_name and not goal.completed:
                goal.completed = True
                self.completed_goals.append(goal_name)
                break
    
    def check_goal_completion(self, memory_data: Optional[Dict] = None, game_state: str = "unknown"):
        """Automatically check and mark goals as complete based on game state.
        
        Args:
            memory_data: Current memory data
            game_state: Current game state
        """
        if not memory_data:
            return
        
        # Check start_game completion
        if "start_game" not in self.completed_goals and game_state != "title_screen":
            if game_state in ["menu", "dialog", "overworld", "battle"]:
                self.mark_goal_complete("start_game")
        
        # Check get_starter completion
        if "get_starter" not in self.completed_goals:
            party = memory_data.get("party", [])
            if len(party) > 0:
                # Check if party has a starter Pokemon (species 1-3)
                starters = [1, 2, 3]  # Bulbasaur, Charmander, Squirtle
                if any(p.get("species", 0) in starters for p in party):
                    self.mark_goal_complete("get_starter")
        
        # Check reach_viridian completion
        if "reach_viridian" not in self.completed_goals:
            map_info = memory_data.get("current_map", {})
            map_id = map_info.get("map_id", 0)
            # Viridian City is map ID 0x01 (1) in Pokemon Red
            if map_id == 1 or map_id == 0x01:
                self.mark_goal_complete("reach_viridian")
        
        # Check reach_pewter completion
        if "reach_pewter" not in self.completed_goals:
            map_info = memory_data.get("current_map", {})
            map_id = map_info.get("map_id", 0)
            if map_id == 0x02:  # Pewter City
                self.mark_goal_complete("reach_pewter")
        
        # Check catch_pokemon completion
        if "catch_pokemon" not in self.completed_goals:
            party = memory_data.get("party", [])
            if len(party) > 1:  # More than just starter
                self.mark_goal_complete("catch_pokemon")
        
        # Check level_up completion
        if "level_up" not in self.completed_goals:
            party = memory_data.get("party", [])
            if party:
                # Check if any Pokemon is above level 5
                if any(p.get("level", 0) > 5 for p in party):
                    self.mark_goal_complete("level_up")
        
        # Check train_pokemon completion
        if "train_pokemon" not in self.completed_goals:
            party = memory_data.get("party", [])
            if party:
                # Check if any Pokemon is level 10+
                if any(p.get("level", 0) >= 10 for p in party):
                    self.mark_goal_complete("train_pokemon")
        
        # Check explore_route_1 completion
        if "explore_route_1" not in self.completed_goals:
            map_info = memory_data.get("current_map", {})
            map_id = map_info.get("map_id", 0)
            if map_id == 0x0B:  # Route 1
                self.mark_goal_complete("explore_route_1")
    
    def get_progress_summary(self) -> Dict:
        """Get summary of agent progress.
        
        Returns:
            Dictionary with progress information
        """
        total_goals = len(self.goals)
        completed_count = len(self.completed_goals)
        progress_percent = (completed_count / total_goals * 100) if total_goals > 0 else 0
        
        return {
            "total_goals": total_goals,
            "completed_goals": completed_count,
            "progress_percent": progress_percent,
            "completed_goal_names": self.completed_goals,
            "current_phase": self.current_phase.value,
            "step_count": self.step_count,
        }
    
    def is_at_boundary(self, position: tuple, direction: str, map_id: int) -> bool:
        """Check if position is at map boundary.
        
        Args:
            position: Player position (x, y)
            direction: Direction to check
            map_id: Current map ID
            
        Returns:
            True if at boundary in that direction
        """
        if not position or len(position) < 2:
            return False
        
        x, y = position
        
        # Basic boundary detection (can be enhanced with map data)
        if direction == 'UP' and y <= 1:
            return True
        elif direction == 'DOWN' and y >= 15:  # Approximate map height
            return True
        elif direction == 'LEFT' and x <= 1:
            return True
        elif direction == 'RIGHT' and x >= 19:  # Approximate map width
            return True
        
        return False

