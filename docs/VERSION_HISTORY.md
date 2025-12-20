# Version History

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

