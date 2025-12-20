# Release Notes

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

**Current Version**: 0.0.5  
**Last Updated**: December 19, 2025  
**Status**: Stable

