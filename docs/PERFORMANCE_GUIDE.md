# Performance Optimization Guide

## Monitoring Performance

**New in v0.0.6**: Comprehensive metrics tracking is now available! See `docs/METRICS_GUIDE.md` for detailed information.

## Performance Fixes Applied (v0.0.5+)

### Sound Optimization
- Sound disabled by default (`sound_emulated=False`, `sound=False`)
- Only enabled when `--sound` flag is used
- Reduces CPU usage significantly (~10-20% improvement)

### Frame Rate Optimization
- Reduced frames per step from 5 to 3 (default)
- Faster decision-making cycle
- Still smooth enough for gameplay
- 40% faster than original

### OCR Optimization
- Increased default OCR interval from 10 to 20 frames
- OCR runs half as often (much faster)
- Minimum OCR interval enforced (20 frames)
- Better balance between speed and information
- 50% reduction in OCR overhead

Metrics help you:
- Identify performance bottlenecks
- Optimize cache settings
- Monitor LLM call efficiency
- Track performance trends over time

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

### 2. Action Caching
- Actions are cached based on game state
- Reduces LLM calls significantly (typically 80-90% cache hit rate)
- **Metrics**: Cache hit rate is tracked - aim for >80% hit rate
- LRU eviction prevents cache from growing too large

### 3. Multiple Frames Per Step
- Game now runs 3 frames per agent decision (default, configurable)
- Makes gameplay smoother and more natural
- Can be reduced to 1 frame with `--fast` mode
- **Metrics**: Step timing is tracked - monitor average step time

### 4. Fast Mode
- Disables OCR completely
- Reduces frames per step to 1
- Much faster but agent can't see screen text
- **Metrics**: Compare metrics between fast and normal mode to see impact

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

## Using Metrics to Optimize

After running the agent, check the metrics summary:

```
Cache Statistics:
  Hit Rate: 88.7%  (Aim for >80%)
  Size: 26/100 (26.0%)

LLM Statistics:
  Total Calls: 42  (Lower is better, out of 500 steps)
  Avg Latency: 484.41ms  (Monitor for performance issues)
```

**Optimization Tips**:
- **Low cache hit rate (<50%)**: Increase `cache_max_size` in config.yaml
- **High LLM call count**: Review cache key generation or increase cache size
- **High latency**: Use faster models or reduce `max_tokens`
- **Slow step times**: Check OCR timing - consider increasing `ocr_interval`

See `docs/METRICS_GUIDE.md` for detailed metrics interpretation.

## Tips for Best Performance

1. **Use `--fast` mode** if you just want to see the agent play quickly
2. **Increase `--ocr-interval`** (e.g., 30-50) for better speed while keeping some info
3. **Disable display** (`--headless`) if you don't need to see the game window
4. **Use smaller models** in Ollama for faster LLM responses (e.g., `llama3.2:1b`)
5. **Monitor metrics** to identify bottlenecks and optimize cache settings

## Expected Performance

- **Fast mode**: ~10-20 steps/second
- **Default mode**: ~3-8 steps/second (improved from v0.0.5)
- **With OCR every frame**: ~0.5-1 steps/second (very slow)
- **With sound**: ~2-6 steps/second (slightly slower)

The main bottleneck is still the LLM calls, but OCR caching and optimizations help significantly!

## Performance Comparison

| Setting | Before (v0.0.4) | After (v0.0.7) | Improvement |
|---------|------------------|----------------|-------------|
| Frames per step | 5 | 3 | 40% faster |
| OCR interval | 10 | 20 | 50% less OCR |
| Sound | On (default) | Off (default) | ~10-20% faster |
| Overall speed | ~1-2 steps/sec | ~3-8 steps/sec | 3-4x faster |

