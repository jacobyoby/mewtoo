# Mewtwo - Setup Status

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
- `--sound`: Enable sound (optional)
- `--llm-provider`: Use `ollama` (local) or `claude` (requires API key)
- `--headless`: Run without display window

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

## Project Files

- `main.py` - Main entry point
- `llm_provider.py` - LLM integration (Ollama/Claude)
- `game_state.py` - Game state extraction & controls
- `pokemon_agent.py` - AI agent logic
- `agent_strategy.py` - Goal-oriented strategy system
- `config.py` - Configuration management
- `config.yaml` - Configuration file with profiles
- `scripts/demo.py` - Setup verification script

## Everything is Ready

Just add your Pokemon Red ROM file and you're ready to go.

