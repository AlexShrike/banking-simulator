"""Fraud pattern generator for banking simulation.

Generates various types of fraud attacks and suspicious transactions
for testing fraud detection systems. Includes coordinated attacks,
money laundering patterns, and individual fraud scenarios.
"""

import random
import math
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple, Set
from enum import Enum
from dataclasses import dataclass, field
from decimal import Decimal

from .customers import CustomerProfile
from .transactions import PendingTransaction, TransactionChannel, TransactionType


class FraudType(Enum):
    """Types of fraud patterns"""
    # Card fraud
    CARD_TESTING = "card_testing"           # Small transactions to test stolen cards
    VELOCITY_ATTACK = "velocity_attack"     # Rapid succession of transactions
    LARGE_AMOUNT = "large_amount"           # Unusually large transactions
    
    # Account fraud
    ACCOUNT_TAKEOVER = "account_takeover"   # Login from unusual location + transfers
    SYNTHETIC_IDENTITY = "synthetic_identity"  # Fake identity creation
    IDENTITY_THEFT = "identity_theft"       # Using stolen real identity
    
    # Money laundering patterns
    LAYERING = "layering"                   # Complex transfer chains
    STRUCTURING = "structuring"             # Breaking large amounts into smaller ones
    SMURFING = "smurfing"                   # Multiple people making small deposits
    
    # Network fraud
    MULE_NETWORK = "mule_network"           # Coordinated money mule operations
    BUST_OUT = "bust_out"                   # Build credit then disappear
    
    # Digital fraud
    ONLINE_FRAUD = "online_fraud"           # Fraudulent online purchases
    UNUSUAL_LOCATION = "unusual_location"   # Transactions from unexpected locations
    
    # Business fraud
    MERCHANT_FRAUD = "merchant_fraud"       # Fake merchant transactions
    REFUND_FRAUD = "refund_fraud"           # Fraudulent refund requests


@dataclass
class FraudProfile:
    """Profile of a fraudulent entity"""
    fraud_id: str
    fraud_type: FraudType
    customer_ids: List[str]  # Compromised or fake customers
    account_ids: List[str]   # Target accounts
    start_time: datetime
    duration_minutes: int
    intensity: float = 1.0   # How aggressive the attack is
    success_rate: float = 0.7  # How many transactions succeed
    sophistication: float = 0.5  # How sophisticated (0=obvious, 1=subtle)
    metadata: Dict[str, any] = field(default_factory=dict)
    
    @property
    def end_time(self) -> datetime:
        return self.start_time + timedelta(minutes=self.duration_minutes)


@dataclass
class FraudNetwork:
    """A network of connected fraud entities"""
    network_id: str
    fraud_profiles: List[FraudProfile]
    connection_strength: float  # How tightly connected
    coordination_level: float   # How coordinated their actions are
    
    def get_active_profiles(self, current_time: datetime) -> List[FraudProfile]:
        """Get fraud profiles active at current time"""
        return [
            profile for profile in self.fraud_profiles
            if profile.start_time <= current_time <= profile.end_time
        ]


class FraudGenerator:
    """Generates various fraud patterns for testing"""
    
    def __init__(self, seed: Optional[int] = None):
        if seed is not None:
            random.seed(seed)
            
        self._initialize_fraud_templates()
        self._active_fraud_profiles: List[FraudProfile] = []
        self._fraud_networks: List[FraudNetwork] = []
        
    def _initialize_fraud_templates(self):
        """Initialize templates for different fraud types"""
        # Define typical patterns for each fraud type
        self.fraud_patterns = {
            FraudType.CARD_TESTING: {
                "transaction_count": (10, 50),
                "amount_range": (0.01, 5.00),
                "time_window_minutes": (5, 30),
                "preferred_channels": [TransactionChannel.CARD, TransactionChannel.ONLINE],
                "merchant_categories": ["small_retail", "online", "gas_station"],
                "geographic_spread": False,
                "detection_difficulty": 0.2  # Easy to detect
            },
            
            FraudType.VELOCITY_ATTACK: {
                "transaction_count": (20, 100),
                "amount_range": (50, 500),
                "time_window_minutes": (1, 10),
                "preferred_channels": [TransactionChannel.CARD, TransactionChannel.ATM],
                "burst_pattern": True,
                "detection_difficulty": 0.3
            },
            
            FraudType.LARGE_AMOUNT: {
                "transaction_count": (1, 5),
                "amount_range": (5000, 50000),
                "time_window_minutes": (10, 120),
                "preferred_channels": [TransactionChannel.WIRE, TransactionChannel.ONLINE],
                "timing": "outside_normal_hours",
                "detection_difficulty": 0.6
            },
            
            FraudType.ACCOUNT_TAKEOVER: {
                "phases": [
                    {"type": "reconnaissance", "duration_minutes": (30, 180)},
                    {"type": "small_test", "transaction_count": (2, 5), "amount_range": (10, 100)},
                    {"type": "drain_account", "transaction_count": (3, 10), "amount_range": (1000, 10000)}
                ],
                "location_change": True,
                "device_change": True,
                "detection_difficulty": 0.5
            },
            
            FraudType.LAYERING: {
                "hops": (3, 10),
                "amount_range": (1000, 25000),
                "time_between_hops_minutes": (10, 60),
                "account_types_used": ["checking", "savings", "business"],
                "obfuscation_techniques": ["amount_variation", "timing_variation"],
                "detection_difficulty": 0.8
            },
            
            FraudType.STRUCTURING: {
                "target_amount": (10000, 50000),  # Amount being structured
                "individual_amount_max": 9999,    # Stay below reporting thresholds
                "transaction_count": (3, 20),
                "time_spread_hours": (1, 168),    # Up to 1 week
                "detection_difficulty": 0.7
            },
            
            FraudType.SYNTHETIC_IDENTITY: {
                "buildup_period_days": (30, 180),  # Build legitimate-looking history
                "initial_transactions": (10, 50),
                "bust_out_amount": (5000, 100000),
                "detection_difficulty": 0.9  # Very hard to detect initially
            },
            
            FraudType.MULE_NETWORK: {
                "mule_count": (5, 20),
                "coordination_pattern": "hub_and_spoke",  # or "chain", "circular"
                "transaction_amount": (2000, 15000),
                "layering_depth": (2, 5),
                "detection_difficulty": 0.8
            }
        }
        
        # Suspicious locations for geographic fraud
        self.suspicious_locations = [
            {"country": "RU", "city": "Moscow", "risk_score": 0.9},
            {"country": "NG", "city": "Lagos", "risk_score": 0.8},
            {"country": "RO", "city": "Bucharest", "risk_score": 0.7},
            {"country": "CN", "city": "Shanghai", "risk_score": 0.6},
            {"country": "BR", "city": "São Paulo", "risk_score": 0.5},
            {"country": "PH", "city": "Manila", "risk_score": 0.7},
            {"country": "VN", "city": "Ho Chi Minh City", "risk_score": 0.6},
        ]
        
    def generate_fraud_attack(self, fraud_type: FraudType, target_customers: List[CustomerProfile],
                            account_mapping: Dict[str, List[str]], start_time: datetime,
                            intensity: float = 1.0, **kwargs) -> FraudProfile:
        """Generate a specific fraud attack"""
        fraud_id = f"FRAUD_{int(start_time.timestamp())}_{random.randint(1000, 9999)}"
        
        if fraud_type == FraudType.CARD_TESTING:
            return self._generate_card_testing(fraud_id, target_customers, account_mapping, start_time, intensity)
        elif fraud_type == FraudType.VELOCITY_ATTACK:
            return self._generate_velocity_attack(fraud_id, target_customers, account_mapping, start_time, intensity)
        elif fraud_type == FraudType.LARGE_AMOUNT:
            return self._generate_large_amount_fraud(fraud_id, target_customers, account_mapping, start_time, intensity)
        elif fraud_type == FraudType.ACCOUNT_TAKEOVER:
            return self._generate_account_takeover(fraud_id, target_customers, account_mapping, start_time, intensity)
        elif fraud_type == FraudType.LAYERING:
            return self._generate_layering_attack(fraud_id, target_customers, account_mapping, start_time, intensity, **kwargs)
        elif fraud_type == FraudType.STRUCTURING:
            return self._generate_structuring_attack(fraud_id, target_customers, account_mapping, start_time, intensity, **kwargs)
        elif fraud_type == FraudType.UNUSUAL_LOCATION:
            return self._generate_unusual_location_fraud(fraud_id, target_customers, account_mapping, start_time, intensity)
        else:
            # Generic fraud pattern
            return self._generate_generic_fraud(fraud_id, fraud_type, target_customers, account_mapping, start_time, intensity)
            
    def _generate_card_testing(self, fraud_id: str, customers: List[CustomerProfile],
                              account_mapping: Dict[str, List[str]], start_time: datetime, intensity: float) -> FraudProfile:
        """Generate card testing fraud pattern"""
        pattern = self.fraud_patterns[FraudType.CARD_TESTING]
        
        # Select random customer as victim
        target_customer = random.choice(customers)
        target_accounts = account_mapping[target_customer.customer_id]
        
        transaction_count = random.randint(*pattern["transaction_count"])
        transaction_count = int(transaction_count * intensity)
        
        duration_minutes = random.randint(*pattern["time_window_minutes"])
        
        return FraudProfile(
            fraud_id=fraud_id,
            fraud_type=FraudType.CARD_TESTING,
            customer_ids=[target_customer.customer_id],
            account_ids=target_accounts,
            start_time=start_time,
            duration_minutes=duration_minutes,
            intensity=intensity,
            success_rate=0.6,  # Many will be declined
            sophistication=0.2,
            metadata={
                "transaction_count": transaction_count,
                "amount_range": pattern["amount_range"],
                "preferred_channels": pattern["preferred_channels"],
                "merchant_categories": pattern["merchant_categories"]
            }
        )
        
    def _generate_velocity_attack(self, fraud_id: str, customers: List[CustomerProfile],
                                 account_mapping: Dict[str, List[str]], start_time: datetime, intensity: float) -> FraudProfile:
        """Generate velocity attack fraud pattern"""
        pattern = self.fraud_patterns[FraudType.VELOCITY_ATTACK]
        
        target_customer = random.choice(customers)
        target_accounts = account_mapping[target_customer.customer_id]
        
        transaction_count = random.randint(*pattern["transaction_count"])
        transaction_count = int(transaction_count * intensity)
        
        # Very short time window for velocity attacks
        duration_minutes = random.randint(*pattern["time_window_minutes"])
        
        return FraudProfile(
            fraud_id=fraud_id,
            fraud_type=FraudType.VELOCITY_ATTACK,
            customer_ids=[target_customer.customer_id],
            account_ids=target_accounts,
            start_time=start_time,
            duration_minutes=duration_minutes,
            intensity=intensity,
            success_rate=0.4,  # High velocity should trigger blocks
            sophistication=0.3,
            metadata={
                "transaction_count": transaction_count,
                "amount_range": pattern["amount_range"],
                "burst_pattern": True,
                "preferred_channels": pattern["preferred_channels"]
            }
        )
        
    def _generate_large_amount_fraud(self, fraud_id: str, customers: List[CustomerProfile],
                                   account_mapping: Dict[str, List[str]], start_time: datetime, intensity: float) -> FraudProfile:
        """Generate large amount fraud pattern"""
        pattern = self.fraud_patterns[FraudType.LARGE_AMOUNT]
        
        # Target customers with higher balances
        high_value_customers = [c for c in customers if c.income_level.value in ["high", "ultra_high"]]
        target_customer = random.choice(high_value_customers if high_value_customers else customers)
        
        return FraudProfile(
            fraud_id=fraud_id,
            fraud_type=FraudType.LARGE_AMOUNT,
            customer_ids=[target_customer.customer_id],
            account_ids=account_mapping[target_customer.customer_id],
            start_time=start_time,
            duration_minutes=random.randint(*pattern["time_window_minutes"]),
            intensity=intensity,
            success_rate=0.3,  # Large amounts should be scrutinized
            sophistication=0.6,
            metadata={
                "transaction_count": random.randint(*pattern["transaction_count"]),
                "amount_range": pattern["amount_range"],
                "timing": "outside_normal_hours",
                "preferred_channels": pattern["preferred_channels"]
            }
        )
        
    def _generate_account_takeover(self, fraud_id: str, customers: List[CustomerProfile],
                                  account_mapping: Dict[str, List[str]], start_time: datetime, intensity: float) -> FraudProfile:
        """Generate account takeover fraud pattern"""
        target_customer = random.choice(customers)
        
        # Account takeover happens in phases
        total_duration = random.randint(120, 480)  # 2-8 hours
        
        return FraudProfile(
            fraud_id=fraud_id,
            fraud_type=FraudType.ACCOUNT_TAKEOVER,
            customer_ids=[target_customer.customer_id],
            account_ids=account_mapping[target_customer.customer_id],
            start_time=start_time,
            duration_minutes=total_duration,
            intensity=intensity,
            success_rate=0.5,
            sophistication=0.7,
            metadata={
                "phases": self.fraud_patterns[FraudType.ACCOUNT_TAKEOVER]["phases"],
                "location_change": True,
                "device_change": True,
                "suspicious_location": random.choice(self.suspicious_locations)
            }
        )
        
    def _generate_layering_attack(self, fraud_id: str, customers: List[CustomerProfile],
                                 account_mapping: Dict[str, List[str]], start_time: datetime, intensity: float, **kwargs) -> FraudProfile:
        """Generate money laundering layering pattern"""
        # Select multiple customers to participate in layering
        num_customers = min(kwargs.get("hops", 5), len(customers))
        involved_customers = random.sample(customers, num_customers)
        
        all_accounts = []
        for customer in involved_customers:
            all_accounts.extend(account_mapping[customer.customer_id])
            
        hops = kwargs.get("hops", random.randint(3, num_customers))
        amounts = kwargs.get("amounts", [random.uniform(1000, 25000) for _ in range(hops)])
        
        return FraudProfile(
            fraud_id=fraud_id,
            fraud_type=FraudType.LAYERING,
            customer_ids=[c.customer_id for c in involved_customers],
            account_ids=all_accounts,
            start_time=start_time,
            duration_minutes=random.randint(60, 480),  # 1-8 hours
            intensity=intensity,
            success_rate=0.8,  # Individual transactions look normal
            sophistication=0.9,
            metadata={
                "hops": hops,
                "amounts": amounts,
                "obfuscation_techniques": ["timing_variation", "amount_variation"],
                "layering_pattern": "complex"
            }
        )
        
    def _generate_structuring_attack(self, fraud_id: str, customers: List[CustomerProfile],
                                    account_mapping: Dict[str, List[str]], start_time: datetime, intensity: float, **kwargs) -> FraudProfile:
        """Generate structuring (smurfing) fraud pattern"""
        target_amount = kwargs.get("threshold", random.uniform(10000, 50000))
        individual_max = kwargs.get("split_into", [9999])[0] if "split_into" in kwargs else 9999
        
        # Calculate how many transactions needed
        transaction_count = math.ceil(target_amount / individual_max)
        
        # Select customer(s) - could be one customer or multiple
        if random.random() < 0.7:  # 70% single customer
            involved_customers = [random.choice(customers)]
        else:  # 30% multiple customers (smurfing)
            num_customers = min(random.randint(2, 5), len(customers))
            involved_customers = random.sample(customers, num_customers)
            
        all_accounts = []
        for customer in involved_customers:
            all_accounts.extend(account_mapping[customer.customer_id])
            
        return FraudProfile(
            fraud_id=fraud_id,
            fraud_type=FraudType.STRUCTURING,
            customer_ids=[c.customer_id for c in involved_customers],
            account_ids=all_accounts,
            start_time=start_time,
            duration_minutes=random.randint(60, 10080),  # 1 hour to 1 week
            intensity=intensity,
            success_rate=0.9,  # Individual transactions under threshold
            sophistication=0.8,
            metadata={
                "target_amount": target_amount,
                "individual_max": individual_max,
                "transaction_count": transaction_count,
                "is_smurfing": len(involved_customers) > 1
            }
        )
        
    def _generate_unusual_location_fraud(self, fraud_id: str, customers: List[CustomerProfile],
                                       account_mapping: Dict[str, List[str]], start_time: datetime, intensity: float) -> FraudProfile:
        """Generate transactions from suspicious locations"""
        target_customer = random.choice(customers)
        suspicious_location = random.choice(self.suspicious_locations)
        
        return FraudProfile(
            fraud_id=fraud_id,
            fraud_type=FraudType.UNUSUAL_LOCATION,
            customer_ids=[target_customer.customer_id],
            account_ids=account_mapping[target_customer.customer_id],
            start_time=start_time,
            duration_minutes=random.randint(30, 240),  # 30 minutes to 4 hours
            intensity=intensity,
            success_rate=0.6,
            sophistication=0.4,
            metadata={
                "suspicious_location": suspicious_location,
                "transaction_count": random.randint(2, 10),
                "amount_range": (100, 2000),
                "geographic_anomaly": True
            }
        )
        
    def _generate_generic_fraud(self, fraud_id: str, fraud_type: FraudType, customers: List[CustomerProfile],
                              account_mapping: Dict[str, List[str]], start_time: datetime, intensity: float) -> FraudProfile:
        """Generate a generic fraud pattern"""
        target_customer = random.choice(customers)
        
        return FraudProfile(
            fraud_id=fraud_id,
            fraud_type=fraud_type,
            customer_ids=[target_customer.customer_id],
            account_ids=account_mapping[target_customer.customer_id],
            start_time=start_time,
            duration_minutes=random.randint(30, 180),
            intensity=intensity,
            success_rate=0.5,
            sophistication=0.5,
            metadata={"pattern": "generic"}
        )
        
    def generate_fraud_transactions(self, fraud_profile: FraudProfile, current_time: datetime) -> List[PendingTransaction]:
        """Generate fraudulent transactions for an active fraud profile"""
        if current_time < fraud_profile.start_time or current_time > fraud_profile.end_time:
            return []
            
        transactions = []
        
        if fraud_profile.fraud_type == FraudType.CARD_TESTING:
            transactions = self._generate_card_testing_transactions(fraud_profile, current_time)
        elif fraud_profile.fraud_type == FraudType.VELOCITY_ATTACK:
            transactions = self._generate_velocity_transactions(fraud_profile, current_time)
        elif fraud_profile.fraud_type == FraudType.LARGE_AMOUNT:
            transactions = self._generate_large_amount_transactions(fraud_profile, current_time)
        elif fraud_profile.fraud_type == FraudType.ACCOUNT_TAKEOVER:
            transactions = self._generate_account_takeover_transactions(fraud_profile, current_time)
        elif fraud_profile.fraud_type == FraudType.LAYERING:
            transactions = self._generate_layering_transactions(fraud_profile, current_time)
        elif fraud_profile.fraud_type == FraudType.STRUCTURING:
            transactions = self._generate_structuring_transactions(fraud_profile, current_time)
        elif fraud_profile.fraud_type == FraudType.UNUSUAL_LOCATION:
            transactions = self._generate_unusual_location_transactions(fraud_profile, current_time)
        else:
            transactions = self._generate_generic_fraud_transactions(fraud_profile, current_time)
            
        # Mark all transactions as fraudulent
        for txn in transactions:
            txn.metadata["is_fraud"] = True
            txn.metadata["fraud_type"] = fraud_profile.fraud_type.value
            txn.metadata["fraud_id"] = fraud_profile.fraud_id
            txn.metadata["sophistication"] = fraud_profile.sophistication
            
        return transactions
        
    def _generate_card_testing_transactions(self, fraud_profile: FraudProfile, current_time: datetime) -> List[PendingTransaction]:
        """Generate card testing transactions"""
        transactions = []
        metadata = fraud_profile.metadata
        
        # Generate small test transactions
        for i in range(metadata["transaction_count"]):
            if random.random() > fraud_profile.success_rate:
                continue  # Transaction would be declined
                
            amount = random.uniform(*metadata["amount_range"])
            channel = random.choice(metadata["preferred_channels"])
            
            # Small random time offset within the attack window
            time_offset = random.randint(0, fraud_profile.duration_minutes)
            txn_time = fraud_profile.start_time + timedelta(minutes=time_offset)
            
            transaction = PendingTransaction(
                transaction_type=TransactionType.ONLINE_PURCHASE,
                amount=round(amount, 2),
                currency="USD",
                description=f"Card Test Transaction #{i+1}",
                channel=channel,
                from_account_id=random.choice(fraud_profile.account_ids),
                to_account_id=None,
                merchant_id=f"TEST_MERCHANT_{random.randint(1000, 9999)}",
                merchant_category=random.choice(metadata["merchant_categories"]),
                reference=f"CARDTEST_{fraud_profile.fraud_id}_{i+1}",
                timestamp=txn_time,
                metadata={
                    "fraud_pattern": "card_testing",
                    "test_sequence": i + 1,
                    "rapid_succession": True
                }
            )
            
            transactions.append(transaction)
            
        return transactions
        
    def _generate_velocity_transactions(self, fraud_profile: FraudProfile, current_time: datetime) -> List[PendingTransaction]:
        """Generate velocity attack transactions"""
        transactions = []
        metadata = fraud_profile.metadata
        
        # Generate burst of transactions in short time window
        for i in range(metadata["transaction_count"]):
            if random.random() > fraud_profile.success_rate:
                continue
                
            amount = random.uniform(*metadata["amount_range"])
            
            # Very tight timing - all within minutes
            time_offset_seconds = random.randint(0, fraud_profile.duration_minutes * 60)
            txn_time = fraud_profile.start_time + timedelta(seconds=time_offset_seconds)
            
            transaction = PendingTransaction(
                transaction_type=TransactionType.WITHDRAWAL,
                amount=round(amount, 2),
                currency="USD",
                description=f"Rapid Transaction #{i+1}",
                channel=random.choice(metadata["preferred_channels"]),
                from_account_id=random.choice(fraud_profile.account_ids),
                to_account_id=None,
                merchant_id=None,
                merchant_category=None,
                reference=f"VELOCITY_{fraud_profile.fraud_id}_{i+1}",
                timestamp=txn_time,
                metadata={
                    "fraud_pattern": "velocity_attack",
                    "burst_sequence": i + 1,
                    "time_window_minutes": fraud_profile.duration_minutes
                }
            )
            
            transactions.append(transaction)
            
        return transactions
        
    def _generate_large_amount_transactions(self, fraud_profile: FraudProfile, current_time: datetime) -> List[PendingTransaction]:
        """Generate large amount fraud transactions"""
        transactions = []
        metadata = fraud_profile.metadata
        
        # Generate 1-3 large transactions
        for i in range(metadata["transaction_count"]):
            if random.random() > fraud_profile.success_rate:
                continue
                
            amount = random.uniform(*metadata["amount_range"])
            
            # Random time within fraud window
            time_offset_minutes = random.randint(0, fraud_profile.duration_minutes)
            txn_time = fraud_profile.start_time + timedelta(minutes=time_offset_minutes)
            
            transaction = PendingTransaction(
                transaction_type=TransactionType.TRANSFER,
                amount=round(amount, 2),
                currency="USD",
                description=f"Large Amount Transfer #{i+1}",
                channel=random.choice([TransactionChannel.WIRE, TransactionChannel.ONLINE]),
                from_account_id=random.choice(fraud_profile.account_ids),
                to_account_id=None,  # External transfer
                merchant_id=None,
                merchant_category=None,
                reference=f"LARGE_{fraud_profile.fraud_id}_{i+1}",
                timestamp=txn_time,
                metadata={
                    "fraud_pattern": "large_amount",
                    "amount_threshold_breach": amount > 10000,
                    "unusual_timing": metadata.get("timing") == "outside_normal_hours"
                }
            )
            
            transactions.append(transaction)
            
        return transactions
        
    def _generate_account_takeover_transactions(self, fraud_profile: FraudProfile, current_time: datetime) -> List[PendingTransaction]:
        """Generate account takeover fraud transactions"""
        transactions = []
        metadata = fraud_profile.metadata
        phases = metadata["phases"]
        
        # Determine which phase we're in based on time elapsed
        elapsed_minutes = (current_time - fraud_profile.start_time).total_seconds() / 60
        
        current_phase = None
        cumulative_duration = 0
        
        for phase in phases:
            phase_duration = phase.get("duration_minutes", (30, 180))
            if isinstance(phase_duration, tuple):
                duration = random.randint(*phase_duration)
            else:
                duration = phase_duration
                
            if elapsed_minutes <= cumulative_duration + duration:
                current_phase = phase
                break
            cumulative_duration += duration
            
        if not current_phase:
            return transactions
            
        # Generate transactions based on current phase
        if current_phase["type"] == "small_test":
            # Small test transactions
            for i in range(current_phase.get("transaction_count", random.randint(2, 5))):
                amount = random.uniform(*current_phase.get("amount_range", (10, 100)))
                
                transaction = PendingTransaction(
                    transaction_type=TransactionType.WITHDRAWAL,
                    amount=round(amount, 2),
                    currency="USD",
                    description=f"Test Transaction #{i+1}",
                    channel=TransactionChannel.ONLINE,
                    from_account_id=random.choice(fraud_profile.account_ids),
                    to_account_id=None,
                    merchant_id=None,
                    merchant_category=None,
                    reference=f"ATO_TEST_{fraud_profile.fraud_id}_{i+1}",
                    timestamp=current_time,
                    metadata={
                        "fraud_pattern": "account_takeover",
                        "phase": "testing",
                        "location_change": metadata.get("location_change", False),
                        "device_change": metadata.get("device_change", False)
                    }
                )
                
                transactions.append(transaction)
                
        elif current_phase["type"] == "drain_account":
            # Large drain transactions
            for i in range(current_phase.get("transaction_count", random.randint(3, 10))):
                amount = random.uniform(*current_phase.get("amount_range", (1000, 10000)))
                
                transaction = PendingTransaction(
                    transaction_type=TransactionType.TRANSFER,
                    amount=round(amount, 2),
                    currency="USD",
                    description=f"Account Drain #{i+1}",
                    channel=TransactionChannel.ONLINE,
                    from_account_id=random.choice(fraud_profile.account_ids),
                    to_account_id=None,  # External transfer
                    merchant_id=None,
                    merchant_category=None,
                    reference=f"ATO_DRAIN_{fraud_profile.fraud_id}_{i+1}",
                    timestamp=current_time,
                    metadata={
                        "fraud_pattern": "account_takeover",
                        "phase": "draining",
                        "location_change": True,
                        "device_change": True,
                        "suspicious_location": metadata.get("suspicious_location")
                    }
                )
                
                transactions.append(transaction)
                
        return transactions
        
    def _generate_layering_transactions(self, fraud_profile: FraudProfile, current_time: datetime) -> List[PendingTransaction]:
        """Generate money laundering layering transactions"""
        transactions = []
        metadata = fraud_profile.metadata
        
        accounts = fraud_profile.account_ids.copy()
        random.shuffle(accounts)
        
        for hop in range(metadata["hops"]):
            if hop >= len(accounts) - 1:
                break
                
            from_account = accounts[hop]
            to_account = accounts[hop + 1]
            amount = metadata["amounts"][hop] if hop < len(metadata["amounts"]) else random.uniform(1000, 25000)
            
            # Add some variation to amounts to obfuscate
            amount_variation = random.uniform(-0.1, 0.1)
            amount = amount * (1 + amount_variation)
            
            # Vary timing between hops
            time_offset_minutes = hop * random.randint(10, 60)
            txn_time = fraud_profile.start_time + timedelta(minutes=time_offset_minutes)
            
            transaction = PendingTransaction(
                transaction_type=TransactionType.TRANSFER,
                amount=round(amount, 2),
                currency="USD",
                description=f"Layer Transfer {hop+1}",
                channel=random.choice([TransactionChannel.ONLINE, TransactionChannel.WIRE]),
                from_account_id=from_account,
                to_account_id=to_account,
                merchant_id=None,
                merchant_category=None,
                reference=f"LAYER_{fraud_profile.fraud_id}_{hop+1}",
                timestamp=txn_time,
                metadata={
                    "fraud_pattern": "layering",
                    "hop_sequence": hop + 1,
                    "total_hops": metadata["hops"],
                    "obfuscation": "amount_timing_variation"
                }
            )
            
            transactions.append(transaction)
            
        return transactions
        
    def _generate_structuring_transactions(self, fraud_profile: FraudProfile, current_time: datetime) -> List[PendingTransaction]:
        """Generate structuring (breaking up large amounts) transactions"""
        transactions = []
        metadata = fraud_profile.metadata
        
        target_amount = metadata["target_amount"]
        individual_max = metadata["individual_max"]
        remaining_amount = target_amount
        
        sequence = 0
        while remaining_amount > 0 and sequence < metadata["transaction_count"]:
            # Amount just under threshold, with some variation
            amount = min(remaining_amount, random.uniform(individual_max * 0.8, individual_max))
            remaining_amount -= amount
            sequence += 1
            
            # Spread transactions over time
            time_offset_hours = random.randint(0, fraud_profile.duration_minutes // 60)
            txn_time = fraud_profile.start_time + timedelta(hours=time_offset_hours)
            
            # Pick random account if smurfing across multiple accounts
            from_account = random.choice(fraud_profile.account_ids)
            
            transaction = PendingTransaction(
                transaction_type=TransactionType.DEPOSIT,
                amount=round(amount, 2),
                currency="USD",
                description=f"Structured Deposit {sequence}",
                channel=random.choice([TransactionChannel.BRANCH, TransactionChannel.ATM]),
                from_account_id=None,  # External deposit
                to_account_id=from_account,
                merchant_id=None,
                merchant_category=None,
                reference=f"STRUCT_{fraud_profile.fraud_id}_{sequence}",
                timestamp=txn_time,
                metadata={
                    "fraud_pattern": "structuring",
                    "sequence": sequence,
                    "target_total": target_amount,
                    "under_threshold": amount < individual_max
                }
            )
            
            transactions.append(transaction)
            
        return transactions
        
    def _generate_unusual_location_transactions(self, fraud_profile: FraudProfile, current_time: datetime) -> List[PendingTransaction]:
        """Generate transactions from unusual locations"""
        transactions = []
        metadata = fraud_profile.metadata
        suspicious_location = metadata["suspicious_location"]
        
        for i in range(metadata["transaction_count"]):
            amount = random.uniform(*metadata["amount_range"])
            
            time_offset = random.randint(0, fraud_profile.duration_minutes)
            txn_time = fraud_profile.start_time + timedelta(minutes=time_offset)
            
            transaction = PendingTransaction(
                transaction_type=TransactionType.SHOPPING,
                amount=round(amount, 2),
                currency="USD",
                description=f"International Purchase {i+1}",
                channel=TransactionChannel.CARD,
                from_account_id=random.choice(fraud_profile.account_ids),
                to_account_id=None,
                merchant_id=f"INTL_MERCHANT_{random.randint(1000, 9999)}",
                merchant_category="international",
                reference=f"UNUSUAL_LOC_{fraud_profile.fraud_id}_{i+1}",
                timestamp=txn_time,
                metadata={
                    "fraud_pattern": "unusual_location",
                    "transaction_country": suspicious_location["country"],
                    "transaction_city": suspicious_location["city"],
                    "location_risk_score": suspicious_location["risk_score"],
                    "geographic_anomaly": True
                }
            )
            
            transactions.append(transaction)
            
        return transactions
        
    def _generate_generic_fraud_transactions(self, fraud_profile: FraudProfile, current_time: datetime) -> List[PendingTransaction]:
        """Generate generic fraudulent transactions"""
        transactions = []
        
        # Generate 2-5 suspicious transactions
        for i in range(random.randint(2, 5)):
            amount = random.uniform(100, 5000)
            
            transaction = PendingTransaction(
                transaction_type=TransactionType.WITHDRAWAL,
                amount=round(amount, 2),
                currency="USD",
                description=f"Suspicious Transaction {i+1}",
                channel=random.choice([TransactionChannel.ONLINE, TransactionChannel.CARD]),
                from_account_id=random.choice(fraud_profile.account_ids),
                to_account_id=None,
                merchant_id=None,
                merchant_category=None,
                reference=f"GENERIC_{fraud_profile.fraud_id}_{i+1}",
                timestamp=current_time,
                metadata={
                    "fraud_pattern": "generic_suspicious",
                    "anomaly_score": random.uniform(0.6, 1.0)
                }
            )
            
            transactions.append(transaction)
            
        return transactions
        
    def create_fraud_network(self, network_type: str, customers: List[CustomerProfile],
                           account_mapping: Dict[str, List[str]], start_time: datetime) -> FraudNetwork:
        """Create a coordinated fraud network"""
        network_id = f"NET_{int(start_time.timestamp())}_{random.randint(100, 999)}"
        
        if network_type == "mule_network":
            return self._create_mule_network(network_id, customers, account_mapping, start_time)
        elif network_type == "synthetic_identity_ring":
            return self._create_synthetic_identity_ring(network_id, customers, account_mapping, start_time)
        else:
            # Generic coordinated fraud
            return self._create_generic_network(network_id, customers, account_mapping, start_time)
            
    def _create_mule_network(self, network_id: str, customers: List[CustomerProfile],
                           account_mapping: Dict[str, List[str]], start_time: datetime) -> FraudNetwork:
        """Create a money mule network"""
        # Select 5-15 customers as mules
        mule_count = random.randint(5, min(15, len(customers)))
        mule_customers = random.sample(customers, mule_count)
        
        fraud_profiles = []
        
        # Create layering fraud profiles connecting the mules
        for i in range(mule_count - 1):
            fraud_profile = self._generate_layering_attack(
                fraud_id=f"{network_id}_LAYER_{i}",
                customers=mule_customers[i:i+3],  # Overlapping groups
                account_mapping=account_mapping,
                start_time=start_time + timedelta(hours=i),  # Staggered start times
                intensity=1.5,
                hops=random.randint(3, 5)
            )
            fraud_profiles.append(fraud_profile)
            
        return FraudNetwork(
            network_id=network_id,
            fraud_profiles=fraud_profiles,
            connection_strength=0.8,
            coordination_level=0.9
        )
        
    def _create_synthetic_identity_ring(self, network_id: str, customers: List[CustomerProfile],
                                      account_mapping: Dict[str, List[str]], start_time: datetime) -> FraudNetwork:
        """Create synthetic identity fraud ring"""
        # Select customers with newer accounts (synthetic identities)
        synthetic_customers = random.sample(customers, min(8, len(customers)))
        
        fraud_profiles = []
        
        for i, customer in enumerate(synthetic_customers):
            # Each synthetic identity runs a bust-out scheme
            fraud_profile = FraudProfile(
                fraud_id=f"{network_id}_SYNTH_{i}",
                fraud_type=FraudType.SYNTHETIC_IDENTITY,
                customer_ids=[customer.customer_id],
                account_ids=account_mapping[customer.customer_id],
                start_time=start_time + timedelta(days=i),  # Coordinated but not simultaneous
                duration_minutes=random.randint(480, 1440),  # 8-24 hours
                intensity=1.0,
                success_rate=0.8,
                sophistication=0.95,
                metadata={
                    "buildup_complete": True,  # Assume identity was built up previously
                    "bust_out_amount": random.uniform(10000, 100000),
                    "coordination_group": network_id
                }
            )
            fraud_profiles.append(fraud_profile)
            
        return FraudNetwork(
            network_id=network_id,
            fraud_profiles=fraud_profiles,
            connection_strength=0.6,  # Loosely connected
            coordination_level=0.8    # Well coordinated timing
        )
        
    def _create_generic_network(self, network_id: str, customers: List[CustomerProfile],
                              account_mapping: Dict[str, List[str]], start_time: datetime) -> FraudNetwork:
        """Create a generic coordinated fraud network"""
        network_customers = random.sample(customers, min(6, len(customers)))
        
        fraud_profiles = []
        fraud_types = [FraudType.VELOCITY_ATTACK, FraudType.LARGE_AMOUNT, FraudType.ACCOUNT_TAKEOVER]
        
        for i, customer in enumerate(network_customers):
            fraud_type = random.choice(fraud_types)
            fraud_profile = self.generate_fraud_attack(
                fraud_type=fraud_type,
                target_customers=[customer],
                account_mapping=account_mapping,
                start_time=start_time + timedelta(minutes=i*30),  # Staggered attacks
                intensity=1.2
            )
            fraud_profile.fraud_id = f"{network_id}_COORD_{i}"
            fraud_profiles.append(fraud_profile)
            
        return FraudNetwork(
            network_id=network_id,
            fraud_profiles=fraud_profiles,
            connection_strength=0.5,
            coordination_level=0.7
        )
        
    def get_active_fraud_profiles(self, current_time: datetime) -> List[FraudProfile]:
        """Get all fraud profiles active at current time"""
        active_profiles = []
        
        # Individual fraud profiles
        for profile in self._active_fraud_profiles:
            if profile.start_time <= current_time <= profile.end_time:
                active_profiles.append(profile)
                
        # Network fraud profiles
        for network in self._fraud_networks:
            active_profiles.extend(network.get_active_profiles(current_time))
            
        return active_profiles
        
    def add_fraud_profile(self, fraud_profile: FraudProfile):
        """Add a fraud profile to active tracking"""
        self._active_fraud_profiles.append(fraud_profile)
        
    def add_fraud_network(self, fraud_network: FraudNetwork):
        """Add a fraud network to active tracking"""
        self._fraud_networks.append(fraud_network)
        
    def estimate_fraud_volume(self, fraud_rate: float, total_transactions: int, intensity_multiplier: float = 1.0) -> int:
        """Estimate number of fraudulent transactions for simulation planning"""
        base_fraud_count = int(total_transactions * fraud_rate)
        return int(base_fraud_count * intensity_multiplier)