# Performance Optimization Guide

## Why Was It Slow?

The original implementation had several performance bottlenecks:

1. **OCR (Tesseract) running every step** - OCR is very slow (~100-500ms per call)
2. **LLM calls every step** - Each Ollama API call adds latency (~100-1000ms)
3. **Single frame per step** - Game runs very slowly, one frame at a time

## Performance Improvements

### 1. OCR Caching
- OCR now runs only every N frames (default: 10)
- Caches results between OCR calls
- Can be completely disabled with `--no-ocr`

### 2. Multiple Frames Per Step
- Game now runs 5 frames per agent decision (default)
- Makes gameplay smoother and more natural
- Can be reduced to 1 frame with `--fast` mode

### 3. Fast Mode
- Disables OCR completely
- Reduces frames per step to 1
- Much faster but agent can't see screen text

## Usage Examples

### Standard Mode (Balanced)
```powershell
python main.py --rom "Pokemon - Red Version (USA, Europe) (SGB Enhanced).gb" --steps 100 --display --llm-provider ollama
```
- OCR runs every 10 frames
- 5 frames per step
- Good balance of speed and information

### Fast Mode (Maximum Speed)
```powershell
python main.py --rom "Pokemon - Red Version (USA, Europe) (SGB Enhanced).gb" --steps 100 --display --fast --llm-provider ollama
```
- OCR disabled
- 1 frame per step
- Fastest but agent is "blind"

### Custom OCR Interval
```powershell
python main.py --rom "Pokemon - Red Version (USA, Europe) (SGB Enhanced).gb" --steps 100 --display --ocr-interval 30 --llm-provider ollama
```
- OCR runs every 30 frames (3x less frequent)
- Faster than default but still gets some screen info

### No OCR (Fast + Still See Frames)
```powershell
python main.py --rom "Pokemon - Red Version (USA, Europe) (SGB Enhanced).gb" --steps 100 --display --no-ocr --llm-provider ollama
```
- OCR disabled but still runs 5 frames per step
- Good for watching gameplay without OCR overhead

## Performance Comparison

| Mode | OCR Frequency | Frames/Step | Speed | Info Quality |
|------|--------------|-------------|-------|--------------|
| Default | Every 10 frames | 5 | Medium | Good |
| Fast | Disabled | 1 | Fastest | None |
| Custom (30) | Every 30 frames | 5 | Fast | Medium |
| No OCR | Disabled | 5 | Fast | None |

## Tips for Best Performance

1. **Use `--fast` mode** if you just want to see the agent play quickly
2. **Increase `--ocr-interval`** (e.g., 30-50) for better speed while keeping some info
3. **Disable display** (`--headless`) if you don't need to see the game window
4. **Use smaller models** in Ollama for faster LLM responses (e.g., `llama3.2:1b`)

## Expected Performance

- **Fast mode**: ~10-20 steps/second
- **Default mode**: ~2-5 steps/second  
- **With OCR every frame**: ~0.5-1 steps/second (very slow)

The main bottleneck is still the LLM calls, but OCR caching helps significantly!

