# Metrics and Analytics Guide

## Overview

Mewtwo now includes comprehensive metrics tracking to help you understand and optimize agent performance. Metrics are automatically collected during execution and displayed at the end of each run.

## Metrics Collected

### Performance Metrics

- **Step Timing**: Time taken for each agent step
  - Average, min, max step times
  - Recent rolling average (last 100 steps)
  - Total runtime

- **OCR Timing**: Time taken for OCR operations
  - Average OCR processing time
  - Total OCR calls
  - Recent performance trends

- **LLM Timing**: Time taken for LLM calls
  - Average latency per call
  - Recent average latency
  - Total LLM call time

### Cache Statistics

- **Hit Rate**: Percentage of cache hits vs misses
- **Hits/Misses**: Total number of cache hits and misses
- **Cache Size**: Current cache utilization (entries used / max size)
- **Evictions**: Number of cache entries evicted (LRU)

### LLM Statistics

- **Total Calls**: Number of LLM API calls made
- **Average Latency**: Average time per LLM call
- **Token Usage**: Total tokens generated (if available from provider)
- **Success Rate**: Percentage of successful LLM calls
- **Errors**: Number of failed LLM calls
- **Timeouts**: Number of timed-out LLM calls

## Viewing Metrics

### During Execution

Metrics are collected automatically during execution. No configuration needed!

### End of Run Summary

At the end of each run, a metrics summary is automatically displayed:

```
======================================================================
METRICS SUMMARY
======================================================================
Runtime: 14.45s

Performance:
  Total Steps: 500
  Avg Step Time: 20.89ms
  Recent Avg Step Time: 0.64ms
  OCR Calls: 0
  Avg OCR Time: 0.00ms

LLM Statistics:
  Total Calls: 42
  Avg Latency: 484.41ms
  Recent Avg Latency: 484.41ms
  Success Rate: 100.0%
  Errors: 0
  Timeouts: 0

Cache Statistics:
  Hits: 205
  Misses: 26
  Hit Rate: 88.7%
  Size: 26/100 (26.0%)
  Evictions: 0
======================================================================
```

### In Log Files

All metrics are automatically saved to JSON log files in the `logs/` directory. The metrics are stored in the `metrics` field:

```json
{
  "rom": "path/to/rom.gb",
  "steps": 500,
  "metrics": {
    "runtime": {
      "total_seconds": 14.45,
      "start_time": "2025-12-21T14:36:34",
      "current_time": "2025-12-21T14:36:48"
    },
    "performance": {
      "step_timing": {
        "total_steps": 500,
        "avg_time": 0.02089,
        "min_time": 0.0001,
        "max_time": 0.5,
        "recent_avg": 0.00064,
        "total_time": 10.445
      },
      "ocr_timing": {...},
      "llm_timing": {...}
    },
    "llm": {
      "total_calls": 42,
      "latency": {
        "avg": 0.48441,
        "recent_avg": 0.48441
      },
      "success_rate": 100.0
    },
    "cache": {
      "hits": 205,
      "misses": 26,
      "hit_rate": 88.7,
      "evictions": 0
    }
  }
}
```

## Interpreting Metrics

### Cache Hit Rate

- **High hit rate (>80%)**: Excellent! The cache is working well, reducing LLM calls significantly.
- **Medium hit rate (50-80%)**: Good caching, but room for improvement.
- **Low hit rate (<50%)**: Consider increasing cache size or improving cache key generation.

### LLM Call Count

Compare `total_calls` to `total_steps`:
- **Low ratio (<20%)**: Excellent! Cache is very effective.
- **Medium ratio (20-50%)**: Good caching performance.
- **High ratio (>50%)**: Consider optimizing cache strategy.

### Step Timing

- **Recent avg < overall avg**: Performance is improving over time (good sign!)
- **Recent avg > overall avg**: Performance may be degrading (investigate bottlenecks)
- **Large gap between min/max**: Inconsistent performance, may indicate bottlenecks

### LLM Latency

- **Low latency (<500ms)**: Fast LLM responses, good for real-time gameplay.
- **High latency (>1000ms)**: Consider using faster models or optimizing prompts.

## Configuration

Metrics are enabled by default. To disable (not recommended), you can modify `config.yaml`:

```yaml
logging:
  metrics_enabled: false  # Default: true
```

## Programmatic Access

You can access metrics programmatically:

```python
from metrics import MetricsCollector

# Metrics are automatically created and passed to components
# Access via agent.metrics or from log files

# Get all stats
stats = metrics.get_all_stats()

# Get summary string
summary = metrics.get_summary()
print(summary)
```

## Best Practices

1. **Monitor cache hit rate**: Aim for >80% hit rate for optimal performance
2. **Watch LLM call count**: Lower is better - indicates effective caching
3. **Check recent vs overall averages**: Recent trends show current performance
4. **Review errors/timeouts**: Investigate if success rate drops below 95%
5. **Compare runs**: Use metrics to compare performance across different configurations

## Troubleshooting

### High LLM Call Count

If LLM calls are too high:
- Increase cache size in `config.yaml`: `performance.cache_max_size: 150`
- Check if cache is being cleared unnecessarily
- Review cache key generation strategy

### Low Cache Hit Rate

If hit rate is low:
- Increase cache size
- Check if game states are too diverse (may be expected)
- Review cache eviction policy

### High Latency

If LLM latency is high:
- Use faster models (e.g., smaller Ollama models)
- Reduce `max_tokens` in config
- Check network latency (for cloud providers)
- Consider using local Ollama instead of cloud API

## Examples

### Analyzing a Run

```bash
# Run agent
python main.py --rom pokemon_red.gb --steps 500 --headless

# Check metrics in log file
python -c "
import json
with open('logs/pokemon_agent_*.json') as f:
    data = json.load(f)
    metrics = data['metrics']
    print(f\"Cache Hit Rate: {metrics['cache']['hit_rate']:.1f}%\")
    print(f\"LLM Calls: {metrics['llm']['total_calls']}\")
    print(f\"Avg Latency: {metrics['llm']['latency']['avg']*1000:.1f}ms\")
"
```

### Comparing Profiles

Run with different profiles and compare metrics:

```bash
# Aggressive profile
python main.py --rom pokemon_red.gb --steps 500 --profile aggressive --headless

# Conservative profile  
python main.py --rom pokemon_red.gb --steps 500 --profile conservative --headless

# Compare cache hit rates and LLM call counts in log files
```

