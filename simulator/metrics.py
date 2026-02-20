"""Real-time metrics collector for banking simulation.

Collects and aggregates metrics during simulation including transaction rates,
fraud detection performance, API latencies, and system health indicators.
Provides real-time data for dashboard visualization.
"""

import asyncio
import time
import csv
import json
from collections import deque, defaultdict
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from statistics import mean, median
from pathlib import Path

from .config import MetricsConfig


@dataclass
class MetricPoint:
    """A single metric data point"""
    timestamp: datetime
    metric_name: str
    value: float
    labels: Dict[str, str] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "metric": self.metric_name,
            "value": self.value,
            "labels": self.labels
        }


@dataclass
class TimeSeries:
    """Time series data for a metric"""
    name: str
    data_points: deque = field(default_factory=lambda: deque(maxlen=1000))
    labels: Dict[str, str] = field(default_factory=dict)
    
    def add_point(self, value: float, timestamp: Optional[datetime] = None):
        """Add a data point to the time series"""
        if timestamp is None:
            timestamp = datetime.now()
        point = MetricPoint(timestamp, self.name, value, self.labels.copy())
        self.data_points.append(point)
        
    def get_recent_values(self, minutes: int = 5) -> List[float]:
        """Get values from the last N minutes"""
        cutoff = datetime.now() - timedelta(minutes=minutes)
        return [point.value for point in self.data_points if point.timestamp >= cutoff]
        
    def get_latest(self) -> Optional[MetricPoint]:
        """Get the most recent data point"""
        return self.data_points[-1] if self.data_points else None
        
    def get_average(self, minutes: int = 5) -> float:
        """Get average value over last N minutes"""
        values = self.get_recent_values(minutes)
        return mean(values) if values else 0.0
        
    def get_rate(self, minutes: int = 1) -> float:
        """Get rate of change (per minute)"""
        values = self.get_recent_values(minutes)
        if len(values) < 2:
            return 0.0
        return (values[-1] - values[0]) / minutes


class MetricsCollector:
    """Collects and manages simulation metrics"""
    
    def __init__(self, config: MetricsConfig):
        self.config = config
        self.enabled = config.enabled
        self.collect_interval = config.collect_interval_seconds
        self.retention_minutes = config.retention_minutes
        
        # Time series storage
        self.time_series: Dict[str, TimeSeries] = {}
        self.counters: Dict[str, int] = defaultdict(int)
        self.gauges: Dict[str, float] = {}
        self.histograms: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        
        # Real-time aggregations
        self.aggregations: Dict[str, Dict[str, Any]] = defaultdict(dict)
        
        # Collection task
        self.collection_task: Optional[asyncio.Task] = None
        self.running = False
        
        # Export settings
        self.export_csv = config.export_csv
        self.export_path = Path(config.export_path) if config.export_path else Path("metrics_export")
        
        # Callbacks for real-time updates
        self.update_callbacks: List[Callable[[Dict[str, Any]], None]] = []
        
        # Start time for simulation metrics
        self.simulation_start_time = datetime.now()
        
    async def start(self):
        """Start the metrics collector"""
        if not self.enabled:
            return
            
        self.running = True
        self.simulation_start_time = datetime.now()
        
        # Start collection task
        self.collection_task = asyncio.create_task(self._collection_loop())
        
        # Initialize core metrics
        self._initialize_metrics()
        
    async def stop(self):
        """Stop the metrics collector"""
        self.running = False
        
        if self.collection_task:
            self.collection_task.cancel()
            try:
                await self.collection_task
            except asyncio.CancelledError:
                pass
                
        # Export metrics if configured
        if self.export_csv:
            await self.export_to_csv()
            
    def _initialize_metrics(self):
        """Initialize core simulation metrics"""
        self.time_series["transactions_per_second"] = TimeSeries("transactions_per_second")
        self.time_series["fraud_transactions_per_second"] = TimeSeries("fraud_transactions_per_second")
        self.time_series["nexum_api_latency_ms"] = TimeSeries("nexum_api_latency_ms")
        self.time_series["bastion_api_latency_ms"] = TimeSeries("bastion_api_latency_ms")
        self.time_series["nexum_success_rate"] = TimeSeries("nexum_success_rate")
        self.time_series["bastion_success_rate"] = TimeSeries("bastion_success_rate")
        self.time_series["average_risk_score"] = TimeSeries("average_risk_score")
        self.time_series["fraud_detection_rate"] = TimeSeries("fraud_detection_rate")
        self.time_series["false_positive_rate"] = TimeSeries("false_positive_rate")
        self.time_series["memory_usage_mb"] = TimeSeries("memory_usage_mb")
        
        # Initialize counters
        self.counters["transactions_total"] = 0
        self.counters["fraud_transactions_total"] = 0
        self.counters["nexum_requests_total"] = 0
        self.counters["bastion_requests_total"] = 0
        self.counters["nexum_errors_total"] = 0
        self.counters["bastion_errors_total"] = 0
        
        # Initialize gauges
        self.gauges["customers_created"] = 0
        self.gauges["accounts_created"] = 0
        self.gauges["simulation_time_multiplier"] = 1.0
        
    async def _collection_loop(self):
        """Main metrics collection loop"""
        try:
            while self.running:
                await self._collect_system_metrics()
                await self._calculate_aggregations()
                await self._notify_callbacks()
                await self._cleanup_old_data()
                
                await asyncio.sleep(self.collect_interval)
                
        except asyncio.CancelledError:
            pass
        except Exception as e:
            print(f"Metrics collection error: {e}")
            
    async def _collect_system_metrics(self):
        """Collect system-level metrics"""
        try:
            import psutil
            process = psutil.Process()
            
            # Memory usage
            memory_mb = process.memory_info().rss / 1024 / 1024
            self.record_gauge("memory_usage_mb", memory_mb)
            
            # CPU usage
            cpu_percent = process.cpu_percent()
            self.record_gauge("cpu_usage_percent", cpu_percent)
            
        except ImportError:
            # psutil not available
            pass
        except Exception as e:
            print(f"System metrics error: {e}")
            
    async def _calculate_aggregations(self):
        """Calculate real-time aggregations"""
        current_time = datetime.now()
        
        # Transaction rates
        for metric_name in ["transactions_per_second", "fraud_transactions_per_second"]:
            if metric_name in self.time_series:
                ts = self.time_series[metric_name]
                self.aggregations[metric_name] = {
                    "current": ts.get_latest().value if ts.get_latest() else 0,
                    "avg_1min": ts.get_average(1),
                    "avg_5min": ts.get_average(5),
                    "peak_1min": max(ts.get_recent_values(1)) if ts.get_recent_values(1) else 0
                }
                
        # Latency percentiles
        for metric_name in ["nexum_api_latency_ms", "bastion_api_latency_ms"]:
            if metric_name in self.histograms and self.histograms[metric_name]:
                values = list(self.histograms[metric_name])
                values.sort()
                n = len(values)
                
                if n > 0:
                    self.aggregations[metric_name] = {
                        "p50": values[int(n * 0.5)],
                        "p95": values[int(n * 0.95)],
                        "p99": values[int(n * 0.99)],
                        "avg": mean(values),
                        "max": max(values),
                        "min": min(values)
                    }
                    
        # Error rates
        total_nexum = self.counters["nexum_requests_total"]
        total_bastion = self.counters["bastion_requests_total"]
        
        if total_nexum > 0:
            nexum_error_rate = self.counters["nexum_errors_total"] / total_nexum
            self.aggregations["nexum_error_rate"] = {
                "current": nexum_error_rate,
                "total_requests": total_nexum,
                "total_errors": self.counters["nexum_errors_total"]
            }
            
        if total_bastion > 0:
            bastion_error_rate = self.counters["bastion_errors_total"] / total_bastion
            self.aggregations["bastion_error_rate"] = {
                "current": bastion_error_rate,
                "total_requests": total_bastion,
                "total_errors": self.counters["bastion_errors_total"]
            }
            
        # Fraud detection metrics
        total_transactions = self.counters["transactions_total"]
        fraud_transactions = self.counters["fraud_transactions_total"]
        
        if total_transactions > 0:
            fraud_rate = fraud_transactions / total_transactions
            self.aggregations["fraud_rate"] = {
                "current": fraud_rate,
                "total_transactions": total_transactions,
                "fraud_transactions": fraud_transactions
            }
            
        # Simulation progress
        elapsed = current_time - self.simulation_start_time
        self.aggregations["simulation_progress"] = {
            "elapsed_seconds": elapsed.total_seconds(),
            "elapsed_formatted": str(elapsed).split('.')[0],
            "customers_created": self.gauges.get("customers_created", 0),
            "accounts_created": self.gauges.get("accounts_created", 0)
        }
        
    async def _notify_callbacks(self):
        """Notify registered callbacks with current metrics"""
        if not self.update_callbacks:
            return
            
        metrics_snapshot = self.get_current_metrics()
        
        for callback in self.update_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(metrics_snapshot)
                else:
                    callback(metrics_snapshot)
            except Exception as e:
                print(f"Metrics callback error: {e}")
                
    async def _cleanup_old_data(self):
        """Remove old data points based on retention policy"""
        cutoff = datetime.now() - timedelta(minutes=self.retention_minutes)
        
        for ts in self.time_series.values():
            while ts.data_points and ts.data_points[0].timestamp < cutoff:
                ts.data_points.popleft()
                
    # Public API methods
    def record_counter(self, name: str, value: int = 1, labels: Optional[Dict[str, str]] = None):
        """Record a counter increment"""
        if not self.enabled:
            return
            
        self.counters[name] += value
        
        # Also track as time series for rates
        if f"{name}_rate" not in self.time_series:
            self.time_series[f"{name}_rate"] = TimeSeries(f"{name}_rate", labels=labels or {})
        self.time_series[f"{name}_rate"].add_point(value)
        
    def record_gauge(self, name: str, value: float, labels: Optional[Dict[str, str]] = None):
        """Record a gauge value"""
        if not self.enabled:
            return
            
        self.gauges[name] = value
        
        # Track as time series
        if name not in self.time_series:
            self.time_series[name] = TimeSeries(name, labels=labels or {})
        self.time_series[name].add_point(value)
        
    def record_histogram(self, name: str, value: float, labels: Optional[Dict[str, str]] = None):
        """Record a histogram value (for latencies, sizes, etc.)"""
        if not self.enabled:
            return
            
        self.histograms[name].append(value)
        
        # Also track as time series for visualization
        if name not in self.time_series:
            self.time_series[name] = TimeSeries(name, labels=labels or {})
        self.time_series[name].add_point(value)
        
    def record_timing(self, name: str, duration_ms: float, labels: Optional[Dict[str, str]] = None):
        """Record a timing metric in milliseconds"""
        self.record_histogram(name, duration_ms, labels)
        
    # Convenience methods for simulation events
    def record_transaction(self, is_fraud: bool = False):
        """Record a transaction"""
        self.record_counter("transactions_total")
        if is_fraud:
            self.record_counter("fraud_transactions_total")
            
    def record_nexum_request(self, latency_ms: float, success: bool = True):
        """Record Nexum API request"""
        self.record_counter("nexum_requests_total")
        self.record_timing("nexum_api_latency_ms", latency_ms)
        if not success:
            self.record_counter("nexum_errors_total")
            
    def record_bastion_request(self, latency_ms: float, risk_score: Optional[float] = None, success: bool = True):
        """Record Bastion API request"""
        self.record_counter("bastion_requests_total")
        self.record_timing("bastion_api_latency_ms", latency_ms)
        if risk_score is not None:
            self.record_gauge("latest_risk_score", risk_score)
        if not success:
            self.record_counter("bastion_errors_total")
            
    def record_fraud_decision(self, predicted_fraud: bool, actual_fraud: bool):
        """Record fraud detection decision for accuracy metrics"""
        if predicted_fraud and actual_fraud:
            self.record_counter("true_positives")
        elif predicted_fraud and not actual_fraud:
            self.record_counter("false_positives")
        elif not predicted_fraud and actual_fraud:
            self.record_counter("false_negatives")
        else:
            self.record_counter("true_negatives")
            
    def calculate_rates(self, window_minutes: int = 1) -> Dict[str, float]:
        """Calculate current rates (per second)"""
        rates = {}
        
        for name, ts in self.time_series.items():
            if name.endswith("_rate"):
                continue
                
            values = ts.get_recent_values(window_minutes)
            if len(values) >= 2:
                total_value = sum(values)
                rate_per_second = total_value / (window_minutes * 60)
                rates[f"{name}_per_second"] = rate_per_second
                
        return rates
        
    def get_current_metrics(self) -> Dict[str, Any]:
        """Get current metrics snapshot"""
        return {
            "timestamp": datetime.now().isoformat(),
            "counters": dict(self.counters),
            "gauges": dict(self.gauges),
            "aggregations": dict(self.aggregations),
            "rates": self.calculate_rates(),
            "simulation_runtime_seconds": (datetime.now() - self.simulation_start_time).total_seconds()
        }
        
    def get_time_series_data(self, metric_name: str, minutes: int = 10) -> List[Dict[str, Any]]:
        """Get time series data for a specific metric"""
        if metric_name not in self.time_series:
            return []
            
        ts = self.time_series[metric_name]
        cutoff = datetime.now() - timedelta(minutes=minutes)
        
        return [
            point.to_dict() 
            for point in ts.data_points 
            if point.timestamp >= cutoff
        ]
        
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get formatted data for dashboard consumption"""
        current_metrics = self.get_current_metrics()
        
        # Format for dashboard
        dashboard_data = {
            "timestamp": current_metrics["timestamp"],
            "overview": {
                "transactions_total": self.counters["transactions_total"],
                "fraud_transactions": self.counters["fraud_transactions_total"],
                "customers_created": self.gauges.get("customers_created", 0),
                "accounts_created": self.gauges.get("accounts_created", 0),
                "simulation_runtime": current_metrics["simulation_runtime_seconds"]
            },
            "performance": {
                "transactions_per_second": self.aggregations.get("transactions_per_second", {}).get("current", 0),
                "nexum_latency_p95": self.aggregations.get("nexum_api_latency_ms", {}).get("p95", 0),
                "bastion_latency_p95": self.aggregations.get("bastion_api_latency_ms", {}).get("p95", 0),
                "nexum_error_rate": self.aggregations.get("nexum_error_rate", {}).get("current", 0),
                "bastion_error_rate": self.aggregations.get("bastion_error_rate", {}).get("current", 0)
            },
            "fraud_detection": {
                "fraud_rate": self.aggregations.get("fraud_rate", {}).get("current", 0),
                "true_positives": self.counters.get("true_positives", 0),
                "false_positives": self.counters.get("false_positives", 0),
                "false_negatives": self.counters.get("false_negatives", 0),
                "true_negatives": self.counters.get("true_negatives", 0)
            }
        }
        
        # Add time series data for charts
        dashboard_data["charts"] = {
            "transaction_rate": self.get_time_series_data("transactions_per_second", 10),
            "fraud_rate": self.get_time_series_data("fraud_transactions_per_second", 10),
            "nexum_latency": self.get_time_series_data("nexum_api_latency_ms", 10),
            "bastion_latency": self.get_time_series_data("bastion_api_latency_ms", 10)
        }
        
        return dashboard_data
        
    # Export functionality
    async def export_to_csv(self):
        """Export metrics to CSV files"""
        if not self.export_path.exists():
            self.export_path.mkdir(parents=True)
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Export counters
        counters_file = self.export_path / f"counters_{timestamp}.csv"
        with open(counters_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["metric", "value"])
            for name, value in self.counters.items():
                writer.writerow([name, value])
                
        # Export gauges
        gauges_file = self.export_path / f"gauges_{timestamp}.csv"
        with open(gauges_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["metric", "value"])
            for name, value in self.gauges.items():
                writer.writerow([name, value])
                
        # Export time series
        for name, ts in self.time_series.items():
            ts_file = self.export_path / f"timeseries_{name}_{timestamp}.csv"
            with open(ts_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["timestamp", "value"])
                for point in ts.data_points:
                    writer.writerow([point.timestamp.isoformat(), point.value])
                    
    def export_to_json(self) -> str:
        """Export current metrics to JSON string"""
        return json.dumps(self.get_current_metrics(), indent=2, default=str)
        
    # Callback management
    def add_update_callback(self, callback: Callable[[Dict[str, Any]], None]):
        """Add callback for real-time metric updates"""
        self.update_callbacks.append(callback)
        
    def remove_update_callback(self, callback: Callable[[Dict[str, Any]], None]):
        """Remove callback"""
        if callback in self.update_callbacks:
            self.update_callbacks.remove(callback)