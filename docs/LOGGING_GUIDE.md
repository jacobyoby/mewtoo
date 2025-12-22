# Logging Guide

## Overview

The Pokemon agent now logs all steps to JSON files, allowing you to analyze and iterate on the agent's behavior.

## Automatic Logging

By default, logs are automatically saved to the `logs/` directory with timestamps:

```powershell
python main.py --rom "Pokemon - Red Version (USA, Europe) (SGB Enhanced).gb" --steps 100 --display --llm-provider ollama
```

This creates: `logs/pokemon_agent_YYYYMMDD_HHMMSS.json`

## Custom Log Location

Specify a custom log file:

```powershell
python main.py --rom "Pokemon - Red Version (USA, Europe) (SGB Enhanced).gb" --steps 100 --log my_run.json
```

Or change the log directory:

```powershell
python main.py --rom "Pokemon - Red Version (USA, Europe) (SGB Enhanced).gb" --steps 100 --log-dir my_logs
```

## Log File Structure

Each log file contains:

```json
{
  "rom": "path/to/rom.gb",
  "steps": 100,
  "llm_provider": "ollama",
  "model": null,
  "profile": "balanced",
  "ocr_enabled": true,
  "ocr_interval": 50,
  "start_time": "2025-12-19T23:07:18",
  "end_time": "2025-12-19T23:07:25",
  "total_steps_completed": 100,
  "metrics": {
    "runtime": {...},
    "performance": {...},
    "llm": {...},
    "cache": {...}
  },
  "steps_log": [
    {
      "step": 1,
      "action": "START",
      "success": true,
      "frame_count": 62,
      "screen_text": "",
      "game_state": "title_screen",
      "timestamp": "2025-12-19T23:07:18"
    },
    ...
  ],
  "final_progress": {
    "completed_goals": 1,
    "total_goals": 10,
    "progress_percent": 10.0
  }
}
```

## Analyzing Logs

Use the analysis script:

```powershell
# Analyze latest log
python scripts/analyze_log.py --latest

# Analyze specific log
python scripts/analyze_log.py logs/pokemon_agent_20251219_230718.json
```

The analysis shows:
- Run information (ROM, steps, provider, etc.)
- Action statistics (most common actions, percentages)
- Success rate
- Screen text detection rate
- Action sequence
- Frame count statistics

## Using Logs to Iterate

1. **Run the agent** and let it complete or stop early
2. **Analyze the log** to see what actions were taken
3. **Identify patterns** - is the agent stuck? Repeating actions?
4. **Adjust prompts** in `pokemon_agent.py` based on findings
5. **Re-run** and compare logs

## Example Workflow

```powershell
# Run agent
python main.py --rom "Pokemon - Red Version (USA, Europe) (SGB Enhanced).gb" --steps 100 --display --llm-provider ollama

# Analyze what happened
python scripts/analyze_log.py --latest

# Make improvements to pokemon_agent.py based on findings

# Run again and compare
python main.py --rom "Pokemon - Red Version (USA, Europe) (SGB Enhanced).gb" --steps 100 --display --llm-provider ollama
python scripts/analyze_log.py --latest
```

## Log Features

- **Incremental saving**: Log is saved after each step (survives crashes)
- **Complete metadata**: All run parameters are logged
- **Screen text**: OCR results are logged for analysis
- **Timestamps**: Each step has a timestamp
- **Error tracking**: Errors and tracebacks are logged

## Metrics in Logs

Log files now include comprehensive metrics data. See `docs/METRICS_GUIDE.md` for detailed information about:
- Performance metrics (step timing, OCR timing, LLM timing)
- Cache statistics (hit rate, evictions)
- LLM statistics (call count, latency, success rate)

Metrics are automatically displayed at the end of each run and saved to log files.

## Tips

- Compare multiple runs to see if improvements help
- Look for action patterns that indicate the agent is stuck
- Check screen text to see if OCR is working well
- Use logs to debug why the agent isn't progressing
- Review metrics to optimize performance (cache hit rate, LLM call count)

