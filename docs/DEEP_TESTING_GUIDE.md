# Deep Testing Guide

This guide explains how to test the agent deeper into Pokemon Red with extended runs and progress tracking.

## Enhanced Features for Deep Testing

### 1. Extended Goal System

The agent now tracks more goals for deeper gameplay:

- **Early Game Goals:**
  - Start game
  - Get starter Pokemon
  - Get Pokedex
  - Explore Route 1

- **Mid Game Goals:**
  - Reach Viridian City
  - Reach Pewter City
  - Catch Pokemon
  - Train Pokemon to level 10+

- **Advanced Goals:**
  - Defeat Brock (first gym leader)
  - Level up through battles

### 2. Automatic Progress Detection

The agent automatically detects when goals are completed by checking:
- **Memory data** (map IDs, party status, Pokemon levels)
- **Game state** (current location, battle status)
- **Progress indicators** (Pokemon caught, levels achieved)

### 3. Progress Tracking

Each step now includes:
- Current goal progress (X/Y goals completed)
- Location information (map name, coordinates)
- Party status (size, Pokemon levels, HP)
- Recent completed goals

## Running Deep Tests

### Basic Extended Run

```bash
python main.py --rom "Pokemon - Red Version (USA, Europe) (SGB Enhanced).gb" --steps 500
```

### Using Deep Test Script

```bash
python scripts/deep_test.py --rom "Pokemon - Red Version (USA, Europe) (SGB Enhanced).gb" --steps 1000
```

### With Display (Watch Progress)

```bash
python scripts/deep_test.py --rom "Pokemon - Red Version (USA, Europe) (SGB Enhanced).gb" --steps 500 --display
```

### Headless Mode (Faster)

```bash
python scripts/deep_test.py --rom "Pokemon - Red Version (USA, Europe) (SGB Enhanced).gb" --steps 1000 --headless
```

## Understanding Output

### Step-by-Step Output

Each step shows:
```
Step 1/500
  Action: START
  Success: True
  Game State: title_screen
  Progress: 0/10 goals (0.0%)
  Location: Unknown
  Position: (0, 0)
```

### Progress Updates

When goals are completed:
```
Step 50/500
  Action: A
  Success: True
  Game State: overworld
  Progress: 2/10 goals (20.0%)
  Recent Goals: start_game, get_starter
  Location: Pallet Town
  Position: (10, 8)
  Party: 1 Pokemon
  First Pokemon: Level 5, HP 20/20
```

### Final Summary

At the end of the run:
```
============================================================
Final Progress Summary
============================================================
Completed Goals: 5/10 (50.0%)
Current Phase: exploration
Total Steps: 500
Completed: start_game, get_starter, reach_viridian, catch_pokemon, level_up
============================================================
```

## Log Analysis

Logs now include:
- Progress information for each step
- Location and position data
- Party status
- Completed goals

Analyze logs:
```bash
python scripts/analyze_log.py logs/pokemon_agent_YYYYMMDD_HHMMSS.json
```

## Tips for Deep Testing

1. **Start with 500 steps** to see meaningful progress
2. **Use display mode** to visually verify agent behavior
3. **Check logs** to see where the agent gets stuck
4. **Monitor progress** to see which goals are being completed
5. **Adjust exploration rate** if agent is too repetitive (in `agent_strategy.py`)

## Expected Progress

### Early Steps (1-100)
- Start game
- Navigate menus
- Get starter Pokemon
- Begin exploration

### Mid Steps (100-300)
- Explore Route 1
- Reach Viridian City
- Catch wild Pokemon
- Train Pokemon

### Later Steps (300+)
- Reach Pewter City
- Level up Pokemon
- Battle trainers
- Progress toward gyms

## Troubleshooting

### Agent Stuck
- Check `stuck_count` in output
- Review recent actions in logs
- Verify memory reading is working

### No Progress
- Ensure memory reading is enabled
- Check if goals are being detected
- Verify game state detection

### Slow Progress
- Use `--fast` mode for faster runs
- Reduce OCR interval
- Use headless mode

## Next Steps

For even deeper testing:
1. Add more goals (gyms, badges, etc.)
2. Implement save state loading
3. Add battle strategy improvements
4. Enhance exploration algorithms

