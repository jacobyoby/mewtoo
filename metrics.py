"""Metrics tracking for performance, cache, and LLM statistics.

Version: 0.0.7
"""
import time
from typing import Dict, List, Optional
from collections import deque
from datetime import datetime


class PerformanceMetrics:
    """Track performance metrics for the agent."""
    
    def __init__(self):
        """Initialize performance metrics tracker."""
        self.step_times: List[float] = []
        self.ocr_times: List[float] = []
        self.llm_times: List[float] = []
        self.total_steps = 0
        self.total_ocr_calls = 0
        self.total_llm_calls = 0
        
        # Keep recent timings for rolling averages
        self.recent_step_times = deque(maxlen=100)
        self.recent_ocr_times = deque(maxlen=100)
        self.recent_llm_times = deque(maxlen=100)
    
    def record_step_time(self, duration: float):
        """Record time taken for a step.
        
        Args:
            duration: Time in seconds
        """
        self.step_times.append(duration)
        self.recent_step_times.append(duration)
        self.total_steps += 1
    
    def record_ocr_time(self, duration: float):
        """Record time taken for OCR operation.
        
        Args:
            duration: Time in seconds
        """
        self.ocr_times.append(duration)
        self.recent_ocr_times.append(duration)
        self.total_ocr_calls += 1
    
    def record_llm_time(self, duration: float):
        """Record time taken for LLM call.
        
        Args:
            duration: Time in seconds
        """
        self.llm_times.append(duration)
        self.recent_llm_times.append(duration)
        self.total_llm_calls += 1
    
    def get_stats(self) -> Dict:
        """Get performance statistics.
        
        Returns:
            Dictionary with performance metrics
        """
        def safe_avg(values: List[float]) -> float:
            """Calculate average safely."""
            return sum(values) / len(values) if values else 0.0
        
        def safe_min(values: List[float]) -> float:
            """Calculate minimum safely."""
            return min(values) if values else 0.0
        
        def safe_max(values: List[float]) -> float:
            """Calculate maximum safely."""
            return max(values) if values else 0.0
        
        return {
            "step_timing": {
                "total_steps": self.total_steps,
                "avg_time": safe_avg(self.step_times),
                "min_time": safe_min(self.step_times),
                "max_time": safe_max(self.step_times),
                "recent_avg": safe_avg(list(self.recent_step_times)),
                "total_time": sum(self.step_times)
            },
            "ocr_timing": {
                "total_calls": self.total_ocr_calls,
                "avg_time": safe_avg(self.ocr_times),
                "min_time": safe_min(self.ocr_times),
                "max_time": safe_max(self.ocr_times),
                "recent_avg": safe_avg(list(self.recent_ocr_times)),
                "total_time": sum(self.ocr_times)
            },
            "llm_timing": {
                "total_calls": self.total_llm_calls,
                "avg_time": safe_avg(self.llm_times),
                "min_time": safe_min(self.llm_times),
                "max_time": safe_max(self.llm_times),
                "recent_avg": safe_avg(list(self.recent_llm_times)),
                "total_time": sum(self.llm_times)
            }
        }


class LLMMetrics:
    """Track LLM call statistics."""
    
    def __init__(self):
        """Initialize LLM metrics tracker."""
        self.call_count = 0
        self.total_tokens = 0
        self.total_latency = 0.0
        self.latencies: List[float] = []
        self.errors = 0
        self.timeouts = 0
        
        # Keep recent data for rolling averages
        self.recent_latencies = deque(maxlen=100)
        self.recent_tokens = deque(maxlen=100)
    
    def record_call(self, latency: float, tokens: Optional[int] = None, error: bool = False, timeout: bool = False):
        """Record an LLM call.
        
        Args:
            latency: Call latency in seconds
            tokens: Number of tokens generated (if available)
            error: Whether the call resulted in an error
            timeout: Whether the call timed out
        """
        self.call_count += 1
        self.total_latency += latency
        self.latencies.append(latency)
        self.recent_latencies.append(latency)
        
        if tokens is not None:
            self.total_tokens += tokens
            self.recent_tokens.append(tokens)
        
        if error:
            self.errors += 1
        
        if timeout:
            self.timeouts += 1
    
    def get_stats(self) -> Dict:
        """Get LLM call statistics.
        
        Returns:
            Dictionary with LLM metrics
        """
        def safe_avg(values: List[float]) -> float:
            """Calculate average safely."""
            return sum(values) / len(values) if values else 0.0
        
        avg_latency = safe_avg(self.latencies)
        recent_avg_latency = safe_avg(list(self.recent_latencies))
        avg_tokens = safe_avg(list(self.recent_tokens)) if self.recent_tokens else None
        
        return {
            "total_calls": self.call_count,
            "total_tokens": self.total_tokens if self.total_tokens > 0 else None,
            "avg_tokens_per_call": avg_tokens,
            "latency": {
                "total": self.total_latency,
                "avg": avg_latency,
                "recent_avg": recent_avg_latency,
                "min": min(self.latencies) if self.latencies else 0.0,
                "max": max(self.latencies) if self.latencies else 0.0
            },
            "errors": self.errors,
            "timeouts": self.timeouts,
            "success_rate": ((self.call_count - self.errors - self.timeouts) / self.call_count * 100) if self.call_count > 0 else 100.0
        }


class CacheMetrics:
    """Track cache statistics."""
    
    def __init__(self):
        """Initialize cache metrics tracker."""
        self.hits = 0
        self.misses = 0
        self.evictions = 0
        self.size = 0
        self.max_size = 0
    
    def record_hit(self):
        """Record a cache hit."""
        self.hits += 1
    
    def record_miss(self):
        """Record a cache miss."""
        self.misses += 1
    
    def record_eviction(self):
        """Record a cache eviction."""
        self.evictions += 1
    
    def update_size(self, current_size: int, max_size: int):
        """Update cache size information.
        
        Args:
            current_size: Current number of cached entries
            max_size: Maximum cache size
        """
        self.size = current_size
        self.max_size = max_size
    
    def get_stats(self) -> Dict:
        """Get cache statistics.
        
        Returns:
            Dictionary with cache metrics
        """
        total_requests = self.hits + self.misses
        hit_rate = (self.hits / total_requests * 100) if total_requests > 0 else 0.0
        
        return {
            "hits": self.hits,
            "misses": self.misses,
            "total_requests": total_requests,
            "hit_rate": hit_rate,
            "evictions": self.evictions,
            "size": self.size,
            "max_size": self.max_size,
            "utilization": (self.size / self.max_size * 100) if self.max_size > 0 else 0.0
        }


class MetricsCollector:
    """Main metrics collector that aggregates all metrics."""
    
    def __init__(self):
        """Initialize metrics collector."""
        self.performance = PerformanceMetrics()
        self.llm = LLMMetrics()
        self.cache = CacheMetrics()
        self.start_time = time.time()
    
    def get_all_stats(self) -> Dict:
        """Get all collected metrics.
        
        Returns:
            Dictionary with all metrics
        """
        elapsed_time = time.time() - self.start_time
        
        return {
            "runtime": {
                "total_seconds": elapsed_time,
                "start_time": datetime.fromtimestamp(self.start_time).isoformat(),
                "current_time": datetime.now().isoformat()
            },
            "performance": self.performance.get_stats(),
            "llm": self.llm.get_stats(),
            "cache": self.cache.get_stats()
        }
    
    def get_summary(self) -> str:
        """Get a human-readable summary of metrics.
        
        Returns:
            Formatted string with metrics summary
        """
        stats = self.get_all_stats()
        perf = stats["performance"]
        llm = stats["llm"]
        cache = stats["cache"]
        
        lines = [
            "=" * 70,
            "METRICS SUMMARY",
            "=" * 70,
            f"Runtime: {stats['runtime']['total_seconds']:.2f}s",
            "",
            "Performance:",
            f"  Total Steps: {perf['step_timing']['total_steps']}",
            f"  Avg Step Time: {perf['step_timing']['avg_time']*1000:.2f}ms",
            f"  Recent Avg Step Time: {perf['step_timing']['recent_avg']*1000:.2f}ms",
            f"  OCR Calls: {perf['ocr_timing']['total_calls']}",
            f"  Avg OCR Time: {perf['ocr_timing']['avg_time']*1000:.2f}ms",
            "",
            "LLM Statistics:",
            f"  Total Calls: {llm['total_calls']}",
            f"  Avg Latency: {llm['latency']['avg']*1000:.2f}ms",
            f"  Recent Avg Latency: {llm['latency']['recent_avg']*1000:.2f}ms",
            f"  Success Rate: {llm['success_rate']:.1f}%",
            f"  Errors: {llm['errors']}",
            f"  Timeouts: {llm['timeouts']}",
        ]
        
        if llm['total_tokens']:
            lines.append(f"  Total Tokens: {llm['total_tokens']}")
            if llm['avg_tokens_per_call']:
                lines.append(f"  Avg Tokens/Call: {llm['avg_tokens_per_call']:.1f}")
        
        lines.extend([
            "",
            "Cache Statistics:",
            f"  Hits: {cache['hits']}",
            f"  Misses: {cache['misses']}",
            f"  Hit Rate: {cache['hit_rate']:.1f}%",
            f"  Size: {cache['size']}/{cache['max_size']} ({cache['utilization']:.1f}%)",
            f"  Evictions: {cache['evictions']}",
            "=" * 70
        ])
        
        return "\n".join(lines)

