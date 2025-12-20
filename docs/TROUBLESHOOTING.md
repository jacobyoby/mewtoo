# Troubleshooting Guide

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

### 6. Expected Behavior

**Title Screen (Steps 1-3):**
- Should press START
- Should press A to select "NEW GAME"

**Name Entry (Steps 4-10):**
- Should navigate with UP/DOWN
- Should press A to confirm

**Game Start (Steps 10+):**
- Should be in Pallet Town
- Should be able to move around

If the agent isn't following this sequence, the improved prompts should help guide it better.

