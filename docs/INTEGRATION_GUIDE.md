# Banking Simulator Integration Guide

This comprehensive guide covers integrating the Banking Simulator with Nexum (core banking system) and Bastion (fraud detection system) for full-stack transaction processing and fraud detection.

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Method 1: Manual Setup (Recommended for Development)](#method-1-manual-setup-recommended-for-development)
4. [Method 2: Docker Compose (One Command)](#method-2-docker-compose-one-command)
5. [Method 3: With Kafka (Event-Driven)](#method-3-with-kafka-event-driven)
6. [Testing Each Scenario](#testing-each-scenario)
7. [Monitoring the Full Stack](#monitoring-the-full-stack)
8. [Custom Scenarios for Integration Testing](#custom-scenarios-for-integration-testing)
9. [Troubleshooting](#troubleshooting)

## Overview

### Architecture Diagram

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│                 │    │                 │    │                 │
│  Banking        │    │     Nexum       │    │    Bastion      │
│  Simulator      │───▶│ (Core Banking)  │───▶│ (Fraud System)  │
│                 │    │                 │    │                 │
│  Port: 8095     │    │  Port: 8090     │    │  Port: 8080     │
│                 │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                        │                        │
         │                        │                        │
         ▼                        ▼                        ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Dashboard      │    │   Dashboard     │    │   Dashboard     │
│  :8095          │    │   :8890         │    │   :8888         │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                    ┌─────────────────┐
                    │     Kafka       │
                    │   (Optional)    │
                    │  Port: 9092     │
                    └─────────────────┘
```

### Data Flow Explanation

1. **Transaction Generation**: Banking Simulator generates realistic transaction patterns
2. **Account Management**: Transactions are sent to Nexum for account validation and processing
3. **Fraud Scoring**: Each transaction is scored by Bastion for fraud risk
4. **Decision Processing**: Based on fraud scores, transactions are approved, flagged for review, or blocked
5. **Real-time Monitoring**: All three dashboards provide different views of the same data flow
6. **Event Streaming** (Optional): Kafka can be used for event-driven architecture

### What Connects to What

- **Simulator → Nexum**: REST API calls for customer/account creation and transaction processing
- **Nexum → Bastion**: REST API calls for fraud scoring on each transaction
- **Simulator → Bastion**: Direct API calls for additional fraud analysis (optional)
- **All → Kafka**: Event streaming for decoupled architecture (optional)
- **Dashboards**: Each service has its own real-time dashboard showing different perspectives

## Prerequisites

Before starting, ensure you have:

### Required
- **All three repositories cloned**:
  - `/Users/alexshrike/.openclaw/workspace/core-banking` (Nexum)
  - `/Users/alexshrike/.openclaw/workspace/bastion` (Bastion)  
  - `/Users/alexshrike/.openclaw/workspace/banking-simulator` (Simulator)
- **Python 3.12+** with shared virtual environment
- **Git** for version control
- **curl** for testing API endpoints

### Optional
- **Docker & Docker Compose** for containerized setup
- **Apache Kafka** for event-driven architecture
- **PostgreSQL** for persistent data storage
- **Redis** for caching (used by Bastion)

### Verify Prerequisites

```bash
# Check Python version
python3 --version  # Should be 3.12+

# Check if all repos exist
ls -la /Users/alexshrike/.openclaw/workspace/ | grep -E "(core-banking|bastion|banking-simulator)"

# Check shared venv
ls -la /Users/alexshrike/.openclaw/workspace/rustcluster/.venv/
```

## Method 1: Manual Setup (Recommended for Development)

This method gives you full control and is ideal for development and debugging.

### Step 1: Activate Shared Virtual Environment

```bash
# Activate the shared virtual environment
source /Users/alexshrike/.openclaw/workspace/rustcluster/.venv/bin/activate

# Verify activation (should show the venv path)
which python
```

### Step 2: Install All Dependencies

Install each package in development mode so changes are reflected immediately:

```bash
# Install Nexum (Core Banking)
cd /Users/alexshrike/.openclaw/workspace/core-banking
pip install -e .
# Verify installation
python -c "import core_banking; print('Nexum installed successfully')"

# Install Bastion (Fraud Detection)
cd /Users/alexshrike/.openclaw/workspace/bastion
pip install -e .
# Verify installation  
python -c "import bastion; print('Bastion installed successfully')"

# Install Banking Simulator
cd /Users/alexshrike/.openclaw/workspace/banking-simulator
pip install -e .
# Verify installation
python -c "import simulator; print('Simulator installed successfully')"
```

### Step 3: Start Nexum (Terminal 1)

```bash
# Navigate to core banking directory
cd /Users/alexshrike/.openclaw/workspace/core-banking

# Set environment variable for Bastion integration
export NEXUM_BASTION_URL=http://localhost:8080
export NEXUM_DATABASE_URL=sqlite:///nexum.db  # or your PostgreSQL URL
export NEXUM_LOG_LEVEL=INFO

# Start Nexum API server
uvicorn core_banking.api_old:app --port 8090 --reload --host 0.0.0.0

# You should see:
# INFO:     Uvicorn running on http://0.0.0.0:8090 (Press CTRL+C to quit)
# INFO:     Started reloader process
```

**Keep this terminal open!**

### Step 4: Start Bastion (Terminal 2)

Open a new terminal and activate the same virtual environment:

```bash
# Activate venv
source /Users/alexshrike/.openclaw/workspace/rustcluster/.venv/bin/activate

# Navigate to Bastion directory
cd /Users/alexshrike/.openclaw/workspace/bastion

# Set environment variables
export BASTION_DATABASE_URL=sqlite:///bastion.db  # or your PostgreSQL URL
export BASTION_REDIS_URL=redis://localhost:6379/0  # if using Redis
export BASTION_LOG_LEVEL=INFO

# Start Bastion API server
uvicorn bastion.api:app --port 8080 --reload --host 0.0.0.0

# You should see:
# INFO:     Uvicorn running on http://0.0.0.0:8080 (Press CTRL+C to quit)  
# INFO:     Started reloader process
```

**Keep this terminal open!**

### Step 5: Start Banking Simulator (Terminal 3)

Open a third terminal:

```bash
# Activate venv
source /Users/alexshrike/.openclaw/workspace/rustcluster/.venv/bin/activate

# Navigate to simulator directory
cd /Users/alexshrike/.openclaw/workspace/banking-simulator

# Start simulator with dashboard
python run.py --scenario normal_day \
  --nexum-url http://localhost:8090 \
  --bastion-url http://localhost:8080 \
  --dashboard --dashboard-port 8095 \
  --log-level INFO

# You should see:
# INFO:     Banking Simulator Dashboard starting on port 8095
# INFO:     Scenario: normal_day loaded
# INFO:     Connecting to Nexum at http://localhost:8090
# INFO:     Connecting to Bastion at http://localhost:8080
```

**Keep this terminal open!**

### Step 6: Open Dashboards

Now you can access all three dashboards:

1. **Simulator Dashboard**: http://localhost:8095
   - Real-time transaction generation and monitoring
   - Control simulation speed and scenarios
   - View fraud detection results

2. **Nexum Dashboard**: http://localhost:8890
   - Customer accounts and balances
   - Transaction history
   - Account management

3. **Bastion Dashboard**: http://localhost:8888
   - Fraud scoring and rules
   - Case management
   - Alert monitoring

### Step 7: Verify Integration

Test that all systems are communicating:

```bash
# Check Nexum health
curl -s http://localhost:8090/health | python -m json.tool

# Check Bastion health  
curl -s http://localhost:8080/health | python -m json.tool

# Check Simulator health
curl -s http://localhost:8095/api/health | python -m json.tool

# Test Nexum → Bastion integration
curl -X POST http://localhost:8090/api/customers \
  -H "Content-Type: application/json" \
  -d '{"name": "Test Customer", "email": "test@example.com"}'
```

## Method 2: Docker Compose (One Command)

For a quick setup without managing individual services:

### Prerequisites

Ensure Docker and Docker Compose are installed:

```bash
docker --version      # Should be 20.10+
docker-compose --version  # Should be 1.29+
```

### Single Command Setup

```bash
# Navigate to simulator directory
cd /Users/alexshrike/.openclaw/workspace/banking-simulator

# Start all services with Docker Compose
docker-compose up --build

# Or run in background
docker-compose up -d --build
```

### What This Starts

The Docker Compose setup starts:

- **Nexum**: http://localhost:8090 (API) + http://localhost:8890 (Dashboard)
- **Bastion**: http://localhost:8080 (API) + http://localhost:8888 (Dashboard)  
- **Simulator**: http://localhost:8095 (Dashboard)
- **PostgreSQL**: localhost:5432 (shared database)
- **Redis**: localhost:6379 (caching for Bastion)
- **Kafka** (optional): localhost:9092

### Docker Compose Commands

```bash
# View logs
docker-compose logs -f

# View logs for specific service
docker-compose logs -f simulator

# Stop all services
docker-compose down

# Stop and remove volumes
docker-compose down -v

# Restart specific service
docker-compose restart nexum

# Scale simulator (run multiple instances)
docker-compose up --scale simulator=3
```

### Docker Environment Variables

Edit `docker-compose.yml` to customize:

```yaml
environment:
  - NEXUM_BASTION_URL=http://bastion:8080
  - BASTION_DATABASE_URL=postgresql://user:password@db:5432/bastion
  - SIMULATOR_SPEED_MULTIPLIER=100
  - SIMULATOR_SCENARIO=normal_day
```

## Method 3: With Kafka (Event-Driven)

For production-like event-driven architecture:

### Step 1: Start Kafka

Using Docker (recommended):

```bash
# Create Kafka network
docker network create kafka-net

# Start Zookeeper
docker run -d --name zookeeper --network kafka-net \
  -p 2181:2181 \
  -e ZOOKEEPER_CLIENT_PORT=2181 \
  confluentinc/cp-zookeeper:latest

# Start Kafka
docker run -d --name kafka --network kafka-net \
  -p 9092:9092 \
  -e KAFKA_ZOOKEEPER_CONNECT=zookeeper:2181 \
  -e KAFKA_ADVERTISED_LISTENERS=PLAINTEXT://localhost:9092 \
  -e KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR=1 \
  confluentinc/cp-kafka:latest

# Verify Kafka is running
docker exec kafka kafka-topics --list --bootstrap-server localhost:9092
```

### Step 2: Create Kafka Topics

```bash
# Create topics for event streaming
docker exec kafka kafka-topics --create \
  --bootstrap-server localhost:9092 \
  --topic transactions \
  --partitions 3 \
  --replication-factor 1

docker exec kafka kafka-topics --create \
  --bootstrap-server localhost:9092 \
  --topic fraud-alerts \
  --partitions 3 \
  --replication-factor 1

docker exec kafka kafka-topics --create \
  --bootstrap-server localhost:9092 \
  --topic account-events \
  --partitions 3 \
  --replication-factor 1
```

### Step 3: Configure Services for Kafka

Set environment variables for all services:

```bash
# Nexum configuration
export NEXUM_KAFKA_BOOTSTRAP_SERVERS=localhost:9092
export NEXUM_KAFKA_ENABLED=true

# Bastion configuration  
export BASTION_KAFKA_BOOTSTRAP_SERVERS=localhost:9092
export BASTION_KAFKA_ENABLED=true

# Simulator configuration
export SIMULATOR_KAFKA_BOOTSTRAP_SERVERS=localhost:9092
export SIMULATOR_KAFKA_ENABLED=true
```

### Step 4: Start Services with Kafka

```bash
# Terminal 1: Nexum with Kafka
cd /Users/alexshrike/.openclaw/workspace/core-banking
export NEXUM_KAFKA_ENABLED=true
uvicorn core_banking.api_old:app --port 8090 --reload

# Terminal 2: Bastion with Kafka
cd /Users/alexshrike/.openclaw/workspace/bastion
export BASTION_KAFKA_ENABLED=true
uvicorn bastion.api:app --port 8080 --reload

# Terminal 3: Simulator with Kafka
cd /Users/alexshrike/.openclaw/workspace/banking-simulator
python run.py --scenario normal_day \
  --nexum-url http://localhost:8090 \
  --bastion-url http://localhost:8080 \
  --kafka-enabled \
  --dashboard --dashboard-port 8095
```

### Step 5: Monitor Event Flow

```bash
# Monitor transaction events
docker exec kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic transactions \
  --from-beginning

# Monitor fraud alerts in another terminal
docker exec kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic fraud-alerts \
  --from-beginning
```

## Testing Each Scenario

### 1. Normal Day Scenario

**What to run:**
```bash
python run.py --scenario normal_day \
  --nexum-url http://localhost:8090 \
  --bastion-url http://localhost:8080 \
  --dashboard --dashboard-port 8095 \
  --duration 300  # 5 minutes
```

**What to expect:**
- 10-50 transactions per second
- Low fraud rate (1-3%)
- Mostly approved transactions
- Normal latency patterns

**What to look for:**
- **Simulator Dashboard**: Steady TPS, low fraud alerts
- **Nexum Dashboard**: Account balances updating, transaction history
- **Bastion Dashboard**: Low-risk scores, few cases created

**Expected metrics:**
- TPS: 10-50
- Fraud Rate: 1-3%
- Average Latency: <100ms
- Error Rate: <1%

**Verify fraud detection:**
```bash
# Check fraud detection stats
curl -s http://localhost:8095/api/metrics | jq '.data.fraud_rate'

# Should show low fraud rate (0.01-0.03)
```

### 2. Fraud Attack Scenario

**What to run:**
```bash
python run.py --scenario fraud_attack \
  --nexum-url http://localhost:8090 \
  --bastion-url http://localhost:8080 \
  --dashboard --dashboard-port 8095 \
  --duration 180  # 3 minutes
```

**What to expect:**
- Higher fraud rate (15-30%)
- Many blocked transactions
- Increased latency due to additional processing
- Fraud alerts in Bastion dashboard

**What to look for:**
- **Simulator Dashboard**: High fraud alerts, many blocked transactions
- **Nexum Dashboard**: Rejected transactions appearing
- **Bastion Dashboard**: High-risk scores, many cases created

**Expected metrics:**
- TPS: 20-40 (reduced due to blocking)
- Fraud Rate: 15-30%
- Average Latency: 100-200ms
- Block Rate: 10-20%

### 3. Peak Hours Scenario

**What to run:**
```bash
python run.py --scenario peak_hours \
  --nexum-url http://localhost:8090 \
  --bastion-url http://localhost:8080 \
  --dashboard --dashboard-port 8095 \
  --speed-multiplier 500  # High speed
```

**What to expect:**
- Very high transaction volume
- System performance under load
- Potential latency increases
- Queue building in systems

**Expected metrics:**
- TPS: 100-500 (depending on speed multiplier)
- Fraud Rate: 2-5%
- Average Latency: 50-300ms (increases with load)
- Error Rate: May increase under high load

### 4. Holiday Rush Scenario

**What to run:**
```bash
python run.py --scenario holiday_rush \
  --nexum-url http://localhost:8090 \
  --bastion-url http://localhost:8080 \
  --dashboard --dashboard-port 8095
```

**What to expect:**
- Bursty transaction patterns
- Mixed transaction types (purchases, transfers)
- Moderate fraud rate
- Variable latency

### 5. System Stress Scenario

**What to run:**
```bash
python run.py --scenario system_stress \
  --nexum-url http://localhost:8090 \
  --bastion-url http://localhost:8080 \
  --dashboard --dashboard-port 8095 \
  --speed-multiplier 1000
```

**What to expect:**
- Maximum transaction load
- System limits tested
- Potential timeouts and errors
- Performance degradation

**How to verify:**
- Monitor error rates in all dashboards
- Check system resource usage
- Verify graceful degradation

## Monitoring the Full Stack

### Simulator Dashboard (Port 8095)

**Real-time monitoring includes:**
- **TPS Gauge**: Current transactions per second
- **Fraud Rate**: Percentage of transactions flagged as fraudulent
- **Live Feed**: Scrolling list of transactions with color coding:
  - Green: Approved transactions
  - Yellow: Under review
  - Red: Blocked/declined

**Key metrics to watch:**
- Transaction throughput
- Fraud detection effectiveness
- System latency
- Error rates

### Nexum Dashboard (Port 8890)

**Banking system monitoring:**
- **Customer Accounts**: Account creation and management
- **Transaction Processing**: Real-time transaction flow
- **Account Balances**: Updated in real-time
- **System Health**: API response times and error rates

**Integration points:**
- Transaction processing latency
- Account validation times
- Database performance metrics

### Bastion Dashboard (Port 8888)

**Fraud detection monitoring:**
- **Risk Scoring**: Real-time fraud score distribution
- **Case Management**: Flagged transactions requiring review
- **Rule Performance**: Effectiveness of fraud detection rules
- **Alert Management**: Real-time fraud alerts

**Fraud detection verification:**
- High-risk transactions should be flagged
- False positive rate should remain low
- Case creation for suspicious activity

### Cross-Dashboard Data Flow

**How the three dashboards show different views:**

1. **Transaction Creation** (Simulator):
   - Shows transaction generation
   - Displays initial fraud scores
   - Monitors throughput

2. **Transaction Processing** (Nexum):
   - Shows account impact
   - Displays balance changes  
   - Tracks processing latency

3. **Fraud Analysis** (Bastion):
   - Shows detailed risk analysis
   - Displays case creation
   - Tracks investigation workflow

**Data consistency checks:**
```bash
# Compare transaction counts across systems
curl -s http://localhost:8095/api/metrics | jq '.data.total_transactions'
curl -s http://localhost:8090/api/metrics | jq '.data.total_transactions'  
curl -s http://localhost:8080/api/metrics | jq '.data.total_transactions'

# All three should show similar numbers (with small delays)
```

## Custom Scenarios for Integration Testing

### Creating Custom Scenarios

Create a new scenario file in `scenarios/` directory:

```python
# scenarios/integration_test.py
from simulator.scenarios import BaseScenario
from datetime import timedelta

class IntegrationTestScenario(BaseScenario):
    """Custom scenario for testing Nexum → Bastion integration"""
    
    def __init__(self):
        super().__init__(
            name="integration_test",
            description="Tests all integration points",
            duration=timedelta(minutes=10)
        )
    
    def generate_events(self):
        # Test customer creation
        yield self.create_customer_event()
        yield self.wait(1)
        
        # Test normal transaction
        yield self.create_transaction_event(amount=100.0, fraud_score=0.1)
        yield self.wait(1)
        
        # Test suspicious transaction  
        yield self.create_transaction_event(amount=10000.0, fraud_score=0.9)
        yield self.wait(1)
        
        # Test account blocking
        yield self.create_block_account_event()
```

### Nexum → Bastion REST Integration Test

```bash
# Run scenario that specifically tests REST integration
python run.py --scenario rest_integration_test \
  --nexum-url http://localhost:8090 \
  --bastion-url http://localhost:8080 \
  --dashboard --dashboard-port 8095

# This should test:
# - Customer creation in Nexum
# - Transaction scoring via Bastion REST API
# - Decision feedback to Nexum
# - Case creation in Bastion for high-risk transactions
```

### Kafka Event Flow Test

```bash
# Run with Kafka enabled to test event-driven flow
python run.py --scenario kafka_integration_test \
  --nexum-url http://localhost:8090 \
  --bastion-url http://localhost:8080 \
  --kafka-enabled \
  --dashboard --dashboard-port 8095

# Monitor events:
# Terminal 1: Transaction events
docker exec kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic transactions

# Terminal 2: Fraud alerts  
docker exec kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic fraud-alerts
```

### Transaction Rejection Test

```bash
# Test fraud blocking (transaction rejection)
python run.py --scenario high_fraud_test \
  --nexum-url http://localhost:8090 \
  --bastion-url http://localhost:8080 \
  --dashboard --dashboard-port 8095

# Verify blocking:
# 1. High fraud scores → Bastion marks as high risk
# 2. Nexum receives rejection recommendation
# 3. Transaction is declined
# 4. Account balance unchanged
# 5. Case created in Bastion
```

### Case Creation Test

```python
# Custom scenario for testing case creation
python run.py --scenario case_creation_test \
  --nexum-url http://localhost:8090 \
  --bastion-url http://localhost:8080 \
  --dashboard --dashboard-port 8095

# This should:
# - Generate transactions with varying risk scores
# - Create cases in Bastion for scores > 0.7
# - Show cases in Bastion dashboard
# - Allow case investigation workflow
```

### Customer Risk Profile Update Test

```bash
# Test customer risk profile updates
python run.py --scenario risk_profile_test \
  --nexum-url http://localhost:8090 \
  --bastion-url http://localhost:8080 \
  --dashboard --dashboard-port 8095

# Should test:
# - Initial customer creation with low risk
# - Multiple high-risk transactions
# - Risk profile update in Nexum
# - Future transactions affected by risk profile
```

## Troubleshooting

### Common Issues and Solutions

#### Connection Refused Errors

**Symptom:**
```
requests.exceptions.ConnectionError: HTTPConnectionPool(host='localhost', port=8090): Max retries exceeded
```

**Solutions:**
1. **Check if service is running:**
   ```bash
   # Check if port is listening
   lsof -i :8090  # For Nexum
   lsof -i :8080  # For Bastion
   lsof -i :8095  # For Simulator
   ```

2. **Verify service health:**
   ```bash
   curl http://localhost:8090/health  # Should return 200 OK
   ```

3. **Check firewall/network:**
   ```bash
   # Test local connectivity
   telnet localhost 8090
   ```

4. **Review service logs:**
   - Check terminal output for error messages
   - Look for port binding issues
   - Verify database connections

#### Kafka Not Available

**Symptom:**
```
kafka.errors.NoBrokersAvailable: NoBrokersAvailable
```

**Solutions:**
1. **Check Kafka status:**
   ```bash
   docker ps | grep kafka
   # Should show running Kafka container
   ```

2. **Restart Kafka:**
   ```bash
   docker restart kafka
   docker restart zookeeper
   ```

3. **Verify Kafka connectivity:**
   ```bash
   docker exec kafka kafka-topics --list --bootstrap-server localhost:9092
   ```

4. **Run without Kafka:**
   ```bash
   # Disable Kafka temporarily
   python run.py --scenario normal_day \
     --nexum-url http://localhost:8090 \
     --bastion-url http://localhost:8080 \
     --no-kafka \
     --dashboard
   ```

#### Port Conflicts

**Symptom:**
```
OSError: [Errno 48] Address already in use
```

**Solutions:**
1. **Find process using port:**
   ```bash
   lsof -i :8090  # Replace with your port
   ```

2. **Kill conflicting process:**
   ```bash
   kill -9 <PID>
   ```

3. **Use alternative ports:**
   ```bash
   # Start on different ports
   uvicorn core_banking.api_old:app --port 8091
   uvicorn bastion.api:app --port 8081
   python run.py --dashboard-port 8096
   ```

#### Authentication/Authorization Issues

**Symptom:**
```
HTTPError: 401 Unauthorized
```

**Solutions:**
1. **Check API keys/tokens:**
   ```bash
   # Verify environment variables
   echo $NEXUM_API_KEY
   echo $BASTION_API_KEY
   ```

2. **Test with curl:**
   ```bash
   # Test authenticated endpoint
   curl -H "Authorization: Bearer $API_TOKEN" \
        http://localhost:8090/api/protected-endpoint
   ```

3. **Disable auth for testing:**
   ```bash
   # Set environment variable to disable auth
   export NEXUM_DISABLE_AUTH=true
   export BASTION_DISABLE_AUTH=true
   ```

#### Database Connection Issues

**Symptom:**
```
sqlalchemy.exc.OperationalError: (psycopg2.OperationalError) connection to server failed
```

**Solutions:**
1. **Check database service:**
   ```bash
   # For PostgreSQL
   brew services list | grep postgresql
   
   # For SQLite (check file permissions)
   ls -la *.db
   ```

2. **Test database connection:**
   ```bash
   # PostgreSQL
   psql -h localhost -p 5432 -U username -d database_name
   
   # SQLite
   sqlite3 nexum.db ".tables"
   ```

3. **Use SQLite for testing:**
   ```bash
   # Switch to SQLite temporarily
   export NEXUM_DATABASE_URL=sqlite:///nexum.db
   export BASTION_DATABASE_URL=sqlite:///bastion.db
   ```

#### Performance Issues

**Symptoms:**
- High latency
- Timeouts
- Slow dashboard updates

**Solutions:**
1. **Check system resources:**
   ```bash
   # Monitor CPU/Memory usage
   top -o cpu
   
   # Monitor disk I/O
   iostat 1
   ```

2. **Reduce simulation speed:**
   ```bash
   # Lower speed multiplier
   python run.py --scenario normal_day --speed-multiplier 10
   ```

3. **Check database performance:**
   ```bash
   # Monitor database queries
   tail -f /var/log/postgresql/postgresql.log
   ```

4. **Optimize database:**
   ```sql
   -- Add indexes for common queries
   CREATE INDEX idx_transactions_timestamp ON transactions(timestamp);
   CREATE INDEX idx_transactions_customer_id ON transactions(customer_id);
   ```

### Log Analysis

#### Enable Debug Logging

```bash
# Enable debug logging for all services
export NEXUM_LOG_LEVEL=DEBUG
export BASTION_LOG_LEVEL=DEBUG  
export SIMULATOR_LOG_LEVEL=DEBUG

# Or set in Python
import logging
logging.getLogger().setLevel(logging.DEBUG)
```

#### Centralized Logging

```bash
# Collect all logs in one place
tail -f /tmp/nexum.log /tmp/bastion.log /tmp/simulator.log

# Or use Docker logs
docker-compose logs -f
```

#### Log Patterns to Watch

**Successful integration:**
```
INFO: Transaction processed successfully
INFO: Fraud score received from Bastion: 0.23
INFO: Transaction approved by Nexum
```

**Integration failures:**
```
ERROR: Failed to connect to Bastion API
WARNING: Fraud scoring timeout, using default score
ERROR: Transaction rejected by Nexum
```

### Health Check Script

Create a health check script to verify all integrations:

```bash
#!/bin/bash
# health_check.sh

echo "Banking Simulator Integration Health Check"
echo "========================================="

# Check each service
services=("nexum:8090" "bastion:8080" "simulator:8095")

for service in "${services[@]}"; do
    name=${service%:*}
    port=${service#*:}
    
    if curl -s -f http://localhost:$port/health > /dev/null; then
        echo "✅ $name (port $port) - OK"
    else
        echo "❌ $name (port $port) - FAILED"
    fi
done

# Test integration
echo ""
echo "Testing Integration..."

# Test transaction flow
response=$(curl -s -X POST http://localhost:8090/api/test-transaction)
if echo $response | grep -q "success"; then
    echo "✅ Nexum → Bastion integration - OK"
else
    echo "❌ Nexum → Bastion integration - FAILED"
fi

echo ""
echo "Health check complete!"
```

### Getting Help

If you encounter issues not covered here:

1. **Check service logs** for error messages
2. **Verify prerequisites** are met
3. **Test individual services** before integration
4. **Use the health check script** to identify issues
5. **Check GitHub issues** for known problems
6. **File a bug report** with:
   - Steps to reproduce
   - Error messages
   - Service logs
   - Environment details

---

## Summary

This guide provides three different methods to integrate the Banking Simulator with Nexum and Bastion:

1. **Manual Setup**: Best for development and debugging
2. **Docker Compose**: Quick setup for testing
3. **Kafka Integration**: Production-like event-driven architecture

Each method provides full integration testing capabilities with comprehensive monitoring through three specialized dashboards. Use the troubleshooting section to resolve common issues and maintain optimal performance.

For additional help or advanced configuration, refer to the individual service documentation or file issues in the respective GitHub repositories.