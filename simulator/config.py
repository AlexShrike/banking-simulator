"""Configuration management for the banking simulator.

Provides pydantic models for all simulation settings including
scenarios, connection settings, and runtime options.
"""

from decimal import Decimal
from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field, validator
from datetime import datetime


class ConnectionConfig(BaseModel):
    """Configuration for external service connections"""
    nexum_url: str = "http://localhost:8090"
    bastion_url: str = "http://localhost:8080" 
    kafka_bootstrap_servers: Optional[str] = None
    auth_enabled: bool = False
    jwt_token: Optional[str] = None
    timeout_seconds: int = 30
    max_retries: int = 3
    
    
class DashboardConfig(BaseModel):
    """Configuration for the real-time dashboard"""
    enabled: bool = True
    port: int = 8095
    host: str = "0.0.0.0"
    websocket_path: str = "/ws"
    static_path: str = "simulator/dashboard/static"
    

class MetricsConfig(BaseModel):
    """Configuration for metrics collection"""
    enabled: bool = True
    collect_interval_seconds: int = 1
    retention_minutes: int = 60
    export_csv: bool = False
    export_path: Optional[str] = None
    

class TransactionRateConfig(BaseModel):
    """Configuration for transaction generation rates"""
    peak_tps: int = 10
    off_peak_tps: int = 2
    business_hours: List[int] = Field(default=[8, 18])  # 8am-6pm
    weekend_multiplier: float = 0.3
    
    @validator("business_hours")
    def validate_business_hours(cls, v):
        if len(v) != 2 or v[0] >= v[1] or v[0] < 0 or v[1] > 24:
            raise ValueError("business_hours must be [start_hour, end_hour] with 0 <= start < end <= 24")
        return v


class FraudPatternConfig(BaseModel):
    """Configuration for a fraud attack pattern"""
    type: str = Field(..., description="Fraud pattern type")
    weight: float = Field(default=1.0, ge=0.0, le=1.0)
    count: Optional[int] = None
    duration_minutes: Optional[int] = None
    intensity: float = Field(default=1.0, ge=0.1, le=10.0)
    follows: Optional[str] = None  # Run after this pattern
    delay_minutes: Optional[int] = None
    
    # Pattern-specific settings
    amounts: Optional[List[float]] = None
    hops: Optional[int] = None
    threshold: Optional[float] = None
    split_into: Optional[List[float]] = None


class FraudConfig(BaseModel):
    """Configuration for fraud generation"""
    rate: float = Field(default=0.001, ge=0.0, le=1.0, description="Fraud rate (0.0-1.0)")
    patterns: List[FraudPatternConfig] = Field(default_factory=list)
    attack_window: Optional[List[int]] = None  # [start_hour, end_hour]
    geographic_focus: Optional[List[str]] = None  # Countries for fraud focus
    

class SimulationConfig(BaseModel):
    """Main configuration for the banking simulator"""
    # Basic simulation settings
    name: str = "Banking Simulation"
    description: str = "Default simulation scenario"
    duration_hours: int = Field(default=24, gt=0)
    speed_multiplier: float = Field(default=100.0, gt=0.0)
    
    # Customer and account settings
    customers: int = Field(default=500, gt=0)
    accounts_per_customer: int = Field(default=2, gt=0, le=10)
    initial_balance: float = Field(default=5000.0, ge=0.0)
    currency: str = "USD"
    
    # Transaction generation
    transaction_rate: TransactionRateConfig = Field(default_factory=TransactionRateConfig)
    
    # Fraud settings
    fraud: FraudConfig = Field(default_factory=FraudConfig)
    
    # Special scenario settings
    new_customers: Optional[int] = None
    kyc_approval_rate: Optional[float] = Field(None, ge=0.0, le=1.0)
    first_transaction_delay_hours: Optional[List[int]] = None
    mule_accounts: Optional[int] = None
    legitimate_accounts: Optional[int] = None
    
    # External connections
    connections: ConnectionConfig = Field(default_factory=ConnectionConfig)
    
    # Dashboard and metrics
    dashboard: DashboardConfig = Field(default_factory=DashboardConfig)
    metrics: MetricsConfig = Field(default_factory=MetricsConfig)
    
    # Runtime options
    dry_run: bool = False
    verbose: bool = False
    seed: Optional[int] = None  # For reproducible runs
    
    @validator("speed_multiplier")
    def validate_speed_multiplier(cls, v):
        if v > 10000:
            raise ValueError("speed_multiplier cannot exceed 10000x")
        return v
    
    @property
    def simulation_duration_seconds(self) -> float:
        """Get actual simulation duration in seconds based on speed multiplier"""
        return (self.duration_hours * 3600) / self.speed_multiplier
    
    @property
    def effective_tps(self) -> float:
        """Get effective transactions per second during peak times"""
        return self.transaction_rate.peak_tps * self.speed_multiplier


class RuntimeStats(BaseModel):
    """Runtime statistics for the simulation"""
    start_time: datetime
    end_time: Optional[datetime] = None
    customers_created: int = 0
    accounts_created: int = 0
    transactions_generated: int = 0
    transactions_processed: int = 0
    fraud_transactions: int = 0
    nexum_api_calls: int = 0
    bastion_api_calls: int = 0
    errors: int = 0
    average_latency_ms: float = 0.0
    
    @property
    def duration_seconds(self) -> float:
        """Get simulation duration in seconds"""
        end = self.end_time or datetime.now()
        return (end - self.start_time).total_seconds()
    
    @property
    def actual_tps(self) -> float:
        """Get actual transactions per second achieved"""
        if self.duration_seconds > 0:
            return self.transactions_processed / self.duration_seconds
        return 0.0