# Mewtwo

**Version 0.0.5.1**

A powerful AI agent that plays Pokemon Red using a Game Boy emulator (PyBoy) and a Large Language Model. Named after the legendary Pokemon Mewtwo, known for its intelligence and psychic abilities.

## Features

- Play Pokemon Red using PyBoy emulator
- AI agent powered by LLMs (Ollama for local, Claude API for cloud)
- Game state extraction via OCR and memory reading
- Goal-oriented strategy system with exploration/exploitation balance
- Action caching and optimization to reduce LLM calls
- Comprehensive configuration system (config.yaml)
- Action-based gameplay control

## Prerequisites

1. **Python 3.8+**
2. **Tesseract OCR** (for text extraction):
   - Windows: Download from [Tesseract GitHub](https://github.com/UB-Mannheim/tesseract/wiki)
   - macOS: `brew install tesseract`
   - Linux: `sudo apt-get install tesseract-ocr`
3. **Pokemon Red ROM** (.gb file) - You must provide your own legal copy
4. **Ollama** (for local LLM) - Download from [ollama.com](https://ollama.com)

## Installation

1. Clone or download this repository:
```bash
cd pokemon
```

2. Create a virtual environment:
```bash
python -m venv venv
```

3. Activate the virtual environment:
```bash
# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

4. Install dependencies:
```bash
pip install -r requirements.txt
```

5. Install and set up Ollama (for local inference):
```bash
# Download and install Ollama from https://ollama.com
# Then pull a model:
ollama pull llama3.2
```

6. (Optional) Set up Claude API:
```bash
# Create a .env file:
echo "ANTHROPIC_API_KEY=your_api_key_here" > .env
```

## Usage

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
2. **Game State Extraction**: Uses OCR to extract text from the screen
3. **LLM Agent**: Analyzes game state and decides on actions
4. **Action Execution**: Sends button presses to the emulator
5. **Loop**: Repeats the process for the specified number of steps

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

## Documentation

See the `docs/` directory for detailed guides:
- `EXTRACT_ROM_GUIDE.md` - How to extract ROM from cartridge
- `LOGGING_GUIDE.md` - Logging and analysis guide
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

## Version

Current version: **0.0.5.1**

See [CHANGELOG.md](CHANGELOG.md) for version history and [docs/VERSION_HISTORY.md](docs/VERSION_HISTORY.md) for detailed version information.

## Contributing

See [TODO.md](TODO.md) for planned improvements and contribution ideas.

## License

This project is for educational purposes. Ensure you have legal rights to use the Pokemon ROM file.

## Disclaimer

This project is not affiliated with Nintendo, Game Freak, or The Pokemon Company. Pokemon is a trademark of Nintendo. Use ROMs only if you own the original game.

