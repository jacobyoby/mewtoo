# Troubleshooting Guide

## Using Metrics for Debugging

**New in v0.0.6**: Use metrics to identify performance issues and bottlenecks.

### Check Metrics Summary

After running the agent, review the metrics summary:

```powershell
# Run agent and check metrics at the end
python main.py --rom "Pokemon - Red Version (USA, Europe) (SGB Enhanced).gb" --steps 100 --headless --llm-provider ollama
```

Look for:
- **Low cache hit rate (<50%)**: Agent is making too many LLM calls
- **High LLM latency (>1000ms)**: Model is too slow or network issues
- **High error rate**: LLM provider connection problems
- **Slow step times**: OCR or LLM bottleneck

### Analyze Log Files

```powershell
# View metrics in latest log
python scripts/analyze_log.py --latest
```

See `docs/METRICS_GUIDE.md` for detailed metrics interpretation.

## Agent Not Making Progress

If the agent isn't reaching the start menu after 100 steps, try these solutions:

### 1. Improve OCR Quality
The agent relies on OCR to read the screen. If OCR isn't working well:

```powershell
# Run with more frequent OCR (slower but more accurate)
python main.py --rom "Pokemon - Red Version (USA, Europe) (SGB Enhanced).gb" --steps 100 --display --ocr-interval 5 --llm-provider ollama
```

### 2. Use Better LLM Model
Smaller models may not follow instructions well. Try a larger model:

```powershell
# Use a larger model (if available)
python main.py --rom "Pokemon - Red Version (USA, Europe) (SGB Enhanced).gb" --steps 100 --display --llm-provider ollama --model llama3.2:3b
```

### 3. Add Manual Start Sequence
The agent should press START on the title screen. If it's not working:

- The improved prompts now include context about being at the title screen
- The agent will try START as a fallback if early in the game

### 4. Check What's Happening
Run with display to see what the agent is doing:

```powershell
python main.py --rom "Pokemon - Red Version (USA, Europe) (SGB Enhanced).gb" --steps 20 --display --ocr-interval 5 --llm-provider ollama
```

Watch the game window to see:
- Is it stuck on title screen?
- Is it pressing buttons but not progressing?
- Is OCR reading the screen correctly?

### 5. Common Issues

**Issue: Agent keeps pressing same button**
- The LLM might be confused. Try restarting with fresh state.
- Check if OCR is returning useful text.

**Issue: Agent presses random buttons**
- The prompt has been improved to be more specific.
- Make sure you're using the latest code.

**Issue: Game runs but agent doesn't progress**
- Pokemon Red has timing requirements - the agent might need to wait.
- Try increasing frames per step in main.py (currently 5).

### 6. Blank Screen Handling

**New in latest version**: The agent now handles blank screens automatically.

If you see blank screens during gameplay:
- The agent will automatically detect blank screens
- It will press A to progress through transitions
- Console will show `[BLANK_SCREEN]` messages indicating blank screen detection
- Screenshots are NOT saved for blank screens (only for actual stuck states with content)

**Common blank screen scenarios:**
- Game transitions (title → menu, menu → game)
- Dialog transitions
- Map loading screens

The agent handles these automatically - no action needed.

### 7. Character Creation Protection

**New in latest version**: The agent is protected from backing out during character creation.

- Agent detects when character creation/naming screens appear
- B button presses are blocked during character creation
- Multiple protection layers ensure agent doesn't cancel new game
- Console will show `[CHARACTER_CREATION]` messages if B is blocked

### 8. Expected Behavior

**Title Screen (Steps 1-3):**
- Should press START
- Should press A to select "NEW GAME"

**Character Creation (Steps 4-50):**
- Should navigate through character creation screens
- Should press A repeatedly (B is blocked)
- Should reach naming prompts

**Name Entry (Steps 50+):**
- Should navigate with UP/DOWN
- Should press A to confirm

**Game Start (Steps 100+):**
- Should be in Pallet Town
- Should be able to move around

If the agent isn't following this sequence, check the console for `[BLANK_SCREEN]` or `[CHARACTER_CREATION]` messages.

