"""Life event generator for banking simulation.

Generates realistic life events that trigger behavioral changes in customers,
such as address changes, new device logins, travel, job changes, etc.
These events affect customer transaction patterns and risk profiles.
"""

import random
from datetime import datetime, timedelta, date
from typing import List, Dict, Optional, Tuple
from enum import Enum
from dataclasses import dataclass

from .customers import CustomerProfile, CustomerLifeStage, IncomeLevel


class EventType(Enum):
    """Types of life events that affect banking behavior"""
    ADDRESS_CHANGE = "address_change"
    NEW_DEVICE_LOGIN = "new_device_login"  
    TRAVEL_DOMESTIC = "travel_domestic"
    TRAVEL_INTERNATIONAL = "travel_international"
    JOB_CHANGE = "job_change"
    INCOME_CHANGE = "income_change"
    MARRIAGE = "marriage"
    DIVORCE = "divorce"
    NEW_BABY = "new_baby"
    HOME_PURCHASE = "home_purchase"
    RETIREMENT = "retirement"
    MEDICAL_EMERGENCY = "medical_emergency"
    ACCOUNT_COMPROMISE = "account_compromise"  # Customer reports fraud
    DEVICE_THEFT = "device_theft"
    IDENTITY_MONITORING_ALERT = "identity_monitoring_alert"


class EventImpact(Enum):
    """Impact levels of life events"""
    LOW = "low"           # Minor behavioral changes
    MEDIUM = "medium"     # Moderate behavioral changes
    HIGH = "high"         # Significant behavioral changes
    CRITICAL = "critical" # Major life disruption


@dataclass
class LifeEvent:
    """A life event affecting a customer"""
    event_id: str
    event_type: EventType
    customer_id: str
    event_date: datetime
    impact_level: EventImpact
    duration_days: int  # How long the impact lasts
    
    # Event-specific details
    details: Dict[str, any]
    
    # Behavioral changes
    transaction_frequency_multiplier: float = 1.0
    spending_pattern_change: Optional[str] = None
    risk_score_adjustment: float = 0.0
    new_locations: List[str] = None
    channel_preferences: Optional[List[str]] = None
    
    @property
    def end_date(self) -> datetime:
        return self.event_date + timedelta(days=self.duration_days)
        
    def is_active(self, current_time: datetime) -> bool:
        """Check if event is currently affecting customer behavior"""
        return self.event_date <= current_time <= self.end_date


class LifeEventGenerator:
    """Generates realistic life events for customers"""
    
    def __init__(self, seed: Optional[int] = None):
        if seed is not None:
            random.seed(seed)
            
        self._initialize_event_patterns()
        
    def _initialize_event_patterns(self):
        """Initialize event patterns and probabilities"""
        # Event probabilities per customer per year by life stage
        self.event_probabilities = {
            CustomerLifeStage.STUDENT: {
                EventType.ADDRESS_CHANGE: 0.4,          # Moving for school/internships
                EventType.NEW_DEVICE_LOGIN: 0.8,        # New devices frequently
                EventType.TRAVEL_DOMESTIC: 0.3,
                EventType.TRAVEL_INTERNATIONAL: 0.1,
                EventType.JOB_CHANGE: 0.6,              # Part-time jobs
                EventType.INCOME_CHANGE: 0.5,
                EventType.DEVICE_THEFT: 0.05,
            },
            
            CustomerLifeStage.YOUNG_PROFESSIONAL: {
                EventType.ADDRESS_CHANGE: 0.25,
                EventType.NEW_DEVICE_LOGIN: 0.6,
                EventType.TRAVEL_DOMESTIC: 0.4,
                EventType.TRAVEL_INTERNATIONAL: 0.2,
                EventType.JOB_CHANGE: 0.3,
                EventType.INCOME_CHANGE: 0.4,
                EventType.MARRIAGE: 0.15,
                EventType.HOME_PURCHASE: 0.1,
                EventType.NEW_BABY: 0.1,
                EventType.DEVICE_THEFT: 0.03,
            },
            
            CustomerLifeStage.FAMILY: {
                EventType.ADDRESS_CHANGE: 0.15,
                EventType.NEW_DEVICE_LOGIN: 0.4,
                EventType.TRAVEL_DOMESTIC: 0.5,         # Family vacations
                EventType.TRAVEL_INTERNATIONAL: 0.15,
                EventType.JOB_CHANGE: 0.2,
                EventType.INCOME_CHANGE: 0.3,
                EventType.HOME_PURCHASE: 0.05,
                EventType.NEW_BABY: 0.08,
                EventType.DIVORCE: 0.02,
                EventType.MEDICAL_EMERGENCY: 0.03,
                EventType.DEVICE_THEFT: 0.02,
            },
            
            CustomerLifeStage.ESTABLISHED: {
                EventType.ADDRESS_CHANGE: 0.08,
                EventType.NEW_DEVICE_LOGIN: 0.3,
                EventType.TRAVEL_DOMESTIC: 0.4,
                EventType.TRAVEL_INTERNATIONAL: 0.3,   # More luxury travel
                EventType.JOB_CHANGE: 0.1,
                EventType.INCOME_CHANGE: 0.2,
                EventType.DIVORCE: 0.015,
                EventType.MEDICAL_EMERGENCY: 0.05,
                EventType.RETIREMENT: 0.05,
                EventType.DEVICE_THEFT: 0.015,
            },
            
            CustomerLifeStage.RETIREE: {
                EventType.ADDRESS_CHANGE: 0.05,        # Moving to retirement communities
                EventType.NEW_DEVICE_LOGIN: 0.15,      # Less tech-savvy
                EventType.TRAVEL_DOMESTIC: 0.3,
                EventType.TRAVEL_INTERNATIONAL: 0.2,
                EventType.INCOME_CHANGE: 0.1,          # Fixed income
                EventType.MEDICAL_EMERGENCY: 0.08,
                EventType.DEVICE_THEFT: 0.01,
                EventType.ACCOUNT_COMPROMISE: 0.02,    # More vulnerable to scams
            }
        }
        
        # Travel destinations by region
        self.domestic_destinations = [
            "Las Vegas, NV", "Miami, FL", "Orlando, FL", "Los Angeles, CA",
            "New York, NY", "Chicago, IL", "Seattle, WA", "Denver, CO",
            "Austin, TX", "Boston, MA", "San Francisco, CA", "Portland, OR"
        ]
        
        self.international_destinations = [
            ("London, UK", 0.8), ("Paris, France", 0.9), ("Tokyo, Japan", 0.7),
            ("Toronto, Canada", 0.9), ("Mexico City, Mexico", 0.6),
            ("Amsterdam, Netherlands", 0.8), ("Rome, Italy", 0.8),
            ("Barcelona, Spain", 0.7), ("Sydney, Australia", 0.8),
            ("Bangkok, Thailand", 0.6), ("Dubai, UAE", 0.5),
            ("Mumbai, India", 0.4), ("São Paulo, Brazil", 0.5),
            ("Berlin, Germany", 0.8), ("Seoul, South Korea", 0.7)
        ]
        
    def generate_life_events(self, customer: CustomerProfile, simulation_start: datetime, 
                           duration_days: int) -> List[LifeEvent]:
        """Generate life events for a customer over the simulation period"""
        events = []
        
        # Get event probabilities for this customer's life stage
        probabilities = self.event_probabilities.get(customer.life_stage, {})
        
        # Convert annual probabilities to simulation period probabilities
        simulation_years = duration_days / 365.0
        
        for event_type, annual_prob in probabilities.items():
            simulation_prob = 1 - (1 - annual_prob) ** simulation_years
            
            # Multiple events of same type possible
            while random.random() < simulation_prob:
                event = self._generate_specific_event(
                    event_type, customer, simulation_start, duration_days
                )
                if event:
                    events.append(event)
                simulation_prob *= 0.5  # Reduce probability for additional events
                
        return sorted(events, key=lambda e: e.event_date)
        
    def _generate_specific_event(self, event_type: EventType, customer: CustomerProfile,
                               simulation_start: datetime, duration_days: int) -> Optional[LifeEvent]:
        """Generate a specific type of life event"""
        # Random date during simulation
        event_date = simulation_start + timedelta(days=random.randint(0, duration_days))
        event_id = f"EVENT_{int(event_date.timestamp())}_{random.randint(1000, 9999)}"
        
        if event_type == EventType.ADDRESS_CHANGE:
            return self._generate_address_change(event_id, customer, event_date)
        elif event_type == EventType.NEW_DEVICE_LOGIN:
            return self._generate_new_device_login(event_id, customer, event_date)
        elif event_type == EventType.TRAVEL_DOMESTIC:
            return self._generate_domestic_travel(event_id, customer, event_date)
        elif event_type == EventType.TRAVEL_INTERNATIONAL:
            return self._generate_international_travel(event_id, customer, event_date)
        elif event_type == EventType.JOB_CHANGE:
            return self._generate_job_change(event_id, customer, event_date)
        elif event_type == EventType.INCOME_CHANGE:
            return self._generate_income_change(event_id, customer, event_date)
        elif event_type == EventType.MARRIAGE:
            return self._generate_marriage(event_id, customer, event_date)
        elif event_type == EventType.DIVORCE:
            return self._generate_divorce(event_id, customer, event_date)
        elif event_type == EventType.NEW_BABY:
            return self._generate_new_baby(event_id, customer, event_date)
        elif event_type == EventType.HOME_PURCHASE:
            return self._generate_home_purchase(event_id, customer, event_date)
        elif event_type == EventType.RETIREMENT:
            return self._generate_retirement(event_id, customer, event_date)
        elif event_type == EventType.MEDICAL_EMERGENCY:
            return self._generate_medical_emergency(event_id, customer, event_date)
        elif event_type == EventType.ACCOUNT_COMPROMISE:
            return self._generate_account_compromise(event_id, customer, event_date)
        elif event_type == EventType.DEVICE_THEFT:
            return self._generate_device_theft(event_id, customer, event_date)
        else:
            return self._generate_generic_event(event_id, event_type, customer, event_date)
            
    def _generate_address_change(self, event_id: str, customer: CustomerProfile, event_date: datetime) -> LifeEvent:
        """Generate address change event"""
        # Different reasons for moving
        reasons = ["job_relocation", "family_reasons", "better_housing", "cost_reduction", "life_change"]
        reason = random.choice(reasons)
        
        # New city (could be same state or different)
        if random.random() < 0.7:  # 70% same state
            new_city = f"New City, {customer.state}"
        else:  # 30% different state
            states = ["CA", "NY", "TX", "FL", "IL", "PA", "OH", "GA", "NC", "MI"]
            new_state = random.choice([s for s in states if s != customer.state])
            new_city = f"New City, {new_state}"
            
        return LifeEvent(
            event_id=event_id,
            event_type=EventType.ADDRESS_CHANGE,
            customer_id=customer.customer_id,
            event_date=event_date,
            impact_level=EventImpact.MEDIUM,
            duration_days=30,  # Address verification period
            details={
                "reason": reason,
                "old_address": f"{customer.city}, {customer.state}",
                "new_address": new_city,
                "requires_verification": True
            },
            risk_score_adjustment=0.1,  # Temporary risk increase
            new_locations=[new_city]
        )
        
    def _generate_new_device_login(self, event_id: str, customer: CustomerProfile, event_date: datetime) -> LifeEvent:
        """Generate new device login event"""
        device_types = ["smartphone", "tablet", "laptop", "desktop"]
        device_type = random.choice(device_types)
        
        # Device OS and browser patterns by age
        if customer.age < 35:
            os_choice = random.choice(["iOS", "Android", "macOS", "Windows"])
        else:
            os_choice = random.choice(["iOS", "Android", "Windows", "Windows"])  # More Windows
            
        return LifeEvent(
            event_id=event_id,
            event_type=EventType.NEW_DEVICE_LOGIN,
            customer_id=customer.customer_id,
            event_date=event_date,
            impact_level=EventImpact.LOW,
            duration_days=7,  # New device verification period
            details={
                "device_type": device_type,
                "os": os_choice,
                "location": f"{customer.city}, {customer.state}",
                "requires_verification": True
            },
            risk_score_adjustment=0.05
        )
        
    def _generate_domestic_travel(self, event_id: str, customer: CustomerProfile, event_date: datetime) -> LifeEvent:
        """Generate domestic travel event"""
        destination = random.choice(self.domestic_destinations)
        trip_duration = random.randint(2, 14)  # 2 days to 2 weeks
        
        trip_types = ["vacation", "business", "family_visit", "conference"]
        trip_type = random.choice(trip_types)
        
        return LifeEvent(
            event_id=event_id,
            event_type=EventType.TRAVEL_DOMESTIC,
            customer_id=customer.customer_id,
            event_date=event_date,
            impact_level=EventImpact.LOW,
            duration_days=trip_duration,
            details={
                "destination": destination,
                "trip_type": trip_type,
                "trip_duration": trip_duration
            },
            transaction_frequency_multiplier=1.3,  # More transactions while traveling
            new_locations=[destination],
            channel_preferences=["card", "mobile"]  # Prefer card/mobile while traveling
        )
        
    def _generate_international_travel(self, event_id: str, customer: CustomerProfile, event_date: datetime) -> LifeEvent:
        """Generate international travel event"""
        destination, safety_score = random.choice(self.international_destinations)
        trip_duration = random.randint(3, 21)  # 3 days to 3 weeks
        
        # Risk adjustment based on destination
        risk_adjustment = (1.0 - safety_score) * 0.2
        
        return LifeEvent(
            event_id=event_id,
            event_type=EventType.TRAVEL_INTERNATIONAL,
            customer_id=customer.customer_id,
            event_date=event_date,
            impact_level=EventImpact.MEDIUM,
            duration_days=trip_duration,
            details={
                "destination": destination,
                "safety_score": safety_score,
                "trip_duration": trip_duration,
                "currency_different": True
            },
            transaction_frequency_multiplier=1.5,
            risk_score_adjustment=risk_adjustment,
            new_locations=[destination],
            channel_preferences=["card"]  # Primarily card usage abroad
        )
        
    def _generate_job_change(self, event_id: str, customer: CustomerProfile, event_date: datetime) -> LifeEvent:
        """Generate job change event"""
        change_types = ["promotion", "new_company", "career_change", "layoff", "retirement"]
        
        # Weight by life stage
        if customer.life_stage == CustomerLifeStage.STUDENT:
            change_types = ["new_job", "internship", "part_time"]
        elif customer.life_stage == CustomerLifeStage.RETIREE:
            change_types = ["retirement", "part_time"]
            
        change_type = random.choice(change_types)
        
        # Impact varies by change type
        if change_type in ["promotion", "new_company"]:
            impact = EventImpact.MEDIUM
            income_change = random.uniform(1.1, 1.5)  # 10-50% increase
        elif change_type == "layoff":
            impact = EventImpact.HIGH
            income_change = 0.0  # No income temporarily
        else:
            impact = EventImpact.LOW
            income_change = random.uniform(0.9, 1.1)
            
        return LifeEvent(
            event_id=event_id,
            event_type=EventType.JOB_CHANGE,
            customer_id=customer.customer_id,
            event_date=event_date,
            impact_level=impact,
            duration_days=90,  # Job transition period
            details={
                "change_type": change_type,
                "income_multiplier": income_change
            },
            spending_pattern_change="conservative" if change_type == "layoff" else None,
            transaction_frequency_multiplier=0.7 if change_type == "layoff" else 1.0
        )
        
    def _generate_medical_emergency(self, event_id: str, customer: CustomerProfile, event_date: datetime) -> LifeEvent:
        """Generate medical emergency event"""
        emergency_types = ["surgery", "accident", "illness", "hospitalization"]
        emergency_type = random.choice(emergency_types)
        
        # Severity affects duration and spending
        severity = random.choice(["minor", "moderate", "major"])
        
        if severity == "minor":
            duration = random.randint(3, 14)
            spending_multiplier = 1.2
        elif severity == "moderate": 
            duration = random.randint(14, 60)
            spending_multiplier = 1.8
        else:  # major
            duration = random.randint(30, 180)
            spending_multiplier = 3.0
            
        return LifeEvent(
            event_id=event_id,
            event_type=EventType.MEDICAL_EMERGENCY,
            customer_id=customer.customer_id,
            event_date=event_date,
            impact_level=EventImpact.HIGH,
            duration_days=duration,
            details={
                "emergency_type": emergency_type,
                "severity": severity,
                "spending_multiplier": spending_multiplier
            },
            transaction_frequency_multiplier=spending_multiplier,
            spending_pattern_change="medical_focus"
        )
        
    def _generate_account_compromise(self, event_id: str, customer: CustomerProfile, event_date: datetime) -> LifeEvent:
        """Generate account compromise event"""
        compromise_types = ["phishing", "data_breach", "card_skimming", "social_engineering"]
        compromise_type = random.choice(compromise_types)
        
        return LifeEvent(
            event_id=event_id,
            event_type=EventType.ACCOUNT_COMPROMISE,
            customer_id=customer.customer_id,
            event_date=event_date,
            impact_level=EventImpact.CRITICAL,
            duration_days=14,  # Account recovery period
            details={
                "compromise_type": compromise_type,
                "requires_account_freeze": True,
                "requires_new_cards": True
            },
            risk_score_adjustment=0.8,  # Temporarily very high risk
            transaction_frequency_multiplier=0.1  # Minimal activity during recovery
        )
        
    def _generate_device_theft(self, event_id: str, customer: CustomerProfile, event_date: datetime) -> LifeEvent:
        """Generate device theft event"""
        device_types = ["smartphone", "laptop", "tablet", "wallet_with_cards"]
        device_type = random.choice(device_types)
        
        return LifeEvent(
            event_id=event_id,
            event_type=EventType.DEVICE_THEFT,
            customer_id=customer.customer_id,
            event_date=event_date,
            impact_level=EventImpact.HIGH,
            duration_days=7,  # Recovery period
            details={
                "device_type": device_type,
                "requires_card_replacement": device_type in ["smartphone", "wallet_with_cards"],
                "location": f"{customer.city}, {customer.state}"
            },
            risk_score_adjustment=0.3,
            transaction_frequency_multiplier=0.3,  # Reduced activity until recovery
            channel_preferences=["branch", "online"]  # Avoid mobile/card initially
        )
        
    def _generate_home_purchase(self, event_id: str, customer: CustomerProfile, event_date: datetime) -> LifeEvent:
        """Generate home purchase event"""
        purchase_types = ["first_home", "upgrade", "downsize", "investment"]
        purchase_type = random.choice(purchase_types)
        
        # Home value based on income
        if customer.income_level == IncomeLevel.LOW:
            home_value = random.uniform(150000, 300000)
        elif customer.income_level == IncomeLevel.MEDIUM:
            home_value = random.uniform(250000, 500000)
        elif customer.income_level == IncomeLevel.HIGH:
            home_value = random.uniform(400000, 800000)
        else:  # ULTRA_HIGH
            home_value = random.uniform(600000, 2000000)
            
        return LifeEvent(
            event_id=event_id,
            event_type=EventType.HOME_PURCHASE,
            customer_id=customer.customer_id,
            event_date=event_date,
            impact_level=EventImpact.HIGH,
            duration_days=60,  # Closing and moving process
            details={
                "purchase_type": purchase_type,
                "home_value": home_value,
                "down_payment": home_value * random.uniform(0.1, 0.3)
            },
            transaction_frequency_multiplier=2.0,  # Lots of home-related purchases
            spending_pattern_change="home_focus"
        )
        
    def _generate_generic_event(self, event_id: str, event_type: EventType, 
                              customer: CustomerProfile, event_date: datetime) -> LifeEvent:
        """Generate a generic life event"""
        return LifeEvent(
            event_id=event_id,
            event_type=event_type,
            customer_id=customer.customer_id,
            event_date=event_date,
            impact_level=EventImpact.LOW,
            duration_days=random.randint(1, 30),
            details={"type": "generic"},
            transaction_frequency_multiplier=random.uniform(0.8, 1.2)
        )
        
    def _generate_marriage(self, event_id: str, customer: CustomerProfile, event_date: datetime) -> LifeEvent:
        """Generate marriage event"""
        return LifeEvent(
            event_id=event_id,
            event_type=EventType.MARRIAGE,
            customer_id=customer.customer_id,
            event_date=event_date,
            impact_level=EventImpact.HIGH,
            duration_days=180,  # Wedding planning and adjustment period
            details={
                "requires_name_change": random.random() < 0.7,
                "joint_accounts": True,
                "wedding_expenses": random.uniform(15000, 50000)
            },
            transaction_frequency_multiplier=1.8,  # Wedding expenses
            spending_pattern_change="wedding_focus"
        )
        
    def _generate_divorce(self, event_id: str, customer: CustomerProfile, event_date: datetime) -> LifeEvent:
        """Generate divorce event"""
        return LifeEvent(
            event_id=event_id,
            event_type=EventType.DIVORCE,
            customer_id=customer.customer_id,
            event_date=event_date,
            impact_level=EventImpact.HIGH,
            duration_days=365,  # Long adjustment period
            details={
                "requires_account_separation": True,
                "asset_division": True,
                "legal_costs": random.uniform(5000, 25000)
            },
            transaction_frequency_multiplier=0.7,  # Reduced spending
            spending_pattern_change="conservative"
        )
        
    def _generate_new_baby(self, event_id: str, customer: CustomerProfile, event_date: datetime) -> LifeEvent:
        """Generate new baby event"""
        return LifeEvent(
            event_id=event_id,
            event_type=EventType.NEW_BABY,
            customer_id=customer.customer_id,
            event_date=event_date,
            impact_level=EventImpact.HIGH,
            duration_days=365,  # First year adjustments
            details={
                "medical_expenses": random.uniform(8000, 15000),
                "baby_supplies": True,
                "potential_income_reduction": random.random() < 0.4  # Maternity/paternity leave
            },
            transaction_frequency_multiplier=1.5,  # Baby-related purchases
            spending_pattern_change="family_focus"
        )
        
    def _generate_income_change(self, event_id: str, customer: CustomerProfile, event_date: datetime) -> LifeEvent:
        """Generate income change event"""
        change_types = ["raise", "bonus", "reduction", "second_income", "loss_income"]
        change_type = random.choice(change_types)
        
        if change_type == "raise":
            multiplier = random.uniform(1.05, 1.25)
            impact = EventImpact.MEDIUM
        elif change_type == "bonus":
            multiplier = 1.0  # One-time, doesn't affect base
            impact = EventImpact.LOW
        elif change_type == "reduction":
            multiplier = random.uniform(0.7, 0.95)
            impact = EventImpact.HIGH
        else:
            multiplier = random.uniform(0.9, 1.3)
            impact = EventImpact.MEDIUM
            
        return LifeEvent(
            event_id=event_id,
            event_type=EventType.INCOME_CHANGE,
            customer_id=customer.customer_id,
            event_date=event_date,
            impact_level=impact,
            duration_days=90,  # Adjustment period
            details={
                "change_type": change_type,
                "income_multiplier": multiplier,
                "is_permanent": change_type in ["raise", "reduction", "second_income"]
            },
            transaction_frequency_multiplier=multiplier if change_type != "bonus" else 1.2
        )
        
    def _generate_retirement(self, event_id: str, customer: CustomerProfile, event_date: datetime) -> LifeEvent:
        """Generate retirement event"""
        return LifeEvent(
            event_id=event_id,
            event_type=EventType.RETIREMENT,
            customer_id=customer.customer_id,
            event_date=event_date,
            impact_level=EventImpact.HIGH,
            duration_days=365,  # First year of retirement
            details={
                "retirement_type": random.choice(["full", "partial", "early"]),
                "pension_available": random.random() < 0.4,
                "401k_rollover": True,
                "income_reduction": random.uniform(0.4, 0.8)
            },
            transaction_frequency_multiplier=0.8,
            spending_pattern_change="fixed_income"
        )
        
    def get_active_events(self, customer_id: str, current_time: datetime, events: List[LifeEvent]) -> List[LifeEvent]:
        """Get life events active for a customer at current time"""
        return [
            event for event in events 
            if event.customer_id == customer_id and event.is_active(current_time)
        ]
        
    def apply_event_effects(self, customer: CustomerProfile, active_events: List[LifeEvent]) -> CustomerProfile:
        """Apply cumulative effects of active life events to customer behavior"""
        if not active_events:
            return customer
            
        # Create a copy to avoid modifying original
        modified_customer = customer.__class__(**customer.__dict__)
        
        # Apply cumulative effects
        total_transaction_multiplier = 1.0
        total_risk_adjustment = 0.0
        new_locations = []
        channel_preferences = None
        
        for event in active_events:
            total_transaction_multiplier *= event.transaction_frequency_multiplier
            total_risk_adjustment += event.risk_score_adjustment
            
            if event.new_locations:
                new_locations.extend(event.new_locations)
                
            if event.channel_preferences:
                channel_preferences = event.channel_preferences
                
        # Apply to customer profile
        modified_customer.transaction_frequency *= total_transaction_multiplier
        
        # Store event effects in metadata for transaction generation
        if not hasattr(modified_customer, 'active_events'):
            modified_customer.active_events = active_events
            modified_customer.event_risk_adjustment = total_risk_adjustment
            modified_customer.event_locations = new_locations
            modified_customer.event_channels = channel_preferences
            
        return modified_customer