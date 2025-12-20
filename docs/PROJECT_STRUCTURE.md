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
│   ├── EXTRACT_ROM_GUIDE.md      # How to extract ROM from cartridge
│   ├── IMPROVEMENTS.md           # Improvement roadmap
│   ├── IMPROVEMENTS_IMPLEMENTED.md # Implemented improvements summary
│   ├── LLM_OPTIMIZATION_GUIDE.md # LLM optimization tips
│   ├── LOGGING_GUIDE.md          # Logging and analysis guide
│   ├── PERFORMANCE_GUIDE.md      # Performance optimization guide
│   ├── PERFORMANCE_FIXES.md      # Performance fixes documentation
│   ├── PROJECT_STRUCTURE.md      # This file
│   ├── REPO_STATUS.md            # Repository status and quick reference
│   ├── SETUP_STATUS.md           # Setup verification status
│   ├── setup_ollama.md           # Ollama installation guide
│   ├── TROUBLESHOOTING.md        # Common issues and solutions
│   └── VERSION_HISTORY.md        # Version history and details
│
├── scripts/                # Utility scripts directory
│   ├── analyze_log.py     # Analyze agent execution logs
│   ├── demo.py            # Setup verification demo
│   ├── verify_rom.py      # ROM file verification script
│   └── visual_demo.py     # Visual demonstration (no ROM needed)
│
├── logs/                   # Agent execution logs (auto-generated)
│   └── pokemon_agent_*.json
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
- **`config.py`** - Configuration management with profile support and Tesseract OCR path setup.
- **`config.yaml`** - YAML configuration file with agent settings and strategy profiles.

## Documentation (`docs/`)

All documentation files are organized in the `docs/` directory:

- **Setup Guides**: `setup_ollama.md`, `EXTRACT_ROM_GUIDE.md`
- **Usage Guides**: `LOGGING_GUIDE.md`, `PERFORMANCE_GUIDE.md`
- **Reference**: `REPO_STATUS.md`, `SETUP_STATUS.md`, `TROUBLESHOOTING.md`

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

## Logs (`logs/`)

Agent execution logs are automatically saved to the `logs/` directory. Each run creates a timestamped JSON file with:
- Run configuration
- Step-by-step action log
- Screen text extraction
- Success/failure status

## ROM Files

ROM files should be placed in the project root directory. They are excluded from git via `.gitignore` for copyright reasons.

## Best Practices

1. **Run scripts from project root** - Scripts are designed to be run from the repository root
2. **Check documentation** - See `docs/` for detailed guides
3. **Use utility scripts** - Use `scripts/verify_rom.py` before running the agent
4. **Analyze logs** - Use `scripts/analyze_log.py` to debug agent behavior

