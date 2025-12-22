# Mewtwo

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Version](https://img.shields.io/badge/version-0.0.7-blue.svg)](VERSION)

A powerful AI agent that plays Pokemon Red using a Game Boy emulator (PyBoy) and a Large Language Model. Named after the legendary Pokemon Mewtwo, known for its intelligence and psychic abilities.

## Quick Start

Get up and running in 5 minutes:

```bash
# 1. Clone the repository
git clone https://github.com/your-username/mewtwo.git
cd mewtwo

# 2. Create virtual environment
python -m venv venv

# 3. Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Install Ollama (for local LLM)
# Download from https://ollama.com, then:
ollama pull llama3.2

# 6. Install Tesseract OCR
# Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki
# macOS: brew install tesseract
# Linux: sudo apt-get install tesseract-ocr

# 7. Run the agent (you need your own Pokemon Red ROM)
python main.py --rom path/to/pokemon_red.gb --steps 100 --display
```

**That's it!** The agent will start playing Pokemon Red. See [Quick Start Guide](#quick-start-guide) below for more details.

## Features

- Play Pokemon Red using PyBoy emulator
- AI agent powered by LLMs (Ollama for local, Claude API for cloud)
- Game state extraction via OCR and memory reading
- Goal-oriented strategy system with exploration/exploitation balance
- Action caching and optimization to reduce LLM calls
- **Performance metrics and analytics** - Track step timing, cache hit rates, and LLM statistics
- Comprehensive configuration system (config.yaml)
- Action-based gameplay control

## Quick Start Guide

### Prerequisites

Before you begin, ensure you have:

1. **Python 3.8+** - [Download Python](https://www.python.org/downloads/)
2. **Tesseract OCR** - Required for text extraction
   - **Windows**: Download from [Tesseract GitHub](https://github.com/UB-Mannheim/tesseract/wiki)
   - **macOS**: `brew install tesseract`
   - **Linux**: `sudo apt-get install tesseract-ocr`
3. **Pokemon Red ROM** (.gb file) - You must provide your own legal copy
4. **Ollama** (for local LLM) - [Download Ollama](https://ollama.com)

### Step-by-Step Installation

#### 1. Clone the Repository

```bash
git clone https://github.com/your-username/mewtwo.git
cd mewtwo
```

#### 2. Set Up Python Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

#### 3. Install Ollama

```bash
# Download and install Ollama from https://ollama.com
# Then pull a model:
ollama pull llama3.2
```

#### 4. Verify Installation

```bash
# Check if everything is set up correctly
python scripts/demo.py
```

#### 5. (Optional) Set Up Claude API

If you prefer using Claude API instead of Ollama:

```bash
# Create a .env file in the project root:
echo "ANTHROPIC_API_KEY=your_api_key_here" > .env
```

### First Run

```bash
# Run with display (recommended for first time)
python main.py --rom path/to/pokemon_red.gb --steps 100 --display --llm-provider ollama
```

**Note**: Replace `path/to/pokemon_red.gb` with the actual path to your Pokemon Red ROM file.

## Usage Examples

### Basic Usage (Local with Ollama)

```bash
python main.py --rom path/to/pokemon_red.gb --steps 100 --display
```

### With Sound

```bash
python main.py --rom path/to/pokemon_red.gb --steps 100 --display --sound
```

### Using Claude API

```bash
python main.py --rom path/to/pokemon_red.gb --steps 100 --llm-provider claude --display
```

### Headless Mode (No Display)

```bash
python main.py --rom path/to/pokemon_red.gb --steps 100 --headless
```

### Fast Mode (Maximum Speed)

```bash
python main.py --rom path/to/pokemon_red.gb --steps 100 --display --fast
```

**See [QUICKSTART.md](QUICKSTART.md) for a detailed quick start guide.**

## Command Line Arguments

- `--rom`: Path to Pokemon Red ROM file (required)
- `--steps`: Number of steps to run (default: 100)
- `--llm-provider`: LLM provider to use - `ollama` or `claude` (default: ollama)
- `--model`: Model name (optional, uses defaults if not specified)
- `--profile`: Strategy profile - `aggressive`, `conservative`, or `balanced` (default: balanced)
- `--display`: Enable display window
- `--sound`: Enable sound
- `--headless`: Run in headless mode (no display)

## Project Structure

```
pokemon/
├── main.py                 # Main entry point
├── pokemon_agent.py        # AI agent logic
├── game_state.py           # Game state extraction & controls
├── llm_provider.py         # LLM integration (Ollama/Claude)
├── llm_optimizer.py        # LLM prompt optimization
├── config.py               # Configuration helpers
├── requirements.txt        # Python dependencies
├── docs/                   # Documentation
│   ├── EXTRACT_ROM_GUIDE.md
│   ├── LLM_OPTIMIZATION_GUIDE.md
│   ├── LOGGING_GUIDE.md
│   ├── METRICS_GUIDE.md    # Metrics and analytics guide
│   ├── PERFORMANCE_GUIDE.md
│   ├── SETUP_STATUS.md
│   └── ...
├── scripts/                # Utility scripts
│   ├── demo.py            # Setup verification demo
│   ├── verify_rom.py      # ROM verification script
│   ├── visual_demo.py     # Visual demonstration
│   └── analyze_log.py     # Log analysis tool
└── logs/                   # Agent execution logs (auto-generated)
```

## How It Works

1. **PyBoy Emulator**: Loads and runs the Pokemon Red ROM
2. **Game State Extraction**: Uses OCR and memory reading to extract game state
3. **LLM Agent**: Analyzes game state and decides on actions
4. **Action Execution**: Sends button presses to the emulator
5. **Metrics Tracking**: Collects performance metrics throughout execution
6. **Loop**: Repeats the process for the specified number of steps

## Available Actions

The agent can use these actions:
- `UP`, `DOWN`, `LEFT`, `RIGHT`: Movement
- `A`: Confirm/interact
- `B`: Cancel/go back
- `START`: Open menu
- `SELECT`: Select button
- `WAIT N`: Wait N frames

## Utility Scripts

### Verify ROM
Check if your ROM file is valid:
```bash
python scripts/verify_rom.py path/to/pokemon_red.gb
```

### Check Setup
Verify your installation:
```bash
python scripts/demo.py
```

### Analyze Logs
Analyze agent execution logs:
```bash
python scripts/analyze_log.py --latest
python scripts/analyze_log.py logs/pokemon_agent_YYYYMMDD_HHMMSS.json
```

### Validate Early Game Sequence
Test agent's ability to complete early game sequence (v1.0.0 requirement):
```bash
# Run validation tests (10 runs by default)
python scripts/validate_early_game.py --rom "path/to/pokemon_red.gb" --runs 10

# Analyze existing log file
python scripts/validate_early_game.py --log-file logs/pokemon_agent_YYYYMMDD_HHMMSS.json
```

See `docs/EARLY_GAME_VALIDATION.md` for detailed validation guide.

## Documentation

See the `docs/` directory for detailed guides:
- `EXTRACT_ROM_GUIDE.md` - How to extract ROM from cartridge
- `LOGGING_GUIDE.md` - Logging and analysis guide
- `METRICS_GUIDE.md` - Metrics and analytics guide
- `PERFORMANCE_GUIDE.md` - Performance optimization tips
- `TROUBLESHOOTING.md` - Common issues and solutions
- `setup_ollama.md` - Ollama setup instructions

## Troubleshooting

### OCR Not Working
- Ensure Tesseract is installed and in your PATH
- On Windows, you may need to set the path: `pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'`

### Ollama Connection Issues
- Ensure Ollama is running: `ollama serve`
- Verify model is installed: `ollama list`
- See `docs/setup_ollama.md` for detailed setup instructions

### ROM Issues
- Ensure you have a valid Pokemon Red ROM (.gb file)
- ROM must be a legal copy you own
- Use `scripts/verify_rom.py` to check your ROM file

## Configuration

Mewtwo uses a YAML configuration file (`config.yaml`) for easy tuning of agent behavior:

- **Agent settings**: Action history, caching, goal checking intervals
- **Strategy settings**: Exploration rate, goal priorities
- **LLM settings**: Token limits, default models
- **Performance settings**: Cache sizes, frame rates
- **OCR/Memory settings**: Check intervals, enable/disable features

Command-line arguments override config file settings. See `config.yaml` for all available options.

### Strategy Profiles

Mewtwo includes three pre-configured strategy profiles:

- **`balanced`** (default): 30% exploration, 70% goal-focused. Standard settings for general gameplay.
- **`aggressive`**: 10% exploration, 90% goal-focused. Fast progress, less exploration, larger cache for speed.
- **`conservative`**: 50% exploration, 50% goal-focused. More thorough exploration, smaller cache, more thoughtful decisions.

Select a profile via command line:
```bash
python main.py --rom path/to/pokemon_red.gb --profile aggressive --steps 200
```

Or set `active_profile` in `config.yaml`. Profiles can be customized by editing the `profiles` section in `config.yaml`.

## Testing

Mewtwo includes a comprehensive test suite with 123 tests covering:

- **Unit Tests**: Core module functionality (95 tests)
- **Integration Tests**: Component integration (11 tests)
- **Performance Tests**: Benchmarks and regression tests (7 tests)
- **End-to-End Tests**: Complete gameplay sequences (5 tests)
- **Stress Tests**: Extended runs and resource limits (6 tests)
- **Edge Case Tests**: Error recovery and stuck detection (10 tests)

Run tests:
```bash
# Run all tests
pytest

# Run specific test categories
pytest -m performance    # Performance benchmarks
pytest -m e2e            # End-to-end tests
pytest -m stress         # Stress tests
pytest -m edge_case      # Edge case tests

# Skip slow tests
pytest -m "not slow"
```

See [tests/README.md](tests/README.md) for detailed testing documentation.

## Version

Current version: **0.0.7**

See [CHANGELOG.md](CHANGELOG.md) for version history and [docs/VERSION_HISTORY.md](docs/VERSION_HISTORY.md) for detailed version information.

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

See [TODO.md](TODO.md) for planned improvements and contribution ideas.

**Quick Links:**
- [Quick Start Guide](QUICKSTART.md) - Get started in 5 minutes
- [Contributing Guide](CONTRIBUTING.md) - How to contribute
- [Documentation](docs/) - Comprehensive guides
- [Changelog](CHANGELOG.md) - Version history

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Legal Disclaimer

**Important:** 
- This project is for **educational purposes only**
- You must own a legal copy of Pokemon Red to use ROM files with this software
- ROM files are **not included** in this repository and must be provided separately
- This project is **not affiliated** with Nintendo, Game Freak, or The Pokemon Company
- Pokemon is a trademark of Nintendo

## Support

- [Quick Start Guide](QUICKSTART.md) - Get started quickly
- [Documentation](docs/) - Comprehensive guides
- [Report a Bug](.github/ISSUE_TEMPLATE/bug_report.md) - Found a bug?
- [Request a Feature](.github/ISSUE_TEMPLATE/feature_request.md) - Have an idea?
- [Ask a Question](.github/ISSUE_TEMPLATE/question.md) - Need help? Use ROMs only if you own the original game.

