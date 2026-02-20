"""Post-simulation analytics and reporting.

Generates comprehensive reports after simulation completion including
performance analysis, fraud detection accuracy, system metrics, and
recommendations for optimization.
"""

import json
import csv
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path
from dataclasses import dataclass
from statistics import mean, median, stdev

from .config import RuntimeStats
from .metrics import MetricsCollector


@dataclass
class SimulationReport:
    """Comprehensive simulation report"""
    simulation_name: str
    start_time: datetime
    end_time: datetime
    duration_seconds: float
    
    # Customer and account metrics
    customers_created: int
    accounts_created: int
    
    # Transaction metrics
    transactions_processed: int
    fraud_transactions: int
    legitimate_transactions: int
    
    # Performance metrics
    peak_tps: float
    average_tps: float
    total_api_calls: int
    
    # Fraud detection metrics
    fraud_detection_accuracy: float
    false_positive_rate: float
    false_negative_rate: float
    precision: float
    recall: float
    
    # API performance
    nexum_stats: Dict[str, Any]
    bastion_stats: Dict[str, Any]
    
    # System performance
    memory_usage_mb: float
    cpu_usage_percent: float
    
    # Recommendations
    recommendations: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert report to dictionary"""
        return {
            "simulation_name": self.simulation_name,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
            "duration_seconds": self.duration_seconds,
            "customers_created": self.customers_created,
            "accounts_created": self.accounts_created,
            "transactions_processed": self.transactions_processed,
            "fraud_transactions": self.fraud_transactions,
            "legitimate_transactions": self.legitimate_transactions,
            "peak_tps": self.peak_tps,
            "average_tps": self.average_tps,
            "total_api_calls": self.total_api_calls,
            "fraud_detection_accuracy": self.fraud_detection_accuracy,
            "false_positive_rate": self.false_positive_rate,
            "false_negative_rate": self.false_negative_rate,
            "precision": self.precision,
            "recall": self.recall,
            "nexum_stats": self.nexum_stats,
            "bastion_stats": self.bastion_stats,
            "memory_usage_mb": self.memory_usage_mb,
            "cpu_usage_percent": self.cpu_usage_percent,
            "recommendations": self.recommendations
        }


class SimulationReporter:
    """Generates comprehensive simulation reports"""
    
    def __init__(self, output_dir: str = "reports"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
    def generate_report(self, simulation_name: str, runtime_stats: RuntimeStats,
                       metrics_collector: MetricsCollector, nexum_stats: Dict[str, Any],
                       bastion_stats: Dict[str, Any]) -> SimulationReport:
        """Generate comprehensive simulation report"""
        
        # Calculate fraud detection metrics
        current_metrics = metrics_collector.get_current_metrics()
        fraud_metrics = self._calculate_fraud_metrics(current_metrics)
        
        # Calculate performance metrics
        performance_metrics = self._calculate_performance_metrics(current_metrics, runtime_stats)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            runtime_stats, nexum_stats, bastion_stats, fraud_metrics
        )
        
        # Create report
        report = SimulationReport(
            simulation_name=simulation_name,
            start_time=runtime_stats.start_time,
            end_time=runtime_stats.end_time or datetime.now(),
            duration_seconds=runtime_stats.duration_seconds,
            customers_created=runtime_stats.customers_created,
            accounts_created=runtime_stats.accounts_created,
            transactions_processed=runtime_stats.transactions_processed,
            fraud_transactions=runtime_stats.fraud_transactions,
            legitimate_transactions=runtime_stats.transactions_processed - runtime_stats.fraud_transactions,
            peak_tps=performance_metrics["peak_tps"],
            average_tps=runtime_stats.actual_tps,
            total_api_calls=runtime_stats.nexum_api_calls + runtime_stats.bastion_api_calls,
            fraud_detection_accuracy=fraud_metrics["accuracy"],
            false_positive_rate=fraud_metrics["false_positive_rate"],
            false_negative_rate=fraud_metrics["false_negative_rate"],
            precision=fraud_metrics["precision"],
            recall=fraud_metrics["recall"],
            nexum_stats=nexum_stats,
            bastion_stats=bastion_stats,
            memory_usage_mb=performance_metrics["memory_usage_mb"],
            cpu_usage_percent=performance_metrics["cpu_usage_percent"],
            recommendations=recommendations
        )
        
        return report
        
    def _calculate_fraud_metrics(self, metrics: Dict[str, Any]) -> Dict[str, float]:
        """Calculate fraud detection accuracy metrics"""
        counters = metrics.get("counters", {})
        
        true_positives = counters.get("true_positives", 0)
        false_positives = counters.get("false_positives", 0)
        true_negatives = counters.get("true_negatives", 0)
        false_negatives = counters.get("false_negatives", 0)
        
        total = true_positives + false_positives + true_negatives + false_negatives
        
        if total == 0:
            return {
                "accuracy": 0.0,
                "precision": 0.0,
                "recall": 0.0,
                "false_positive_rate": 0.0,
                "false_negative_rate": 0.0
            }
            
        accuracy = (true_positives + true_negatives) / total
        
        precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0.0
        recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0.0
        
        false_positive_rate = false_positives / (false_positives + true_negatives) if (false_positives + true_negatives) > 0 else 0.0
        false_negative_rate = false_negatives / (false_negatives + true_positives) if (false_negatives + true_positives) > 0 else 0.0
        
        return {
            "accuracy": accuracy,
            "precision": precision,
            "recall": recall,
            "false_positive_rate": false_positive_rate,
            "false_negative_rate": false_negative_rate
        }
        
    def _calculate_performance_metrics(self, metrics: Dict[str, Any], runtime_stats: RuntimeStats) -> Dict[str, float]:
        """Calculate system performance metrics"""
        aggregations = metrics.get("aggregations", {})
        
        # Get peak TPS
        transaction_aggregations = aggregations.get("transactions_per_second", {})
        peak_tps = transaction_aggregations.get("peak_1min", 0.0)
        
        # Get resource usage
        gauges = metrics.get("gauges", {})
        memory_usage = gauges.get("memory_usage_mb", 0.0)
        cpu_usage = gauges.get("cpu_usage_percent", 0.0)
        
        return {
            "peak_tps": peak_tps,
            "memory_usage_mb": memory_usage,
            "cpu_usage_percent": cpu_usage
        }
        
    def _generate_recommendations(self, runtime_stats: RuntimeStats, nexum_stats: Dict[str, Any],
                                bastion_stats: Dict[str, Any], fraud_metrics: Dict[str, float]) -> List[str]:
        """Generate optimization recommendations"""
        recommendations = []
        
        # Performance recommendations
        if runtime_stats.actual_tps < 10:
            recommendations.append("Consider increasing speed multiplier for higher transaction throughput")
            
        if runtime_stats.errors > runtime_stats.transactions_processed * 0.01:
            recommendations.append("High error rate detected - check API connectivity and configuration")
            
        # API performance recommendations
        avg_nexum_latency = nexum_stats.get("average_latency_ms", 0)
        if avg_nexum_latency > 100:
            recommendations.append("Nexum API latency is high - consider optimizing database queries or scaling")
            
        avg_bastion_latency = bastion_stats.get("average_scoring_latency_ms", 0)
        if avg_bastion_latency > 50:
            recommendations.append("Bastion scoring latency is high - consider model optimization or caching")
            
        # Fraud detection recommendations
        if fraud_metrics["false_positive_rate"] > 0.05:
            recommendations.append("High false positive rate - consider tuning fraud detection thresholds")
            
        if fraud_metrics["false_negative_rate"] > 0.1:
            recommendations.append("High false negative rate - consider enhancing fraud detection rules")
            
        if fraud_metrics["precision"] < 0.8:
            recommendations.append("Low precision in fraud detection - review and optimize detection models")
            
        # Scalability recommendations
        if runtime_stats.customers_created > 1000:
            recommendations.append("Large simulation completed successfully - system handles high customer volumes well")
        else:
            recommendations.append("Consider testing with larger customer counts to validate scalability")
            
        if not recommendations:
            recommendations.append("Simulation completed successfully with good performance metrics")
            
        return recommendations
        
    def save_report(self, report: SimulationReport, format: str = "json") -> Path:
        """Save report to file"""
        timestamp = report.start_time.strftime("%Y%m%d_%H%M%S")
        
        if format == "json":
            filename = f"simulation_report_{timestamp}.json"
            filepath = self.output_dir / filename
            
            with open(filepath, 'w') as f:
                json.dump(report.to_dict(), f, indent=2, default=str)
                
        elif format == "csv":
            filename = f"simulation_report_{timestamp}.csv"
            filepath = self.output_dir / filename
            
            # Flatten the report for CSV
            flattened = self._flatten_report(report)
            
            with open(filepath, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["Metric", "Value"])
                for key, value in flattened.items():
                    writer.writerow([key, value])
                    
        else:
            raise ValueError(f"Unsupported format: {format}")
            
        return filepath
        
    def _flatten_report(self, report: SimulationReport) -> Dict[str, Any]:
        """Flatten report structure for CSV export"""
        flattened = {}
        report_dict = report.to_dict()
        
        for key, value in report_dict.items():
            if isinstance(value, dict):
                for sub_key, sub_value in value.items():
                    flattened[f"{key}.{sub_key}"] = sub_value
            elif isinstance(value, list):
                flattened[key] = "; ".join(str(item) for item in value)
            else:
                flattened[key] = value
                
        return flattened
        
    def generate_html_report(self, report: SimulationReport) -> str:
        """Generate HTML report"""
        html_template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Banking Simulation Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; line-height: 1.6; }
        .header { background: #f4f4f4; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
        .section { margin-bottom: 30px; }
        .metrics-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; }
        .metric-card { background: #f9f9f9; padding: 15px; border-radius: 6px; text-align: center; }
        .metric-value { font-size: 24px; font-weight: bold; color: #333; }
        .metric-label { font-size: 12px; color: #666; text-transform: uppercase; }
        .recommendations { background: #e8f5e8; padding: 15px; border-radius: 6px; }
        .recommendations ul { margin: 0; padding-left: 20px; }
        table { width: 100%; border-collapse: collapse; margin-top: 10px; }
        th, td { text-align: left; padding: 8px; border-bottom: 1px solid #ddd; }
        th { background-color: #f2f2f2; }
    </style>
</head>
<body>
    <div class="header">
        <h1>Banking Simulation Report</h1>
        <p><strong>Simulation:</strong> {simulation_name}</p>
        <p><strong>Duration:</strong> {duration:.1f} seconds</p>
        <p><strong>Period:</strong> {start_time} to {end_time}</p>
    </div>
    
    <div class="section">
        <h2>Overview</h2>
        <div class="metrics-grid">
            <div class="metric-card">
                <div class="metric-value">{customers_created}</div>
                <div class="metric-label">Customers Created</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{accounts_created}</div>
                <div class="metric-label">Accounts Created</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{transactions_processed}</div>
                <div class="metric-label">Transactions Processed</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{fraud_transactions}</div>
                <div class="metric-label">Fraud Transactions</div>
            </div>
        </div>
    </div>
    
    <div class="section">
        <h2>Performance</h2>
        <div class="metrics-grid">
            <div class="metric-card">
                <div class="metric-value">{average_tps:.1f}</div>
                <div class="metric-label">Average TPS</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{peak_tps:.1f}</div>
                <div class="metric-label">Peak TPS</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{nexum_avg_latency:.0f}ms</div>
                <div class="metric-label">Nexum Latency</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{bastion_avg_latency:.0f}ms</div>
                <div class="metric-label">Bastion Latency</div>
            </div>
        </div>
    </div>
    
    <div class="section">
        <h2>Fraud Detection</h2>
        <div class="metrics-grid">
            <div class="metric-card">
                <div class="metric-value">{accuracy:.1%}</div>
                <div class="metric-label">Accuracy</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{precision:.1%}</div>
                <div class="metric-label">Precision</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{recall:.1%}</div>
                <div class="metric-label">Recall</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{false_positive_rate:.1%}</div>
                <div class="metric-label">False Positive Rate</div>
            </div>
        </div>
    </div>
    
    <div class="section recommendations">
        <h2>Recommendations</h2>
        <ul>
            {recommendations_html}
        </ul>
    </div>
</body>
</html>
"""
        
        recommendations_html = "".join(f"<li>{rec}</li>" for rec in report.recommendations)
        
        return html_template.format(
            simulation_name=report.simulation_name,
            duration=report.duration_seconds,
            start_time=report.start_time.strftime("%Y-%m-%d %H:%M:%S"),
            end_time=report.end_time.strftime("%Y-%m-%d %H:%M:%S"),
            customers_created=report.customers_created,
            accounts_created=report.accounts_created,
            transactions_processed=report.transactions_processed,
            fraud_transactions=report.fraud_transactions,
            average_tps=report.average_tps,
            peak_tps=report.peak_tps,
            nexum_avg_latency=report.nexum_stats.get("average_latency_ms", 0),
            bastion_avg_latency=report.bastion_stats.get("average_scoring_latency_ms", 0),
            accuracy=report.fraud_detection_accuracy,
            precision=report.precision,
            recall=report.recall,
            false_positive_rate=report.false_positive_rate,
            recommendations_html=recommendations_html
        )
        
    def save_html_report(self, report: SimulationReport) -> Path:
        """Save HTML report to file"""
        html_content = self.generate_html_report(report)
        timestamp = report.start_time.strftime("%Y%m%d_%H%M%S")
        filename = f"simulation_report_{timestamp}.html"
        filepath = self.output_dir / filename
        
        with open(filepath, 'w') as f:
            f.write(html_content)
            
        return filepath