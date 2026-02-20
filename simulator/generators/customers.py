"""Customer profile generator for realistic banking simulation.

Generates diverse customer profiles with demographics, behavioral patterns,
and risk characteristics that drive transaction generation.
"""

import random
import string
from datetime import datetime, timedelta, date
from typing import List, Dict, Optional, Tuple
from enum import Enum
from dataclasses import dataclass
from faker import Faker

# Initialize faker for realistic data generation
fake = Faker(['en_US', 'es_MX', 'zh_CN', 'hi_IN', 'ar_SA'])


class IncomeLevel(Enum):
    """Customer income levels affecting spending patterns"""
    LOW = "low"           # <$30k - frugal, price-sensitive
    MEDIUM = "medium"     # $30k-$80k - balanced spending
    HIGH = "high"         # $80k-$200k - comfortable spending  
    ULTRA_HIGH = "ultra_high"  # >$200k - luxury spending


class RiskProfile(Enum):
    """Customer risk profiles affecting transaction behavior"""
    LOW_RISK = "low_risk"           # Retirees, stable patterns
    MEDIUM_RISK = "medium_risk"     # Working professionals
    HIGH_RISK = "high_risk"         # Students, gig workers, new immigrants


class BehaviorPattern(Enum):
    """Spending behavior patterns"""
    SAVER = "saver"                 # Minimal spending, high balances
    SPENDER = "spender"             # Regular spending, moderate balances
    IRREGULAR = "irregular"         # Inconsistent patterns
    BUSINESS = "business"           # Business-like transaction patterns


class CustomerLifeStage(Enum):
    """Life stage affecting financial behavior"""
    STUDENT = "student"             # 18-25, low income, irregular
    YOUNG_PROFESSIONAL = "young_professional"  # 25-35, growing income
    FAMILY = "family"               # 35-55, stable income, regular bills
    ESTABLISHED = "established"     # 55-65, peak income, investing
    RETIREE = "retiree"            # 65+, fixed income, conservative


@dataclass
class CustomerProfile:
    """Complete customer profile for simulation"""
    customer_id: str
    first_name: str
    last_name: str
    email: str
    phone: str
    date_of_birth: date
    
    # Address information
    address_line1: str
    city: str
    state: str
    postal_code: str
    country: str
    
    # Demographic and behavior
    income_level: IncomeLevel
    risk_profile: RiskProfile
    behavior_pattern: BehaviorPattern
    life_stage: CustomerLifeStage
    
    # Financial characteristics
    credit_score: int  # 300-850
    monthly_income: float
    monthly_expenses: float
    preferred_balance: float
    
    # Transaction preferences
    primary_channel: str  # online, mobile, atm, branch
    transaction_frequency: float  # transactions per week
    international_activity: bool
    high_risk_tolerance: bool
    
    # Fraud susceptibility factors
    tech_savvy: bool
    fraud_awareness: float  # 0.0-1.0
    social_media_presence: bool
    
    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"
    
    @property
    def age(self) -> int:
        today = date.today()
        return today.year - self.date_of_birth.year - (
            (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
        )
    
    @property
    def risk_score(self) -> float:
        """Calculate synthetic risk score 0.0-1.0"""
        score = 0.0
        
        # Age factor (younger = higher risk)
        if self.age < 25:
            score += 0.3
        elif self.age < 35:
            score += 0.2
        elif self.age > 65:
            score += 0.1
            
        # Income factor (lower income = higher risk)
        if self.income_level == IncomeLevel.LOW:
            score += 0.2
        elif self.income_level == IncomeLevel.ULTRA_HIGH:
            score -= 0.1
            
        # Behavior factor
        if self.behavior_pattern == BehaviorPattern.IRREGULAR:
            score += 0.2
        elif self.behavior_pattern == BehaviorPattern.SAVER:
            score -= 0.1
            
        # Tech and awareness factors
        if not self.tech_savvy:
            score += 0.1
        if self.fraud_awareness < 0.3:
            score += 0.2
            
        return max(0.0, min(1.0, score))


class CustomerGenerator:
    """Generates realistic customer profiles"""
    
    def __init__(self, seed: Optional[int] = None):
        if seed is not None:
            random.seed(seed)
            fake.seed_instance(seed)
            
        # Load realistic data distributions
        self._load_distributions()
        
    def _load_distributions(self):
        """Load realistic demographic distributions"""
        # US metropolitan areas with populations
        self.metro_areas = [
            ("New York", "NY", 8400000),
            ("Los Angeles", "CA", 3900000),
            ("Chicago", "IL", 2700000), 
            ("Houston", "TX", 2300000),
            ("Phoenix", "AZ", 1700000),
            ("Philadelphia", "PA", 1600000),
            ("San Antonio", "TX", 1500000),
            ("San Diego", "CA", 1400000),
            ("Dallas", "TX", 1300000),
            ("San Jose", "CA", 1000000),
            ("Austin", "TX", 950000),
            ("Jacksonville", "FL", 900000),
            ("Fort Worth", "TX", 875000),
            ("Columbus", "OH", 850000),
            ("Charlotte", "NC", 850000),
            ("San Francisco", "CA", 825000),
            ("Indianapolis", "IN", 825000),
            ("Seattle", "WA", 750000),
            ("Denver", "CO", 715000),
            ("Washington", "DC", 700000)
        ]
        
        # International locations for diverse customers
        self.international_locations = [
            ("Toronto", "ON", "CA"),
            ("London", "ENG", "GB"), 
            ("Mumbai", "MH", "IN"),
            ("Mexico City", "DF", "MX"),
            ("Shanghai", "SH", "CN"),
            ("Tokyo", "TK", "JP"),
            ("Lagos", "LA", "NG"),
            ("São Paulo", "SP", "BR"),
            ("Cairo", "C", "EG"),
            ("Sydney", "NSW", "AU")
        ]
        
        # Common company domains for email generation
        self.email_domains = [
            "gmail.com", "yahoo.com", "hotmail.com", "outlook.com",
            "icloud.com", "aol.com", "protonmail.com", "company.com",
            "university.edu", "startup.io", "enterprise.net"
        ]
        
        # Transaction channels with usage patterns
        self.channel_preferences = {
            CustomerLifeStage.STUDENT: ["mobile", "online", "atm"],
            CustomerLifeStage.YOUNG_PROFESSIONAL: ["mobile", "online", "atm"],
            CustomerLifeStage.FAMILY: ["online", "mobile", "branch"],
            CustomerLifeStage.ESTABLISHED: ["online", "branch", "mobile"],
            CustomerLifeStage.RETIREE: ["branch", "online", "atm"]
        }
        
    def generate_customer(self, customer_id: Optional[str] = None) -> CustomerProfile:
        """Generate a single realistic customer profile"""
        if customer_id is None:
            customer_id = self._generate_customer_id()
            
        # Determine life stage first as it affects everything else
        life_stage = self._select_life_stage()
        
        # Generate basic demographics
        first_name = fake.first_name()
        last_name = fake.last_name()
        date_of_birth = self._generate_birth_date(life_stage)
        
        # Select location (90% domestic, 10% international for diversity)
        if random.random() < 0.9:
            city, state, country = self._select_domestic_location()
        else:
            city, state, country = self._select_international_location()
            
        # Generate address
        address_line1 = fake.street_address()
        postal_code = fake.postcode() if country == "US" else fake.postcode()
        
        # Contact information
        phone = fake.phone_number()
        email = self._generate_email(first_name, last_name)
        
        # Financial characteristics based on life stage
        income_level, monthly_income = self._generate_income(life_stage)
        risk_profile = self._generate_risk_profile(life_stage, income_level)
        behavior_pattern = self._generate_behavior_pattern(life_stage, income_level)
        
        # Calculate financial metrics
        credit_score = self._generate_credit_score(life_stage, income_level, risk_profile)
        monthly_expenses = self._generate_expenses(monthly_income, behavior_pattern)
        preferred_balance = self._generate_preferred_balance(monthly_income, behavior_pattern)
        
        # Transaction preferences
        primary_channel = self._select_primary_channel(life_stage)
        transaction_frequency = self._generate_transaction_frequency(behavior_pattern, income_level)
        international_activity = self._generate_international_activity(income_level, life_stage)
        
        # Risk factors
        tech_savvy = self._generate_tech_savvy(life_stage)
        fraud_awareness = self._generate_fraud_awareness(life_stage, tech_savvy)
        social_media_presence = self._generate_social_media_presence(life_stage)
        high_risk_tolerance = self._generate_risk_tolerance(life_stage, income_level)
        
        return CustomerProfile(
            customer_id=customer_id,
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone=phone,
            date_of_birth=date_of_birth,
            address_line1=address_line1,
            city=city,
            state=state,
            postal_code=postal_code,
            country=country,
            income_level=income_level,
            risk_profile=risk_profile,
            behavior_pattern=behavior_pattern,
            life_stage=life_stage,
            credit_score=credit_score,
            monthly_income=monthly_income,
            monthly_expenses=monthly_expenses,
            preferred_balance=preferred_balance,
            primary_channel=primary_channel,
            transaction_frequency=transaction_frequency,
            international_activity=international_activity,
            high_risk_tolerance=high_risk_tolerance,
            tech_savvy=tech_savvy,
            fraud_awareness=fraud_awareness,
            social_media_presence=social_media_presence
        )
        
    def generate_customers(self, count: int) -> List[CustomerProfile]:
        """Generate multiple customer profiles"""
        return [self.generate_customer() for _ in range(count)]
        
    def _generate_customer_id(self) -> str:
        """Generate unique customer ID"""
        timestamp = int(datetime.now().timestamp() * 1000)
        random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
        return f"CUST_{timestamp}_{random_part}"
        
    def _select_life_stage(self) -> CustomerLifeStage:
        """Select life stage with realistic distribution"""
        weights = [0.15, 0.25, 0.30, 0.20, 0.10]  # Student, Young Prof, Family, Established, Retiree
        return random.choices(list(CustomerLifeStage), weights=weights)[0]
        
    def _generate_birth_date(self, life_stage: CustomerLifeStage) -> date:
        """Generate birth date appropriate for life stage"""
        today = date.today()
        
        if life_stage == CustomerLifeStage.STUDENT:
            age_range = (18, 25)
        elif life_stage == CustomerLifeStage.YOUNG_PROFESSIONAL:
            age_range = (25, 35)
        elif life_stage == CustomerLifeStage.FAMILY:
            age_range = (35, 55)
        elif life_stage == CustomerLifeStage.ESTABLISHED:
            age_range = (55, 65)
        else:  # RETIREE
            age_range = (65, 85)
            
        age = random.randint(*age_range)
        birth_year = today.year - age
        birth_month = random.randint(1, 12)
        
        # Handle leap years and month boundaries
        if birth_month == 2:
            birth_day = random.randint(1, 28)
        elif birth_month in [4, 6, 9, 11]:
            birth_day = random.randint(1, 30)
        else:
            birth_day = random.randint(1, 31)
            
        return date(birth_year, birth_month, birth_day)
        
    def _select_domestic_location(self) -> Tuple[str, str, str]:
        """Select US metropolitan area weighted by population"""
        total_pop = sum(area[2] for area in self.metro_areas)
        r = random.uniform(0, total_pop)
        
        current = 0
        for city, state, population in self.metro_areas:
            current += population
            if r <= current:
                return city, state, "US"
                
        # Fallback
        return "New York", "NY", "US"
        
    def _select_international_location(self) -> Tuple[str, str, str]:
        """Select international location"""
        return random.choice(self.international_locations)
        
    def _generate_email(self, first_name: str, last_name: str) -> str:
        """Generate realistic email address"""
        domain = random.choice(self.email_domains)
        
        # Common email patterns
        patterns = [
            f"{first_name.lower()}.{last_name.lower()}",
            f"{first_name.lower()}{last_name.lower()}",
            f"{first_name.lower()}{random.randint(1, 999)}",
            f"{first_name[0].lower()}{last_name.lower()}",
            f"{first_name.lower()}.{last_name[0].lower()}{random.randint(1, 99)}"
        ]
        
        username = random.choice(patterns)
        return f"{username}@{domain}"
        
    def _generate_income(self, life_stage: CustomerLifeStage) -> Tuple[IncomeLevel, float]:
        """Generate income level and amount based on life stage"""
        # Income distributions by life stage (in USD annually)
        income_ranges = {
            CustomerLifeStage.STUDENT: {
                IncomeLevel.LOW: (15000, 25000, 0.8),      # Part-time jobs
                IncomeLevel.MEDIUM: (25000, 40000, 0.2),    # Full-time + school
            },
            CustomerLifeStage.YOUNG_PROFESSIONAL: {
                IncomeLevel.LOW: (30000, 45000, 0.2),
                IncomeLevel.MEDIUM: (45000, 75000, 0.6),
                IncomeLevel.HIGH: (75000, 120000, 0.2),
            },
            CustomerLifeStage.FAMILY: {
                IncomeLevel.MEDIUM: (50000, 85000, 0.4),
                IncomeLevel.HIGH: (85000, 150000, 0.5),
                IncomeLevel.ULTRA_HIGH: (150000, 300000, 0.1),
            },
            CustomerLifeStage.ESTABLISHED: {
                IncomeLevel.HIGH: (80000, 180000, 0.6),
                IncomeLevel.ULTRA_HIGH: (180000, 500000, 0.4),
            },
            CustomerLifeStage.RETIREE: {
                IncomeLevel.LOW: (20000, 35000, 0.3),       # Social Security only
                IncomeLevel.MEDIUM: (35000, 65000, 0.5),    # Pension + SS
                IncomeLevel.HIGH: (65000, 120000, 0.2),     # Good savings
            }
        }
        
        stage_ranges = income_ranges[life_stage]
        levels = list(stage_ranges.keys())
        weights = [stage_ranges[level][2] for level in levels]
        
        selected_level = random.choices(levels, weights=weights)[0]
        min_income, max_income, _ = stage_ranges[selected_level]
        annual_income = random.uniform(min_income, max_income)
        
        return selected_level, annual_income / 12  # Return monthly income
        
    def _generate_risk_profile(self, life_stage: CustomerLifeStage, income_level: IncomeLevel) -> RiskProfile:
        """Generate risk profile based on demographics"""
        if life_stage == CustomerLifeStage.STUDENT:
            return random.choices([RiskProfile.HIGH_RISK, RiskProfile.MEDIUM_RISK], weights=[0.7, 0.3])[0]
        elif life_stage == CustomerLifeStage.RETIREE:
            return random.choices([RiskProfile.LOW_RISK, RiskProfile.MEDIUM_RISK], weights=[0.8, 0.2])[0]
        elif income_level == IncomeLevel.ULTRA_HIGH:
            return random.choices([RiskProfile.LOW_RISK, RiskProfile.MEDIUM_RISK], weights=[0.6, 0.4])[0]
        else:
            return random.choices(list(RiskProfile), weights=[0.2, 0.6, 0.2])[0]
            
    def _generate_behavior_pattern(self, life_stage: CustomerLifeStage, income_level: IncomeLevel) -> BehaviorPattern:
        """Generate spending behavior pattern"""
        if life_stage == CustomerLifeStage.STUDENT:
            return random.choices([BehaviorPattern.IRREGULAR, BehaviorPattern.SAVER], weights=[0.7, 0.3])[0]
        elif life_stage == CustomerLifeStage.RETIREE:
            return random.choices([BehaviorPattern.SAVER, BehaviorPattern.SPENDER], weights=[0.6, 0.4])[0]
        elif income_level == IncomeLevel.ULTRA_HIGH:
            return random.choices([BehaviorPattern.SPENDER, BehaviorPattern.BUSINESS], weights=[0.7, 0.3])[0]
        else:
            return random.choices(list(BehaviorPattern), weights=[0.2, 0.5, 0.2, 0.1])[0]
            
    def _generate_credit_score(self, life_stage: CustomerLifeStage, income_level: IncomeLevel, risk_profile: RiskProfile) -> int:
        """Generate realistic credit score"""
        base_score = 650
        
        # Life stage adjustments
        if life_stage == CustomerLifeStage.STUDENT:
            base_score = 600  # Limited credit history
        elif life_stage == CustomerLifeStage.ESTABLISHED:
            base_score = 720  # Established credit
        elif life_stage == CustomerLifeStage.RETIREE:
            base_score = 750  # Long history, paid off debts
            
        # Income adjustments
        if income_level == IncomeLevel.ULTRA_HIGH:
            base_score += 50
        elif income_level == IncomeLevel.LOW:
            base_score -= 30
            
        # Risk adjustments
        if risk_profile == RiskProfile.LOW_RISK:
            base_score += 40
        elif risk_profile == RiskProfile.HIGH_RISK:
            base_score -= 40
            
        # Add some randomness
        score = base_score + random.randint(-50, 50)
        return max(300, min(850, score))
        
    def _generate_expenses(self, monthly_income: float, behavior_pattern: BehaviorPattern) -> float:
        """Generate monthly expenses based on income and behavior"""
        if behavior_pattern == BehaviorPattern.SAVER:
            expense_ratio = random.uniform(0.5, 0.7)
        elif behavior_pattern == BehaviorPattern.SPENDER:
            expense_ratio = random.uniform(0.8, 0.95)
        elif behavior_pattern == BehaviorPattern.IRREGULAR:
            expense_ratio = random.uniform(0.6, 1.1)  # Can exceed income sometimes
        else:  # BUSINESS
            expense_ratio = random.uniform(0.7, 0.85)
            
        return monthly_income * expense_ratio
        
    def _generate_preferred_balance(self, monthly_income: float, behavior_pattern: BehaviorPattern) -> float:
        """Generate preferred account balance"""
        if behavior_pattern == BehaviorPattern.SAVER:
            balance_months = random.uniform(3, 12)  # 3-12 months of income
        elif behavior_pattern == BehaviorPattern.SPENDER:
            balance_months = random.uniform(0.5, 2)
        elif behavior_pattern == BehaviorPattern.IRREGULAR:
            balance_months = random.uniform(0.2, 4)
        else:  # BUSINESS
            balance_months = random.uniform(1, 6)
            
        return monthly_income * balance_months
        
    def _select_primary_channel(self, life_stage: CustomerLifeStage) -> str:
        """Select primary transaction channel"""
        channels = self.channel_preferences.get(life_stage, ["online", "mobile"])
        return random.choice(channels)
        
    def _generate_transaction_frequency(self, behavior_pattern: BehaviorPattern, income_level: IncomeLevel) -> float:
        """Generate transactions per week"""
        base_frequency = {
            BehaviorPattern.SAVER: random.uniform(2, 5),
            BehaviorPattern.SPENDER: random.uniform(8, 15),
            BehaviorPattern.IRREGULAR: random.uniform(1, 20),
            BehaviorPattern.BUSINESS: random.uniform(15, 40)
        }[behavior_pattern]
        
        # Income adjustment
        if income_level == IncomeLevel.ULTRA_HIGH:
            base_frequency *= 1.5
        elif income_level == IncomeLevel.LOW:
            base_frequency *= 0.7
            
        return base_frequency
        
    def _generate_international_activity(self, income_level: IncomeLevel, life_stage: CustomerLifeStage) -> bool:
        """Determine if customer has international transaction activity"""
        prob = 0.1  # Base 10% probability
        
        if income_level == IncomeLevel.ULTRA_HIGH:
            prob = 0.6
        elif income_level == IncomeLevel.HIGH:
            prob = 0.3
            
        if life_stage == CustomerLifeStage.YOUNG_PROFESSIONAL:
            prob += 0.1
        elif life_stage == CustomerLifeStage.STUDENT:
            prob -= 0.05
            
        return random.random() < prob
        
    def _generate_tech_savvy(self, life_stage: CustomerLifeStage) -> bool:
        """Determine tech-savviness"""
        probabilities = {
            CustomerLifeStage.STUDENT: 0.9,
            CustomerLifeStage.YOUNG_PROFESSIONAL: 0.8,
            CustomerLifeStage.FAMILY: 0.6,
            CustomerLifeStage.ESTABLISHED: 0.4,
            CustomerLifeStage.RETIREE: 0.2
        }
        
        return random.random() < probabilities[life_stage]
        
    def _generate_fraud_awareness(self, life_stage: CustomerLifeStage, tech_savvy: bool) -> float:
        """Generate fraud awareness score 0.0-1.0"""
        base_awareness = {
            CustomerLifeStage.STUDENT: 0.3,
            CustomerLifeStage.YOUNG_PROFESSIONAL: 0.6,
            CustomerLifeStage.FAMILY: 0.7,
            CustomerLifeStage.ESTABLISHED: 0.8,
            CustomerLifeStage.RETIREE: 0.4
        }[life_stage]
        
        if tech_savvy:
            base_awareness += 0.2
        else:
            base_awareness -= 0.1
            
        # Add randomness
        awareness = base_awareness + random.uniform(-0.2, 0.2)
        return max(0.0, min(1.0, awareness))
        
    def _generate_social_media_presence(self, life_stage: CustomerLifeStage) -> bool:
        """Determine social media presence"""
        probabilities = {
            CustomerLifeStage.STUDENT: 0.95,
            CustomerLifeStage.YOUNG_PROFESSIONAL: 0.85,
            CustomerLifeStage.FAMILY: 0.70,
            CustomerLifeStage.ESTABLISHED: 0.50,
            CustomerLifeStage.RETIREE: 0.30
        }
        
        return random.random() < probabilities[life_stage]
        
    def _generate_risk_tolerance(self, life_stage: CustomerLifeStage, income_level: IncomeLevel) -> bool:
        """Determine high risk tolerance"""
        prob = 0.2  # Base 20%
        
        if life_stage in [CustomerLifeStage.YOUNG_PROFESSIONAL, CustomerLifeStage.STUDENT]:
            prob += 0.2
        elif life_stage == CustomerLifeStage.RETIREE:
            prob -= 0.1
            
        if income_level == IncomeLevel.ULTRA_HIGH:
            prob += 0.3
        elif income_level == IncomeLevel.LOW:
            prob -= 0.1
            
        return random.random() < prob