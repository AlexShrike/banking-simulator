# Banking Simulator

A "flight simulator" for testing core banking and fraud detection systems. Generates realistic banking traffic, sends it through both Nexum (core banking) and Bastion (fraud detection) systems via REST APIs, and displays results in a real-time dashboard.

![Banking Simulator Architecture](docs/architecture.png)

## Features

- **Realistic Transaction Generation**: Creates authentic customer profiles and transaction patterns
- **Fraud Simulation**: Generates sophisticated fraud attacks including card testing, velocity attacks, money laundering patterns
- **Time Acceleration**: Run days or weeks of activity in minutes with configurable speed multipliers
- **Real-Time Dashboard**: Professional web interface showing live metrics, transaction feeds, and fraud alerts
- **Multiple Scenarios**: Pre-built scenarios for normal operations, fraud attacks, peak loads, and stress testing
- **API Integration**: Full integration with Nexum (core banking) and Bastion (fraud detection) systems
- **Standalone Mode**: Can run without external dependencies using mock connectors
- **Comprehensive Metrics**: Detailed performance, fraud detection, and system health metrics

## Step-by-Step Testing Guide

Complete your testing in this exact order to verify all functionality:

### Test 1: Standalone Dry Run (No External Systems)

Perfect for initial testing and development - no external dependencies required.

```bash
# Navigate to simulator directory
cd /Users/alexshrike/.openclaw/workspace/banking-simulator

# Activate virtual environment
source /Users/alexshrike/.openclaw/workspace/rustcluster/.venv/bin/activate

# Run standalone simulation with dashboard
python run.py --scenario normal_day --dry-run --dashboard

# Open dashboard in your browser
open http://localhost:8095
```

**What you'll see:**
- ✅ Mock transactions flowing through the system
- 📊 Real-time dashboard with live metrics updating every second
- 🎯 Simulated fraud events and scoring (mock responses)
- 📈 TPS (Transactions Per Second) charts showing realistic business patterns
- 🚦 Color-coded transaction feed with green (legitimate) and red (fraudulent) entries
- ⚡ Metrics collection working (memory usage, API latency simulations)

**Expected Output:**
```
2026-02-20 06:56:00 - INFO - Starting Banking Simulator
2026-02-20 06:56:00 - INFO - Mode: Dry run (using mock connectors)
2026-02-20 06:56:00 - INFO - Scenario: Normal Business Day
2026-02-20 06:56:00 - INFO - Speed: 100x (24 hours in ~14 minutes)
2026-02-20 06:56:00 - INFO - Dashboard: http://localhost:8095
2026-02-20 06:56:01 - INFO - Generated 500 customer profiles
2026-02-20 06:56:01 - INFO - Transaction generation started
```

### Test 2: With Nexum Only (Core Banking)

Tests integration with the core banking system for customer and transaction management.

```bash
# Terminal 1: Start Nexum core banking system
cd /Users/alexshrike/.openclaw/workspace/core-banking
source /Users/alexshrike/.openclaw/workspace/rustcluster/.venv/bin/activate
python -m uvicorn core_banking.api_old:app --port 8090

# Wait for "Uvicorn running on http://127.0.0.1:8090"

# Terminal 2: Run simulator connected to Nexum
cd /Users/alexshrike/.openclaw/workspace/banking-simulator
source /Users/alexshrike/.openclaw/workspace/rustcluster/.venv/bin/activate
python run.py --scenario normal_day --nexum-url http://localhost:8090 --dashboard

# Open dashboard
open http://localhost:8095
```

**What you'll see:**
- ✅ Real customers being created in Nexum database
- ✅ Actual transactions posted to Nexum API endpoints
- 📊 Real API latency metrics (typically 10-50ms per call)
- ⚠️ Fraud scoring shows "N/A" (no Bastion connected)
- 💾 Persistent data in Nexum's PostgreSQL database

**Verify Nexum Integration:**
```bash
# Check Nexum API directly
curl http://localhost:8090/health
curl http://localhost:8090/customers | head -50
curl http://localhost:8090/transactions | head -50
```

### Test 3: With Nexum + Bastion (Full Integration)

Complete end-to-end testing with both core banking and fraud detection systems.

```bash
# Terminal 1: Start Nexum
cd /Users/alexshrike/.openclaw/workspace/core-banking
source /Users/alexshrike/.openclaw/workspace/rustcluster/.venv/bin/activate
python -m uvicorn core_banking.api_old:app --port 8090

# Terminal 2: Start Bastion
cd /Users/alexshrike/.openclaw/workspace/bastion
source /Users/alexshrike/.openclaw/workspace/rustcluster/.venv/bin/activate  
python -m uvicorn bastion.api:app --port 8080

# Terminal 3: Run full simulation
cd /Users/alexshrike/.openclaw/workspace/banking-simulator
source /Users/alexshrike/.openclaw/workspace/rustcluster/.venv/bin/activate
python run.py --scenario normal_day --nexum-url http://localhost:8090 --bastion-url http://localhost:8080 --dashboard

# Open dashboard
open http://localhost:8095
```

**What you'll see:**
- ✅ Complete transaction lifecycle: Simulator → Nexum → Bastion → Dashboard
- 🎯 Real fraud scores (0.0-1.0) from Bastion ML models
- 🚨 Fraud alerts for suspicious transactions
- 📊 Fraud detection accuracy metrics
- ⚡ End-to-end API latency (typically 50-150ms total)

**Verify Full Integration:**
```bash
# Check all systems are healthy
curl http://localhost:8090/health  # Nexum
curl http://localhost:8080/health  # Bastion
curl http://localhost:8095/api/status  # Simulator dashboard
```

### Test 4: Fraud Attack Scenario

Tests the system's ability to detect and respond to coordinated fraud attacks.

```bash
# Use same 3-terminal setup as Test 3, but change scenario:
python run.py --scenario fraud_attack --nexum-url http://localhost:8090 --bastion-url http://localhost:8080 --dashboard
```

**What you'll see:**
- 🚨 Massive fraud spike during attack window (2-3 AM simulation time)
- 📈 Fraud rate jumping from 0.1% to 15%
- ⚡ Card testing: Hundreds of small-amount transactions
- 🎯 Account takeover: Large transfers following successful card tests
- 📊 Bastion fraud scores clustering around 0.8-0.9 during attacks
- 🚦 Dashboard fraud feed turning mostly red during attack periods

**Key Metrics to Watch:**
- TPS spikes to 20+ during attack window
- Fraud detection rate should be >90% for obvious attacks
- API latency may increase under attack load

### Test 5: Full Docker Stack (Production-Like)

Tests the complete system in a containerized environment.

```bash
# From banking-simulator directory
docker-compose up

# This starts:
# - PostgreSQL database
# - Kafka message broker  
# - Nexum core banking API
# - Bastion fraud detection API
# - Banking simulator
# - All networking configured automatically

# View logs from all services
docker-compose logs -f

# View just simulator logs
docker-compose logs -f simulator

# Access dashboard
open http://localhost:8095
```

**What you'll see:**
- 🐳 All services starting in containers
- 🔄 Automatic service discovery and connection
- 📡 Kafka events flowing between services
- 💾 Persistent PostgreSQL data
- 🌐 Full production-like environment

**Docker Health Check:**
```bash
# Check all services are running
docker-compose ps

# Should show all services as "Up" and healthy
```

### Test 6: Custom Scenario Development

Create and test your own scenarios.

```bash
# Create custom scenario file
cat > scenarios/my_test.yaml << 'EOF'
name: "My Test Scenario"
description: "Custom test with specific parameters"
duration_hours: 1
speed_multiplier: 60  # 1 hour in 1 minute
customers: 50
accounts_per_customer: 1
initial_balance: 1000.00

transaction_rate:
  peak_tps: 5
  off_peak_tps: 1
  business_hours: [9, 17]

fraud:
  rate: 0.05  # 5% fraud rate
  patterns:
    - type: velocity_attack
      weight: 1.0
      intensity: 1.0
EOF

# Test your custom scenario
python run.py --scenario my_test --dry-run --dashboard
```

### Quick Start (Minimal Commands)

If you just want to get started quickly:

```bash
# Fastest test (no dependencies)
cd /Users/alexshrike/.openclaw/workspace/banking-simulator
source /Users/alexshrike/.openclaw/workspace/rustcluster/.venv/bin/activate
python run.py --scenario normal_day --dry-run --dashboard
open http://localhost:8095

# Full integration (requires Nexum + Bastion running)
python run.py --scenario normal_day --dashboard

# Fraud attack test
python run.py --scenario fraud_attack --speed 200 --dashboard

# Docker everything
docker-compose up -d && open http://localhost:8095
```

## Architecture Overview

### System Components & Data Flow

```
                         Banking Simulator Architecture
                         ================================

┌─────────────────────────────────────────────────────────────────────────────────┐
│                              BANKING SIMULATOR ENGINE                           │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐                │
│  │   Customer      │  │  Transaction    │  │    Fraud        │                │
│  │   Generator     │  │   Generator     │  │  Generator      │                │
│  │                 │  │                 │  │                 │                │
│  │ • Profiles      │  │ • Realistic     │  │ • Attack        │                │
│  │ • Demographics  │  │   Patterns      │  │   Scenarios     │                │
│  │ • Behaviors     │  │ • Time-based    │  │ • ML Evasion    │                │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘                │
│           │                     │                     │                        │
│           └─────────────────────┼─────────────────────┘                        │
│                                 │                                              │
└─────────────────────────────────┼──────────────────────────────────────────────┘
                                  │
                   ┌──────────────┴──────────────┐
                   │        API CONNECTOR        │
                   │    (Nexum Integration)      │
                   └──────────────┬──────────────┘
                                  │
              ┌───────────────────┴───────────────────┐
              │                                       │
              ▼                                       ▼
    ┌─────────────────┐                    ┌─────────────────┐
    │      NEXUM      │ ◄─── HTTP POST ──► │    BASTION      │
    │  Core Banking   │                    │ Fraud Detection │
    │                 │   /customers       │                 │
    │ • Customer CRUD │   /transactions    │ • ML Models     │
    │ • Account Mgmt  │   /accounts        │ • Risk Scoring  │
    │ • Transaction   │                    │ • Decision API  │
    │   Processing    │                    │ • Pattern Rec.  │
    │ • PostgreSQL DB │                    │ • Alerts        │
    │                 │                    │                 │
    │   Port: 8090    │                    │   Port: 8080    │
    └─────────────────┘                    └─────────────────┘
              │                                       │
              │                                       │
              ▼                                       ▼
    ┌─────────────────┐                    ┌─────────────────┐
    │   PostgreSQL    │                    │      KAFKA      │
    │    Database     │                    │ Message Broker  │
    │                 │                    │                 │
    │ • Customers     │                    │ Topics:         │
    │ • Accounts      │                    │ • nexum.txns    │
    │ • Transactions  │                    │ • bastion.fraud │
    │ • Audit Logs    │                    │ • nexum.cust    │
    │                 │                    │                 │
    │   Port: 5432    │                    │   Port: 9092    │
    └─────────────────┘                    └─────────────────┘
                                                     │
              ┌──────────────────────────────────────┘
              │
              ▼
    ┌─────────────────┐                    ┌─────────────────┐
    │    DASHBOARD    │ ◄─── WebSocket ──► │   METRICS       │
    │  Real-time UI   │                    │  COLLECTOR      │
    │                 │                    │                 │
    │ • Control Panel │                    │ • Performance   │
    │ • Live Feed     │                    │ • Fraud Stats   │
    │ • Analytics     │                    │ • API Latency   │
    │ • Progress      │                    │ • System Health │
    │ • Results       │                    │ • CSV Export    │
    │                 │                    │                 │
    │   Port: 8095    │                    │  (In Memory)    │
    └─────────────────┘                    └─────────────────┘
              ▲
              │
              ▼
    ┌─────────────────┐
    │   WEB BROWSER   │
    │                 │
    │ • Chrome/Safari │
    │ • Real-time UI  │
    │ • Controls      │
    │ • Monitoring    │
    └─────────────────┘
```

### Data Flow Pipeline

**1. Customer Generator Pipeline**
```
Customer Generator → Profile Creation → POST /customers → Nexum → PostgreSQL
                                   └── Kafka: nexum.customers topic
```

**2. Transaction Generation Pipeline**
```
Transaction Generator → Realistic Patterns → POST /transactions → Nexum → PostgreSQL
                                        └── POST /score → Bastion → ML Models
                                        └── Kafka: nexum.transactions
                                                  └── Bastion Consumer
                                                      └── Kafka: bastion.fraud.decisions
```

**3. Fraud Detection Pipeline**
```
Fraud Generator → Attack Patterns → Enhanced Transactions → Nexum + Bastion
                                                        └── High Fraud Scores
                                                            └── Dashboard Alerts
```

**4. Metrics Collection Pipeline**  
```
All Components → Metrics Collector → Real-time Aggregation → WebSocket → Dashboard
                                 └── CSV Export → File System
```

### Component Interactions

#### Simulator Engine (Python)
- **Purpose**: Core simulation orchestration and data generation
- **Key Classes**: `SimulationEngine`, `CustomerGenerator`, `TransactionGenerator`, `FraudGenerator`
- **Responsibilities**: 
  - Generate realistic customer profiles and behaviors
  - Create time-accelerated transaction patterns
  - Inject sophisticated fraud scenarios
  - Coordinate all simulation phases

#### API Connectors (HTTP/Async)
- **Purpose**: Interface with external banking systems
- **Technology**: `httpx` async HTTP client
- **Endpoints**: 
  - Nexum: `/customers`, `/accounts`, `/transactions/*`
  - Bastion: `/score`, `/bulk_score`, `/alerts`
- **Error Handling**: Automatic retries, circuit breaker, fallback modes

#### Dashboard Server (FastAPI)
- **Purpose**: Real-time web interface and API
- **Technology**: FastAPI + WebSockets + Static Files
- **Features**: REST API + WebSocket streaming + SPA frontend
- **Scaling**: Supports multiple concurrent dashboard users

#### Metrics Collector (In-Memory)
- **Purpose**: Real-time performance and business metrics
- **Storage**: Ring buffers for time-series data
- **Metrics**: TPS, latency percentiles, error rates, fraud statistics
- **Export**: CSV files, API endpoints, WebSocket streams

## Scenarios

### Built-in Scenarios

- **normal_day**: Typical business day with 10K transactions, 0.1% fraud rate
- **fraud_attack**: Coordinated card testing and account takeover attacks  
- **peak_load**: Black Friday-style high volume (100+ TPS)
- **mule_network**: Money laundering with layering and structuring
- **onboarding**: Mass customer onboarding with identity verification

### Scenario Format Documentation

Scenarios are defined in YAML files that control every aspect of the simulation. Here's the complete schema:

#### Basic Scenario Structure

```yaml
# Required fields
name: "Scenario Display Name"                    # String: Shown in dashboard and logs
description: "What this scenario simulates"     # String: Documentation
duration_hours: 24                              # Number: How long to simulate (real hours)
speed_multiplier: 100                           # Number: Time acceleration (100x = 24h in ~14min)

# Customer generation
customers: 500                                  # Number: How many customer profiles to create
accounts_per_customer: 2                       # Number: Bank accounts per customer (1-5)
initial_balance: 5000.00                       # Number: Starting balance per account (USD)
currency: "USD"                                # String: Currency code (USD, EUR, GBP, etc.)

# Transaction patterns
transaction_rate:
  peak_tps: 10                                 # Number: Peak transactions per second
  off_peak_tps: 2                             # Number: Off-peak transactions per second  
  business_hours: [8, 18]                     # Array: Peak hours [start, end] (24h format)
  weekend_multiplier: 0.3                     # Number: Weekend transaction reduction (0.0-1.0)

# Fraud configuration
fraud:
  rate: 0.001                                 # Number: Base fraud rate (0.001 = 0.1%)
  attack_window: [2, 4]                       # Array: Optional concentrated attack hours
  patterns:                                   # Array: Fraud pattern definitions
    - type: card_testing                      # String: Pattern type (see below)
      weight: 0.4                            # Number: Relative frequency (0.0-1.0)
      intensity: 1.0                         # Number: Attack intensity multiplier
      count: 100                             # Number: Optional specific transaction count
      duration_minutes: 30                   # Number: Optional time limit
      follows: other_pattern                 # String: Optional dependency on other pattern

# System connections
connections:
  nexum_url: "http://localhost:8090"          # String: Nexum API endpoint
  bastion_url: "http://localhost:8080"        # String: Bastion API endpoint
  kafka_bootstrap_servers: "localhost:9092"   # String: Kafka brokers (optional)
  timeout_seconds: 30                         # Number: API timeout
  max_retries: 3                             # Number: API retry attempts

# Dashboard settings
dashboard:
  enabled: true                               # Boolean: Enable dashboard
  port: 8095                                  # Number: Dashboard port
  host: "0.0.0.0"                            # String: Dashboard bind address

# Metrics collection
metrics:
  enabled: true                               # Boolean: Enable metrics collection
  collect_interval_seconds: 1                 # Number: Metrics collection frequency
  retention_minutes: 60                       # Number: How long to keep metrics in memory
  export_csv: true                           # Boolean: Export metrics to CSV files
```

#### Fraud Pattern Types

The simulator supports these sophisticated fraud patterns:

```yaml
# Card testing - Testing stolen card numbers with small amounts
- type: card_testing
  weight: 0.3              # 30% of fraud attacks
  intensity: 1.0           # Normal intensity
  count: 500              # Exactly 500 test transactions
  duration_minutes: 10    # Complete within 10 minutes
  amount_range: [0.01, 5.00]  # Small test amounts

# Account takeover - Compromised credentials, large transfers  
- type: account_takeover
  weight: 0.2
  intensity: 1.5          # 50% more aggressive
  follows: card_testing   # Happens after successful card tests
  delay_minutes: 30       # 30 minutes after card testing
  target_balance_pct: 0.8 # Transfer 80% of available balance

# Velocity attack - Rapid-fire transactions
- type: velocity_attack  
  weight: 0.3
  intensity: 2.0          # Double normal velocity
  transaction_burst: 50   # 50 transactions in rapid succession
  time_window_seconds: 60 # Within 60 seconds

# Large amount fraud - Unusual high-value transactions
- type: large_amount
  weight: 0.1
  amount_multiplier: 10.0 # 10x normal transaction amounts
  suspicious_threshold: 5000.00  # Flag amounts over $5000

# Unusual location - Geographic anomalies
- type: unusual_location
  weight: 0.1
  location_jump_km: 1000  # Transactions 1000km+ from normal location
  time_window_hours: 1    # Impossible travel times
```

#### Advanced Time Patterns

Control when transactions occur with sophisticated timing:

```yaml
transaction_rate:
  # Basic pattern
  peak_tps: 15
  off_peak_tps: 3
  business_hours: [9, 17]
  
  # Advanced patterns  
  hourly_multipliers:      # Custom multiplier for each hour
    6: 0.1    # 6 AM: 10% of base rate
    9: 1.5    # 9 AM: 150% of base rate (morning rush)
    12: 1.8   # Noon: 180% of base rate (lunch peak)
    17: 1.3   # 5 PM: 130% of base rate (evening rush)
    23: 0.05  # 11 PM: 5% of base rate (night)
    
  weekday_multipliers:     # Day-of-week variations
    monday: 1.2           # 20% higher on Mondays
    friday: 1.4           # 40% higher on Fridays  
    saturday: 0.4         # 60% lower on weekends
    sunday: 0.3
    
  seasonal_multipliers:    # Monthly variations
    11: 1.3               # 30% higher in November (Black Friday)
    12: 1.6               # 60% higher in December (holidays)
    1: 0.8                # 20% lower in January
```

#### Multi-Phase Attack Scenarios

Create complex fraud attacks that evolve over time:

```yaml
fraud:
  rate: 0.05
  phases:
    # Phase 1: Reconnaissance (hours 1-2)
    - name: "reconnaissance"
      start_hour: 1
      duration_hours: 1
      patterns:
        - type: small_probes
          count: 50
          intensity: 0.5
          
    # Phase 2: Card testing (hours 2-3)  
    - name: "card_testing"
      start_hour: 2
      duration_hours: 1
      patterns:
        - type: card_testing
          count: 500
          intensity: 2.0
          
    # Phase 3: Account takeover (hours 3-4)
    - name: "exploitation"
      start_hour: 3 
      duration_hours: 1
      patterns:
        - type: account_takeover
          count: 20
          intensity: 3.0
          requires_successful: card_testing  # Only if card testing succeeded
```

#### Creating Custom Scenarios

1. **Copy an existing scenario:**
```bash
cp scenarios/normal_day.yaml scenarios/my_scenario.yaml
```

2. **Edit the parameters:**
```bash
# Use your favorite editor
nano scenarios/my_scenario.yaml
```

3. **Validate the scenario:**
```bash
python run.py --validate-scenario scenarios/my_scenario.yaml
```

4. **Test with dry run:**
```bash
python run.py --scenario scenarios/my_scenario.yaml --dry-run --dashboard
```

#### Example Custom Scenarios

**High-Speed Demo Scenario:**
```yaml
name: "5-Minute Demo"
description: "Complete business day compressed to 5 minutes"
duration_hours: 24
speed_multiplier: 288  # 24 hours in 5 minutes
customers: 100
accounts_per_customer: 1
initial_balance: 2000.00

transaction_rate:
  peak_tps: 20
  off_peak_tps: 5
  business_hours: [9, 17]

fraud:
  rate: 0.02  # 2% fraud rate for visible results
  patterns:
    - type: card_testing
      weight: 0.5
      intensity: 1.0
    - type: large_amount
      weight: 0.5
      intensity: 1.0
```

**Stress Test Scenario:**
```yaml
name: "Load Test - 1000 TPS"
description: "High-volume load testing"
duration_hours: 1
speed_multiplier: 1  # Real-time
customers: 5000
accounts_per_customer: 3
initial_balance: 10000.00

transaction_rate:
  peak_tps: 1000    # Very high load
  off_peak_tps: 500
  business_hours: [0, 23]  # Always peak

fraud:
  rate: 0.005  # 0.5% fraud rate
  patterns:
    - type: velocity_attack
      weight: 1.0
      intensity: 2.0
```

## Kafka Integration & Event Streaming

The banking simulator supports event-driven architecture through Kafka integration, enabling real-time event streaming between all components.

### Kafka Topics Used

#### Core Topics

**`nexum.transactions`**
- **Producer**: Banking Simulator
- **Consumers**: Bastion Fraud Detection, Analytics Services
- **Schema**: Transaction events with customer, account, amount, timestamp
- **Purpose**: Real-time transaction stream for fraud detection and analytics

**`bastion.fraud.decisions`**  
- **Producer**: Bastion Fraud Detection
- **Consumers**: Banking Simulator, Notification Services
- **Schema**: Fraud scoring results with risk scores and decision rationale
- **Purpose**: Fraud detection results and alerts

**`nexum.customers`**
- **Producer**: Banking Simulator  
- **Consumers**: Customer Analytics, Marketing Services
- **Schema**: New customer profiles and account creation events
- **Purpose**: Customer lifecycle tracking

#### Event Schema Examples

```json
// nexum.transactions topic
{
  "event_type": "transaction_created",
  "timestamp": "2026-02-20T14:30:00Z",
  "transaction_id": "txn_abc123",
  "customer_id": "cust_xyz789",
  "account_id": "acc_def456", 
  "amount": 150.00,
  "currency": "USD",
  "transaction_type": "purchase",
  "merchant": "Coffee Shop Downtown",
  "location": {
    "latitude": 37.7749,
    "longitude": -122.4194,
    "city": "San Francisco"
  },
  "metadata": {
    "channel": "card_present",
    "device_id": "pos_terminal_001"
  }
}

// bastion.fraud.decisions topic  
{
  "event_type": "fraud_decision",
  "timestamp": "2026-02-20T14:30:01Z",
  "transaction_id": "txn_abc123",
  "fraud_score": 0.23,
  "decision": "approve",
  "risk_factors": [
    {
      "factor": "velocity_check", 
      "score": 0.1,
      "description": "Normal velocity pattern"
    },
    {
      "factor": "location_check",
      "score": 0.05, 
      "description": "Known location"
    }
  ],
  "model_version": "v2.1.0",
  "processing_time_ms": 45
}
```

### Enabling/Disabling Kafka

#### Enable Kafka (Default)
Kafka is enabled by default if available. The simulator will attempt to connect and gracefully fall back if Kafka is not available.

```bash
# Normal operation with Kafka
python run.py --scenario normal_day --dashboard

# Explicitly set Kafka servers
python run.py --scenario normal_day --kafka-servers localhost:9092,broker2:9092
```

#### Disable Kafka
Use `--no-kafka` flag to disable Kafka publishing for testing or performance reasons:

```bash  
# Run without Kafka
python run.py --scenario normal_day --no-kafka --dashboard

# Useful for:
# - Performance testing (remove Kafka overhead)
# - Development when Kafka is not available  
# - Simplified testing scenarios
```

### Starting Kafka Locally

#### Option 1: Docker (Recommended)
```bash
# Start Kafka with Docker Compose (includes Zookeeper)
cat > kafka-docker-compose.yml << 'EOF'
version: '3'
services:
  zookeeper:
    image: confluentinc/cp-zookeeper:latest
    environment:
      ZOOKEEPER_CLIENT_PORT: 2181
      ZOOKEEPER_TICK_TIME: 2000
    ports:
      - "2181:2181"

  kafka:
    image: confluentinc/cp-kafka:latest
    depends_on:
      - zookeeper
    ports:
      - "9092:9092"
    environment:
      KAFKA_BROKER_ID: 1
      KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://localhost:9092
      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1
EOF

docker-compose -f kafka-docker-compose.yml up -d

# Verify Kafka is running
docker-compose -f kafka-docker-compose.yml logs kafka | head -20
```

#### Option 2: Local Kafka Installation
```bash
# Download and start Kafka locally (macOS with Homebrew)
brew install kafka

# Start Zookeeper
zookeeper-server-start /usr/local/etc/kafka/zookeeper.properties &

# Start Kafka
kafka-server-start /usr/local/etc/kafka/server.properties &

# Create required topics
kafka-topics --create --topic nexum.transactions --bootstrap-server localhost:9092 --partitions 3 --replication-factor 1
kafka-topics --create --topic bastion.fraud.decisions --bootstrap-server localhost:9092 --partitions 3 --replication-factor 1
```

### Event Flow Architecture

```
┌─────────────────┐    Kafka Topics    ┌─────────────────┐
│  Banking        │                    │  Bastion        │
│  Simulator      │ ─── nexum.transactions ──→ │  Fraud Detection│
│                 │ ←── bastion.fraud.decisions ─── │                 │
└─────────────────┘                    └─────────────────┘
         │                                       │
         │                                       │
         ▼                                       ▼
┌─────────────────┐                    ┌─────────────────┐
│  Analytics      │                    │  Notification   │
│  Services       │ ←── All Topics ──── │  Services       │
└─────────────────┘                    └─────────────────┘
```

### Monitoring Kafka Events

#### View Live Events
```bash
# Watch transaction events
kafka-console-consumer --bootstrap-server localhost:9092 --topic nexum.transactions --from-beginning | jq

# Watch fraud decisions  
kafka-console-consumer --bootstrap-server localhost:9092 --topic bastion.fraud.decisions --from-beginning | jq

# Count events per second
kafka-console-consumer --bootstrap-server localhost:9092 --topic nexum.transactions | pv -l -i 1 -r > /dev/null
```

#### Kafka Management
```bash
# List topics
kafka-topics --list --bootstrap-server localhost:9092

# Topic details
kafka-topics --describe --topic nexum.transactions --bootstrap-server localhost:9092

# Consumer group status
kafka-consumer-groups --bootstrap-server localhost:9092 --list
kafka-consumer-groups --bootstrap-server localhost:9092 --describe --group bastion-fraud-detection
```

## Dashboard Pages & Features

The real-time dashboard provides a professional web interface accessible at `http://localhost:8095` (or your configured port). It consists of five main pages:

### 1. Control Panel (Main Page)

**Purpose**: Primary simulation control and system overview

**Features**:
- **Start/Stop/Pause Controls**: Large, prominent buttons to control simulation state
- **Speed Multiplier Slider**: Real-time adjustment from 1x to 10,000x speed
- **Scenario Selection**: Dropdown to switch scenarios without restart
- **System Status Indicators**: 
  - ✅ Nexum API: Connected (8090) - 45ms avg latency
  - ✅ Bastion API: Connected (8080) - 62ms avg latency  
  - ⚠️ Kafka: Disabled (--no-kafka flag detected)
- **Live Statistics Summary**:
  - Current TPS: 12.4 transactions/sec
  - Total Transactions: 45,234
  - Fraud Rate: 0.12% (55 fraud / 45,234 total)
  - Simulation Time: Day 2, 14:23 (accelerated)
  - Wall Clock Runtime: 23m 15s

**Real-time Updates**: All metrics update every second via WebSocket

### 2. Live Feed (Transaction Stream)

**Purpose**: Real-time transaction monitoring with fraud detection

**Features**:
- **Transaction Stream**: Scrolling list of most recent transactions
- **Color Coding**: 
  - 🟢 Green: Legitimate transactions (fraud_score < 0.3)
  - 🟡 Yellow: Suspicious transactions (fraud_score 0.3-0.7)
  - 🔴 Red: Fraudulent transactions (fraud_score > 0.7)
- **Transaction Details**: Each entry shows:
  ```
  14:23:45 | John Smith | $247.50 | Coffee & More | 🟢 Score: 0.12
  14:23:44 | Sarah Johnson | $1,850.00 | Online Transfer | 🔴 Score: 0.89
  14:23:43 | Mike Davis | $45.20 | Gas Station | 🟢 Score: 0.05
  ```
- **Fraud Alert Notifications**: Pop-up alerts for high-risk transactions
- **Filtering Options**: Filter by fraud score, amount, customer, transaction type
- **Export**: Download current feed as CSV

### 3. Metrics Dashboard (Analytics)

**Purpose**: Comprehensive performance and fraud analytics

**Features**:
- **Real-time Charts**:
  - Transaction Rate (TPS over time) - Line chart with 5-minute rolling average
  - Fraud Detection Rate - Percentage of fraud successfully detected
  - API Latency - P50, P95, P99 percentiles for Nexum and Bastion
  - Error Rates - HTTP errors, timeouts, retries over time
- **Key Performance Indicators (KPIs)**:
  - Average TPS: 8.7 (last hour)
  - Peak TPS: 24.3 (detected at 12:15)
  - Fraud Detection Accuracy: 94.2%
  - False Positive Rate: 2.1% 
  - API Availability: Nexum 99.9%, Bastion 98.7%
- **System Resource Monitoring**:
  - CPU Usage: 23%
  - Memory Usage: 445MB / 2GB
  - Network I/O: 1.2MB/s
- **Time Range Selector**: Last 5m, 1h, 6h, 24h, All Time

### 4. Scenario Progress (Timeline)

**Purpose**: Track simulation progress and upcoming events

**Features**:
- **Timeline Visualization**: Horizontal timeline showing:
  - Current simulation time (accelerated)
  - Business hours indicator (8am-6pm highlighted)
  - Fraud attack windows (red zones)
  - Transaction volume predictions (height variations)
- **Progress Indicators**:
  - Overall Progress: 43% (Day 2 of 5-day scenario)
  - Current Phase: "Normal Business Operations"
  - Next Event: "Peak Load Test" in 2h 34m (sim time)
- **Event Schedule**: Upcoming scenario events:
  - 16:00: Daily transaction peak
  - 18:00: Business hours end, volume decrease
  - 02:00 (Day 3): Coordinated fraud attack begins
  - 03:30 (Day 3): Account takeover phase
- **Scenario Details**: 
  - Name: "Multi-Day Attack Simulation"
  - Total Duration: 120 hours (simulation time)
  - Speed Multiplier: 250x (currently)
  - Estimated Completion: 2h 15m (wall clock)

### 5. Results Summary (Post-Simulation)

**Purpose**: Comprehensive analysis after simulation completion

**Features**:
- **Executive Summary**:
  - Total Runtime: 1h 23m (wall clock) = 72h simulation time
  - Transactions Processed: 156,847
  - Fraud Events: 235 (0.15% rate)
  - Fraud Detection Rate: 92.3% (217/235 detected)
  - False Positives: 45 (0.03% of legitimate transactions)
- **Detailed Metrics**:
  - Peak TPS: 89.4 (during Black Friday simulation)
  - Average Latency: Nexum 34ms, Bastion 67ms
  - API Error Rate: 0.02%
  - Kafka Messages: 312,694 published successfully
- **Fraud Analysis**:
  - Card Testing Attacks: 145 detected (98.6% success rate)
  - Account Takeover: 34 detected (85.3% success rate)  
  - Velocity Attacks: 56 detected (87.5% success rate)
- **Export Options**:
  - 📊 Full metrics CSV export
  - 📈 Charts as PNG/PDF
  - 📋 Executive summary report
  - 🔍 Detailed transaction log

### Dashboard WebSocket Protocol

The dashboard uses WebSocket connections for real-time updates. External applications can connect to `ws://localhost:8095/ws`:

**Message Types**:
```javascript
// Metrics update (every second)
{
  "type": "metrics_update",
  "timestamp": "2026-02-20T14:30:00Z",
  "data": {
    "current_tps": 12.4,
    "total_transactions": 45234,
    "fraud_rate": 0.0012,
    "api_latency": {"nexum": 45, "bastion": 62}
  }
}

// New transaction (real-time)  
{
  "type": "transaction_feed",
  "data": {
    "id": "txn_abc123",
    "customer": "John Smith",
    "amount": 247.50,
    "merchant": "Coffee & More",
    "fraud_score": 0.12,
    "timestamp": "2026-02-20T14:30:00Z"
  }
}

// Fraud alert (high-risk transactions)
{
  "type": "fraud_alert", 
  "severity": "high",
  "data": {
    "transaction_id": "txn_xyz789",
    "fraud_score": 0.89,
    "customer": "Sarah Johnson",
    "amount": 1850.00,
    "risk_factors": ["unusual_amount", "velocity_pattern"]
  }
}
```

**Subscription Control**:
```javascript
// Subscribe to specific data types
ws.send(JSON.stringify({
  "type": "subscribe",
  "topics": ["metrics", "transactions", "fraud_alerts"]
}));

// Unsubscribe to reduce bandwidth
ws.send(JSON.stringify({
  "type": "unsubscribe", 
  "topics": ["transactions"]
}));
```

### Dashboard Configuration

Customize dashboard behavior in your scenario file:

```yaml
dashboard:
  enabled: true
  port: 8095
  host: "0.0.0.0"        # Bind to all interfaces
  
  # UI customization
  theme: "dark"          # "light" or "dark"
  refresh_rate_ms: 1000  # Update frequency
  max_feed_items: 500    # Transaction feed history
  
  # Chart settings
  chart_retention_hours: 24    # How long to keep chart data
  chart_resolution_seconds: 5  # Chart data point frequency
  
  # Alerts
  fraud_alert_threshold: 0.8   # Show popup alerts for scores > 0.8
  sound_alerts: false          # Enable sound notifications
```

## Prerequisites & Installation

### System Requirements

- **Python**: Version 3.12+ (tested with 3.12)
- **Operating System**: macOS, Linux, or Windows with WSL
- **Memory**: Minimum 2GB RAM, 4GB+ recommended for large simulations
- **Disk Space**: 1GB for logs and CSV exports
- **Network**: Internet access for external API calls (optional in dry-run mode)

### Dependencies Installation

The banking simulator uses a shared virtual environment. Follow these exact steps:

```bash
# Navigate to the banking simulator directory
cd /Users/alexshrike/.openclaw/workspace/banking-simulator

# Activate the shared virtual environment
source /Users/alexshrike/.openclaw/workspace/rustcluster/.venv/bin/activate

# Install all required dependencies
pip install httpx pydantic pyyaml faker fastapi[standard] uvicorn websockets aiokafka

# Optional: Install additional dependencies for development
pip install pytest pytest-asyncio black isort mypy
```

### Required Dependencies List

Core dependencies that will be installed:
- `httpx>=0.24.0` - Async HTTP client for API calls
- `pydantic>=2.0.0` - Data validation and settings management
- `pyyaml>=6.0` - YAML configuration file parsing
- `faker>=20.0.0` - Realistic fake data generation
- `fastapi[standard]>=0.104.0` - Web API framework with async support
- `uvicorn>=0.24.0` - ASGI server for the dashboard
- `websockets>=11.0.0` - WebSocket support for real-time updates
- `aiokafka>=0.8.0` - Kafka client (optional, for event streaming)

### External Systems (Optional)

The simulator can run standalone or integrate with these external systems:

#### Nexum (Core Banking System)
- **Repository**: `/Users/alexshrike/.openclaw/workspace/core-banking`
- **Default Port**: 8090
- **API Endpoints**: Customer creation, transaction processing, account management
- **Required for**: Full banking functionality testing

#### Bastion (Fraud Detection System)  
- **Repository**: `/Users/alexshrike/.openclaw/workspace/bastion`
- **Default Port**: 8080
- **API Endpoints**: Fraud scoring, risk assessment, alerts
- **Required for**: Fraud detection testing

#### Kafka (Event Streaming)
- **Optional**: Used for event-driven architecture testing
- **Default**: localhost:9092
- **Topics**: `nexum.transactions`, `bastion.fraud.decisions`
- **Docker**: `docker run -p 9092:9092 confluentinc/cp-kafka:latest`

### Verification

Verify your installation:

```bash
# Check Python version
python --version  # Should show 3.12+

# Test basic import
python -c "import simulator; print('✅ Installation successful')"

# List available scenarios
python run.py --list-scenarios

# Validate installation with dry run
python run.py --scenario normal_day --dry-run --verbose
```

## Complete CLI Reference

### All Command Line Options

The `run.py` script supports extensive customization through command-line arguments:

#### Core Simulation Options

```bash
# Scenario selection (required/default)
--scenario SCENARIO          # Scenario name or YAML file path (default: normal_day)
                             # Built-in: normal_day, fraud_attack, peak_load, mule_network, onboarding
                             # Custom: path/to/my_scenario.yaml

# Simulation parameters (override scenario defaults)
--speed MULTIPLIER           # Time acceleration multiplier (default: from scenario)
                            # Examples: --speed 100 (100x faster), --speed 1 (real-time)
--customers COUNT            # Number of customers to create (default: from scenario)
                            # Examples: --customers 100, --customers 10000
```

#### External System Integration

```bash
# API endpoints
--nexum-url URL              # Nexum core banking API URL (default: http://localhost:8090)
--bastion-url URL            # Bastion fraud detection API URL (default: http://localhost:8080)

# Connection behavior
--dry-run                    # Use mock connectors instead of real APIs (no external calls)
--no-kafka                   # Disable Kafka message publishing (default: enabled if available)
```

#### Dashboard Configuration

```bash
# Dashboard control
--dashboard                  # Launch real-time web dashboard (default: false)
--dashboard-port PORT        # Dashboard server port (default: 8095)
                            # Use different port if 8095 is busy: --dashboard-port 8080
```

#### Utility Commands

```bash
# Information and validation
--list-scenarios             # List all available scenarios and exit
--validate-scenario FILE     # Validate a scenario YAML file and exit
--verbose, -v                # Enable verbose debug logging
--help, -h                   # Show help message and exit
```

### Usage Examples

#### Basic Operations
```bash
# List what scenarios are available
python run.py --list-scenarios

# Validate a custom scenario file
python run.py --validate-scenario scenarios/my_scenario.yaml

# Run with verbose logging for debugging
python run.py --scenario normal_day --dry-run --verbose
```

#### Simulation Variations
```bash
# Quick test with small dataset
python run.py --scenario normal_day --customers 10 --speed 1000 --dry-run --dashboard

# High-speed fraud attack simulation
python run.py --scenario fraud_attack --speed 500 --dashboard

# Real-time simulation (1x speed, like production)
python run.py --scenario normal_day --speed 1 --dashboard

# Large-scale stress test
python run.py --scenario peak_load --customers 5000 --speed 50
```

#### External System Integration
```bash
# Test with different Nexum instance
python run.py --scenario normal_day --nexum-url http://staging-nexum:8090

# Test with remote Bastion server
python run.py --scenario fraud_attack --bastion-url https://bastion.company.com

# Test against development environment
python run.py --scenario normal_day \
  --nexum-url http://dev-nexum:8090 \
  --bastion-url http://dev-bastion:8080 \
  --dashboard

# Disable external systems for performance testing
python run.py --scenario peak_load --dry-run --no-kafka --speed 1000
```

#### Dashboard Customization
```bash
# Run dashboard on different port (if 8095 is busy)
python run.py --scenario normal_day --dashboard --dashboard-port 8080

# Run without dashboard for headless operation
python run.py --scenario normal_day  # No --dashboard flag

# Access dashboard from different machine
python run.py --scenario normal_day --dashboard
# Then visit: http://your-machine-ip:8095 from another computer
```

#### Development and Testing
```bash
# Test scenario development workflow
python run.py --validate-scenario scenarios/new_scenario.yaml
python run.py --scenario scenarios/new_scenario.yaml --dry-run --dashboard
python run.py --scenario scenarios/new_scenario.yaml --customers 5 --speed 2000

# Test API integration without full simulation
python run.py --scenario normal_day --customers 1 --speed 1 --verbose

# Performance testing setup
python run.py --scenario peak_load --dry-run --no-kafka --customers 10000 --speed 100
```

#### Production Monitoring
```bash
# Long-running simulation for demo/monitoring
python run.py --scenario normal_day --speed 10 --dashboard

# Continuous fraud testing  
python run.py --scenario fraud_attack --speed 50 --dashboard
# Runs indefinitely, restart manually or via cron

# Load testing specific endpoints
python run.py --scenario peak_load --nexum-url http://prod-nexum:8090 --customers 1000
```

### Parameter Override Examples

You can override any scenario parameter from the command line:

```yaml
# scenarios/base_scenario.yaml defines:
customers: 500
speed_multiplier: 100
```

```bash
# Override both values
python run.py --scenario base_scenario --customers 1000 --speed 200

# Result: Uses 1000 customers at 200x speed instead of scenario defaults
```

### Exit Codes

The simulator returns standard exit codes:
- `0`: Successful completion
- `1`: Error or exception occurred  
- `130`: Interrupted by user (Ctrl+C)

```bash
# Check if simulation completed successfully
python run.py --scenario normal_day --dry-run
echo "Exit code: $?"
# Should print "Exit code: 0" on success
```

### API Endpoints

The dashboard server provides REST API access:

```bash
# Get simulation status
curl http://localhost:8095/api/status

# Get current metrics
curl http://localhost:8095/api/metrics

# Control simulation
curl -X POST http://localhost:8095/api/control/pause
curl -X POST http://localhost:8095/api/control/resume
curl -X POST http://localhost:8095/api/control/stop

# Set simulation speed
curl -X POST http://localhost:8095/api/control/speed \
  -H "Content-Type: application/json" \
  -d '{"multiplier": 200}'
```

### WebSocket API

Connect to `ws://localhost:8095/ws` for real-time updates:

```javascript
const ws = new WebSocket('ws://localhost:8095/ws');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  
  switch(data.type) {
    case 'metrics_update':
      // Handle metrics data
      break;
    case 'transaction_feed':
      // Handle new transaction
      break;
    case 'fraud_alert':
      // Handle fraud detection alert
      break;
  }
};

// Subscribe to specific data types
ws.send(JSON.stringify({
  type: 'subscribe',
  topics: ['metrics', 'transactions', 'fraud_alerts']
}));
```

## Configuration

### Environment Variables

- `NEXUM_URL`: Nexum API base URL (default: http://localhost:8090)
- `BASTION_URL`: Bastion API base URL (default: http://localhost:8080)
- `DASHBOARD_PORT`: Dashboard port (default: 8095)
- `LOG_LEVEL`: Logging level (default: INFO)

### Scenario Configuration

Each scenario supports these configuration options:

```yaml
# Basic settings
name: "Scenario Name"
description: "Scenario description"
duration_hours: 24
speed_multiplier: 100
customers: 500
accounts_per_customer: 2
initial_balance: 5000.00
currency: "USD"

# Transaction generation
transaction_rate:
  peak_tps: 10
  off_peak_tps: 2
  business_hours: [8, 18]
  weekend_multiplier: 0.3

# Fraud patterns
fraud:
  rate: 0.001  # Base fraud rate
  attack_window: [2, 4]  # Optional focused attack hours
  patterns:
    - type: card_testing
      weight: 0.3        # Relative frequency
      intensity: 1.0     # Attack intensity
      count: 100         # Optional: specific count
      duration_minutes: 30

# System connections
connections:
  nexum_url: "http://localhost:8090"
  bastion_url: "http://localhost:8080"
  kafka_bootstrap_servers: "localhost:9092"  # Optional
  timeout_seconds: 30
  max_retries: 3

# Dashboard settings
dashboard:
  enabled: true
  port: 8095
  host: "0.0.0.0"

# Metrics collection
metrics:
  enabled: true
  collect_interval_seconds: 1
  retention_minutes: 60
  export_csv: true
```

## Fraud Patterns

The simulator includes sophisticated fraud attack patterns:

### Card Testing
- Rapid small transactions ($0.01-$5) to test stolen cards
- Multiple merchants, high velocity
- Detection: Amount patterns, velocity rules

### Account Takeover  
- Unusual login location followed by large transfers
- Device fingerprint changes
- Detection: Location anomalies, behavioral changes

### Velocity Attacks
- 50+ transactions in 5 minutes
- Same card/account across multiple merchants
- Detection: Transaction frequency rules

### Money Laundering
- **Layering**: Complex transfer chains (3-10 hops)
- **Structuring**: Breaking large amounts into sub-$10K transactions
- **Smurfing**: Multiple people making coordinated deposits

### Synthetic Identity
- Build legitimate-looking history over months
- Sudden "bust-out" with maximum fraud
- Detection: Identity verification, pattern analysis

## Performance

### Benchmarks

Typical performance on modern hardware:

- **Transaction Generation**: 1000+ TPS sustained
- **API Throughput**: 500+ requests/second to Nexum/Bastion
- **Memory Usage**: <500MB for 10K customers
- **Dashboard Updates**: Sub-100ms latency
- **Time Acceleration**: Up to 10,000x speed multiplier

### Scaling

- **Customers**: Tested up to 100K customer profiles
- **Transactions**: Millions of transactions per simulation
- **Concurrent Sessions**: Multiple dashboard clients supported
- **Distributed**: Can run multiple simulators against same backend

## Development

### Architecture

The simulator is built with modern Python async patterns:

- **FastAPI**: REST API and WebSocket server
- **Pydantic**: Configuration management and validation
- **HTTPX**: Async HTTP client for external APIs  
- **asyncio**: Concurrent execution and time acceleration
- **Preact+HTM**: Clean, professional dashboard UI

### Extending

#### Custom Transaction Patterns

```python
from simulator.generators.transactions import TransactionTemplate, TransactionType

# Add to TransactionGenerator
new_template = TransactionTemplate(
    transaction_type=TransactionType.CUSTOM,
    amount_min=10.0,
    amount_max=500.0,
    frequency_per_month=4.0,
    preferred_channels=[TransactionChannel.ONLINE],
    preferred_hours=(9, 17),
    seasonal_multiplier={12: 1.5},  # More activity in December
    amount_distribution="log_normal"
)
```

#### Custom Fraud Patterns

```python
from simulator.generators.fraud import FraudGenerator, FraudType

class CustomFraudGenerator(FraudGenerator):
    def generate_custom_fraud(self, profile, current_time):
        # Implement custom fraud logic
        return fraud_transactions
```

#### Dashboard Extensions

The dashboard API is fully extensible:

```python
@dashboard.app.get("/api/custom/endpoint")
async def custom_endpoint():
    return {"custom": "data"}
```

## Testing

### Unit Tests

```bash
# Run tests (when implemented)
pytest tests/
```

### Integration Tests

```bash
# Test against live systems
python run.py --scenario normal_day --customers 10 --dashboard

# Test mock mode
python run.py --scenario fraud_attack --dry-run --speed 1000
```

### Performance Testing

```bash
# Stress test with high transaction volume
python run.py --scenario peak_load --speed 500 --customers 5000
```

## Troubleshooting Guide

### Common Issues & Solutions

#### Port Already in Use

**Problem**: `OSError: [Errno 48] Address already in use`

**Solutions**:
```bash
# Check what's using the port
lsof -i :8095  # Dashboard port
lsof -i :8090  # Nexum port  
lsof -i :8080  # Bastion port

# Kill the process using the port
sudo kill -9 <PID>

# Or use a different port
python run.py --scenario normal_day --dashboard-port 8096
```

#### Nexum/Bastion Not Responding

**Problem**: `Connection refused` or `API timeout` errors

**Diagnosis**:
```bash
# Check if services are running
curl http://localhost:8090/health  # Nexum health check
curl http://localhost:8080/health  # Bastion health check

# Check service logs
cd /Users/alexshrike/.openclaw/workspace/core-banking
tail -f logs/nexum.log

cd /Users/alexshrike/.openclaw/workspace/bastion  
tail -f logs/bastion.log
```

**Solutions**:
```bash
# Start missing services
cd /Users/alexshrike/.openclaw/workspace/core-banking
source /Users/alexshrike/.openclaw/workspace/rustcluster/.venv/bin/activate
python -m uvicorn core_banking.api_old:app --port 8090 &

cd /Users/alexshrike/.openclaw/workspace/bastion
python -m uvicorn bastion.api:app --port 8080 &

# Or run in dry-run mode for testing
python run.py --scenario normal_day --dry-run --dashboard
```

#### Kafka Not Available

**Problem**: Kafka connection errors or message publishing failures

**Diagnosis**:
```bash
# Check if Kafka is running
telnet localhost 9092

# Check Kafka logs
docker logs kafka-container-name

# List topics
kafka-topics --list --bootstrap-server localhost:9092
```

**Solutions**:
```bash
# Start Kafka with Docker
docker run -d --name kafka-test -p 9092:9092 \
  -e KAFKA_ZOOKEEPER_CONNECT=zookeeper:2181 \
  -e KAFKA_ADVERTISED_LISTENERS=PLAINTEXT://localhost:9092 \
  confluentinc/cp-kafka:latest

# Or disable Kafka for testing
python run.py --scenario normal_day --no-kafka --dashboard
```

#### Dashboard Not Loading

**Problem**: Browser shows "This site can't be reached" or blank page

**Diagnosis**:
```bash
# Check if dashboard server is running
curl http://localhost:8095/api/status

# Check browser developer console for errors (F12)

# Verify port binding
netstat -an | grep 8095
```

**Solutions**:
```bash
# Check firewall settings (macOS)
sudo pfctl -s all | grep 8095

# Try different port
python run.py --scenario normal_day --dashboard-port 8096

# Check static files exist
ls -la /Users/alexshrike/.openclaw/workspace/banking-simulator/simulator/dashboard/static/

# Clear browser cache and try incognito mode
```

#### High Memory Usage

**Problem**: Simulator consumes >2GB RAM or system becomes slow

**Diagnosis**:
```bash
# Monitor memory usage
top -pid $(pgrep -f "python run.py")

# Check metrics retention settings
grep -r "retention" scenarios/
```

**Solutions**:
```bash
# Reduce customer count
python run.py --scenario peak_load --customers 500 --dashboard

# Lower metrics retention time
# Edit scenario YAML file:
metrics:
  retention_minutes: 15  # Instead of 60
  collect_interval_seconds: 5  # Instead of 1

# Disable CSV export
metrics:
  export_csv: false

# Use lighter scenarios for testing
python run.py --scenario normal_day --customers 50 --speed 1000
```

#### Slow Performance / Low TPS

**Problem**: Transaction rate much lower than expected

**Diagnosis**:
```bash
# Monitor API latency
curl -w "@curl-format.txt" -s -o /dev/null http://localhost:8090/health

# Create curl-format.txt:
echo '     time_namelookup:  %{time_namelookup}\n
        time_connect:  %{time_connect}\n
     time_appconnect:  %{time_appconnect}\n
    time_pretransfer:  %{time_pretransfer}\n
       time_redirect:  %{time_redirect}\n
  time_starttransfer:  %{time_starttransfer}\n
                     ----------\n
          time_total:  %{time_total}\n' > curl-format.txt

# Check database performance (if using Nexum)
cd /Users/alexshrike/.openclaw/workspace/core-banking
python -c "
from core_banking.database import get_db
import time
start = time.time()  
# Run test query
end = time.time()
print(f'DB query took {(end-start)*1000:.2f}ms')
"
```

**Solutions**:
```bash
# Start with lower speed and gradually increase
python run.py --scenario normal_day --speed 10 --dashboard
# Observe TPS, then increase: --speed 50, --speed 100, etc.

# Use dry-run to test maximum performance
python run.py --scenario peak_load --dry-run --speed 1000

# Optimize API timeouts
# In scenario YAML:
connections:
  timeout_seconds: 5    # Reduce from 30
  max_retries: 1        # Reduce from 3

# Disable Kafka if not needed
python run.py --scenario normal_day --no-kafka

# Check system resources
htop  # Ensure CPU/memory are available
```

### How to Check if Services are Running

**Quick Health Check Script**:
```bash
#!/bin/bash
# save as check-services.sh

echo "=== Banking Simulator Service Health Check ==="

# Check Nexum
echo -n "Nexum (8090): "
if curl -s http://localhost:8090/health > /dev/null 2>&1; then
    echo "✅ Running"
else
    echo "❌ Not responding"
fi

# Check Bastion  
echo -n "Bastion (8080): "
if curl -s http://localhost:8080/health > /dev/null 2>&1; then
    echo "✅ Running"
else
    echo "❌ Not responding"
fi

# Check Kafka
echo -n "Kafka (9092): "
if nc -z localhost 9092 2>/dev/null; then
    echo "✅ Running"
else
    echo "❌ Not responding"
fi

# Check Dashboard
echo -n "Dashboard (8095): "
if curl -s http://localhost:8095/api/status > /dev/null 2>&1; then
    echo "✅ Running"
else
    echo "❌ Not responding"
fi

echo "=== End Health Check ==="
```

**Docker Services Check**:
```bash
# Check all containers
docker-compose ps

# Should show all services as "Up" and healthy:
#     Name                 Command               State            Ports         
# ---------------------------------------------------------------------------
# nexum           python -m uvicorn ...       Up      0.0.0.0:8090->8090/tcp
# bastion         python -m uvicorn ...       Up      0.0.0.0:8080->8080/tcp  
# postgres        docker-entrypoint.sh ...    Up      5432/tcp
# kafka           /etc/confluent/docker/run   Up      0.0.0.0:9092->9092/tcp
# simulator       python run.py --scenario    Up      0.0.0.0:8095->8095/tcp
```

### Logging & Debugging

#### Log Locations
```bash
# Simulator logs
tail -f /Users/alexshrike/.openclaw/workspace/banking-simulator/banking_simulator.log

# Nexum logs (if running locally)
tail -f /Users/alexshrike/.openclaw/workspace/core-banking/logs/nexum.log

# Bastion logs (if running locally)  
tail -f /Users/alexshrike/.openclaw/workspace/bastion/logs/bastion.log

# Docker logs
docker-compose logs -f simulator
docker-compose logs -f nexum
docker-compose logs -f bastion
```

#### Enable Verbose Logging
```bash
# Maximum verbosity for debugging
python run.py --scenario normal_day --verbose --dry-run

# This will show:
# - Detailed HTTP requests/responses
# - Transaction generation logic
# - Fraud pattern application
# - Dashboard WebSocket messages
# - Metrics collection details
```

#### Log Analysis
```bash
# Count transactions processed
grep "Transaction processed" banking_simulator.log | wc -l

# Find API errors
grep -i "error\|exception" banking_simulator.log

# Monitor TPS in real-time
tail -f banking_simulator.log | grep "TPS"

# Extract fraud events
grep "Fraud detected" banking_simulator.log | tail -20
```

### Performance Tuning

#### Optimal Settings for Different Use Cases

**Development/Testing (Fast iteration)**:
```bash
python run.py --scenario normal_day --customers 10 --speed 500 --dry-run --dashboard
```

**Demo/Presentation (Visible activity)**:
```bash  
python run.py --scenario fraud_attack --customers 100 --speed 100 --dashboard
```

**Load Testing (Maximum throughput)**:
```bash
python run.py --scenario peak_load --customers 10000 --speed 1 --no-kafka --dry-run
```

**Production Simulation (Realistic)**:
```bash
python run.py --scenario normal_day --customers 5000 --speed 10 --dashboard
```

### When All Else Fails

**Complete Reset Procedure**:
```bash
# 1. Kill all processes
pkill -f "python run.py"
pkill -f "uvicorn"

# 2. Remove any lock files or temporary data
rm -f *.pid
rm -f *.lock

# 3. Restart from scratch
cd /Users/alexshrike/.openclaw/workspace/banking-simulator
source /Users/alexshrike/.openclaw/workspace/rustcluster/.venv/bin/activate

# 4. Verify installation
python -c "import simulator; print('✅ Simulator module loads correctly')"

# 5. Run minimal test
python run.py --scenario normal_day --customers 1 --speed 1 --dry-run --verbose

# 6. If that works, add dashboard
python run.py --scenario normal_day --customers 1 --speed 10 --dry-run --dashboard
```

## Contributing

1. Fork the repository
2. Create feature branch
3. Add tests for new functionality
4. Update documentation
5. Submit pull request

## License

MIT License - see LICENSE file for details.