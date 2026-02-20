# Architecture Documentation

This document provides detailed technical architecture documentation for the Banking Simulator, including component design, data flows, interfaces, and extension points.

## Table of Contents

1. [System Overview](#system-overview)
2. [Component Architecture](#component-architecture)
3. [Data Flow Diagrams](#data-flow-diagrams)
4. [Generator Pipeline](#generator-pipeline)
5. [Connector Interfaces](#connector-interfaces)
6. [Metrics Collection](#metrics-collection)
7. [Dashboard WebSocket Protocol](#dashboard-websocket-protocol)
8. [Extension Points](#extension-points)
9. [Performance Considerations](#performance-considerations)
10. [Deployment Architecture](#deployment-architecture)

---

## System Overview

### Design Principles

The Banking Simulator is built on these core architectural principles:

- **Event-Driven**: Async event processing with minimal blocking
- **Modular**: Loosely coupled components with clear interfaces
- **Observable**: Rich metrics and monitoring at every level
- **Scalable**: Designed to handle high transaction volumes
- **Testable**: Mock connectors and dependency injection
- **Configurable**: YAML-driven configuration for all scenarios

### Technology Stack

```
┌─────────────────┐
│   Presentation  │  HTML5 + CSS3 + JavaScript (ES6 Modules)
├─────────────────┤
│   API Layer     │  FastAPI + WebSockets + REST
├─────────────────┤  
│   Business      │  Python 3.12 + AsyncIO + Pydantic
│   Logic         │
├─────────────────┤
│   Integration   │  HTTPX + Kafka (aiokafka) + PostgreSQL
├─────────────────┤
│   Infrastructure│  Docker + Docker Compose + Uvicorn
└─────────────────┘
```

### Core Dependencies

```python
# Core Framework
fastapi[standard] >= 0.104.0    # Web framework + dependencies
uvicorn >= 0.24.0               # ASGI server
websockets >= 11.0.0            # WebSocket support

# Data & Configuration
pydantic >= 2.0.0               # Data validation & settings
pyyaml >= 6.0                   # YAML configuration parsing
faker >= 20.0.0                 # Realistic fake data generation

# External Integration
httpx >= 0.24.0                 # Async HTTP client
aiokafka >= 0.8.0               # Kafka async client (optional)

# Development & Testing
pytest >= 7.0.0                 # Testing framework
pytest-asyncio >= 0.21.0        # Async test support
mypy >= 1.0.0                   # Type checking
```

---

## Component Architecture

### High-Level Component Diagram

```
┌──────────────────────────────────────────────────────────────────────┐
│                          BANKING SIMULATOR                           │
├──────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐      │
│  │  Configuration  │  │   Simulation    │  │    Dashboard    │      │
│  │    Manager      │  │     Engine      │  │     Server      │      │
│  │                 │  │                 │  │                 │      │
│  │ • YAML Loading  │  │ • Orchestration │  │ • FastAPI App   │      │
│  │ • Validation    │  │ • Time Accel.   │  │ • WebSocket Hub │      │
│  │ • Env Override  │  │ • Generators    │  │ • Static Files  │      │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘      │
│           │                     │                     │              │
├───────────┼─────────────────────┼─────────────────────┼──────────────┤
│  ┌────────▼─────────┐  ┌────────▼─────────┐  ┌────────▼─────────┐    │
│  │    Customer      │  │   Transaction    │  │      Fraud       │    │
│  │   Generator      │  │    Generator     │  │   Generator      │    │
│  │                  │  │                  │  │                  │    │
│  │ • Profile Gen    │  │ • Pattern Gen    │  │ • Attack Gen     │    │
│  │ • Demographics   │  │ • Time-based     │  │ • ML Evasion     │    │
│  │ • Behavior Model │  │ • Amount Dist.   │  │ • Coordination   │    │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘    │
│           │                     │                     │              │
├───────────┼─────────────────────┼─────────────────────┼──────────────┤
│  ┌────────▼──────────────────────▼─────────────────────▼─────────┐    │
│  │                    API CONNECTORS                             │    │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐           │    │
│  │  │   Nexum     │  │   Bastion   │  │    Kafka    │           │    │
│  │  │ Connector   │  │ Connector   │  │ Publisher   │           │    │
│  │  │             │  │             │  │             │           │    │
│  │  │ • Customer  │  │ • Fraud     │  │ • Events    │           │    │
│  │  │   CRUD      │  │   Scoring   │  │ • Topics    │           │    │
│  │  │ • Txn API   │  │ • Alerts    │  │ • Reliability│           │    │
│  │  └─────────────┘  └─────────────┘  └─────────────┘           │    │
│  └───────────────────────────────────────────────────────────────┘    │
│           │                     │                     │              │
├───────────┼─────────────────────┼─────────────────────┼──────────────┤
│  ┌────────▼──────────────────────▼─────────────────────▼─────────┐    │
│  │                   METRICS COLLECTION                          │    │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐           │    │
│  │  │   System    │  │   Business  │  │  Performance│           │    │
│  │  │  Metrics    │  │   Metrics   │  │   Metrics   │           │    │
│  │  │             │  │             │  │             │           │    │
│  │  │ • CPU/Mem   │  │ • TPS       │  │ • Latency   │           │    │
│  │  │ • Network   │  │ • Fraud Rate│  │ • Error Rate│           │    │
│  │  │ • Disk I/O  │  │ • Volume    │  │ • Throughput│           │    │
│  │  └─────────────┘  └─────────────┘  └─────────────┘           │    │
│  └───────────────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

#### Configuration Manager (`simulator/config.py`)
- **Purpose**: Central configuration management and validation
- **Responsibilities**:
  - Load and parse YAML scenario files
  - Validate configuration against Pydantic schemas
  - Handle environment variable overrides
  - Provide type-safe configuration access
- **Key Classes**: `SimulationConfig`, `ConnectionConfig`, `DashboardConfig`

#### Simulation Engine (`simulator/engine.py`)
- **Purpose**: Core orchestration and time management
- **Responsibilities**:
  - Coordinate all generator components
  - Manage simulation time acceleration
  - Handle start/stop/pause controls
  - Monitor component health
- **Key Classes**: `SimulationEngine`, `TimeManager`

#### Customer Generator (`simulator/generators/customers.py`)
- **Purpose**: Generate realistic customer profiles and demographics
- **Responsibilities**:
  - Create diverse customer profiles
  - Generate realistic personal information
  - Model customer behavior patterns
  - Handle customer lifecycle events
- **Key Classes**: `CustomerGenerator`, `CustomerProfile`, `DemographicModel`

#### Transaction Generator (`simulator/generators/transactions.py`)
- **Purpose**: Generate realistic transaction patterns and behaviors
- **Responsibilities**:
  - Create time-based transaction patterns
  - Model different transaction types
  - Handle business hour variations
  - Generate realistic amounts and merchants
- **Key Classes**: `TransactionGenerator`, `TransactionPattern`, `AmountDistribution`

#### Fraud Generator (`simulator/generators/fraud.py`)
- **Purpose**: Generate sophisticated fraud attacks and patterns
- **Responsibilities**:
  - Create coordinated attack scenarios
  - Model evasion techniques
  - Generate realistic fraud patterns
  - Handle attack timing and sequencing
- **Key Classes**: `FraudGenerator`, `AttackPattern`, `FraudCoordinator`

---

## Data Flow Diagrams

### Transaction Processing Flow

```
┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
│   SCENARIO      │      │   GENERATORS    │      │   CONNECTORS    │
│   LOADER        │      │                 │      │                 │
│                 │      │                 │      │                 │
│ • Load YAML     │ ──── │ • Generate      │ ──── │ • API Calls     │
│ • Validate      │      │ • Transform     │      │ • Error Handle  │
│ • Configure     │      │ • Schedule      │      │ • Retry Logic   │
└─────────────────┘      └─────────────────┘      └─────────────────┘
         │                        │                        │
         ▼                        ▼                        ▼
┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
│    ENGINE       │      │    METRICS      │      │   EXTERNAL      │
│ ORCHESTRATION   │ ──── │  COLLECTION     │ ──── │    SYSTEMS      │
│                 │      │                 │      │                 │
│ • Time Accel    │      │ • Aggregate     │      │ • Nexum API     │
│ • Scheduling    │      │ • Store         │      │ • Bastion API   │
│ • Coordination  │      │ • Stream        │      │ • Kafka Topics  │
└─────────────────┘      └─────────────────┘      └─────────────────┘
         │                        │                        │
         ▼                        ▼                        ▼
┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
│    DASHBOARD    │      │    WEBSOCKET    │      │     STORAGE     │
│      SERVER     │ ◄──── │    MANAGER      │ ◄──── │                 │
│                 │      │                 │      │ • Memory Buf    │
│ • HTTP API      │      │ • Real-time     │      │ • CSV Export    │
│ • Static Files  │      │ • Broadcast     │      │ • Log Files     │
│ • WebSocket     │      │ • Subscriptions │      │                 │
└─────────────────┘      └─────────────────┘      └─────────────────┘
```

### Event Flow Architecture

```
                              EVENT FLOW ARCHITECTURE
                              ======================

   Generator Layer                Message Layer               Consumer Layer
┌─────────────────┐           ┌─────────────────┐           ┌─────────────────┐
│    Customer     │           │                 │           │    Nexum API    │
│   Generator     │ ────────► │     NEXUM       │ ────────► │                 │
│                 │           │   CUSTOMERS     │           │ • Create Profile│
│ • Profile Data  │           │     TOPIC       │           │ • Validation    │
│ • Demographics  │           │                 │           │ • Storage       │
└─────────────────┘           └─────────────────┘           └─────────────────┘
                                       │
┌─────────────────┐           ┌─────────▼───────┐           ┌─────────────────┐
│  Transaction    │           │                 │           │  Nexum + Bastion│
│   Generator     │ ────────► │    NEXUM        │ ────────► │                 │
│                 │           │ TRANSACTIONS    │           │ • Process Txn   │
│ • Realistic     │           │     TOPIC       │           │ • Fraud Score   │
│   Patterns      │           │                 │           │ • Store Result  │
└─────────────────┘           └─────────────────┘           └─────────────────┘
                                       │
┌─────────────────┐           ┌─────────▼───────┐           ┌─────────────────┐
│     Fraud       │           │                 │           │   Dashboard     │
│   Generator     │ ────────► │   BASTION       │ ────────► │                 │
│                 │           │    FRAUD        │           │ • Real-time     │
│ • Attack        │           │  DECISIONS      │           │   Updates       │
│   Patterns      │           │    TOPIC        │           │ • Alerts        │
└─────────────────┘           └─────────────────┘           └─────────────────┘

                   Time Flow (Left to Right)
                   Message Flow (Top to Bottom)
                   Feedback Loop (Dashboard → Engine Controls)
```

---

## Generator Pipeline

### Customer Generation Pipeline

```python
class CustomerGenerator:
    """
    Generates realistic customer profiles with demographics and behavior patterns
    """
    
    def __init__(self, config: CustomerConfig):
        self.faker = Faker()
        self.demographic_model = DemographicModel()
        self.behavior_model = BehaviorModel()
        
    async def generate_customers(self, count: int) -> List[Customer]:
        """Generate batch of customer profiles"""
        customers = []
        
        for i in range(count):
            # 1. Generate basic profile
            profile = await self._generate_profile()
            
            # 2. Add demographic data  
            demographics = await self._generate_demographics(profile)
            
            # 3. Model behavior patterns
            behavior = await self._model_behavior(profile, demographics)
            
            # 4. Create customer object
            customer = Customer(
                profile=profile,
                demographics=demographics, 
                behavior=behavior
            )
            
            customers.append(customer)
            
        return customers
    
    async def _generate_profile(self) -> CustomerProfile:
        """Generate basic customer profile"""
        return CustomerProfile(
            first_name=self.faker.first_name(),
            last_name=self.faker.last_name(),
            email=self.faker.email(),
            phone=self.faker.phone_number(),
            date_of_birth=self.faker.date_of_birth(minimum_age=18, maximum_age=80),
            ssn=self.faker.ssn(),
            address=self._generate_address()
        )
    
    async def _generate_demographics(self, profile: CustomerProfile) -> Demographics:
        """Generate demographic and economic data"""
        age = calculate_age(profile.date_of_birth)
        
        # Age-based income distribution
        income_brackets = {
            (18, 25): (25000, 45000),
            (26, 35): (35000, 75000), 
            (36, 50): (45000, 120000),
            (51, 65): (40000, 150000),
            (66, 100): (20000, 80000)
        }
        
        min_income, max_income = next(
            (bracket for age_range, bracket in income_brackets.items()
             if age_range[0] <= age <= age_range[1]),
            (30000, 60000)  # default
        )
        
        return Demographics(
            age=age,
            income=random.randint(min_income, max_income),
            credit_score=self._generate_credit_score(age),
            employment_status=self._generate_employment(age),
            education_level=self.faker.random_element([
                'high_school', 'some_college', 'bachelor', 'master', 'doctorate'
            ])
        )
    
    async def _model_behavior(self, profile: CustomerProfile, 
                            demographics: Demographics) -> BehaviorModel:
        """Model customer transaction behavior patterns"""
        
        # Income-based transaction patterns
        monthly_transaction_count = self._calculate_transaction_frequency(
            demographics.income
        )
        
        # Age-based channel preferences
        digital_preference = self._calculate_digital_preference(demographics.age)
        
        # Risk tolerance based on demographics
        risk_tolerance = self._calculate_risk_tolerance(
            demographics.age, demographics.income
        )
        
        return BehaviorModel(
            monthly_transactions=monthly_transaction_count,
            preferred_channels=['online' if digital_preference > 0.7 else 'branch'],
            avg_transaction_amount=demographics.income / 50,  # ~2% of monthly income
            risk_tolerance=risk_tolerance,
            time_patterns=self._generate_time_patterns(demographics)
        )
```

### Transaction Generation Pipeline  

```python
class TransactionGenerator:
    """
    Generates realistic transaction patterns based on customer behavior
    """
    
    def __init__(self, customers: List[Customer], config: TransactionConfig):
        self.customers = customers
        self.config = config
        self.transaction_templates = self._load_transaction_templates()
        
    async def generate_transaction_stream(self) -> AsyncGenerator[Transaction, None]:
        """Generate continuous stream of transactions"""
        
        while self.simulation_running:
            # 1. Select customer based on activity probability
            customer = await self._select_active_customer()
            
            # 2. Choose transaction type based on patterns
            tx_template = await self._select_transaction_template(customer)
            
            # 3. Generate transaction details
            transaction = await self._generate_transaction(customer, tx_template)
            
            # 4. Apply time-based scheduling
            await self._schedule_transaction(transaction)
            
            yield transaction
    
    async def _select_active_customer(self) -> Customer:
        """Select customer based on behavior patterns and time of day"""
        current_hour = self.time_manager.current_simulation_hour()
        
        # Weight customers by their activity patterns
        weights = []
        for customer in self.customers:
            activity_score = customer.behavior.get_activity_score(current_hour)
            weights.append(activity_score)
        
        return random.choices(self.customers, weights=weights)[0]
    
    async def _select_transaction_template(self, customer: Customer) -> TransactionTemplate:
        """Choose transaction type based on customer behavior"""
        
        # Filter templates by customer preferences
        applicable_templates = [
            template for template in self.transaction_templates
            if self._template_matches_customer(template, customer)
        ]
        
        # Weight by frequency and customer behavior
        weights = [
            template.base_frequency * customer.behavior.get_template_affinity(template)
            for template in applicable_templates
        ]
        
        return random.choices(applicable_templates, weights=weights)[0]
    
    async def _generate_transaction(self, customer: Customer, 
                                  template: TransactionTemplate) -> Transaction:
        """Generate specific transaction details"""
        
        # 1. Generate amount based on template and customer income
        amount = self._generate_amount(template, customer)
        
        # 2. Select merchant based on transaction type and location
        merchant = await self._select_merchant(template, customer)
        
        # 3. Determine payment method
        payment_method = self._select_payment_method(customer, amount)
        
        # 4. Add metadata and context
        metadata = await self._generate_metadata(customer, template)
        
        return Transaction(
            customer_id=customer.id,
            account_id=customer.primary_account_id,
            amount=amount,
            transaction_type=template.transaction_type,
            merchant=merchant,
            payment_method=payment_method,
            timestamp=self.time_manager.current_simulation_time(),
            metadata=metadata
        )
```

### Fraud Generation Pipeline

```python
class FraudGenerator:
    """
    Generates sophisticated fraud attack patterns and scenarios
    """
    
    def __init__(self, customers: List[Customer], config: FraudConfig):
        self.customers = customers
        self.config = config
        self.attack_coordinator = AttackCoordinator()
        self.evasion_engine = EvasionEngine()
        
    async def generate_fraud_events(self) -> AsyncGenerator[FraudEvent, None]:
        """Generate coordinated fraud attacks"""
        
        for attack_pattern in self.config.attack_patterns:
            # 1. Wait for attack window
            await self._wait_for_attack_window(attack_pattern)
            
            # 2. Select target customers/accounts
            targets = await self._select_attack_targets(attack_pattern)
            
            # 3. Generate coordinated attack
            fraud_events = await self._orchestrate_attack(attack_pattern, targets)
            
            # 4. Apply evasion techniques
            evaded_events = await self._apply_evasion(fraud_events)
            
            for event in evaded_events:
                yield event
    
    async def _orchestrate_attack(self, pattern: AttackPattern, 
                                targets: List[Customer]) -> List[FraudEvent]:
        """Coordinate multi-phase fraud attack"""
        
        if pattern.type == 'card_testing':
            return await self._card_testing_attack(pattern, targets)
        elif pattern.type == 'account_takeover':
            return await self._account_takeover_attack(pattern, targets)
        elif pattern.type == 'velocity_attack':
            return await self._velocity_attack(pattern, targets)
        elif pattern.type == 'layering':
            return await self._money_laundering_attack(pattern, targets)
        else:
            raise ValueError(f"Unknown attack pattern: {pattern.type}")
    
    async def _card_testing_attack(self, pattern: AttackPattern, 
                                 targets: List[Customer]) -> List[FraudEvent]:
        """Generate card testing attack sequence"""
        events = []
        
        for target in targets:
            # Generate rapid sequence of small-amount transactions
            for i in range(pattern.transaction_count):
                amount = random.uniform(0.01, 5.00)  # Small test amounts
                merchant = self._select_random_merchant()
                
                event = FraudEvent(
                    customer_id=target.id,
                    attack_type='card_testing',
                    amount=amount,
                    merchant=merchant,
                    timestamp=self.time_manager.current_simulation_time() + i * 30,  # 30s apart
                    risk_indicators=['small_amount', 'high_velocity', 'random_merchant']
                )
                
                events.append(event)
        
        return events
    
    async def _apply_evasion(self, events: List[FraudEvent]) -> List[FraudEvent]:
        """Apply ML evasion techniques to avoid detection"""
        
        evaded_events = []
        
        for event in events:
            # 1. Amount manipulation to avoid thresholds
            if event.amount > 9500:  # Just under $10k reporting limit
                event.amount = random.uniform(9000, 9499)
            
            # 2. Timing manipulation to avoid velocity detection  
            jitter = random.uniform(-30, 30)  # Add timing noise
            event.timestamp += jitter
            
            # 3. Geographic dispersion
            if 'location_spoofing' in event.evasion_techniques:
                event.location = self._generate_spoofed_location(event.customer_id)
            
            # 4. Transaction metadata manipulation
            event = await self._manipulate_metadata(event)
            
            evaded_events.append(event)
        
        return evaded_events
```

---

## Connector Interfaces

### Base Connector Interface

```python
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class BaseConnector(ABC):
    """Abstract base class for all external system connectors"""
    
    def __init__(self, config: ConnectionConfig):
        self.config = config
        self.client = None
        self.is_connected = False
        self.error_count = 0
        self.last_error = None
        
    @abstractmethod
    async def connect(self) -> bool:
        """Establish connection to external system"""
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        """Clean up connection resources"""
        pass
    
    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """Check system health and return status"""
        pass
    
    @abstractmethod
    async def handle_error(self, error: Exception) -> bool:
        """Handle connection/API errors, return True if retryable"""
        pass
```

### Nexum Connector Implementation

```python
import httpx
from typing import List, Dict, Any
from .base import BaseConnector

class NexumConnector(BaseConnector):
    """Connector for Nexum core banking system"""
    
    async def connect(self) -> bool:
        """Connect to Nexum API"""
        try:
            self.client = httpx.AsyncClient(
                base_url=self.config.nexum_url,
                timeout=self.config.timeout_seconds,
                limits=httpx.Limits(max_connections=50, max_keepalive_connections=10)
            )
            
            # Test connection
            health = await self.health_check()
            self.is_connected = health['status'] == 'healthy'
            
            return self.is_connected
            
        except Exception as e:
            await self.handle_error(e)
            return False
    
    async def create_customer(self, customer: Customer) -> Dict[str, Any]:
        """Create new customer in Nexum"""
        endpoint = "/customers"
        payload = {
            "first_name": customer.profile.first_name,
            "last_name": customer.profile.last_name,
            "email": customer.profile.email,
            "phone": customer.profile.phone,
            "date_of_birth": customer.profile.date_of_birth.isoformat(),
            "address": {
                "street": customer.profile.address.street,
                "city": customer.profile.address.city,
                "state": customer.profile.address.state,
                "zip_code": customer.profile.address.zip_code
            }
        }
        
        return await self._make_request("POST", endpoint, json=payload)
    
    async def create_account(self, customer_id: str, account_type: str, 
                           initial_balance: float) -> Dict[str, Any]:
        """Create new account for customer"""
        endpoint = "/accounts"
        payload = {
            "customer_id": customer_id,
            "account_type": account_type,
            "initial_balance": initial_balance,
            "currency": "USD"
        }
        
        return await self._make_request("POST", endpoint, json=payload)
    
    async def process_transaction(self, transaction: Transaction) -> Dict[str, Any]:
        """Process transaction through Nexum"""
        endpoint = f"/transactions/{transaction.transaction_type}"
        payload = {
            "customer_id": transaction.customer_id,
            "account_id": transaction.account_id,
            "amount": transaction.amount,
            "merchant": transaction.merchant.name if transaction.merchant else None,
            "payment_method": transaction.payment_method,
            "metadata": transaction.metadata
        }
        
        result = await self._make_request("POST", endpoint, json=payload)
        
        # Add processing metadata
        result['api_response_time'] = result.get('response_time_ms', 0)
        result['nexum_transaction_id'] = result.get('transaction_id')
        
        return result
    
    async def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make HTTP request with retry logic and error handling"""
        
        for attempt in range(self.config.max_retries + 1):
            try:
                start_time = time.time()
                
                response = await self.client.request(method, endpoint, **kwargs)
                response.raise_for_status()
                
                end_time = time.time()
                result = response.json()
                result['response_time_ms'] = (end_time - start_time) * 1000
                
                return result
                
            except httpx.TimeoutException:
                if attempt < self.config.max_retries:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                    continue
                raise
                
            except httpx.HTTPStatusError as e:
                if e.response.status_code >= 500 and attempt < self.config.max_retries:
                    await asyncio.sleep(2 ** attempt)
                    continue
                raise
                
            except Exception as e:
                await self.handle_error(e)
                if attempt < self.config.max_retries:
                    continue
                raise
    
    async def health_check(self) -> Dict[str, Any]:
        """Check Nexum system health"""
        try:
            response = await self.client.get("/health")
            response.raise_for_status()
            
            data = response.json()
            return {
                'status': 'healthy',
                'response_time_ms': data.get('response_time', 0),
                'version': data.get('version', 'unknown'),
                'database_status': data.get('database', 'unknown')
            }
            
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
                'last_check': time.time()
            }
```

### Mock Connector for Testing

```python
class MockConnector(BaseConnector):
    """Mock connector for testing without external dependencies"""
    
    def __init__(self, config: ConnectionConfig):
        super().__init__(config)
        self.mock_latency_ms = 25  # Simulated API latency
        self.mock_error_rate = 0.01  # 1% error rate
        
    async def connect(self) -> bool:
        """Mock connection always succeeds"""
        await asyncio.sleep(0.1)  # Simulate connection delay
        self.is_connected = True
        return True
    
    async def create_customer(self, customer: Customer) -> Dict[str, Any]:
        """Mock customer creation"""
        await self._simulate_api_call()
        
        return {
            'customer_id': f'mock_cust_{uuid.uuid4().hex[:8]}',
            'status': 'created',
            'response_time_ms': self.mock_latency_ms
        }
    
    async def process_transaction(self, transaction: Transaction) -> Dict[str, Any]:
        """Mock transaction processing"""
        await self._simulate_api_call()
        
        # Mock fraud score (if this were Bastion)
        mock_fraud_score = random.random() * 0.3  # Low fraud scores for normal tx
        
        return {
            'transaction_id': f'mock_txn_{uuid.uuid4().hex[:8]}',
            'status': 'approved',
            'fraud_score': mock_fraud_score,
            'response_time_ms': self.mock_latency_ms
        }
    
    async def _simulate_api_call(self):
        """Simulate API call with realistic timing and error rates"""
        
        # Simulate network latency
        latency_seconds = self.mock_latency_ms / 1000
        await asyncio.sleep(latency_seconds)
        
        # Simulate random errors
        if random.random() < self.mock_error_rate:
            raise httpx.HTTPStatusError("Mock API error", 
                                      request=None, 
                                      response=httpx.Response(500))
```

---

## Metrics Collection

### Metrics Architecture

```python
from dataclasses import dataclass
from typing import Dict, List, Any, Optional
import time
from collections import deque, defaultdict
import asyncio

@dataclass
class MetricPoint:
    """Individual metric data point"""
    timestamp: float
    value: float
    tags: Dict[str, str] = None
    
class MetricsCollector:
    """Central metrics collection and aggregation system"""
    
    def __init__(self, config: MetricsConfig):
        self.config = config
        self.metrics: Dict[str, deque] = defaultdict(
            lambda: deque(maxlen=self._calculate_max_points())
        )
        self.aggregations: Dict[str, Dict[str, float]] = defaultdict(dict)
        self.subscribers: List[callable] = []
        
        # Start collection background task
        self._collection_task = None
        if config.enabled:
            self._collection_task = asyncio.create_task(self._collection_loop())
    
    def _calculate_max_points(self) -> int:
        """Calculate maximum points to retain in memory"""
        retention_seconds = self.config.retention_minutes * 60
        collection_interval = self.config.collect_interval_seconds
        return int(retention_seconds / collection_interval) + 1
    
    async def record_metric(self, name: str, value: float, tags: Dict[str, str] = None):
        """Record a single metric point"""
        point = MetricPoint(
            timestamp=time.time(),
            value=value,
            tags=tags or {}
        )
        
        self.metrics[name].append(point)
        
        # Notify subscribers of new metric
        for subscriber in self.subscribers:
            try:
                await subscriber(name, point)
            except Exception as e:
                logger.warning(f"Metrics subscriber error: {e}")
    
    async def record_transaction_metric(self, transaction: Transaction, 
                                      api_response: Dict[str, Any]):
        """Record transaction-specific metrics"""
        
        # Transaction rate (TPS)
        await self.record_metric("transactions_per_second", 1.0)
        
        # Transaction amount
        await self.record_metric("transaction_amount", transaction.amount, {
            "type": transaction.transaction_type,
            "customer": transaction.customer_id
        })
        
        # API performance
        if 'response_time_ms' in api_response:
            await self.record_metric("api_latency_ms", 
                                    api_response['response_time_ms'], {
                "service": "nexum"
            })
        
        # Fraud scoring
        if 'fraud_score' in api_response:
            await self.record_metric("fraud_score", 
                                    api_response['fraud_score'], {
                "transaction_id": transaction.id
            })
    
    async def get_aggregated_metrics(self, time_window_minutes: int = 5) -> Dict[str, Dict[str, float]]:
        """Get aggregated metrics for specified time window"""
        
        cutoff_time = time.time() - (time_window_minutes * 60)
        aggregated = {}
        
        for metric_name, points in self.metrics.items():
            # Filter points within time window
            recent_points = [p for p in points if p.timestamp >= cutoff_time]
            
            if not recent_points:
                continue
            
            values = [p.value for p in recent_points]
            
            aggregated[metric_name] = {
                'count': len(values),
                'sum': sum(values),
                'avg': sum(values) / len(values),
                'min': min(values),
                'max': max(values),
                'p50': self._percentile(values, 50),
                'p95': self._percentile(values, 95),
                'p99': self._percentile(values, 99)
            }
        
        return aggregated
    
    def subscribe(self, callback: callable):
        """Subscribe to real-time metric updates"""
        self.subscribers.append(callback)
    
    async def _collection_loop(self):
        """Background task for periodic metric collection"""
        
        while True:
            try:
                # Collect system metrics
                await self._collect_system_metrics()
                
                # Update aggregations
                await self._update_aggregations()
                
                # Export to CSV if configured
                if self.config.export_csv:
                    await self._export_csv()
                
                # Wait for next collection interval
                await asyncio.sleep(self.config.collect_interval_seconds)
                
            except Exception as e:
                logger.error(f"Metrics collection error: {e}")
                await asyncio.sleep(1)  # Brief pause before retry
    
    async def _collect_system_metrics(self):
        """Collect system-level metrics"""
        import psutil
        
        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=None)
        await self.record_metric("system_cpu_percent", cpu_percent)
        
        # Memory usage  
        memory = psutil.virtual_memory()
        await self.record_metric("system_memory_percent", memory.percent)
        await self.record_metric("system_memory_used_mb", memory.used / 1024 / 1024)
        
        # Network I/O
        net_io = psutil.net_io_counters()
        await self.record_metric("network_bytes_sent", net_io.bytes_sent)
        await self.record_metric("network_bytes_recv", net_io.bytes_recv)
        
        # Disk I/O
        disk_io = psutil.disk_io_counters()
        if disk_io:  # May be None on some systems
            await self.record_metric("disk_read_bytes", disk_io.read_bytes)
            await self.record_metric("disk_write_bytes", disk_io.write_bytes)
    
    @staticmethod
    def _percentile(values: List[float], percentile: int) -> float:
        """Calculate percentile of values"""
        if not values:
            return 0.0
        
        sorted_values = sorted(values)
        index = (percentile / 100) * (len(sorted_values) - 1)
        
        if index.is_integer():
            return sorted_values[int(index)]
        
        # Interpolate between values
        lower_index = int(index)
        upper_index = lower_index + 1
        weight = index - lower_index
        
        return (sorted_values[lower_index] * (1 - weight) + 
                sorted_values[upper_index] * weight)
```

---

## Dashboard WebSocket Protocol

### WebSocket Manager

```python
from fastapi import WebSocket
from typing import Dict, List, Set
import json
import asyncio
from enum import Enum

class MessageType(Enum):
    SUBSCRIBE = "subscribe"
    UNSUBSCRIBE = "unsubscribe"
    METRICS_UPDATE = "metrics_update"
    TRANSACTION_FEED = "transaction_feed"
    FRAUD_ALERT = "fraud_alert"
    SYSTEM_STATUS = "system_status"
    CONTROL_COMMAND = "control_command"

class WebSocketManager:
    """Manages WebSocket connections and message broadcasting"""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.subscriptions: Dict[WebSocket, Set[str]] = {}
        self.connection_metadata: Dict[WebSocket, Dict] = {}
    
    async def connect(self, websocket: WebSocket):
        """Accept new WebSocket connection"""
        await websocket.accept()
        self.active_connections.append(websocket)
        self.subscriptions[websocket] = set()
        self.connection_metadata[websocket] = {
            'connected_at': time.time(),
            'message_count': 0,
            'last_activity': time.time()
        }
        
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")
    
    async def disconnect(self, websocket: WebSocket):
        """Clean up disconnected WebSocket"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            
        if websocket in self.subscriptions:
            del self.subscriptions[websocket]
            
        if websocket in self.connection_metadata:
            del self.connection_metadata[websocket]
        
        logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")
    
    async def handle_message(self, websocket: WebSocket, message: str):
        """Handle incoming WebSocket message"""
        try:
            data = json.loads(message)
            message_type = data.get('type')
            
            self.connection_metadata[websocket]['message_count'] += 1
            self.connection_metadata[websocket]['last_activity'] = time.time()
            
            if message_type == MessageType.SUBSCRIBE.value:
                await self._handle_subscribe(websocket, data)
            elif message_type == MessageType.UNSUBSCRIBE.value:
                await self._handle_unsubscribe(websocket, data)
            elif message_type == MessageType.CONTROL_COMMAND.value:
                await self._handle_control_command(websocket, data)
            else:
                await self._send_error(websocket, f"Unknown message type: {message_type}")
                
        except json.JSONDecodeError:
            await self._send_error(websocket, "Invalid JSON format")
        except Exception as e:
            await self._send_error(websocket, f"Message handling error: {str(e)}")
    
    async def _handle_subscribe(self, websocket: WebSocket, data: Dict):
        """Handle subscription request"""
        topics = data.get('topics', [])
        
        if not isinstance(topics, list):
            await self._send_error(websocket, "Topics must be a list")
            return
        
        valid_topics = {'metrics', 'transactions', 'fraud_alerts', 'system_status'}
        invalid_topics = set(topics) - valid_topics
        
        if invalid_topics:
            await self._send_error(websocket, f"Invalid topics: {invalid_topics}")
            return
        
        self.subscriptions[websocket].update(topics)
        
        await self._send_message(websocket, {
            'type': 'subscription_confirmed',
            'topics': list(self.subscriptions[websocket])
        })
    
    async def _handle_unsubscribe(self, websocket: WebSocket, data: Dict):
        """Handle unsubscription request"""
        topics = data.get('topics', [])
        
        for topic in topics:
            self.subscriptions[websocket].discard(topic)
        
        await self._send_message(websocket, {
            'type': 'unsubscription_confirmed',
            'topics': list(self.subscriptions[websocket])
        })
    
    async def broadcast_metrics(self, metrics: Dict[str, Any]):
        """Broadcast metrics update to subscribed clients"""
        message = {
            'type': MessageType.METRICS_UPDATE.value,
            'timestamp': time.time(),
            'data': metrics
        }
        
        await self._broadcast_to_topic('metrics', message)
    
    async def broadcast_transaction(self, transaction: Transaction, fraud_score: float):
        """Broadcast new transaction to subscribed clients"""
        message = {
            'type': MessageType.TRANSACTION_FEED.value,
            'timestamp': time.time(),
            'data': {
                'id': transaction.id,
                'customer': f"{transaction.customer.profile.first_name} {transaction.customer.profile.last_name}",
                'amount': transaction.amount,
                'merchant': transaction.merchant.name if transaction.merchant else 'N/A',
                'fraud_score': fraud_score,
                'risk_level': self._calculate_risk_level(fraud_score),
                'transaction_type': transaction.transaction_type
            }
        }
        
        await self._broadcast_to_topic('transactions', message)
        
        # Also send fraud alert if high risk
        if fraud_score > 0.8:
            await self.broadcast_fraud_alert(transaction, fraud_score)
    
    async def broadcast_fraud_alert(self, transaction: Transaction, fraud_score: float):
        """Broadcast fraud alert for high-risk transactions"""
        message = {
            'type': MessageType.FRAUD_ALERT.value,
            'timestamp': time.time(),
            'severity': 'high' if fraud_score > 0.9 else 'medium',
            'data': {
                'transaction_id': transaction.id,
                'customer': f"{transaction.customer.profile.first_name} {transaction.customer.profile.last_name}",
                'amount': transaction.amount,
                'fraud_score': fraud_score,
                'risk_factors': transaction.risk_factors if hasattr(transaction, 'risk_factors') else []
            }
        }
        
        await self._broadcast_to_topic('fraud_alerts', message)
    
    async def _broadcast_to_topic(self, topic: str, message: Dict):
        """Broadcast message to all clients subscribed to topic"""
        disconnected = []
        
        for websocket in self.active_connections:
            if topic in self.subscriptions.get(websocket, set()):
                try:
                    await self._send_message(websocket, message)
                except Exception as e:
                    logger.warning(f"Failed to send message to WebSocket: {e}")
                    disconnected.append(websocket)
        
        # Clean up disconnected clients
        for websocket in disconnected:
            await self.disconnect(websocket)
    
    async def _send_message(self, websocket: WebSocket, message: Dict):
        """Send message to specific WebSocket"""
        try:
            await websocket.send_text(json.dumps(message))
        except Exception as e:
            logger.error(f"WebSocket send error: {e}")
            raise
    
    async def _send_error(self, websocket: WebSocket, error_message: str):
        """Send error message to WebSocket"""
        error_response = {
            'type': 'error',
            'message': error_message,
            'timestamp': time.time()
        }
        
        try:
            await self._send_message(websocket, error_response)
        except Exception as e:
            logger.error(f"Failed to send error message: {e}")
    
    @staticmethod
    def _calculate_risk_level(fraud_score: float) -> str:
        """Convert fraud score to risk level"""
        if fraud_score >= 0.8:
            return 'high'
        elif fraud_score >= 0.5:
            return 'medium'
        elif fraud_score >= 0.3:
            return 'low'
        else:
            return 'very_low'

# Global WebSocket manager instance
websocket_manager = WebSocketManager()
```

### Dashboard WebSocket Endpoints

```python
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from .ws import websocket_manager

app = FastAPI()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Main WebSocket endpoint for dashboard communication"""
    await websocket_manager.connect(websocket)
    
    try:
        while True:
            # Wait for messages from client
            message = await websocket.receive_text()
            await websocket_manager.handle_message(websocket, message)
            
    except WebSocketDisconnect:
        await websocket_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await websocket_manager.disconnect(websocket)

@app.get("/api/status")
async def get_status():
    """REST API endpoint for system status"""
    return {
        'status': 'running',
        'active_connections': len(websocket_manager.active_connections),
        'uptime': time.time() - app.start_time if hasattr(app, 'start_time') else 0
    }
```

---

## Extension Points

### Custom Transaction Patterns

```python
# Custom transaction pattern example
from simulator.generators.transactions import TransactionTemplate, TransactionType

def register_custom_patterns():
    """Register custom transaction patterns"""
    
    # Cryptocurrency exchange pattern
    crypto_pattern = TransactionTemplate(
        name="crypto_exchange",
        transaction_type=TransactionType.TRANSFER,
        amount_min=50.0,
        amount_max=50000.0,
        frequency_per_month=2.0,
        preferred_channels=[TransactionChannel.ONLINE],
        preferred_hours=(0, 23),  # 24/7 crypto markets
        amount_distribution="power_law",  # Most small, few large
        seasonal_multiplier={1: 2.0, 12: 1.5},  # Higher in Jan/Dec
        risk_factors=["high_volatility", "regulatory_uncertainty"],
        metadata_generators=[
            CryptoCurrencyGenerator(),
            ExchangePlatformGenerator(),
            WalletAddressGenerator()
        ]
    )
    
    # Register with transaction generator
    TransactionGenerator.register_template(crypto_pattern)

# Custom fraud pattern example
class AIEvasionFraud(FraudPattern):
    """Advanced AI-powered evasion fraud pattern"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.ml_model = self.load_evasion_model()
        self.detection_history = []
    
    async def generate_fraud_transactions(self, targets: List[Customer]) -> List[Transaction]:
        """Generate AI-evaded fraud transactions"""
        
        transactions = []
        
        for target in targets:
            # Use ML model to predict detection likelihood
            base_transaction = self.generate_base_transaction(target)
            detection_probability = self.ml_model.predict_detection(base_transaction)
            
            # If high detection risk, apply evasion techniques
            if detection_probability > 0.7:
                evaded_transaction = await self.apply_evasion_techniques(
                    base_transaction, detection_probability
                )
                transactions.append(evaded_transaction)
            else:
                transactions.append(base_transaction)
        
        return transactions
    
    async def apply_evasion_techniques(self, transaction: Transaction, 
                                     detection_risk: float) -> Transaction:
        """Apply ML-guided evasion techniques"""
        
        # Amount manipulation
        if detection_risk > 0.8:
            transaction.amount *= random.uniform(0.7, 0.9)  # Reduce amount
        
        # Timing manipulation
        if "velocity_detection" in self.get_risk_factors():
            delay = self.calculate_optimal_delay(transaction)
            transaction.schedule_after_delay(delay)
        
        # Geographic spoofing
        if "location_detection" in self.get_risk_factors():
            transaction.location = self.generate_believable_location(
                transaction.customer_id
            )
        
        return transaction

# Register custom fraud pattern
FraudGenerator.register_pattern("ai_evasion", AIEvasionFraud)
```

### Custom Metrics

```python
class CustomMetricsCollector:
    """Custom business metrics collection"""
    
    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics = metrics_collector
        
        # Subscribe to transaction events
        self.metrics.subscribe(self.handle_metric_event)
    
    async def handle_metric_event(self, metric_name: str, point: MetricPoint):
        """Handle metric events and derive custom metrics"""
        
        if metric_name == "transaction_amount":
            await self.calculate_business_metrics(point)
    
    async def calculate_business_metrics(self, point: MetricPoint):
        """Calculate business-specific metrics"""
        
        amount = point.value
        customer_type = point.tags.get('customer_type', 'standard')
        
        # Revenue calculation
        if customer_type == 'premium':
            revenue = amount * 0.015  # 1.5% fee for premium
        else:
            revenue = amount * 0.010  # 1.0% fee for standard
        
        await self.metrics.record_metric("revenue", revenue, {
            'customer_type': customer_type
        })
        
        # Risk-adjusted volume
        fraud_score = point.tags.get('fraud_score', 0.0)
        risk_weight = 1.0 - min(float(fraud_score), 0.9)  # Higher risk = lower weight
        
        risk_adjusted_volume = amount * risk_weight
        await self.metrics.record_metric("risk_adjusted_volume", 
                                        risk_adjusted_volume)
```

---

## Performance Considerations

### Async Programming Patterns

The simulator is built on async/await patterns for maximum concurrency:

```python
# Example: Processing multiple transactions concurrently
async def process_transaction_batch(transactions: List[Transaction]) -> List[Dict]:
    """Process multiple transactions concurrently"""
    
    # Create tasks for concurrent execution
    tasks = []
    for transaction in transactions:
        task = asyncio.create_task(self.process_single_transaction(transaction))
        tasks.append(task)
    
    # Wait for all tasks to complete
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Handle any exceptions
    successful_results = []
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            logger.error(f"Transaction {transactions[i].id} failed: {result}")
        else:
            successful_results.append(result)
    
    return successful_results
```

### Memory Management

```python
class MemoryEfficientGenerator:
    """Generator that manages memory usage for large simulations"""
    
    def __init__(self, config: Config):
        self.config = config
        self.batch_size = min(config.customers // 10, 1000)  # Adaptive batch size
        
    async def generate_customers_streaming(self) -> AsyncGenerator[Customer, None]:
        """Generate customers in batches to manage memory"""
        
        total_customers = self.config.customers
        
        for batch_start in range(0, total_customers, self.batch_size):
            batch_end = min(batch_start + self.batch_size, total_customers)
            batch_size = batch_end - batch_start
            
            # Generate batch
            customers = await self.generate_customer_batch(batch_size)
            
            # Yield each customer
            for customer in customers:
                yield customer
            
            # Clear batch from memory
            del customers
            
            # Optional: Force garbage collection for large batches
            if batch_size > 500:
                import gc
                gc.collect()
```

### Database Connection Optimization

```python
class OptimizedNexumConnector(NexumConnector):
    """Optimized connector with connection pooling and batching"""
    
    def __init__(self, config: ConnectionConfig):
        super().__init__(config)
        self.batch_queue = []
        self.batch_size = 100
        self.batch_timeout = 5.0  # seconds
        
    async def connect(self) -> bool:
        """Connect with optimized connection pool"""
        
        # Configure connection pool for high throughput
        limits = httpx.Limits(
            max_connections=50,
            max_keepalive_connections=20,
            keepalive_expiry=300  # 5 minutes
        )
        
        timeout = httpx.Timeout(
            connect=10.0,
            read=30.0,
            write=10.0,
            pool=5.0
        )
        
        self.client = httpx.AsyncClient(
            base_url=self.config.nexum_url,
            limits=limits,
            timeout=timeout,
            http2=True  # Enable HTTP/2 for better performance
        )
        
        return await super().connect()
    
    async def process_transaction_batch(self, transactions: List[Transaction]) -> List[Dict]:
        """Process transactions in batches for better performance"""
        
        # Prepare batch payload
        batch_payload = {
            'transactions': [
                {
                    'customer_id': tx.customer_id,
                    'amount': tx.amount,
                    'type': tx.transaction_type,
                    'merchant': tx.merchant.name if tx.merchant else None
                }
                for tx in transactions
            ]
        }
        
        # Single API call for entire batch
        response = await self.client.post('/transactions/batch', json=batch_payload)
        response.raise_for_status()
        
        return response.json()['results']
```

---

## Deployment Architecture

### Docker Compose Production Setup

```yaml
# production-docker-compose.yml
version: '3.8'

services:
  simulator:
    build: .
    environment:
      - NEXUM_URL=http://nexum:8090
      - BASTION_URL=http://bastion:8080
      - KAFKA_SERVERS=kafka:9092
      - LOG_LEVEL=INFO
    depends_on:
      - nexum
      - bastion
      - kafka
    ports:
      - "8095:8095"
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: '2.0'
        reservations:
          memory: 1G
          cpus: '1.0'
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8095/api/status"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  nexum:
    image: nexum:latest
    environment:
      - DATABASE_URL=postgresql://nexum:password@postgres:5432/nexum
    depends_on:
      - postgres
    ports:
      - "8090:8090"

  bastion:
    image: bastion:latest
    environment:
      - KAFKA_SERVERS=kafka:9092
    depends_on:
      - kafka
    ports:
      - "8080:8080"

  postgres:
    image: postgres:14
    environment:
      - POSTGRES_DB=nexum
      - POSTGRES_USER=nexum
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  kafka:
    image: confluentinc/cp-kafka:latest
    environment:
      - KAFKA_ZOOKEEPER_CONNECT=zookeeper:2181
      - KAFKA_ADVERTISED_LISTENERS=PLAINTEXT://kafka:9092
      - KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR=1
    depends_on:
      - zookeeper
    ports:
      - "9092:9092"

  zookeeper:
    image: confluentinc/cp-zookeeper:latest
    environment:
      - ZOOKEEPER_CLIENT_PORT=2181
    ports:
      - "2181:2181"

volumes:
  postgres_data:
```

### Kubernetes Deployment

```yaml
# kubernetes/simulator-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: banking-simulator
spec:
  replicas: 3
  selector:
    matchLabels:
      app: banking-simulator
  template:
    metadata:
      labels:
        app: banking-simulator
    spec:
      containers:
      - name: simulator
        image: banking-simulator:latest
        ports:
        - containerPort: 8095
        env:
        - name: NEXUM_URL
          value: "http://nexum-service:8090"
        - name: BASTION_URL
          value: "http://bastion-service:8080"
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "2"
        livenessProbe:
          httpGet:
            path: /api/status
            port: 8095
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /api/status
            port: 8095
          initialDelaySeconds: 5
          periodSeconds: 5

---
apiVersion: v1
kind: Service
metadata:
  name: simulator-service
spec:
  selector:
    app: banking-simulator
  ports:
  - protocol: TCP
    port: 8095
    targetPort: 8095
  type: LoadBalancer
```

This architecture provides a solid foundation for extending and customizing the Banking Simulator while maintaining performance, observability, and reliability at scale.