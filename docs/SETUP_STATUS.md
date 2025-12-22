# Mewtwo - Setup Status

**Version**: 0.0.7  
**Last Updated**: 2025-12-21

## All Components Ready

### 1. Python Dependencies
- PyBoy (Game Boy emulator)
- OpenCV (Image processing)
- Pytesseract (OCR wrapper)
- Ollama (Local LLM client)
- Anthropic (Claude API client - optional)

### 2. Ollama Setup
- Ollama v0.13.5 installed
- llama3.2:latest model downloaded (2.0 GB)
- Connection tested and working

### 3. Tesseract OCR
- Tesseract v5.4.0 installed
- Auto-detected at: `C:\Program Files\Tesseract-OCR\tesseract.exe`
- Python integration working

## Project Structure

### Core Files
- `main.py` - Main entry point (supports configuration profiles and metrics)
- `llm_provider.py` - LLM integration (Ollama/Claude) with metrics tracking
- `game_state.py` - Game state extraction & controls with OCR timing and blank screen detection
- `pokemon_agent.py` - AI agent logic (with profile support, metrics, and character creation protection)
- `metrics.py` - Performance metrics and analytics tracking (v0.0.7)
- `config.py` - Configuration helpers (profile management)
- `config.yaml` - Configuration file with profiles
- `agent_strategy.py` - Goal-oriented strategy system
- `memory_reader.py` - Direct memory access for accurate game state
- `llm_optimizer.py` - LLM prompt optimization and caching
- `ocr_enhancer.py` - Enhanced OCR with region detection

### Documentation
- `README.md` - Main documentation
- `CHANGELOG.md` - Version changelog
- `docs/` - Comprehensive documentation directory
  - `SETUP_STATUS.md` - This file
  - `TROUBLESHOOTING.md` - Troubleshooting guide
  - `METRICS_GUIDE.md` - Metrics and analytics guide
  - `PERFORMANCE_GUIDE.md` - Performance optimization guide
  - `EARLY_GAME_VALIDATION.md` - Early game validation documentation
  - `VERSION_HISTORY.md` - Detailed version history
  - And more...

### Utility Scripts
- `scripts/validate_early_game.py` - Early game sequence validation
- `scripts/analyze_log.py` - Log analysis tool
- `scripts/verify_rom.py` - ROM verification script
- `scripts/demo.py` - Setup verification demo

## ROM File Status

ROM Found and Verified
- File: `Pokemon - Red Version (USA, Europe) (SGB Enhanced).gb`
- Size: 1.00 MB
- Title: POKEMON RED
- PyBoy Test: Loads successfully
- Status: READY TO USE

## Ready to Play

### What You Need:
- **Pokemon Red ROM file** (.gb format) - You must provide your own legal copy

### How to Run:

```powershell
python main.py --rom path/to/pokemon_red.gb --steps 100 --display --llm-provider ollama
```

### Options:
- `--rom`: Path to your Pokemon Red ROM (required)
- `--steps`: Number of steps to run (default: 100)
- `--profile`: Strategy profile - `aggressive`, `conservative`, or `balanced` (default: balanced)
- `--display`: Show the game window
- `--headless`: Run without display window
- `--sound`: Enable sound (optional)
- `--llm-provider`: Use `ollama` (local) or `claude` (requires API key)
- `--ocr-interval`: OCR frequency (default: 20 frames)
- `--fast`: Fast mode (disables OCR, 1 frame per step)

### Example Commands:

**Basic run with display:**
```powershell
python main.py --rom pokemon_red.gb --steps 50 --display
```

**With sound:**
```powershell
python main.py --rom pokemon_red.gb --steps 100 --display --sound
```

**Headless mode (no window):**
```powershell
python main.py --rom pokemon_red.gb --steps 200 --headless
```

**With profile:**
```powershell
python main.py --rom pokemon_red.gb --steps 100 --display --profile aggressive
```

**Validation testing:**
```powershell
python scripts/validate_early_game.py --rom "Pokemon - Red Version (USA, Europe) (SGB Enhanced).gb" --runs 10 --max-steps 500
```

## New in v0.0.7

- **Blank Screen Detection**: Automatic detection and handling of blank screens during gameplay
- **Character Creation Protection**: Prevents agent from backing out during character creation
- **Enhanced State Detection**: State detection validates screen content before reporting state
- **Screenshot Saving**: Automatic screenshots when stuck (non-blank screens only)
- **Improved Blank Screen Handling**: Aggressive A-press strategy for transitions

## Everything is Ready

Just add your Pokemon Red ROM file and you're ready to go.
