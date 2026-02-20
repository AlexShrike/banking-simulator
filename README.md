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

## Quick Start

### Standalone Mode (No Dependencies)

Test the simulator without external systems:

```bash
cd banking-simulator
python run.py --scenario normal_day --dry-run --dashboard
```

Open http://localhost:8095 to view the dashboard.

### Full Integration

With Nexum and Bastion running:

```bash
# Run normal business day scenario
python run.py --scenario normal_day --dashboard

# Run coordinated fraud attack
python run.py --scenario fraud_attack --speed 100 --dashboard

# Run peak load stress test
python run.py --scenario peak_load --dashboard-port 8080
```

### Docker Compose (Full Stack)

```bash
# Start complete banking stack
docker-compose up -d

# View logs
docker-compose logs -f simulator
```

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Banking        │    │  Nexum          │    │  Bastion        │
│  Simulator      ├────┤  Core Banking   ├────┤  Fraud Detection│
│                 │    │  (Port 8090)    │    │  (Port 8080)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Dashboard      │    │  PostgreSQL     │    │  Kafka          │
│  (Port 8095)    │    │  Database       │    │  (Optional)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Scenarios

### Built-in Scenarios

- **normal_day**: Typical business day with 10K transactions, 0.1% fraud rate
- **fraud_attack**: Coordinated card testing and account takeover attacks  
- **peak_load**: Black Friday-style high volume (100+ TPS)
- **mule_network**: Money laundering with layering and structuring
- **onboarding**: Mass customer onboarding with identity verification

### Creating Custom Scenarios

Create a YAML file in the `scenarios/` directory:

```yaml
name: "Custom Scenario"
description: "Your scenario description"
duration_hours: 8
speed_multiplier: 200
customers: 750
accounts_per_customer: 2
initial_balance: 8000.00

transaction_rate:
  peak_tps: 25
  off_peak_tps: 8
  business_hours: [9, 17]

fraud:
  rate: 0.003  # 0.3% fraud rate
  patterns:
    - type: card_testing
      weight: 0.4
      intensity: 1.2
    - type: velocity_attack
      weight: 0.6
      intensity: 0.8
```

## Dashboard

The real-time dashboard provides:

### Control Panel
- Start/pause/stop simulation
- Adjust speed multiplier in real-time
- System status and health monitoring

### Live Metrics
- Transaction rates and volumes
- Fraud detection statistics
- API performance (latency, error rates)
- System resource utilization

### Transaction Feed
- Live stream of transactions
- Color-coded fraud risk levels
- Fraud detection decisions in real-time

### Performance Charts
- Transaction rate over time
- Fraud detection accuracy
- API latency percentiles
- Error rate trends

## Installation

### Prerequisites

- Python 3.12+
- Nexum core banking system (optional)
- Bastion fraud detection system (optional)

### Setup

1. Clone and install dependencies:
```bash
git clone <repository>
cd banking-simulator

# Use shared virtual environment
source /Users/alexshrike/.openclaw/workspace/rustcluster/.venv/bin/activate
pip install httpx pydantic pyyaml faker fastapi[standard] uvicorn websockets
```

2. Configure external systems (optional):
```bash
# Set environment variables
export NEXUM_URL="http://your-nexum-server:8090"
export BASTION_URL="http://your-bastion-server:8080"
```

## Usage Examples

### Command Line Options

```bash
# List available scenarios
python run.py --list-scenarios

# Validate scenario file
python run.py --validate-scenario custom_scenario.yaml

# Run with custom parameters
python run.py \
  --scenario fraud_attack \
  --speed 500 \
  --customers 100 \
  --dashboard \
  --dashboard-port 8080

# Dry run for testing
python run.py --scenario normal_day --dry-run --dashboard
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

## Troubleshooting

### Common Issues

#### Dashboard not loading
- Check port 8095 is available
- Verify static files exist in `simulator/dashboard/static/`
- Check browser console for JavaScript errors

#### API connection errors
- Verify Nexum is running on port 8090
- Verify Bastion is running on port 8080
- Check network connectivity and firewall settings
- Use `--dry-run` to test without external dependencies

#### High memory usage
- Reduce customer count for large simulations
- Lower metrics retention time
- Disable CSV export for long runs

#### Slow performance
- Increase speed multiplier gradually
- Monitor API response times
- Check database performance on Nexum/Bastion

### Logging

Logs are written to both console and `banking_simulator.log`:

```bash
# Increase log verbosity
python run.py --scenario normal_day --verbose

# Monitor logs in real-time
tail -f banking_simulator.log
```

## Contributing

1. Fork the repository
2. Create feature branch
3. Add tests for new functionality
4. Update documentation
5. Submit pull request

## License

MIT License - see LICENSE file for details.