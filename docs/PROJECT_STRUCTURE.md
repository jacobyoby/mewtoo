# Project Structure

This document describes the organization of the Mewtwo repository.

## Directory Structure

```
pokemon/
├── main.py                 # Main entry point - run the agent here
├── pokemon_agent.py        # AI agent logic and decision-making
├── game_state.py           # Game state extraction & controls
├── memory_reader.py        # Memory-based game state reading
├── agent_strategy.py       # Goal-oriented strategy system
├── llm_provider.py         # LLM integration (Ollama/Claude)
├── llm_optimizer.py        # LLM prompt optimization and caching
├── ocr_enhancer.py         # Enhanced OCR with region detection
├── metrics.py              # Performance metrics and analytics tracking
├── config.py               # Configuration management and Tesseract setup
├── config.yaml             # Configuration file with profiles
├── requirements.txt        # Python dependencies
├── README.md               # Main project documentation
├── CHANGELOG.md            # Version changelog
├── TODO.md                 # TODO list and planned improvements
├── VERSION                 # Current version number
├── .gitignore             # Git ignore rules
│
├── docs/                   # Documentation directory
│   ├── SETUP_STATUS.md          # Setup status and quick start guide (consolidated)
│   ├── TROUBLESHOOTING.md        # Troubleshooting guide
│   ├── METRICS_GUIDE.md          # Metrics and analytics guide
│   ├── PERFORMANCE_GUIDE.md      # Performance optimization guide (includes fixes)
│   ├── EARLY_GAME_VALIDATION.md  # Early game validation documentation
│   ├── EXTRACT_ROM_GUIDE.md     # How to extract ROM from cartridge
│   ├── setup_ollama.md           # Ollama setup guide
│   ├── LLM_OPTIMIZATION_GUIDE.md # LLM optimization tips
│   ├── LOGGING_GUIDE.md          # Logging and analysis guide
│   ├── PROJECT_STRUCTURE.md      # This file
│   ├── VERSION_HISTORY.md        # Detailed version history
│   ├── RELEASE_NOTES.md          # Release notes
│   ├── IMPROVEMENTS.md           # Improvement roadmap
│   ├── IMPROVEMENTS_IMPLEMENTED.md # Implemented improvements summary
│   ├── V1_READINESS_ASSESSMENT.md # v1.0.0 readiness assessment
│   ├── BEST_PRACTICES_STUCK_DETECTION.md # Best practices reference
│   └── ARCHIVE_LOG_ANALYSIS_ISSUES.md # Archived historical issues
│
├── scripts/                # Utility scripts directory
│   ├── analyze_log.py     # Analyze agent execution logs
│   ├── check_stucks.py    # Analyze stuck patterns in logs
│   ├── demo.py            # Setup verification demo
│   ├── deep_test.py       # Deep testing utilities
│   ├── test_memory_reader.py # Memory reader testing script
│   ├── validate_early_game.py # Early game sequence validation script
│   ├── verify_rom.py      # ROM file verification script
│   └── visual_demo.py     # Visual demonstration (no ROM needed)
│
├── tests/                  # Test suite directory
│   ├── test_memory_reader.py # Memory reader tests (20 tests)
│   ├── test_game_state.py    # Game state tests (20 tests)
│   ├── test_llm_optimizer.py # LLM optimizer tests (11 tests)
│   ├── test_pokemon_agent.py # Pokemon agent tests (10 tests)
│   ├── test_metrics.py       # Metrics unit tests (19 tests)
│   ├── test_metrics_integration.py # Metrics integration tests (11 tests)
│   ├── test_performance.py   # Performance benchmarks (7 tests)
│   ├── test_end_to_end.py    # End-to-end tests (5 tests)
│   ├── test_stress.py        # Stress tests (6 tests)
│   ├── test_edge_cases.py    # Edge case tests (10 tests)
│   ├── conftest.py           # Pytest fixtures and configuration
│   └── README.md             # Test suite documentation
│
├── logs/                   # Agent execution logs (auto-generated)
│   ├── pokemon_agent_*.json  # Execution logs with metrics
│   └── screenshots/          # Debug screenshots when stuck detected
│
└── [ROM files]            # User-provided ROM files (not in repo)
    └── *.gb, *.gbc        # Game Boy ROM files
```

## Core Files

### Main Entry Point
- **`main.py`** - Main entry point for running the agent. Handles command-line arguments, initializes PyBoy, LLM providers, and runs the agent loop.

### Core Modules
- **`pokemon_agent.py`** - Contains the `PokemonAgent` class that makes decisions based on game state using LLMs.
- **`game_state.py`** - Handles game state extraction via OCR and memory reading, provides controls for button presses.
- **`memory_reader.py`** - Direct memory access for accurate game state (player position, map, party, health).
- **`agent_strategy.py`** - Goal-oriented strategy system with exploration/exploitation balance.
- **`llm_provider.py`** - Abstract interface for LLM providers (Ollama and Claude implementations).
- **`llm_optimizer.py`** - Optimizes prompts and caches responses for better performance.
- **`ocr_enhancer.py`** - Enhanced OCR with text region detection and Game Boy font support.
- **`metrics.py`** - Performance metrics tracking (step timing, cache statistics, LLM call statistics).
- **`config.py`** - Configuration management with profile support and Tesseract OCR path setup.
- **`config.yaml`** - YAML configuration file with agent settings and strategy profiles.

## Documentation (`docs/`)

All documentation files are organized in the `docs/` directory:

- **Setup Guides**: `SETUP_STATUS.md`, `setup_ollama.md`, `EXTRACT_ROM_GUIDE.md`
- **Usage Guides**: `LOGGING_GUIDE.md`, `METRICS_GUIDE.md`, `PERFORMANCE_GUIDE.md`, `LLM_OPTIMIZATION_GUIDE.md`
- **Reference**: `TROUBLESHOOTING.md`, `PROJECT_STRUCTURE.md`, `VERSION_HISTORY.md`
- **Validation**: `EARLY_GAME_VALIDATION.md`, `V1_READINESS_ASSESSMENT.md`
- **History**: `RELEASE_NOTES.md`, `IMPROVEMENTS_IMPLEMENTED.md`

## Utility Scripts (`scripts/`)

All utility scripts are in the `scripts/` directory:

- **`demo.py`** - Verifies your setup without needing a ROM file
- **`verify_rom.py`** - Checks if your ROM file is valid
- **`analyze_log.py`** - Analyzes agent execution logs for debugging
- **`visual_demo.py`** - Visual demonstration without ROM

### Running Scripts

Scripts should be run from the project root:
```bash
python scripts/demo.py
python scripts/verify_rom.py path/to/rom.gb
python scripts/analyze_log.py --latest
```

## Test Suite (`tests/`)

Comprehensive test suite with 123 tests:

- **Unit Tests**: Core module functionality
  - `test_memory_reader.py` (20 tests)
  - `test_game_state.py` (20 tests)
  - `test_llm_optimizer.py` (11 tests)
  - `test_pokemon_agent.py` (10 tests)
  - `test_metrics.py` (19 tests)
- **Integration Tests**: `test_metrics_integration.py` (11 tests)
- **Performance Tests**: `test_performance.py` - Benchmarks and regression tests (7 tests)
- **End-to-End Tests**: `test_end_to_end.py` - Complete gameplay sequences (5 tests)
- **Stress Tests**: `test_stress.py` - Extended runs and resource limits (6 tests)
- **Edge Case Tests**: `test_edge_cases.py` - Error recovery and stuck detection (10 tests)

### Running Tests

```bash
# Run all tests
pytest

# Run specific categories
pytest -m performance    # Performance benchmarks
pytest -m e2e            # End-to-end tests
pytest -m stress         # Stress tests
pytest -m edge_case      # Edge case tests

# Skip slow tests
pytest -m "not slow"
```

See `tests/README.md` for detailed testing documentation.

## Logs (`logs/`)

Agent execution logs are automatically saved to the `logs/` directory. Each run creates a timestamped JSON file with:
- Run configuration
- Step-by-step action log
- Screen text extraction
- Success/failure status
- Performance metrics (step timing, cache statistics, LLM statistics)
- Screenshots saved when stuck patterns are detected

## ROM Files

ROM files should be placed in the project root directory. They are excluded from git via `.gitignore` for copyright reasons.

## Best Practices

1. **Run scripts from project root** - Scripts are designed to be run from the repository root
2. **Check documentation** - See `docs/` for detailed guides
3. **Use utility scripts** - Use `scripts/verify_rom.py` before running the agent
4. **Analyze logs** - Use `scripts/analyze_log.py` to debug agent behavior

