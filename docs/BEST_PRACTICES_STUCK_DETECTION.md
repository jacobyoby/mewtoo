# Best Practices for Stuck Detection and Action Diversity

Based on research and analysis of game AI agents, here are best practices for handling stuck states and improving action diversity.

## 1. Multi-Modal Stuck Detection

### Current Issue
- Only checks state key (game_state + text)
- Frame count changes even when stuck, so detection fails
- No position-based detection

### Best Practice: Combine Multiple Signals

**Recommended Approach:**
```python
# Combine multiple signals for robust stuck detection
stuck_signals = {
    'state_key_same': last_state_key == current_state_key,
    'position_unchanged': position == last_position and action in MOVEMENT_ACTIONS,
    'action_repetition': action_count(action, last_n=10) > threshold,
    'no_progress': no_goal_progress_for_n_steps > threshold
}

is_stuck = sum(stuck_signals.values()) >= 2  # Require multiple signals
```

**Key Principles:**
- Use position data when available (most reliable)
- Combine with action history analysis
- Check goal progress over time
- Require multiple signals to avoid false positives

## 2. Action Diversity Enforcement

### Current Issue
- 77.4% UP actions - no diversity enforcement
- Strategy always suggests same action
- No mechanism to force exploration

### Best Practice: Action Diversity Metrics

**Recommended Approach:**
```python
def check_action_diversity(action_history, window=15, threshold=0.6):
    """Check if action diversity is too low."""
    recent = action_history[-window:]
    action_counts = Counter(recent)
    most_common_ratio = action_counts.most_common(1)[0][1] / len(recent)
    
    # If one action is >60% of recent actions, force diversity
    if most_common_ratio > threshold:
        return True, action_counts.most_common(1)[0][0]
    return False, None
```

**Key Principles:**
- Track action distribution over sliding window (10-20 actions)
- Force diversity when one action exceeds threshold (50-60%)
- Use entropy-based metrics for more sophisticated detection
- Temporarily disable strategy suggestions when stuck

## 3. Position-Based Movement Validation

### Current Issue
- Position doesn't change after movement actions
- No validation that movement actually occurred
- Strategy suggests UP even when hitting wall

### Best Practice: Movement Validation

**Recommended Approach:**
```python
def validate_movement(action, pre_position, post_position, stuck_threshold=3):
    """Validate that movement action actually moved the player."""
    if action in MOVEMENT_ACTIONS:
        if pre_position == post_position:
            # Movement didn't occur - likely hitting wall
            self.movement_failures[action] += 1
            
            if self.movement_failures[action] >= stuck_threshold:
                # This direction is blocked, try different direction
                return False, get_alternative_direction(action)
    
    return True, None
```

**Key Principles:**
- Track movement failures per direction
- After N failures in same direction, try perpendicular directions
- Use position delta to validate movement
- Maintain "blocked directions" memory

## 4. Exploration vs Exploitation Balance

### Current Issue
- Strategy always exploits (suggests UP)
- No forced exploration when stuck
- Exploration rate doesn't increase when stuck

### Best Practice: Adaptive Exploration Rate

**Recommended Approach:**
```python
def get_exploration_rate(base_rate, stuck_count, action_diversity):
    """Adaptively adjust exploration rate based on stuck state."""
    # Increase exploration when stuck
    if stuck_count > 5:
        return min(0.8, base_rate + 0.3)  # Force more exploration
    
    # Increase exploration when action diversity is low
    if action_diversity < 0.3:
        return min(0.7, base_rate + 0.2)
    
    return base_rate
```

**Key Principles:**
- Increase exploration rate when stuck
- Temporarily disable strategy suggestions when stuck
- Use epsilon-greedy with adaptive epsilon
- Force random actions periodically when stuck

## 5. Pattern Detection Improvements

### Current Issue
- Only detects exact patterns (A-A-SELECT)
- Doesn't detect "mostly UP" patterns
- Pattern threshold too high

### Best Practice: Statistical Pattern Detection

**Recommended Approach:**
```python
def detect_statistical_pattern(action_history, window=15):
    """Detect statistical patterns (e.g., mostly UP)."""
    recent = action_history[-window:]
    action_counts = Counter(recent)
    
    # Check if one action dominates
    total = len(recent)
    for action, count in action_counts.items():
        ratio = count / total
        if ratio > 0.6:  # More than 60% of actions
            return True, action, ratio
    
    return False, None, 0
```

**Key Principles:**
- Use statistical analysis, not just exact patterns
- Detect "mostly X" patterns (60%+ threshold)
- Use sliding windows of different sizes
- Consider action sequences, not just individual actions

## 6. Strategy System Improvements

### Current Issue
- Strategy always suggests UP for movement
- No use of position data
- No boundary/wall detection

### Best Practice: Context-Aware Strategy

**Recommended Approach:**
```python
def suggest_action_for_goal(goal, game_state, memory_data):
    """Use position and map data to suggest actual direction."""
    if goal.name == "reach_viridian":
        if game_state == "overworld":
            pos = memory_data.get("player_position", (0, 0))
            map_info = memory_data.get("current_map", {})
            
            # Use actual map knowledge
            if map_info.get("map_id") == 0x00:  # Pallet Town
                # Need to go north to Route 1
                # But check if we're already at north boundary
                if pos[1] <= 1:  # Already at top
                    return "RIGHT"  # Try different direction
                return "UP"
            
            # Use position relative to goal
            target_pos = get_target_position(goal)
            direction = calculate_direction(pos, target_pos)
            return direction
    
    return None
```

**Key Principles:**
- Use position data to determine actual direction needed
- Check boundaries before suggesting movement
- Use map knowledge when available
- Fall back to exploration when position data unavailable

## 7. Reinforcement Learning Techniques

### Best Practice: Reward Shaping

**Recommended Approach:**
```python
def calculate_reward(action, pre_state, post_state):
    """Calculate reward with penalty for stuck behavior."""
    reward = 0
    
    # Positive rewards
    if goal_completed:
        reward += 100
    if position_changed:
        reward += 1
    if new_area_discovered:
        reward += 10
    
    # Negative rewards (penalties)
    if position_unchanged and action in MOVEMENT_ACTIONS:
        reward -= 2  # Penalty for failed movement
    if action_diversity_low:
        reward -= 1  # Penalty for repetitive actions
    if stuck_count > 5:
        reward -= 5  # Large penalty for being stuck
    
    return reward
```

**Key Principles:**
- Penalize repetitive actions
- Reward position changes
- Penalize failed movements
- Reward goal progress

## 8. Implementation Priority

### Phase 1: Quick Wins (High Impact, Low Effort)
1. ✅ Add position-based stuck detection
2. ✅ Add action diversity checking
3. ✅ Force exploration when stuck_count > threshold

### Phase 2: Strategy Improvements (Medium Effort)
4. ✅ Use position data in strategy suggestions
5. ✅ Add movement validation
6. ✅ Improve pattern detection for "mostly X" patterns

### Phase 3: Advanced Features (Higher Effort)
7. ✅ Implement adaptive exploration rate
8. ✅ Add reward shaping for training
9. ✅ Implement boundary detection

## 9. Testing and Validation

### Metrics to Track
- Action diversity (entropy of action distribution)
- Position changes per step
- Stuck detection accuracy
- Goal completion rate
- Movement success rate

### Test Scenarios
1. Agent hitting wall repeatedly
2. Agent in dialog loop
3. Agent stuck in menu
4. Agent making no progress

## 10. References

- **Reinforcement Learning**: Q-Learning, DQN for game AI
- **Exploration Strategies**: Epsilon-greedy, UCB, Thompson Sampling
- **Stuck Detection**: Multi-modal signal fusion
- **Action Diversity**: Entropy-based metrics, statistical analysis

## Implementation Checklist

- [ ] Add position-based stuck detection
- [ ] Implement action diversity checking
- [ ] Add movement validation
- [ ] Improve pattern detection (statistical)
- [ ] Use position data in strategy
- [ ] Add adaptive exploration rate
- [ ] Implement boundary detection
- [ ] Add reward shaping
- [ ] Test with various scenarios
- [ ] Monitor metrics and iterate




