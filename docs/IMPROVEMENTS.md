# Improvement Plan for Mewtwo

**Current Version**: 0.0.7  
**Last Updated**: 2025-12-21

This document outlines planned improvements. For implemented improvements, see `docs/IMPROVEMENTS_IMPLEMENTED.md`.

**Note**: Many improvements from earlier versions have been implemented. This document focuses on remaining work toward v1.0.0.

## Critical Improvements (High Impact)

### 1. **Memory-Based Game State Reading**
**Current Issue**: Agent relies only on OCR which produces garbled text ("Gres/06%9¢ Nintendo")

**Solution**: Read actual game state from memory addresses
- Player position (X, Y coordinates)
- Current map/location
- Player name
- Pokemon party status
- Health/HP values
- Items in inventory
- Current menu state

**Impact**: Massive - agent will have accurate game state instead of guessing

**Implementation**: Create `memory_reader.py` module with Pokemon Red memory addresses

### 2. **Improved OCR Preprocessing**
**Current Issue**: OCR produces garbled text, especially on title screens

**Solution**: 
- Better image preprocessing (scaling, contrast enhancement)
- Game Boy-specific OCR tuning
- Text region detection (focus on dialog boxes)
- Character-level OCR for Game Boy font

**Impact**: High - better text extraction when memory reading isn't available

### 3. **Better Agent Strategy**
**Current Issue**: Agent presses A 62% of the time, SELECT 30% - very repetitive

**Solution**:
- Add goal-oriented behavior (e.g., "get starter Pokemon", "reach next town")
- Implement state machine for different game phases
- Add exploration vs exploitation balance
- Better understanding of game context (menu vs overworld vs battle)

**Impact**: High - agent will make more meaningful progress

## Important Improvements (Medium Impact)

### 4. **Enhanced Prompt Engineering**
**Current Issue**: Prompts are very basic and don't provide enough context

**Solution**:
- Include game state summary (location, health, objectives)
- Add recent game events (what happened last few steps)
- Provide action explanations (why certain actions are good)
- Context-aware prompts based on game phase

**Impact**: Medium-High - better decision making

### 5. **Action Validation & Feedback**
**Current Issue**: No validation that actions had intended effect

**Solution**:
- Check if game state changed after action
- Detect if stuck (same state for N steps)
- Validate actions (e.g., don't press A if already in menu)
- Learn from failed actions

**Impact**: Medium - reduces wasted actions

### 6. **Better Repetition Detection**
**Current Issue**: Repetition detector only checks last action, not patterns

**Solution**:
- Detect action sequences (A-A-SELECT pattern)
- Detect state loops (same game state repeating)
- More sophisticated alternative action selection
- Pattern-based action avoidance

**Impact**: Medium - reduces getting stuck

## Nice-to-Have Improvements (Lower Priority)

### 7. **Visual State Analysis**
**Current Issue**: Only uses OCR, not visual features

**Solution**:
- Detect visual patterns (menus, battles, overworld)
- Object detection (NPCs, items, Pokemon)
- Screen transition detection
- Visual similarity matching

**Impact**: Medium - complements memory reading

### 8. **Performance Optimizations**
**Current Issue**: Could be faster

**Solution**:
- Parallel OCR processing
- Smarter caching strategies
- Reduce LLM calls when possible
- Batch action processing

**Impact**: Low-Medium - better user experience

### 9. **Better Logging & Analysis**
**Current Issue**: Logs exist but could be more informative

**Solution**:
- Add game state to logs
- Track progress metrics (distance traveled, Pokemon caught)
- Visualize agent behavior
- Compare runs

**Impact**: Low - better debugging and analysis

### 10. **Configuration & Tuning**
**Current Issue**: Hard-coded values throughout

**Solution**:
- Config file for all parameters
- Easy tuning of agent behavior
- Different strategies/profiles
- A/B testing framework

**Impact**: Low - easier experimentation

## Priority Matrix

| Improvement | Impact | Effort | Priority |
|------------|--------|--------|----------|
| Memory Reading | High | High | 1 |
| OCR Preprocessing | High | Medium | 2 |
| Agent Strategy | High | High | 3 |
| Prompt Engineering | Medium | Low | 4 |
| Action Validation | Medium | Medium | 5 |
| Repetition Detection | Medium | Low | 6 |
| Visual Analysis | Low | High | 7 |
| Performance | Low | Medium | 8 |
| Logging | Low | Low | 9 |
| Configuration | Low | Medium | 10 |

## Quick Wins (Easy + High Impact)

1. **Improve OCR preprocessing** - Better image processing before OCR
2. **Better prompts** - Add more context to LLM prompts
3. **Pattern detection** - Detect A-A-SELECT patterns and break them
4. **State validation** - Check if actions actually changed game state

## Implementation Notes

### Memory Reading Implementation
Pokemon Red memory addresses (example):
- Player X: 0xD362
- Player Y: 0xD361
- Current Map: 0xD35E
- Player Name: 0xD158-0xD161
- Party Pokemon: 0xD16B+
- HP: Various addresses per Pokemon

Use PyBoy's memory access: `pyboy.memory[address]`

### OCR Improvements
- Scale image 4x for better OCR
- Use adaptive thresholding
- Focus on text regions (bottom of screen for dialog)
- Train OCR on Game Boy font if possible

### Agent Strategy
Implement phases:
1. **Startup**: Navigate title screen, start new game
2. **Character Creation**: Enter name, choose starter
3. **Early Game**: Get starter, learn controls
4. **Exploration**: Explore routes, catch Pokemon
5. **Battles**: Fight wild Pokemon, trainers
6. **Progression**: Complete objectives, advance story

## Success Metrics

Track these to measure improvements:
- **Progress**: Distance traveled, badges earned, Pokemon caught
- **Efficiency**: Actions per objective completed
- **Success Rate**: % of actions that achieve intended goal
- **Diversity**: Action distribution (less repetitive = better)
- **Stuck Detection**: Time spent in same state

## Iterative Approach

1. Start with Quick Wins (OCR, prompts, patterns)
2. Implement Memory Reading (biggest impact)
3. Add Agent Strategy improvements
4. Polish with remaining improvements

