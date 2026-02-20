"""Transaction pattern generator for realistic banking simulation.

Generates realistic transaction patterns based on customer profiles,
including regular payments, shopping patterns, and seasonal variations.
"""

import random
import math
from datetime import datetime, time, timedelta
from typing import List, Dict, Optional, Tuple
from enum import Enum
from dataclasses import dataclass
from decimal import Decimal

from .customers import CustomerProfile, IncomeLevel, BehaviorPattern, CustomerLifeStage


class TransactionType(Enum):
    """Types of transactions in the banking system"""
    # Basic operations
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"
    TRANSFER = "transfer"
    
    # Specific patterns
    SALARY = "salary"
    RENT_MORTGAGE = "rent_mortgage"
    UTILITY_BILL = "utility_bill"
    GROCERY = "grocery"
    RESTAURANT = "restaurant"
    SHOPPING = "shopping"
    ATM_WITHDRAWAL = "atm_withdrawal"
    ONLINE_PURCHASE = "online_purchase"
    GAS_STATION = "gas_station"
    SUBSCRIPTION = "subscription"
    P2P_TRANSFER = "p2p_transfer"
    INVESTMENT = "investment"
    LOAN_PAYMENT = "loan_payment"
    CREDIT_PAYMENT = "credit_payment"
    CASH_ADVANCE = "cash_advance"
    INTERNATIONAL = "international"


class TransactionChannel(Enum):
    """Transaction channels"""
    ONLINE = "online"
    MOBILE = "mobile"
    ATM = "atm"
    BRANCH = "branch"
    CARD = "card"
    WIRE = "wire"
    ACH = "ach"


@dataclass
class TransactionTemplate:
    """Template for generating transactions of a specific type"""
    transaction_type: TransactionType
    amount_min: float
    amount_max: float
    frequency_per_month: float  # How many times per month this occurs
    preferred_channels: List[TransactionChannel]
    preferred_hours: Tuple[int, int]  # Hour range (24h format)
    seasonal_multiplier: Dict[int, float]  # Month -> multiplier
    day_of_month_preference: Optional[List[int]] = None  # Preferred days of month
    merchant_categories: Optional[List[str]] = None
    is_recurring: bool = False
    amount_distribution: str = "uniform"  # uniform, normal, log_normal
    
    def generate_amount(self) -> float:
        """Generate transaction amount based on distribution"""
        if self.amount_distribution == "normal":
            # Normal distribution centered between min and max
            mean = (self.amount_min + self.amount_max) / 2
            std = (self.amount_max - self.amount_min) / 6  # 99.7% within range
            amount = random.normalvariate(mean, std)
            return max(self.amount_min, min(self.amount_max, amount))
        elif self.amount_distribution == "log_normal":
            # Log-normal distribution (more small amounts)
            log_min = math.log(max(0.01, self.amount_min))
            log_max = math.log(self.amount_max)
            log_mean = (log_min + log_max) / 2
            log_std = (log_max - log_min) / 6
            log_amount = random.normalvariate(log_mean, log_std)
            amount = math.exp(log_amount)
            return max(self.amount_min, min(self.amount_max, amount))
        else:  # uniform
            return random.uniform(self.amount_min, self.amount_max)
    
    def should_generate(self, current_month: int, customer: CustomerProfile) -> bool:
        """Determine if this transaction type should be generated now"""
        # Apply seasonal multiplier
        base_prob = self.frequency_per_month / 30  # Daily probability
        seasonal_mult = self.seasonal_multiplier.get(current_month, 1.0)
        adjusted_prob = base_prob * seasonal_mult
        
        # Apply customer behavior modifiers
        if customer.behavior_pattern == BehaviorPattern.SAVER:
            adjusted_prob *= 0.7
        elif customer.behavior_pattern == BehaviorPattern.SPENDER:
            adjusted_prob *= 1.3
        elif customer.behavior_pattern == BehaviorPattern.IRREGULAR:
            adjusted_prob *= random.uniform(0.2, 2.0)
            
        return random.random() < adjusted_prob


@dataclass
class PendingTransaction:
    """A transaction ready to be submitted"""
    transaction_type: TransactionType
    amount: float
    currency: str
    description: str
    channel: TransactionChannel
    from_account_id: Optional[str]
    to_account_id: Optional[str]
    merchant_id: Optional[str]
    merchant_category: Optional[str]
    reference: Optional[str]
    timestamp: datetime
    metadata: Dict[str, any]


class TransactionGenerator:
    """Generates realistic transaction patterns for customers"""
    
    def __init__(self, seed: Optional[int] = None):
        if seed is not None:
            random.seed(seed)
            
        self._initialize_templates()
        self._initialize_merchants()
        
    def _initialize_templates(self):
        """Initialize transaction templates for different types"""
        self.templates = {
            # Regular income
            TransactionType.SALARY: TransactionTemplate(
                transaction_type=TransactionType.SALARY,
                amount_min=2000, amount_max=15000,
                frequency_per_month=1.0,  # Usually monthly
                preferred_channels=[TransactionChannel.ACH],
                preferred_hours=(9, 17),
                seasonal_multiplier={12: 1.2},  # December bonus
                day_of_month_preference=[1, 15, 30],  # Common paydays
                is_recurring=True,
                amount_distribution="normal"
            ),
            
            # Fixed expenses
            TransactionType.RENT_MORTGAGE: TransactionTemplate(
                transaction_type=TransactionType.RENT_MORTGAGE,
                amount_min=800, amount_max=4500,
                frequency_per_month=1.0,
                preferred_channels=[TransactionChannel.ACH, TransactionChannel.ONLINE],
                preferred_hours=(9, 23),
                seasonal_multiplier={},
                day_of_month_preference=[1, 2, 3],  # Due at start of month
                is_recurring=True,
                amount_distribution="normal"
            ),
            
            TransactionType.UTILITY_BILL: TransactionTemplate(
                transaction_type=TransactionType.UTILITY_BILL,
                amount_min=50, amount_max=300,
                frequency_per_month=3.0,  # Electric, gas, water/sewer
                preferred_channels=[TransactionChannel.ONLINE, TransactionChannel.ACH],
                preferred_hours=(10, 22),
                seasonal_multiplier={1: 1.5, 2: 1.3, 7: 1.4, 8: 1.4, 12: 1.3},  # Seasonal heating/cooling
                day_of_month_preference=list(range(1, 31)),  # Spread throughout month
                is_recurring=True,
                amount_distribution="normal"
            ),
            
            # Regular shopping
            TransactionType.GROCERY: TransactionTemplate(
                transaction_type=TransactionType.GROCERY,
                amount_min=25, amount_max=200,
                frequency_per_month=8.0,  # 2x per week
                preferred_channels=[TransactionChannel.CARD],
                preferred_hours=(7, 22),
                seasonal_multiplier={11: 1.3, 12: 1.4},  # Holiday cooking
                merchant_categories=["grocery", "supermarket", "food"],
                amount_distribution="log_normal"
            ),
            
            TransactionType.RESTAURANT: TransactionTemplate(
                transaction_type=TransactionType.RESTAURANT,
                amount_min=15, amount_max=150,
                frequency_per_month=12.0,  # 3x per week
                preferred_channels=[TransactionChannel.CARD, TransactionChannel.MOBILE],
                preferred_hours=(11, 22),  # Lunch and dinner
                seasonal_multiplier={12: 1.2, 5: 1.1},  # Holidays and graduation season
                merchant_categories=["restaurant", "fast_food", "bar", "cafe"],
                amount_distribution="log_normal"
            ),
            
            TransactionType.SHOPPING: TransactionTemplate(
                transaction_type=TransactionType.SHOPPING,
                amount_min=20, amount_max=500,
                frequency_per_month=6.0,
                preferred_channels=[TransactionChannel.CARD, TransactionChannel.ONLINE],
                preferred_hours=(10, 21),
                seasonal_multiplier={11: 2.0, 12: 2.5, 1: 0.7},  # Holiday shopping
                merchant_categories=["retail", "clothing", "electronics", "home"],
                amount_distribution="log_normal"
            ),
            
            # ATM and cash
            TransactionType.ATM_WITHDRAWAL: TransactionTemplate(
                transaction_type=TransactionType.ATM_WITHDRAWAL,
                amount_min=20, amount_max=300,
                frequency_per_month=4.0,  # Weekly
                preferred_channels=[TransactionChannel.ATM],
                preferred_hours=(7, 23),
                seasonal_multiplier={},
                amount_distribution="uniform"
            ),
            
            # Online and digital
            TransactionType.ONLINE_PURCHASE: TransactionTemplate(
                transaction_type=TransactionType.ONLINE_PURCHASE,
                amount_min=10, amount_max=800,
                frequency_per_month=8.0,
                preferred_channels=[TransactionChannel.ONLINE, TransactionChannel.MOBILE],
                preferred_hours=(19, 23),  # Evening shopping
                seasonal_multiplier={11: 3.0, 12: 3.5, 1: 1.5},  # Cyber Monday, holiday shopping
                merchant_categories=["ecommerce", "digital", "subscription"],
                amount_distribution="log_normal"
            ),
            
            # Transportation
            TransactionType.GAS_STATION: TransactionTemplate(
                transaction_type=TransactionType.GAS_STATION,
                amount_min=25, amount_max=85,
                frequency_per_month=6.0,
                preferred_channels=[TransactionChannel.CARD],
                preferred_hours=(6, 22),
                seasonal_multiplier={6: 1.2, 7: 1.3, 8: 1.2},  # Summer driving
                merchant_categories=["gas_station", "fuel"],
                amount_distribution="normal"
            ),
            
            # Subscriptions and recurring
            TransactionType.SUBSCRIPTION: TransactionTemplate(
                transaction_type=TransactionType.SUBSCRIPTION,
                amount_min=5, amount_max=50,
                frequency_per_month=3.0,  # Multiple subscriptions
                preferred_channels=[TransactionChannel.ACH, TransactionChannel.ONLINE],
                preferred_hours=(0, 23),  # Automated
                seasonal_multiplier={},
                is_recurring=True,
                merchant_categories=["streaming", "software", "gym"],
                amount_distribution="uniform"
            ),
            
            # P2P and transfers
            TransactionType.P2P_TRANSFER: TransactionTemplate(
                transaction_type=TransactionType.P2P_TRANSFER,
                amount_min=10, amount_max=1000,
                frequency_per_month=4.0,
                preferred_channels=[TransactionChannel.MOBILE, TransactionChannel.ONLINE],
                preferred_hours=(8, 23),
                seasonal_multiplier={12: 1.5, 1: 1.3},  # Holiday gifts
                merchant_categories=["p2p", "venmo", "paypal"],
                amount_distribution="log_normal"
            ),
            
            # Investments and savings
            TransactionType.INVESTMENT: TransactionTemplate(
                transaction_type=TransactionType.INVESTMENT,
                amount_min=100, amount_max=5000,
                frequency_per_month=1.0,
                preferred_channels=[TransactionChannel.ONLINE, TransactionChannel.ACH],
                preferred_hours=(9, 17),  # Business hours
                seasonal_multiplier={1: 1.5, 12: 1.2},  # New Year resolutions, year-end
                is_recurring=True,
                amount_distribution="normal"
            ),
            
            # Credit and loans
            TransactionType.CREDIT_PAYMENT: TransactionTemplate(
                transaction_type=TransactionType.CREDIT_PAYMENT,
                amount_min=50, amount_max=2000,
                frequency_per_month=1.0,
                preferred_channels=[TransactionChannel.ONLINE, TransactionChannel.ACH],
                preferred_hours=(9, 22),
                seasonal_multiplier={1: 1.3},  # Paying off holiday spending
                day_of_month_preference=list(range(1, 28)),  # Due dates throughout month
                is_recurring=True,
                amount_distribution="normal"
            ),
            
            TransactionType.LOAN_PAYMENT: TransactionTemplate(
                transaction_type=TransactionType.LOAN_PAYMENT,
                amount_min=200, amount_max=3000,
                frequency_per_month=1.0,
                preferred_channels=[TransactionChannel.ACH, TransactionChannel.ONLINE],
                preferred_hours=(9, 17),
                seasonal_multiplier={},
                day_of_month_preference=[1, 15],  # Common due dates
                is_recurring=True,
                amount_distribution="normal"
            ),
            
            # International
            TransactionType.INTERNATIONAL: TransactionTemplate(
                transaction_type=TransactionType.INTERNATIONAL,
                amount_min=50, amount_max=2000,
                frequency_per_month=0.5,  # Rare for most customers
                preferred_channels=[TransactionChannel.CARD, TransactionChannel.WIRE],
                preferred_hours=(0, 23),
                seasonal_multiplier={6: 2.0, 7: 2.5, 8: 2.0, 12: 1.5},  # Vacation and holiday seasons
                merchant_categories=["international", "travel", "foreign"],
                amount_distribution="log_normal"
            )
        }
        
    def _initialize_merchants(self):
        """Initialize merchant database for realistic transaction descriptions"""
        self.merchants = {
            "grocery": [
                ("Whole Foods Market", "WFM"),
                ("Safeway", "SAFEWAY"),
                ("Kroger", "KROGER"),
                ("Walmart Supercenter", "WALMART"),
                ("Target", "TARGET"),
                ("Costco Wholesale", "COSTCO"),
                ("Trader Joe's", "TRADERJOES"),
                ("Fresh Market", "FRESHMARKET")
            ],
            "restaurant": [
                ("McDonald's", "MCD"),
                ("Starbucks", "STARBUCKS"),
                ("Chipotle", "CHIPOTLE"),
                ("Subway", "SUBWAY"),
                ("Olive Garden", "OLIVEGARDEN"),
                ("Local Cafe", "CAFE"),
                ("Pizza Hut", "PIZZAHUT"),
                ("Panda Express", "PANDA")
            ],
            "retail": [
                ("Amazon", "AMAZON"),
                ("Best Buy", "BESTBUY"),
                ("Home Depot", "HOMEDEPOT"),
                ("Macy's", "MACYS"),
                ("Nike Store", "NIKE"),
                ("Apple Store", "APPLE"),
                ("Nordstrom", "NORDSTROM"),
                ("CVS Pharmacy", "CVS")
            ],
            "gas_station": [
                ("Shell", "SHELL"),
                ("Chevron", "CHEVRON"),
                ("Exxon", "EXXON"),
                ("BP", "BP"),
                ("Mobil", "MOBIL"),
                ("Arco", "ARCO")
            ],
            "streaming": [
                ("Netflix", "NETFLIX"),
                ("Spotify", "SPOTIFY"),
                ("Amazon Prime", "AMAZONPRIME"),
                ("Disney+", "DISNEYPLUS"),
                ("Hulu", "HULU"),
                ("YouTube Premium", "YOUTUBE")
            ]
        }
        
    def generate_transactions_for_customer(self, customer: CustomerProfile, account_ids: List[str], 
                                         simulation_start: datetime, duration_hours: int) -> List[PendingTransaction]:
        """Generate realistic transactions for a customer over the simulation period"""
        transactions = []
        current_time = simulation_start
        end_time = simulation_start + timedelta(hours=duration_hours)
        
        # Adjust transaction templates based on customer profile
        adjusted_templates = self._adjust_templates_for_customer(customer)
        
        # Generate transactions day by day
        while current_time < end_time:
            daily_transactions = self._generate_daily_transactions(
                customer, account_ids, current_time, adjusted_templates
            )
            transactions.extend(daily_transactions)
            current_time += timedelta(days=1)
            
        return transactions
        
    def _adjust_templates_for_customer(self, customer: CustomerProfile) -> Dict[TransactionType, TransactionTemplate]:
        """Adjust transaction templates based on customer profile"""
        adjusted = {}
        
        for tx_type, template in self.templates.items():
            # Create a copy of the template
            new_template = TransactionTemplate(
                transaction_type=template.transaction_type,
                amount_min=template.amount_min,
                amount_max=template.amount_max,
                frequency_per_month=template.frequency_per_month,
                preferred_channels=template.preferred_channels.copy(),
                preferred_hours=template.preferred_hours,
                seasonal_multiplier=template.seasonal_multiplier.copy(),
                day_of_month_preference=template.day_of_month_preference,
                merchant_categories=template.merchant_categories,
                is_recurring=template.is_recurring,
                amount_distribution=template.amount_distribution
            )
            
            # Adjust amounts based on income level
            income_multiplier = {
                IncomeLevel.LOW: 0.6,
                IncomeLevel.MEDIUM: 1.0,
                IncomeLevel.HIGH: 1.8,
                IncomeLevel.ULTRA_HIGH: 3.0
            }[customer.income_level]
            
            new_template.amount_min *= income_multiplier
            new_template.amount_max *= income_multiplier
            
            # Adjust frequency based on behavior pattern
            if customer.behavior_pattern == BehaviorPattern.SAVER:
                if tx_type not in [TransactionType.SALARY, TransactionType.RENT_MORTGAGE, TransactionType.UTILITY_BILL]:
                    new_template.frequency_per_month *= 0.7
            elif customer.behavior_pattern == BehaviorPattern.SPENDER:
                if tx_type not in [TransactionType.SALARY]:
                    new_template.frequency_per_month *= 1.3
            elif customer.behavior_pattern == BehaviorPattern.IRREGULAR:
                new_template.frequency_per_month *= random.uniform(0.5, 1.8)
                
            # Life stage specific adjustments
            if customer.life_stage == CustomerLifeStage.STUDENT:
                # Students have less regular income, more irregular spending
                if tx_type == TransactionType.SALARY:
                    new_template.frequency_per_month *= 0.3  # Part-time work
                    new_template.amount_min *= 0.4
                    new_template.amount_max *= 0.4
                elif tx_type == TransactionType.RESTAURANT:
                    new_template.frequency_per_month *= 1.5  # Fast food
                elif tx_type == TransactionType.INVESTMENT:
                    new_template.frequency_per_month *= 0.1  # Minimal investing
                    
            elif customer.life_stage == CustomerLifeStage.RETIREE:
                # Retirees have fixed income, different spending patterns
                if tx_type == TransactionType.SALARY:
                    new_template.frequency_per_month *= 0.5  # Pension/SS
                    new_template.amount_min *= 0.6
                    new_template.amount_max *= 0.8
                elif tx_type == TransactionType.SHOPPING:
                    new_template.frequency_per_month *= 0.7
                elif tx_type in [TransactionType.RESTAURANT, TransactionType.ONLINE_PURCHASE]:
                    new_template.frequency_per_month *= 0.8
                    
            # International activity
            if not customer.international_activity:
                if tx_type == TransactionType.INTERNATIONAL:
                    new_template.frequency_per_month *= 0.1
            else:
                if tx_type == TransactionType.INTERNATIONAL:
                    new_template.frequency_per_month *= 3.0
                    
            # Skip certain transaction types for some customers
            if tx_type == TransactionType.INVESTMENT and customer.income_level == IncomeLevel.LOW:
                new_template.frequency_per_month *= 0.2
                
            adjusted[tx_type] = new_template
            
        return adjusted
        
    def _generate_daily_transactions(self, customer: CustomerProfile, account_ids: List[str], 
                                   day: datetime, templates: Dict[TransactionType, TransactionTemplate]) -> List[PendingTransaction]:
        """Generate transactions for a single day"""
        transactions = []
        
        for tx_type, template in templates.items():
            if template.should_generate(day.month, customer):
                # Skip if wrong day of month for recurring transactions
                if template.day_of_month_preference and day.day not in template.day_of_month_preference:
                    if template.is_recurring and random.random() < 0.9:  # 90% strict about due dates
                        continue
                        
                # Generate transaction time
                start_hour, end_hour = template.preferred_hours
                hour = random.randint(start_hour, end_hour)
                minute = random.randint(0, 59)
                tx_time = day.replace(hour=hour, minute=minute, second=random.randint(0, 59))
                
                # Generate transaction
                transaction = self._create_transaction(
                    customer, account_ids, tx_type, template, tx_time
                )
                
                transactions.append(transaction)
                
        return transactions
        
    def _create_transaction(self, customer: CustomerProfile, account_ids: List[str],
                          tx_type: TransactionType, template: TransactionTemplate, 
                          timestamp: datetime) -> PendingTransaction:
        """Create a single transaction"""
        amount = template.generate_amount()
        channel = random.choice(template.preferred_channels)
        
        # Select account (prefer primary checking/savings for most transactions)
        from_account = random.choice(account_ids)
        to_account = None
        
        # Determine transaction direction and accounts
        if tx_type in [TransactionType.SALARY, TransactionType.DEPOSIT]:
            # Incoming money - this is a deposit
            to_account = from_account
            from_account = None
        elif tx_type == TransactionType.P2P_TRANSFER:
            # Could be incoming or outgoing
            if random.random() < 0.4:  # 40% incoming
                to_account = from_account
                from_account = None
            else:  # 60% outgoing - select different account or external
                if len(account_ids) > 1 and random.random() < 0.3:
                    to_account = random.choice([aid for aid in account_ids if aid != from_account])
                else:
                    to_account = None  # External P2P
        elif tx_type == TransactionType.TRANSFER:
            # Internal transfer between accounts
            if len(account_ids) > 1:
                to_account = random.choice([aid for aid in account_ids if aid != from_account])
            else:
                # Convert to withdrawal if only one account
                to_account = None
                
        # Generate merchant information
        merchant_id = None
        merchant_category = None
        if template.merchant_categories:
            category = random.choice(template.merchant_categories)
            if category in self.merchants:
                merchant_name, merchant_code = random.choice(self.merchants[category])
                merchant_id = f"{merchant_code}_{random.randint(1000, 9999)}"
                merchant_category = category
                
        # Generate description
        description = self._generate_description(tx_type, merchant_id, amount)
        
        # Generate reference
        reference = f"REF_{int(timestamp.timestamp())}_{random.randint(1000, 9999)}"
        
        # Metadata for fraud detection
        metadata = {
            "customer_risk_score": customer.risk_score,
            "customer_life_stage": customer.life_stage.value,
            "customer_income_level": customer.income_level.value,
            "transaction_hour": timestamp.hour,
            "is_weekend": timestamp.weekday() >= 5,
            "is_recurring": template.is_recurring,
            "customer_location": f"{customer.city}, {customer.state}, {customer.country}",
            "primary_channel": customer.primary_channel
        }
        
        return PendingTransaction(
            transaction_type=tx_type,
            amount=round(amount, 2),
            currency="USD",
            description=description,
            channel=channel,
            from_account_id=from_account,
            to_account_id=to_account,
            merchant_id=merchant_id,
            merchant_category=merchant_category,
            reference=reference,
            timestamp=timestamp,
            metadata=metadata
        )
        
    def _generate_description(self, tx_type: TransactionType, merchant_id: Optional[str], amount: float) -> str:
        """Generate human-readable transaction description"""
        if merchant_id:
            merchant_name = merchant_id.split('_')[0]
            return f"{merchant_name} - {tx_type.value.replace('_', ' ').title()}"
        
        descriptions = {
            TransactionType.SALARY: "Salary Deposit - Direct Deposit",
            TransactionType.RENT_MORTGAGE: f"Rent/Mortgage Payment - ${amount:.2f}",
            TransactionType.UTILITY_BILL: f"Utility Payment - ${amount:.2f}",
            TransactionType.ATM_WITHDRAWAL: f"ATM Withdrawal - ${amount:.2f}",
            TransactionType.P2P_TRANSFER: f"P2P Transfer - ${amount:.2f}",
            TransactionType.INVESTMENT: f"Investment Transfer - ${amount:.2f}",
            TransactionType.CREDIT_PAYMENT: f"Credit Card Payment - ${amount:.2f}",
            TransactionType.LOAN_PAYMENT: f"Loan Payment - ${amount:.2f}",
            TransactionType.SUBSCRIPTION: f"Subscription Service - ${amount:.2f}",
            TransactionType.INTERNATIONAL: f"International Transaction - ${amount:.2f}"
        }
        
        return descriptions.get(tx_type, f"{tx_type.value.replace('_', ' ').title()} - ${amount:.2f}")
        
    def get_expected_daily_volume(self, customer: CustomerProfile) -> float:
        """Get expected daily transaction volume for a customer"""
        total_frequency = 0
        for template in self.templates.values():
            total_frequency += template.frequency_per_month
            
        # Adjust for customer behavior
        if customer.behavior_pattern == BehaviorPattern.SAVER:
            total_frequency *= 0.7
        elif customer.behavior_pattern == BehaviorPattern.SPENDER:
            total_frequency *= 1.3
        elif customer.behavior_pattern == BehaviorPattern.IRREGULAR:
            total_frequency *= random.uniform(0.5, 1.8)
            
        return total_frequency / 30  # Convert to daily
        
    def estimate_simulation_volume(self, customers: List[CustomerProfile], duration_hours: int) -> Dict[str, int]:
        """Estimate total transaction volume for simulation planning"""
        total_daily_volume = sum(self.get_expected_daily_volume(customer) for customer in customers)
        simulation_days = duration_hours / 24
        
        total_transactions = int(total_daily_volume * simulation_days)
        
        # Break down by type (rough estimates)
        breakdown = {
            "total_transactions": total_transactions,
            "deposits": int(total_transactions * 0.15),
            "withdrawals": int(total_transactions * 0.20),
            "transfers": int(total_transactions * 0.10),
            "purchases": int(total_transactions * 0.45),
            "bills": int(total_transactions * 0.10),
        }
        
        return breakdown