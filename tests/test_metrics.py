"""Tests for metrics module."""

import pytest

from metrics import CacheMetrics, LLMMetrics, MetricsCollector, PerformanceMetrics


class TestPerformanceMetrics:
    """Test PerformanceMetrics class."""
    
    def test_init(self):
        """Test PerformanceMetrics initialization."""
        metrics = PerformanceMetrics()
        assert len(metrics.step_times) == 0
        assert len(metrics.ocr_times) == 0
        assert len(metrics.llm_times) == 0
        assert metrics.total_steps == 0
        assert metrics.total_ocr_calls == 0
        assert metrics.total_llm_calls == 0
    
    def test_record_step_time(self):
        """Test recording step time."""
        metrics = PerformanceMetrics()
        metrics.record_step_time(0.1)
        assert len(metrics.step_times) == 1
        assert metrics.step_times[0] == 0.1
        assert metrics.total_steps == 1
    
    def test_record_ocr_time(self):
        """Test recording OCR time."""
        metrics = PerformanceMetrics()
        metrics.record_ocr_time(0.05)
        assert len(metrics.ocr_times) == 1
        assert metrics.ocr_times[0] == 0.05
        assert metrics.total_ocr_calls == 1
    
    def test_record_llm_time(self):
        """Test recording LLM time."""
        metrics = PerformanceMetrics()
        metrics.record_llm_time(0.2)
        assert len(metrics.llm_times) == 1
        assert metrics.llm_times[0] == 0.2
        assert metrics.total_llm_calls == 1
    
    def test_get_stats(self):
        """Test getting statistics."""
        metrics = PerformanceMetrics()
        metrics.record_step_time(0.1)
        metrics.record_step_time(0.2)
        metrics.record_ocr_time(0.05)
        metrics.record_llm_time(0.15)
        
        stats = metrics.get_stats()
        assert stats['step_timing']['total_steps'] == 2
        assert stats['step_timing']['avg_time'] == pytest.approx(0.15, rel=0.01)
        assert stats['step_timing']['min_time'] == 0.1
        assert stats['step_timing']['max_time'] == 0.2
        assert stats['ocr_timing']['total_calls'] == 1
        assert stats['llm_timing']['total_calls'] == 1


class TestLLMMetrics:
    """Test LLMMetrics class."""
    
    def test_init(self):
        """Test LLMMetrics initialization."""
        metrics = LLMMetrics()
        assert metrics.call_count == 0
        assert metrics.total_tokens == 0
        assert metrics.total_latency == 0.0
        assert metrics.errors == 0
        assert metrics.timeouts == 0
    
    def test_record_call(self):
        """Test recording LLM call."""
        metrics = LLMMetrics()
        metrics.record_call(0.1, tokens=10)
        assert metrics.call_count == 1
        assert metrics.total_tokens == 10
        assert metrics.total_latency == 0.1
        assert len(metrics.latencies) == 1
    
    def test_record_call_with_error(self):
        """Test recording LLM call with error."""
        metrics = LLMMetrics()
        metrics.record_call(0.1, error=True)
        assert metrics.call_count == 1
        assert metrics.errors == 1
        assert metrics.timeouts == 0
    
    def test_record_call_with_timeout(self):
        """Test recording LLM call with timeout."""
        metrics = LLMMetrics()
        metrics.record_call(30.0, timeout=True)
        assert metrics.call_count == 1
        assert metrics.timeouts == 1
        assert metrics.errors == 0
    
    def test_get_stats(self):
        """Test getting statistics."""
        metrics = LLMMetrics()
        metrics.record_call(0.1, tokens=10)
        metrics.record_call(0.2, tokens=20)
        metrics.record_call(0.15, tokens=15)
        
        stats = metrics.get_stats()
        assert stats['total_calls'] == 3
        assert stats['total_tokens'] == 45
        assert stats['latency']['avg'] == 0.15
        assert stats['success_rate'] == 100.0


class TestCacheMetrics:
    """Test CacheMetrics class."""
    
    def test_init(self):
        """Test CacheMetrics initialization."""
        metrics = CacheMetrics()
        assert metrics.hits == 0
        assert metrics.misses == 0
        assert metrics.evictions == 0
        assert metrics.size == 0
        assert metrics.max_size == 0
    
    def test_record_hit(self):
        """Test recording cache hit."""
        metrics = CacheMetrics()
        metrics.record_hit()
        assert metrics.hits == 1
        assert metrics.misses == 0
    
    def test_record_miss(self):
        """Test recording cache miss."""
        metrics = CacheMetrics()
        metrics.record_miss()
        assert metrics.hits == 0
        assert metrics.misses == 1
    
    def test_record_eviction(self):
        """Test recording cache eviction."""
        metrics = CacheMetrics()
        metrics.record_eviction()
        assert metrics.evictions == 1
    
    def test_update_size(self):
        """Test updating cache size."""
        metrics = CacheMetrics()
        metrics.update_size(50, 100)
        assert metrics.size == 50
        assert metrics.max_size == 100
    
    def test_get_stats(self):
        """Test getting statistics."""
        metrics = CacheMetrics()
        metrics.record_hit()
        metrics.record_hit()
        metrics.record_miss()
        metrics.record_eviction()
        metrics.update_size(50, 100)
        
        stats = metrics.get_stats()
        assert stats['hits'] == 2
        assert stats['misses'] == 1
        assert stats['total_requests'] == 3
        assert stats['hit_rate'] == pytest.approx(66.67, rel=0.1)
        assert stats['evictions'] == 1
        assert stats['utilization'] == 50.0


class TestMetricsCollector:
    """Test MetricsCollector class."""
    
    def test_init(self):
        """Test MetricsCollector initialization."""
        collector = MetricsCollector()
        assert collector.performance is not None
        assert collector.llm is not None
        assert collector.cache is not None
        assert collector.start_time > 0
    
    def test_get_all_stats(self):
        """Test getting all statistics."""
        collector = MetricsCollector()
        collector.performance.record_step_time(0.1)
        collector.llm.record_call(0.2, tokens=10)
        collector.cache.record_hit()
        
        stats = collector.get_all_stats()
        assert 'runtime' in stats
        assert 'performance' in stats
        assert 'llm' in stats
        assert 'cache' in stats
        assert stats['performance']['step_timing']['total_steps'] == 1
        assert stats['llm']['total_calls'] == 1
        assert stats['cache']['hits'] == 1
    
    def test_get_summary(self):
        """Test getting summary string."""
        collector = MetricsCollector()
        collector.performance.record_step_time(0.1)
        collector.llm.record_call(0.2, tokens=10)
        collector.cache.record_hit()
        collector.cache.record_miss()
        
        summary = collector.get_summary()
        assert isinstance(summary, str)
        assert 'METRICS SUMMARY' in summary
        assert 'Performance' in summary
        assert 'LLM Statistics' in summary
        assert 'Cache Statistics' in summary

