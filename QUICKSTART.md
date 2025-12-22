# Quick Start Guide

Get Mewtwo up and running in minutes!

## Prerequisites Checklist

- [ ] Python 3.8+ installed
- [ ] Tesseract OCR installed
- [ ] Ollama installed and running
- [ ] Pokemon Red ROM file (.gb) ready
- [ ] Git installed (for cloning)

## Installation (5 minutes)

### 1. Clone Repository

```bash
git clone https://github.com/your-username/mewtwo.git
cd mewtwo
```

### 2. Create Virtual Environment

```bash
python -m venv venv
```

**Activate it:**
- **Windows**: `venv\Scripts\activate`
- **macOS/Linux**: `source venv/bin/activate`

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Install Ollama

1. Download from [ollama.com](https://ollama.com)
2. Install and start Ollama
3. Pull a model:
   ```bash
   ollama pull llama3.2
   ```

### 5. Install Tesseract OCR

- **Windows**: Download installer from [Tesseract GitHub](https://github.com/UB-Mannheim/tesseract/wiki)
- **macOS**: `brew install tesseract`
- **Linux**: `sudo apt-get install tesseract-ocr`

### 6. Verify Setup

```bash
python scripts/demo.py
```

If you see "All components ready!", you're good to go!

## First Run

### Basic Usage

```bash
python main.py --rom path/to/pokemon_red.gb --steps 100 --display
```

### Common Options

```bash
# With sound
python main.py --rom pokemon_red.gb --steps 100 --display --sound

# Headless mode (no window)
python main.py --rom pokemon_red.gb --steps 100 --headless

# Using Claude API instead of Ollama
python main.py --rom pokemon_red.gb --steps 100 --display --llm-provider claude

# Fast mode (maximum speed)
python main.py --rom pokemon_red.gb --steps 100 --display --fast
```

## Troubleshooting

### "Tesseract not found"
- Ensure Tesseract is installed and in your PATH
- Windows: May need to set path manually in code or environment variables

### "Ollama connection failed"
- Ensure Ollama is running: `ollama serve`
- Verify model is installed: `ollama list`
- Check if Ollama is accessible: `curl http://localhost:11434`

### "ROM file not found"
- Ensure you have a valid Pokemon Red ROM (.gb file)
- Use `python scripts/verify_rom.py path/to/rom.gb` to verify

### "Import errors"
- Ensure virtual environment is activated
- Reinstall dependencies: `pip install -r requirements.txt`

## Next Steps

- Read the [README.md](README.md) for detailed documentation
- Check [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) for common issues
- Explore [docs/](docs/) for guides on metrics, performance, and more
- Run validation tests: `python scripts/validate_early_game.py --rom path/to/rom.gb`

## Need Help?

- Check [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)
- Open an issue on GitHub
- Review [docs/SETUP_STATUS.md](docs/SETUP_STATUS.md) for detailed setup info

## Important Notes

- **ROM Files**: You must provide your own legal copy of Pokemon Red
- **Legal**: This project is for educational purposes only
- **Not Affiliated**: Not affiliated with Nintendo, Game Freak, or The Pokemon Company

