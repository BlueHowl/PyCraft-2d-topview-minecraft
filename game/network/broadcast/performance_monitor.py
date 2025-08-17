"""
Performance Monitoring System for PyCraft 2D Multiplayer Broadcasting

Provides comprehensive performance monitoring, metrics collection,
and optimization recommendations for the message broadcasting system.
"""

import time
import threading
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from collections import deque, defaultdict
from enum import Enum
import statistics
import json

from ..message_types import MessageType
from .message_queue import MessagePriority


class MetricType(Enum):
    """Types of metrics to collect."""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"


@dataclass
class MetricValue:
    """A single metric measurement."""
    value: float
    timestamp: float = field(default_factory=time.time)
    tags: Dict[str, str] = field(default_factory=dict)


@dataclass
class PerformanceAlert:
    """Performance alert definition."""
    metric_name: str
    threshold: float
    condition: str  # "greater_than", "less_than", "equals"
    message: str
    callback: Optional[Callable] = None
    triggered: bool = False
    trigger_count: int = 0
    last_triggered: float = 0.0


class MetricCollector:
    """
    Collects and stores performance metrics.
    
    Provides efficient storage and retrieval of various metric types
    with automatic aggregation and history management.
    """
    
    def __init__(self, max_history: int = 1000):
        """
        Initialize metric collector.
        
        Args:
            max_history: Maximum number of metric values to keep
        """
        self.max_history = max_history
        self.metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=max_history))
        self.metric_types: Dict[str, MetricType] = {}
        self.metric_lock = threading.Lock()
        
        # Performance counters
        self.counters: Dict[str, float] = defaultdict(float)
        self.gauges: Dict[str, float] = defaultdict(float)
        
        # Timing contexts
        self.active_timers: Dict[str, float] = {}
    
    def increment_counter(self, name: str, value: float = 1.0, tags: Optional[Dict[str, str]] = None):
        """Increment a counter metric."""
        with self.metric_lock:
            self.counters[name] += value
            self._record_metric(name, value, MetricType.COUNTER, tags or {})
    
    def set_gauge(self, name: str, value: float, tags: Optional[Dict[str, str]] = None):
        """Set a gauge metric value."""
        with self.metric_lock:
            self.gauges[name] = value
            self._record_metric(name, value, MetricType.GAUGE, tags or {})
    
    def record_histogram(self, name: str, value: float, tags: Optional[Dict[str, str]] = None):
        """Record a histogram value."""
        with self.metric_lock:
            self._record_metric(name, value, MetricType.HISTOGRAM, tags or {})
    
    def start_timer(self, name: str) -> str:
        """Start a timer and return timer ID."""
        timer_id = f"{name}_{time.time()}_{id(threading.current_thread())}"
        self.active_timers[timer_id] = time.time()
        return timer_id
    
    def end_timer(self, timer_id: str, tags: Optional[Dict[str, str]] = None) -> float:
        """End a timer and record the duration."""
        if timer_id not in self.active_timers:
            return 0.0
        
        duration = time.time() - self.active_timers[timer_id]
        del self.active_timers[timer_id]
        
        # Extract metric name from timer_id
        name = timer_id.split('_')[0]
        with self.metric_lock:
            self._record_metric(name, duration, MetricType.TIMER, tags or {})
        
        return duration
    
    def _record_metric(self, name: str, value: float, metric_type: MetricType, tags: Dict[str, str]):
        """Record a metric value."""
        metric_value = MetricValue(value=value, tags=tags)
        self.metrics[name].append(metric_value)
        self.metric_types[name] = metric_type
    
    def get_metric_stats(self, name: str, time_window: Optional[float] = None) -> Dict[str, Any]:
        """
        Get statistics for a metric.
        
        Args:
            name: Metric name
            time_window: Time window in seconds (None for all data)
            
        Returns:
            Dictionary with metric statistics
        """
        if name not in self.metrics:
            return {}
        
        with self.metric_lock:
            metric_values = list(self.metrics[name])
            metric_type = self.metric_types.get(name, MetricType.GAUGE)
        
        # Filter by time window if specified
        if time_window:
            cutoff_time = time.time() - time_window
            metric_values = [mv for mv in metric_values if mv.timestamp >= cutoff_time]
        
        if not metric_values:
            return {}
        
        values = [mv.value for mv in metric_values]
        
        stats = {
            'metric_type': metric_type.value,
            'count': len(values),
            'latest': values[-1] if values else 0,
            'latest_timestamp': metric_values[-1].timestamp if metric_values else 0
        }
        
        if metric_type in [MetricType.HISTOGRAM, MetricType.TIMER]:
            stats.update({
                'min': min(values),
                'max': max(values),
                'mean': statistics.mean(values),
                'median': statistics.median(values),
                'sum': sum(values)
            })
            
            if len(values) > 1:
                stats['stddev'] = statistics.stdev(values)
                
            # Percentiles
            if len(values) >= 5:
                sorted_values = sorted(values)
                stats.update({
                    'p50': statistics.median(sorted_values),
                    'p90': sorted_values[int(len(sorted_values) * 0.9)],
                    'p95': sorted_values[int(len(sorted_values) * 0.95)],
                    'p99': sorted_values[int(len(sorted_values) * 0.99)]
                })
        
        elif metric_type == MetricType.COUNTER:
            stats.update({
                'total': self.counters.get(name, 0),
                'rate_per_second': len(values) / time_window if time_window else 0
            })
        
        elif metric_type == MetricType.GAUGE:
            stats.update({
                'current': self.gauges.get(name, 0),
                'min': min(values),
                'max': max(values),
                'mean': statistics.mean(values)
            })
        
        return stats
    
    def get_all_metrics(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all metrics."""
        all_stats = {}
        for metric_name in self.metrics:
            all_stats[metric_name] = self.get_metric_stats(metric_name, time_window=300)  # 5 minutes
        return all_stats
    
    def clear_metrics(self, metric_name: Optional[str] = None):
        """Clear metrics."""
        with self.metric_lock:
            if metric_name:
                self.metrics.pop(metric_name, None)
                self.metric_types.pop(metric_name, None)
                self.counters.pop(metric_name, None)
                self.gauges.pop(metric_name, None)
            else:
                self.metrics.clear()
                self.metric_types.clear()
                self.counters.clear()
                self.gauges.clear()


class BroadcastPerformanceMonitor:
    """
    Main performance monitoring system for message broadcasting.
    
    Monitors all aspects of the broadcasting system including
    message throughput, latency, compression efficiency, and resource usage.
    """
    
    def __init__(self):
        """Initialize performance monitor."""
        self.metric_collector = MetricCollector()
        self.alerts: List[PerformanceAlert] = []
        self.monitoring_enabled = True
        self.alert_lock = threading.Lock()
        
        # Default alerts
        self._setup_default_alerts()
        
        # Performance tracking
        self.start_time = time.time()
        self.last_stats_update = time.time()
    
    def _setup_default_alerts(self):
        """Setup default performance alerts."""
        self.add_alert("message_queue_size", 1000, "greater_than", 
                      "Message queue size is too high")
        self.add_alert("broadcast_latency_p95", 0.1, "greater_than",
                      "Broadcast latency P95 is too high")
        self.add_alert("compression_ratio", 0.9, "greater_than",
                      "Compression ratio is poor")
        self.add_alert("memory_usage_mb", 1000, "greater_than",
                      "Memory usage is too high")
    
    def add_alert(self, metric_name: str, threshold: float, condition: str, 
                  message: str, callback: Optional[Callable] = None):
        """Add performance alert."""
        alert = PerformanceAlert(
            metric_name=metric_name,
            threshold=threshold,
            condition=condition,
            message=message,
            callback=callback
        )
        
        with self.alert_lock:
            self.alerts.append(alert)
    
    def remove_alert(self, metric_name: str):
        """Remove alerts for metric."""
        with self.alert_lock:
            self.alerts = [alert for alert in self.alerts if alert.metric_name != metric_name]
    
    def check_alerts(self):
        """Check all alerts and trigger if necessary."""
        if not self.monitoring_enabled:
            return
        
        current_time = time.time()
        
        with self.alert_lock:
            for alert in self.alerts:
                stats = self.metric_collector.get_metric_stats(alert.metric_name, time_window=60)
                if not stats:
                    continue
                
                # Get value to check
                check_value = None
                if 'p95' in alert.metric_name and 'p95' in stats:
                    check_value = stats['p95']
                elif 'latest' in stats:
                    check_value = stats['latest']
                elif 'current' in stats:
                    check_value = stats['current']
                
                if check_value is None:
                    continue
                
                # Check condition
                triggered = False
                if alert.condition == "greater_than" and check_value > alert.threshold:
                    triggered = True
                elif alert.condition == "less_than" and check_value < alert.threshold:
                    triggered = True
                elif alert.condition == "equals" and abs(check_value - alert.threshold) < 0.001:
                    triggered = True
                
                # Handle alert
                if triggered and not alert.triggered:
                    alert.triggered = True
                    alert.trigger_count += 1
                    alert.last_triggered = current_time
                    
                    print(f"PERFORMANCE ALERT: {alert.message} "
                          f"(metric: {alert.metric_name}, value: {check_value}, "
                          f"threshold: {alert.threshold})")
                    
                    if alert.callback:
                        try:
                            alert.callback(alert, check_value)
                        except Exception as e:
                            print(f"Alert callback failed: {e}")
                
                elif not triggered and alert.triggered:
                    alert.triggered = False
                    print(f"Performance alert resolved: {alert.metric_name}")
    
    # Message Broadcasting Metrics
    def record_message_sent(self, message_type: MessageType, priority: MessagePriority, 
                           size: int, target_count: int):
        """Record a message being sent."""
        if not self.monitoring_enabled:
            return
        
        self.metric_collector.increment_counter("messages_sent_total")
        self.metric_collector.increment_counter(f"messages_sent_{message_type.value}")
        self.metric_collector.increment_counter(f"messages_sent_priority_{priority.name.lower()}")
        self.metric_collector.record_histogram("message_size_bytes", size)
        self.metric_collector.record_histogram("broadcast_target_count", target_count)
    
    def record_message_processed(self, processing_time: float):
        """Record message processing time."""
        if not self.monitoring_enabled:
            return
        
        self.metric_collector.increment_counter("messages_processed_total")
        self.metric_collector.record_histogram("message_processing_time", processing_time)
    
    def record_broadcast_latency(self, latency: float):
        """Record broadcast latency."""
        if not self.monitoring_enabled:
            return
        
        self.metric_collector.record_histogram("broadcast_latency", latency)
    
    def record_queue_size(self, total_size: int, priority_sizes: Dict[str, int]):
        """Record message queue sizes."""
        if not self.monitoring_enabled:
            return
        
        self.metric_collector.set_gauge("message_queue_size", total_size)
        for priority, size in priority_sizes.items():
            self.metric_collector.set_gauge(f"queue_size_{priority}", size)
    
    def record_compression_stats(self, original_size: int, compressed_size: int, 
                               compression_time: float, algorithm: str):
        """Record compression statistics."""
        if not self.monitoring_enabled:
            return
        
        compression_ratio = compressed_size / original_size if original_size > 0 else 1.0
        
        self.metric_collector.record_histogram("compression_ratio", compression_ratio)
        self.metric_collector.record_histogram("compression_time", compression_time)
        self.metric_collector.record_histogram("compression_original_size", original_size)
        self.metric_collector.record_histogram("compression_compressed_size", compressed_size)
        self.metric_collector.increment_counter(f"compression_algorithm_{algorithm}")
    
    def record_client_stats(self, client_count: int, active_clients: int):
        """Record client statistics."""
        if not self.monitoring_enabled:
            return
        
        self.metric_collector.set_gauge("total_clients", client_count)
        self.metric_collector.set_gauge("active_clients", active_clients)
    
    def record_bandwidth_usage(self, bytes_sent: int, bytes_received: int):
        """Record bandwidth usage."""
        if not self.monitoring_enabled:
            return
        
        self.metric_collector.increment_counter("bytes_sent", bytes_sent)
        self.metric_collector.increment_counter("bytes_received", bytes_received)
    
    def record_error(self, error_type: str, error_message: str):
        """Record an error."""
        if not self.monitoring_enabled:
            return
        
        self.metric_collector.increment_counter("errors_total")
        self.metric_collector.increment_counter(f"error_type_{error_type}")
    
    # System Resource Metrics
    def record_memory_usage(self, memory_mb: float):
        """Record memory usage."""
        if not self.monitoring_enabled:
            return
        
        self.metric_collector.set_gauge("memory_usage_mb", memory_mb)
    
    def record_cpu_usage(self, cpu_percent: float):
        """Record CPU usage."""
        if not self.monitoring_enabled:
            return
        
        self.metric_collector.set_gauge("cpu_usage_percent", cpu_percent)
    
    # Performance Analysis
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get comprehensive performance summary."""
        uptime = time.time() - self.start_time
        all_metrics = self.metric_collector.get_all_metrics()
        
        summary = {
            'uptime_seconds': uptime,
            'monitoring_enabled': self.monitoring_enabled,
            'alert_count': len(self.alerts),
            'active_alerts': len([a for a in self.alerts if a.triggered]),
            'metrics': all_metrics
        }
        
        # Calculate derived metrics
        if 'messages_sent_total' in all_metrics:
            msg_stats = all_metrics['messages_sent_total']
            if uptime > 0:
                summary['messages_per_second'] = msg_stats.get('total', 0) / uptime
        
        if 'bytes_sent' in all_metrics and 'bytes_received' in all_metrics:
            sent_stats = all_metrics['bytes_sent']
            received_stats = all_metrics['bytes_received']
            total_bytes = sent_stats.get('total', 0) + received_stats.get('total', 0)
            if uptime > 0:
                summary['bandwidth_bytes_per_second'] = total_bytes / uptime
                summary['bandwidth_mbps'] = (total_bytes * 8) / (uptime * 1_000_000)
        
        return summary
    
    def get_optimization_recommendations(self) -> List[str]:
        """Get performance optimization recommendations."""
        recommendations = []
        summary = self.get_performance_summary()
        metrics = summary.get('metrics', {})
        
        # Check message queue size
        if 'message_queue_size' in metrics:
            queue_stats = metrics['message_queue_size']
            if queue_stats.get('current', 0) > 500:
                recommendations.append(
                    "Message queue size is high. Consider increasing processing rate "
                    "or reducing message generation."
                )
        
        # Check compression ratio
        if 'compression_ratio' in metrics:
            comp_stats = metrics['compression_ratio']
            if comp_stats.get('mean', 0) > 0.8:
                recommendations.append(
                    "Compression ratio is poor. Consider using different compression "
                    "algorithms or implementing better delta compression."
                )
        
        # Check broadcast latency
        if 'broadcast_latency' in metrics:
            latency_stats = metrics['broadcast_latency']
            if latency_stats.get('p95', 0) > 0.1:
                recommendations.append(
                    "Broadcast latency P95 is high. Consider optimizing message "
                    "routing or reducing message size."
                )
        
        # Check memory usage
        if 'memory_usage_mb' in metrics:
            memory_stats = metrics['memory_usage_mb']
            if memory_stats.get('current', 0) > 800:
                recommendations.append(
                    "Memory usage is high. Consider reducing message history size "
                    "or implementing better garbage collection."
                )
        
        # Check error rate
        if 'errors_total' in metrics:
            error_stats = metrics['errors_total']
            uptime = summary.get('uptime_seconds', 1)
            error_rate = error_stats.get('total', 0) / uptime
            if error_rate > 0.1:  # More than 0.1 errors per second
                recommendations.append(
                    "Error rate is high. Check logs for recurring issues and "
                    "implement better error handling."
                )
        
        return recommendations
    
    def generate_performance_report(self) -> str:
        """Generate detailed performance report."""
        summary = self.get_performance_summary()
        recommendations = self.get_optimization_recommendations()
        
        report = {
            'timestamp': time.time(),
            'summary': summary,
            'recommendations': recommendations,
            'alerts': [
                {
                    'metric': alert.metric_name,
                    'threshold': alert.threshold,
                    'condition': alert.condition,
                    'triggered': alert.triggered,
                    'trigger_count': alert.trigger_count,
                    'message': alert.message
                }
                for alert in self.alerts
            ]
        }
        
        return json.dumps(report, indent=2)
    
    def enable_monitoring(self):
        """Enable performance monitoring."""
        self.monitoring_enabled = True
    
    def disable_monitoring(self):
        """Disable performance monitoring."""
        self.monitoring_enabled = False
    
    def reset_stats(self):
        """Reset all statistics."""
        self.metric_collector.clear_metrics()
        self.start_time = time.time()
        with self.alert_lock:
            for alert in self.alerts:
                alert.triggered = False
                alert.trigger_count = 0


# Context manager for timing operations
class TimingContext:
    """Context manager for timing operations."""
    
    def __init__(self, monitor: BroadcastPerformanceMonitor, metric_name: str):
        """
        Initialize timing context.
        
        Args:
            monitor: Performance monitor instance
            metric_name: Name of the metric to record
        """
        self.monitor = monitor
        self.metric_name = metric_name
        self.timer_id = None
    
    def __enter__(self):
        """Start timing."""
        self.timer_id = self.monitor.metric_collector.start_timer(self.metric_name)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """End timing and record result."""
        if self.timer_id:
            self.monitor.metric_collector.end_timer(self.timer_id)


# Global performance monitor instance
performance_monitor = BroadcastPerformanceMonitor()
