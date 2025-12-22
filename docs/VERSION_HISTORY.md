# Version History

## Version 0.0.7 (2025-12-21)

### Enhanced State Detection and Blank Screen Handling

**Status**: Stable

**Key Features**:
- Blank screen detection and validation
- Enhanced state detection with screen content validation
- Character creation protection (prevents backing out)
- Automatic screenshot saving when stuck (non-blank screens only)
- Improved blank screen handling during gameplay transitions

**Improvements**:
- State detection now validates screen content before reporting state
- Blank screens (>80% white/black) correctly detected and handled
- Agent successfully reaches character creation/naming screens
- Multiple layers of protection prevent backing out during character creation
- Screenshots saved automatically when agent gets stuck (with content)
- Blank screen handling with aggressive A-press strategy for transitions

**Bug Fixes**:
- Fixed false "overworld" state detection on blank screens
- Fixed agent backing out after starting new game
- Fixed screenshot saving for blank screens (now skipped)

**Files Modified**:
- `game_state.py` - Added `detect_blank_screen()` method, enhanced state detection
- `pokemon_agent.py` - Added blank screen handling, character creation protection, screenshot saving
- `llm_optimizer.py` - Updated prompts to warn against B during character creation

## Version 0.0.6 (2025-12-21)

### Enhanced Logging and Analytics

**Status**: Stable

**Key Features**:
- Comprehensive metrics tracking system
- Performance metrics (step timing, OCR timing, LLM timing)
- Cache statistics (hit rate, evictions, utilization)
- LLM call statistics (count, latency, tokens, success rate)

**Improvements**:
- Metrics automatically collected during execution
- Metrics displayed in human-readable summary at end of runs
- Metrics saved to JSON log files for analysis
- Rolling averages for recent performance trends
- Integration into all components (agent, LLM provider, game state)

**New Files**:
- `metrics.py` - Metrics tracking module
- `docs/METRICS_GUIDE.md` - Comprehensive metrics documentation
- `tests/test_metrics.py` - Unit tests for metrics (19 tests)
- `tests/test_metrics_integration.py` - Integration tests (11 tests)
- `tests/test_performance.py` - Performance benchmarks and regression tests (7 tests)
- `tests/test_end_to_end.py` - End-to-end gameplay sequence tests (5 tests)
- `tests/test_stress.py` - Stress tests for extended runs (6 tests)
- `tests/test_edge_cases.py` - Edge case and error recovery tests (10 tests)

**Documentation**:
- Created METRICS_GUIDE.md with usage examples
- Updated README.md with metrics information
- Updated LOGGING_GUIDE.md with metrics section
- Updated CHANGELOG.md with v0.0.6 changes
- Updated tests/README.md with comprehensive test documentation

**Testing**:
- Expanded test suite from 95 to 123 tests
- Added performance benchmark tests
- Added end-to-end gameplay tests
- Added stress tests for extended runs
- Added comprehensive edge case tests
- All tests passing (122 passing, 1 skipped)

**Next Version Plans**:
- OCR training on Game Boy font samples
- Expanded visual state analysis
- Additional performance optimizations

## Version 0.0.5.1 (2025-12-19)

### Bug Fixes

**Status**: Stable

**Fixes**:
- Fixed missing `List` import in `config.py`
- Resolved `NameError` when importing config module

## Version 0.0.5 (2025-12-19)

### Configuration Profiles

**Status**: Stable

**Key Features**:
- Configuration profiles system (aggressive, conservative, balanced)
- Profile-based strategy customization
- Command-line profile selection (`--profile`)
- Profile settings override defaults automatically

**Improvements**:
- Three pre-configured strategy profiles
- Profile settings for exploration rate, goal checking, token limits, cache sizes
- Profile name logged in execution logs
- Easy profile switching via command line or config file

**Documentation**:
- Updated README with profile usage
- Profile documentation in config.yaml

**Next Version Plans**:
- Enhanced logging and analytics
- Performance metrics tracking
- Cache hit rate monitoring

## Version 0.0.4.1 (2025-12-19)

### Bug Fixes and Configuration System

**Status**: Stable

**Key Features**:
- YAML-based configuration system (`config.yaml`)
- Performance optimizations (reduced LLM calls, smarter caching)
- Fixed `UnboundLocalError` bug

**Improvements**:
- Configuration file for all agent parameters
- LRU cache eviction
- State-based action shortcuts
- Skip LLM calls for predictable states

## Version 0.0.4 (2025-12-19)

### Enhanced Strategy and OCR

**Status**: Stable

**Key Features**:
- Goal-oriented agent strategy
- Enhanced OCR with region detection
- Improved prompt engineering

**Improvements**:
- Character-level OCR for Game Boy font
- Text region detection (dialog boxes)
- Goal-oriented behavior system
- State machine for game phases
- Exploration vs exploitation balance

## Version 0.0.3 (2025-12-19)

### Memory Reading and Testing

**Status**: Stable

**Key Features**:
- Memory-based game state reading
- Comprehensive test suite

**Improvements**:
- Direct memory access for game state
- Player position, map, party, health reading
- Unit tests for all core modules

## Version 0.0.2 (2025-12-19)

### Memory Reading Implementation

**Status**: Stable

**Key Features**:
- Memory-based game state reading
- Pokemon Red memory addresses

**Improvements**:
- Player position reading
- Current map detection
- Pokemon party status
- Health/HP values

## Version 0.0.1 (2025-12-19)

### Initial Release

**Status**: Stable

**Key Features**:
- AI agent for playing Pokemon Red
- LLM integration (Ollama/Claude)
- OCR-based game state extraction
- Action optimization and caching
- Comprehensive logging

**Improvements**:
- Enhanced OCR preprocessing
- Game state detection
- Pattern-based repetition detection
- Action validation

**Documentation**:
- Complete setup guides
- Performance optimization guides
- Troubleshooting documentation
- Improvement roadmap

**Known Issues**:
- OCR accuracy varies
- Limited game state awareness
- May get stuck in repetitive patterns

**Next Version Plans**:
- Memory-based game state reading
- Further OCR improvements
- Enhanced agent strategy

