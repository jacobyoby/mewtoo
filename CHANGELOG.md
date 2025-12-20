# Changelog

All notable changes to Mewtwo will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.0.5.1] - 2025-12-19

### Fixed
- Fixed missing `Tuple` import in `pokemon_agent.py` that caused `NameError` when using type hints
- Fixed stuck detection not working properly in dialogues with garbled OCR text
- Improved dialogue detection to work even when OCR produces short/garbled text (like "reese")

### Added
- **Screenshot functionality for debugging stuck situations**
  - Automatic screenshots saved to `logs/screenshots/` when stuck patterns detected
  - Screenshots captured for: repetitive actions, same-state persistence, dialogue stuck, movement stuck
  - Rate limiting prevents screenshot spam (max 1 per 10 steps)
  - Screenshot filenames include step number and stuck type
  
- **Enhanced stuck detection**
  - Action diversity checking runs before same-state optimization
  - Detects A button spam even when dialogue isn't detected
  - Same-state counter tracks persistent stuck states
  - Visual dialogue box detection as fallback when OCR fails
  
- **Configurable OCR scale factor**
  - Default increased from 4x to 6x for better OCR accuracy
  - Command-line argument `--ocr-scale` for customization (recommended: 6-8 for headless)
  - Config file option `ocr.scale_factor`
  - Better interpolation (Lanczos4) for sharper upscaling
  - Works in headless mode (PyBoy renders internally)

- **Stuck pattern analysis script**
  - `scripts/check_stucks.py` analyzes log files for stuck patterns
  - Detects: repetitive actions (7+ same action in 10 steps), same-state persistence (10+ steps), position stuck, A button spam in overworld

### Changed
- Visual dialogue box detection now runs even when memory says "overworld" (if screen text exists)
- Lowered dialogue detection threshold from 10 to 3 characters for short garbled text
- Improved visual detection sensitivity (lowered thresholds for better detection)
- OCR preprocessing now uses Lanczos4 interpolation instead of cubic for better quality

## [0.0.5] - 2025-12-19

### Added
- **Configuration Profiles**
  - Three pre-configured strategy profiles: `aggressive`, `conservative`, and `balanced`
  - `--profile` command-line argument to select profile
  - Profile settings override default configuration values
  - Profiles customize exploration rate, goal checking frequency, token limits, cache sizes, and frame rates
  - Active profile is logged in execution logs

### Changed
- `AgentStrategy.__init__()` now accepts `exploration_rate` and `max_recent_events` parameters
- `config.py` includes profile management methods (`get_profile()`, `apply_profile()`, `list_profiles()`)
- Profile settings are applied automatically from `config.yaml` or via command line
- Log files now include the active profile name

### Profile Details
- **Aggressive**: 10% exploration, faster gameplay, larger cache (150), fewer tokens (8)
- **Conservative**: 50% exploration, slower gameplay, smaller cache (75), more tokens (15)
- **Balanced**: 30% exploration, standard settings (default)

## [0.0.4.1] - 2025-12-19

### Fixed
- Fixed `UnboundLocalError` in `pokemon_agent.py` where `state_changed` was accessed before being defined
- Moved `state_changed` calculation before its first use in goal checking logic

### Added
- **Configuration system** (`config.yaml`)
  - YAML-based configuration file for all agent parameters
  - Easy tuning without code changes
  - Command-line arguments override config file settings
  - Configurable agent, strategy, LLM, OCR, memory, and performance settings
- PyYAML dependency for configuration file support

### Changed
- `main.py` now loads and uses configuration from `config.yaml`
- `pokemon_agent.py` uses config values for max_history, max_tokens, cache size, and exploration rate
- Default values now come from config file when available

### Performance Improvements
- **Reduced LLM calls**: Skip LLM calls when game state hasn't changed significantly
- **Smarter caching**: Improved cache keys using game state + position for better hit rates
- **State-based shortcuts**: Skip LLM for predictable states (e.g., dialog always uses A)
- **LRU cache eviction**: ActionCache now uses Least Recently Used eviction instead of FIFO
- **Optimized prompt generation**: Only generate prompts when LLM call is actually needed

## [0.0.4] - 2025-12-19

### Added
- **Enhanced OCR system** (`ocr_enhancer.py`)
  - Text region detection (dialog boxes, menus, battle text)
  - Character-level OCR support for Game Boy font
  - Improved text cleaning for Game Boy-specific OCR errors
  - Region prioritization (dialog boxes prioritized)
- **Goal-oriented agent strategy** (`agent_strategy.py`)
  - Goal system with priorities (start game, get starter, reach towns, etc.)
  - State machine for game phases (Title Screen, Early Game, Exploration, Battle, etc.)
  - Exploration vs exploitation balance (configurable exploration rate)
  - Recent events tracking and history
  - Goal completion tracking
- **Enhanced prompt engineering**
  - Game state summary in prompts (position, map, party, health)
  - Recent game events context
  - Action explanations with context-aware hints
  - Strategy context (current goals, phase, completed goals)
  - Improved system prompts with goal awareness

### Changed
- `GameState.get_screen_text()` now uses enhanced OCR with fallback
- `PokemonAgent` integrates strategy system for goal-oriented behavior
- `PromptOptimizer.optimize_prompt()` includes game state summary, events, and strategy
- Prompts now include comprehensive context for better decision-making

### Improved
- OCR accuracy through region detection and prioritization
- Agent decision-making through goal-oriented strategy
- Prompt quality with full game context

## [0.0.3] - 2025-12-19

### Added
- **Comprehensive test suite** using pytest
  - Unit tests for `memory_reader.py` module
  - Unit tests for `game_state.py` module
  - Unit tests for `llm_optimizer.py` module
  - Unit tests for `pokemon_agent.py` module
  - Pytest fixtures and configuration
  - Test documentation (`tests/README.md`)
- Test dependencies: pytest, pytest-cov, pytest-mock
- Mock fixtures for PyBoy and LLM providers
- Coverage reporting support

### Testing
- All core modules now have unit tests
- Tests use mocks to avoid requiring ROM files or external APIs
- Can run tests with: `pytest`
- Coverage reports available with: `pytest --cov=. --cov-report=html`

## [0.0.2] - 2025-12-19

### Added
- **Memory-based game state reading** - Direct memory access for accurate game state
  - Player position (X, Y coordinates) reading
  - Current map/location detection
  - Pokemon party status reading
  - Health/HP values for party Pokemon
  - Inventory items reading
  - Menu state detection
  - Battle state detection
- `memory_reader.py` module with Pokemon Red memory addresses
- Memory reading integration into `game_state.py`
- Test script `scripts/test_memory_reader.py` for memory reading verification
- Configurable memory reading (can be enabled/disabled)
- Graceful fallback to OCR if memory reading fails

### Changed
- `GameState.get_game_info()` now uses memory reading as primary source with OCR fallback
- Improved game state detection using memory data
- Enhanced error handling for memory access

### Fixed
- Fixed missing `List` import in `llm_optimizer.py`

### Technical Details
- Memory addresses based on Pokemon Red disassembly
- Supports multiple PyBoy API versions for memory access
- Comprehensive error handling for memory reading failures

## [0.0.1] - 2025-12-19

### Added
- Initial release of Mewtwo
- Core AI agent for playing Pokemon Red
- LLM integration (Ollama and Claude API support)
- OCR-based game state extraction using Tesseract
- Action caching and optimization system
- Pattern-based repetition detection
- Comprehensive logging system
- Utility scripts for ROM verification and log analysis
- Game state detection (title screen, menu, battle, dialog, overworld)
- Action validation and stuck detection

### Features
- **Main Agent**: `main.py` - Run the AI agent with configurable options
- **LLM Providers**: Support for Ollama (local) and Claude API (cloud)
- **Game State**: OCR-based text extraction with improved preprocessing
- **Optimization**: Action caching, prompt optimization, repetition detection
- **Scripts**: 
  - `scripts/demo.py` - Setup verification
  - `scripts/verify_rom.py` - ROM file validation
  - `scripts/analyze_log.py` - Log analysis tool
  - `scripts/visual_demo.py` - Visual demonstration

### Documentation
- Comprehensive README with setup instructions
- Setup guides for Ollama and ROM extraction
- Performance and optimization guides
- Troubleshooting guide
- Logging guide
- Project structure documentation
- Improvement roadmap

### Improvements
- Enhanced OCR preprocessing (4x scaling, adaptive thresholding)
- Context-aware prompts based on game state
- Pattern-based repetition detection (A-A-SELECT patterns)
- Action validation to detect stuck states
- Improved output display with game state information

### Technical Details
- Python 3.8+ support
- PyBoy emulator integration
- Tesseract OCR integration
- Ollama client integration
- Anthropic Claude API integration

### Known Limitations
- Relies on OCR for game state (memory reading not yet implemented)
- OCR accuracy varies with screen content
- Agent may get stuck in repetitive patterns
- Limited game state awareness (no position, health, etc. yet)

### Future Plans
- Memory-based game state reading (Priority #1)
- Further OCR improvements
- Enhanced agent strategy with goal-oriented behavior
- Visual state analysis
- Performance optimizations

