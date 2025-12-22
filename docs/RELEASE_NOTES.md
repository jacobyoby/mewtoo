# Release Notes

## Version 0.0.7 - Enhanced State Detection and Blank Screen Handling (In Progress)

This release focuses on improving the agent's ability to progress through the early game sequence, particularly character creation and transitions.

### Key Features

- **Blank Screen Detection**: Automatic detection of blank screens (>80% white/black) with proper handling
- **State Detection Validation**: State detection now validates screen content before reporting state
- **Character Creation Protection**: Multiple layers of protection prevent agent from backing out during character creation
- **Enhanced Stuck Detection**: Automatic screenshot saving when stuck (only for screens with content)
- **Improved Blank Screen Handling**: Aggressive handling of blank screens during gameplay transitions

### Improvements

- State detection validates screen content before reporting "overworld" state
- Blank screens correctly detected and reported as "loading" state
- Agent successfully reaches character creation/naming screens
- B button presses blocked during character creation (prevents canceling new game)
- Screenshots automatically saved when agent gets stuck (skips blank screens)
- Blank screen handling with progressive A-press strategy for transitions

### Bug Fixes

- Fixed false "overworld" state detection on blank screens
- Fixed agent backing out after starting new game
- Fixed screenshot saving for blank screens (now skipped)

### Files Modified

- `game_state.py` - Added `detect_blank_screen()` method, enhanced state detection
- `pokemon_agent.py` - Added blank screen handling, character creation protection, screenshot saving
- `llm_optimizer.py` - Updated prompts to warn against B during character creation

### Usage

The agent now handles blank screens automatically. You'll see console messages like:
```
[BLANK_SCREEN] Step 150: Blank screen for 5 steps, pressing A
[CHARACTER_CREATION] Blocked B press, using A instead
[STUCK] Saved screenshot (multi_modal_stuck): logs/screenshots/stuck_multi_modal_stuck_step5.png
```

## Version 0.0.6 - Enhanced Logging and Analytics (2025-12-21)

This release introduces comprehensive metrics tracking to help optimize agent performance and understand system behavior.

### Key Features

- **Performance Metrics**: Track step timing, OCR timing, and LLM timing with averages, min/max, and recent trends
- **Cache Statistics**: Monitor cache hit rates, evictions, and utilization
- **LLM Statistics**: Track call count, latency, token usage, success rate, errors, and timeouts
- **Automatic Collection**: Metrics are automatically collected during execution
- **Human-Readable Summaries**: Metrics summary displayed at end of each run
- **JSON Logging**: All metrics saved to log files for analysis

### New Components

- **`metrics.py`**: New metrics tracking module with `MetricsCollector`, `PerformanceMetrics`, `LLMMetrics`, and `CacheMetrics` classes
- **Integration**: Metrics integrated into `pokemon_agent.py`, `llm_provider.py`, and `game_state.py`
- **Logging**: Metrics automatically included in JSON log files

### Usage

Metrics are enabled by default. At the end of each run, you'll see a summary like:

```
======================================================================
METRICS SUMMARY
======================================================================
Runtime: 14.45s

Performance:
  Total Steps: 500
  Avg Step Time: 20.89ms
  Recent Avg Step Time: 0.64ms
  OCR Calls: 0
  Avg OCR Time: 0.00ms

LLM Statistics:
  Total Calls: 42
  Avg Latency: 484.41ms
  Success Rate: 100.0%

Cache Statistics:
  Hits: 205
  Misses: 26
  Hit Rate: 88.7%
======================================================================
```

### Documentation

- Created `docs/METRICS_GUIDE.md` with comprehensive metrics documentation
- Updated `README.md` with metrics overview
- Updated `docs/LOGGING_GUIDE.md` with metrics information

### Testing

- Added 19 unit tests for metrics module
- Added 11 integration tests for metrics system
- All 95 tests passing

### What's Changed

- Added `metrics.py` module
- Updated `pokemon_agent.py` to track step timing and cache operations
- Updated `llm_provider.py` to track LLM call latency and tokens
- Updated `game_state.py` to track OCR timing
- Updated `main.py` to initialize and log metrics
- Updated `llm_optimizer.py` to track cache evictions

---

## Version 0.0.5.1 - Bug Fix (2025-12-19)

This patch release fixes an import error that prevented the config module from loading.

### Fixed

- Missing `List` import in `config.py` causing `NameError`
- Config module now imports correctly

---

## Version 0.0.5 - Configuration Profiles (2025-12-19)

This release introduces configuration profiles, making it easy to switch between different agent strategies without modifying code.

### Key Features

- **Configuration Profiles**: Three pre-configured profiles (aggressive, conservative, balanced)
- **Profile Selection**: Choose profile via `--profile` command-line argument or `config.yaml`
- **Automatic Application**: Profile settings automatically override defaults
- **Profile Logging**: Active profile is logged in execution logs

### New Profiles

- **Aggressive**: Fast progress, 10% exploration, larger cache (150), fewer tokens (8)
- **Conservative**: Thorough exploration, 50% exploration, smaller cache (75), more tokens (15)
- **Balanced**: Standard approach, 30% exploration, default settings

### Usage

```bash
# Use aggressive profile
python main.py --rom "pokemon_red.gb" --profile aggressive --steps 200

# Use conservative profile
python main.py --rom "pokemon_red.gb" --profile conservative

# Use balanced (default)
python main.py --rom "pokemon_red.gb" --profile balanced
```

### What's Changed

- Added profile definitions to `config.yaml`
- Enhanced `config.py` with profile management methods
- Updated `agent_strategy.py` to accept profile parameters
- Profile settings applied automatically at startup

### Documentation

- Updated README with profile usage examples
- Profile documentation in `config.yaml`
- Updated version history

---

## Version 0.0.4.1 - Configuration System and Performance (2025-12-19)

This release adds a comprehensive configuration system and significant performance optimizations.

### Key Features

- **YAML Configuration**: `config.yaml` for all agent parameters
- **Performance Optimizations**: Reduced LLM calls, smarter caching
- **Bug Fixes**: Fixed `UnboundLocalError` in `pokemon_agent.py`

### Performance Improvements

- Skip LLM calls when game state hasn't changed
- Improved cache keys using game state + position
- State-based shortcuts (dialog always uses A)
- LRU cache eviction instead of FIFO

### Configuration

All settings now configurable via `config.yaml`:
- Agent settings (history, caching, goal intervals)
- Strategy settings (exploration rate)
- LLM settings (token limits, models)
- Performance settings (cache sizes, frame rates)
- OCR/Memory settings (intervals, enable/disable)

---

## Version 0.0.1 - Initial Release (2025-12-19)

This is the initial release of Mewtwo, an AI agent that plays Pokemon Red using LLMs and OCR.

### Key Features

- **AI Agent**: LLM-powered agent that makes decisions based on game state
- **Dual LLM Support**: Works with Ollama (local) and Claude API (cloud)
- **OCR Integration**: Extracts text from game screens using Tesseract
- **Action Optimization**: Caching and repetition detection for efficient gameplay
- **Comprehensive Logging**: Detailed logs for analysis and debugging
- **Game State Detection**: Automatically detects title screen, menu, battle, dialog, and overworld states

### What's Included

**Core Components:**
- Main agent (`main.py`)
- Game state extraction (`game_state.py`)
- LLM providers (`llm_provider.py`)
- Agent logic (`pokemon_agent.py`)
- Optimization system (`llm_optimizer.py`)

**Utility Scripts:**
- ROM verification (`scripts/verify_rom.py`)
- Setup demo (`scripts/demo.py`)
- Log analysis (`scripts/analyze_log.py`)
- Visual demo (`scripts/visual_demo.py`)

**Documentation:**
- Complete setup guides
- Performance optimization tips
- Troubleshooting guide
- Improvement roadmap

### Improvements in This Release

- Enhanced OCR preprocessing (4x scaling, adaptive thresholding)
- Context-aware prompts based on game state
- Pattern-based repetition detection
- Action validation and stuck detection
- Improved error handling

### Requirements

- Python 3.8+
- Tesseract OCR
- Ollama (for local LLM) or Claude API key
- Pokemon Red ROM file (.gb)

### Installation

See [README.md](../README.md) for full installation instructions.

### Known Limitations

- Relies on OCR for game state (memory reading not yet implemented)
- OCR accuracy varies with screen content
- Agent may get stuck in repetitive patterns
- Limited game state awareness (no position, health, etc. yet)

### What's Next

See [TODO.md](../TODO.md) and [docs/IMPROVEMENTS.md](IMPROVEMENTS.md) for planned improvements:
- Memory-based game state reading (Priority #1)
- Further OCR improvements
- Enhanced agent strategy
- Performance optimizations

### Documentation

- [README.md](../README.md) - Main documentation
- [CHANGELOG.md](../CHANGELOG.md) - Version history
- [docs/VERSION_HISTORY.md](VERSION_HISTORY.md) - Detailed version info
- [docs/IMPROVEMENTS.md](IMPROVEMENTS.md) - Improvement roadmap

### Credits

Built with:
- PyBoy - Game Boy emulator
- Tesseract OCR - Text extraction
- Ollama - Local LLM inference
- Anthropic Claude API - Cloud LLM

### License

This project is for educational purposes. Ensure you have legal rights to use the Pokemon ROM file.

---

**Current Version**: 0.0.7  
**Last Updated**: December 19, 2025  
**Status**: Stable

