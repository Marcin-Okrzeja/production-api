"""
Monitoring module for Production AI API
Metrics collection and performance tracking
"""

import time
from typing import Dict, Any
from datetime import datetime
from models import MetricsResponse, ModelMetrics


class MetricsCollector:
    """Collect and track API metrics"""
    
    def __init__(self):
        self.start_time = time.time()
        self.requests_total = 0
        self.cache_hits = 0
        self.errors_total = 0
        self.total_tokens = 0
        self.processing_times = []
        self.model_metrics = {}
    
    def record_request(self) -> None:
        """Record a request"""
        self.requests_total += 1
    
    def record_cache_hit(self) -> None:
        """Record a cache hit"""
        self.cache_hits += 1
    
    def record_error(self) -> None:
        """Record an error"""
        self.errors_total += 1
    
    def record_tokens(self, tokens: int) -> None:
        """Record token usage"""
        self.total_tokens += tokens
    
    def record_processing_time(self, time_ms: float) -> None:
        """Record processing time"""
        self.processing_times.append(time_ms)
        
        # Keep only last 1000 measurements
        if len(self.processing_times) > 1000:
            self.processing_times = self.processing_times[-1000:]
    
    def record_model_usage(self, model_name: str, tokens: int, latency_ms: float, success: bool) -> None:
        """Record model-specific metrics"""
        if model_name not in self.model_metrics:
            self.model_metrics[model_name] = ModelMetrics(
                model_name=model_name,
                requests_count=0,
                total_tokens=0,
                average_latency_ms=0.0,
                success_rate=1.0,
                last_used=None
            )
        
        metrics = self.model_metrics[model_name]
        metrics.requests_count += 1
        metrics.total_tokens += tokens
        metrics.last_used = datetime.utcnow()
        
        # Update average latency
        if metrics.requests_count == 1:
            metrics.average_latency_ms = latency_ms
        else:
            metrics.average_latency_ms = (
                (metrics.average_latency_ms * (metrics.requests_count - 1) + latency_ms) / 
                metrics.requests_count
            )
        
        # Update success rate
        if not success:
            metrics.success_rate = (metrics.success_rate * (metrics.requests_count - 1)) / metrics.requests_count
    
    def get_summary(self) -> MetricsResponse:
        """Get metrics summary"""
        uptime = time.time() - self.start_time
        cache_hit_rate = self.cache_hits / max(self.requests_total, 1)
        error_rate = self.errors_total / max(self.requests_total, 1)
        avg_processing_time = sum(self.processing_times) / len(self.processing_times) if self.processing_times else 0
        
        return MetricsResponse(
            requests_total=self.requests_total,
            cache_hits=self.cache_hits,
            errors_total=self.errors_total,
            total_tokens=self.total_tokens,
            cache_hit_rate=cache_hit_rate,
            error_rate=error_rate,
            average_processing_time_ms=avg_processing_time
        )
    
    def get_model_metrics(self) -> Dict[str, ModelMetrics]:
        """Get model-specific metrics"""
        return self.model_metrics.copy()
    
    def reset(self) -> None:
        """Reset all metrics"""
        self.requests_total = 0
        self.cache_hits = 0
        self.errors_total = 0
        self.total_tokens = 0
        self.processing_times = []
        self.model_metrics = {}


class PerformanceTracker:
    """Track individual request performance"""
    
    def __init__(self):
        self.start_time = None
    
    def start(self) -> None:
        """Start tracking"""
        self.start_time = time.time()
    
    def stop(self) -> float:
        """Stop tracking and return elapsed time in milliseconds"""
        if self.start_time is None:
            return 0.0
        
        elapsed = (time.time() - self.start_time) * 1000
        self.start_time = None
        return elapsed


# Global metrics collector
metrics = MetricsCollector()


def get_metrics() -> MetricsCollector:
    """Get global metrics collector"""
    return metrics


def create_tracker() -> PerformanceTracker:
    """Create a new performance tracker"""
    return PerformanceTracker()


if __name__ == "__main__":
    # Test monitoring
    print("📊 Testing monitoring module...")
    
    # Simulate some requests
    tracker = create_tracker()
    
    for i in range(5):
        tracker.start()
        time.sleep(0.1)  # Simulate processing
        processing_time = tracker.stop()
        
        metrics.record_request()
        metrics.record_processing_time(processing_time)
        metrics.record_tokens(100 + i * 10)
        
        if i % 2 == 0:
            metrics.record_cache_hit()
    
    # Get summary
    summary = metrics.get_summary()
    print(f"✅ Requests: {summary.requests_total}")
    print(f"✅ Cache hits: {summary.cache_hits}")
    print(f"✅ Cache hit rate: {summary.cache_hit_rate:.2%}")
    print(f"✅ Avg processing time: {summary.average_processing_time_ms:.2f}ms")
    
    print("🎉 Monitoring module working!")
