"""Scenario management for the banking simulator.

Provides loading of scenarios from YAML files and pre-built scenario definitions.
Scenarios define complete simulation parameters including transaction patterns,
fraud rates, customer behavior, and timing.
"""

import os
import yaml
from typing import Dict, List, Optional
from pathlib import Path

from .config import SimulationConfig, TransactionRateConfig, FraudConfig, FraudPatternConfig


class ScenarioLoader:
    """Loads simulation scenarios from YAML files"""
    
    def __init__(self, scenarios_dir: str = "scenarios"):
        self.scenarios_dir = Path(scenarios_dir)
        
    def load_scenario(self, scenario_name: str) -> SimulationConfig:
        """Load a scenario by name or file path"""
        if scenario_name.endswith('.yaml') or scenario_name.endswith('.yml'):
            # Treat as file path
            scenario_path = Path(scenario_name)
        else:
            # Treat as scenario name - look in scenarios directory
            scenario_path = self.scenarios_dir / f"{scenario_name}.yaml"
            
        if not scenario_path.exists():
            raise FileNotFoundError(f"Scenario file not found: {scenario_path}")
            
        with open(scenario_path, 'r') as f:
            data = yaml.safe_load(f)
            
        return self._parse_scenario_data(data)
    
    def list_scenarios(self) -> List[str]:
        """List available scenarios in the scenarios directory"""
        if not self.scenarios_dir.exists():
            return []
            
        scenarios = []
        for file_path in self.scenarios_dir.glob("*.yaml"):
            scenarios.append(file_path.stem)
            
        return sorted(scenarios)
    
    def _parse_scenario_data(self, data: dict) -> SimulationConfig:
        """Parse scenario data dict into SimulationConfig"""
        # Convert transaction_rate if present
        if 'transaction_rate' in data:
            rate_data = data['transaction_rate']
            data['transaction_rate'] = TransactionRateConfig(**rate_data)
            
        # Convert fraud config if present
        if 'fraud' in data:
            fraud_data = data['fraud']
            if 'patterns' in fraud_data:
                patterns = [FraudPatternConfig(**p) for p in fraud_data['patterns']]
                fraud_data['patterns'] = patterns
            data['fraud'] = FraudConfig(**fraud_data)
            
        return SimulationConfig(**data)


# Pre-built scenario definitions
BUILTIN_SCENARIOS = {
    "normal_day": {
        "name": "Normal Business Day",
        "description": "Typical day with 10K transactions, 0.1% fraud rate",
        "duration_hours": 24,
        "speed_multiplier": 100,
        "customers": 500,
        "accounts_per_customer": 2,
        "initial_balance": 5000.0,
        "transaction_rate": {
            "peak_tps": 10,
            "off_peak_tps": 2,
            "business_hours": [8, 18],
            "weekend_multiplier": 0.3
        },
        "fraud": {
            "rate": 0.001,
            "patterns": [
                {"type": "card_testing", "weight": 0.3},
                {"type": "velocity_attack", "weight": 0.2},
                {"type": "large_amount", "weight": 0.3},
                {"type": "unusual_location", "weight": 0.2}
            ]
        }
    },
    
    "fraud_attack": {
        "name": "Coordinated Fraud Attack",
        "description": "Card testing attack at 2am followed by large fraudulent transfers",
        "duration_hours": 4,
        "speed_multiplier": 50,
        "customers": 200,
        "accounts_per_customer": 2,
        "initial_balance": 10000.0,
        "transaction_rate": {
            "peak_tps": 20,
            "off_peak_tps": 5,
            "business_hours": [2, 4],  # Attack window
        },
        "fraud": {
            "rate": 0.15,  # 15% fraud rate during attack
            "attack_window": [2, 3],  # 2am-3am
            "patterns": [
                {
                    "type": "card_testing",
                    "count": 500,
                    "duration_minutes": 10,
                    "weight": 0.6
                },
                {
                    "type": "account_takeover", 
                    "count": 20,
                    "follows": "card_testing",
                    "delay_minutes": 30,
                    "weight": 0.4
                }
            ]
        }
    },
    
    "peak_load": {
        "name": "Black Friday Peak Load",
        "description": "Extreme transaction volume — stress test",
        "duration_hours": 8,
        "speed_multiplier": 200,
        "customers": 1000,
        "accounts_per_customer": 3,
        "initial_balance": 15000.0,
        "transaction_rate": {
            "peak_tps": 100,
            "off_peak_tps": 50,
            "business_hours": [6, 22],  # Extended hours
        },
        "fraud": {
            "rate": 0.005,  # Slightly higher fraud during peak shopping
            "patterns": [
                {"type": "card_testing", "weight": 0.4},
                {"type": "online_fraud", "weight": 0.6}
            ]
        }
    },
    
    "mule_network": {
        "name": "Money Mule Network",
        "description": "Detect circular transfers and layering",
        "duration_hours": 72,
        "speed_multiplier": 500,
        "customers": 50,
        "mule_accounts": 20,
        "legitimate_accounts": 30,
        "initial_balance": 25000.0,
        "fraud": {
            "rate": 0.3,  # High fraud rate for mule detection
            "patterns": [
                {
                    "type": "layering",
                    "hops": 5,
                    "amounts": [1000, 5000, 10000],
                    "weight": 0.6
                },
                {
                    "type": "structuring",
                    "threshold": 10000,
                    "split_into": [4500, 4800, 4700],
                    "weight": 0.4
                }
            ]
        }
    },
    
    "onboarding": {
        "name": "Customer Onboarding Wave",
        "description": "100 new customers, KYC verification, first transactions",
        "duration_hours": 48,
        "speed_multiplier": 200,
        "new_customers": 100,
        "customers": 100,  # All new
        "accounts_per_customer": 1,
        "kyc_approval_rate": 0.85,
        "first_transaction_delay_hours": [1, 24],
        "initial_balance": 1000.0,
        "transaction_rate": {
            "peak_tps": 5,
            "off_peak_tps": 1,
            "business_hours": [9, 17],
        },
        "fraud": {
            "rate": 0.05,  # 5% identity theft attempts
            "patterns": [
                {"type": "synthetic_identity", "weight": 0.6},
                {"type": "identity_theft", "weight": 0.4}
            ]
        }
    },
    
    "regression_test": {
        "name": "Regression Test Suite",
        "description": "Comprehensive test covering all transaction types",
        "duration_hours": 12,
        "speed_multiplier": 300,
        "customers": 100,
        "accounts_per_customer": 4,  # Savings, checking, credit, loan
        "initial_balance": 20000.0,
        "transaction_rate": {
            "peak_tps": 25,
            "off_peak_tps": 10,
            "business_hours": [0, 24],  # Around the clock
        },
        "fraud": {
            "rate": 0.02,  # Cover all fraud patterns
            "patterns": [
                {"type": "card_testing", "weight": 0.15},
                {"type": "velocity_attack", "weight": 0.15},
                {"type": "large_amount", "weight": 0.15},
                {"type": "unusual_location", "weight": 0.15},
                {"type": "account_takeover", "weight": 0.10},
                {"type": "layering", "weight": 0.10},
                {"type": "structuring", "weight": 0.10},
                {"type": "synthetic_identity", "weight": 0.10}
            ]
        }
    }
}


def get_builtin_scenario(name: str) -> SimulationConfig:
    """Get a built-in scenario by name"""
    if name not in BUILTIN_SCENARIOS:
        available = ", ".join(BUILTIN_SCENARIOS.keys())
        raise ValueError(f"Unknown built-in scenario: {name}. Available: {available}")
        
    data = BUILTIN_SCENARIOS[name].copy()
    loader = ScenarioLoader()
    return loader._parse_scenario_data(data)


def create_scenario_file(scenario_name: str, config: SimulationConfig, output_dir: str = "scenarios"):
    """Create a YAML scenario file from a SimulationConfig"""
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    # Convert config to dict, handling special types
    data = config.dict()
    
    # Write to YAML file
    scenario_file = output_path / f"{scenario_name}.yaml"
    with open(scenario_file, 'w') as f:
        yaml.safe_dump(data, f, default_flow_style=False, sort_keys=False, indent=2)
        
    return scenario_file