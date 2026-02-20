# Scenario Documentation

This document provides detailed descriptions of all built-in scenarios, what they simulate, expected results, and how to interpret the outcomes.

## Built-in Scenarios Overview

| Scenario | Duration | Customers | Fraud Rate | Primary Focus | Difficulty |
|----------|----------|-----------|------------|---------------|------------|
| `normal_day` | 24h | 500 | 0.1% | Baseline operations | ⭐ Easy |
| `fraud_attack` | 4h | 200 | 15% | Attack detection | ⭐⭐⭐ Hard |
| `peak_load` | 2h | 1000 | 0.3% | Performance testing | ⭐⭐ Medium |
| `mule_network` | 48h | 300 | 2% | Money laundering | ⭐⭐⭐⭐ Expert |
| `onboarding` | 8h | 2000 | 0.05% | Customer growth | ⭐⭐ Medium |

---

## normal_day.yaml - Baseline Business Operations

### Overview
Simulates a typical business day at a mid-size bank with normal transaction patterns and minimal fraud. This is the **recommended starting scenario** for new users.

### What It Simulates
- **Customer Base**: 500 active customers with 1,000 total accounts
- **Transaction Volume**: ~10,000 transactions over 24 hours
- **Business Patterns**: Clear peaks during business hours (8am-6pm), reduced weekend activity
- **Fraud Level**: Minimal (0.1% rate) representing normal background fraud

### Expected Results

#### Transaction Patterns
```
Hours    | TPS  | Volume | Description
---------|------|--------|---------------------------
00-06    | 2    | 1,200  | Overnight/automated transactions  
06-08    | 4    | 960    | Early morning ramp-up
08-12    | 10   | 3,600  | Morning business peak
12-14    | 8    | 1,680  | Lunch slight decrease
14-18    | 10   | 3,600  | Afternoon business peak  
18-00    | 3    | 1,080  | Evening wind-down
Weekend  | 3    | 720    | 30% reduction (0.3x multiplier)
```

#### Fraud Distribution
- **Card Testing**: ~30 attempts (small amounts $0.01-$5.00)
- **Velocity Attacks**: ~20 rapid-fire transaction bursts
- **Large Amount Fraud**: ~30 unusually large transactions
- **Location Anomalies**: ~20 impossible travel scenarios

### Key Performance Indicators

**Ideal Results** (what to expect with healthy systems):
- **Average TPS**: 4.2 transactions per second
- **Peak TPS**: 10-12 during business hours
- **API Latency**: Nexum <50ms, Bastion <100ms
- **Fraud Detection Rate**: >90% (should catch 45+ of 50 fraud attempts)
- **False Positive Rate**: <5% (fewer than 500 legitimate transactions flagged)

### Use Cases
- **System Validation**: Verify basic functionality works
- **Performance Baseline**: Establish normal operation metrics
- **Demo/Training**: Show how the system works under normal conditions
- **Regression Testing**: Ensure changes don't break basic functionality

### What to Watch For
- **Smooth TPS curves** following business hour patterns
- **Consistent API response times** without spikes or errors
- **Clear fraud scoring** with legitimate transactions scoring <0.3
- **Dashboard updates** flowing smoothly every second

---

## fraud_attack.yaml - Coordinated Attack Scenario

### Overview
Simulates a sophisticated, multi-phase cyber attack on the banking system. This scenario tests the fraud detection system's ability to identify and respond to coordinated attacks.

### What It Simulates
- **Attack Timeline**: 4-hour compressed attack simulation
- **Attack Window**: Concentrated fraud during 2am-3am (night attack)
- **Attack Phases**: Card testing followed by account takeover
- **Legitimate Cover**: Normal transactions continue to mask the attack

### Attack Phases

#### Phase 1: Reconnaissance (Hour 1)
- Low-level probing transactions
- Testing system response times
- Mapping account/card validation patterns

#### Phase 2: Card Testing Barrage (Hour 2, 2am-3am)
- **Volume**: 500 card test transactions in 10 minutes
- **Pattern**: Small amounts ($0.01-$5.00) across multiple merchants
- **Goal**: Validate stolen credit card numbers
- **Detection Challenge**: High velocity, small amounts

#### Phase 3: Account Takeover (Hour 3-4)
- **Trigger**: Follows successful card tests with 30-minute delay
- **Volume**: 20 high-value transfers
- **Pattern**: Large amounts (80% of account balances)
- **Detection Challenge**: Legitimate-looking amounts, validated credentials

### Expected Results

#### Attack Metrics
```
Time Window | Fraud TPS | Fraud % | Attack Type
------------|-----------|---------|------------------
Hour 1      | 1         | 5%      | Reconnaissance
Hour 2      | 8         | 40%     | Card Testing Peak  
Hour 3      | 2         | 25%     | Account Takeover
Hour 4      | 0.5       | 10%     | Cleanup/Extraction
```

#### Detection Challenges
- **Velocity Detection**: System must catch 50+ transactions in 10 minutes
- **Amount Pattern Recognition**: Small tests followed by large transfers  
- **Timing Correlation**: Link card testing success to account takeover
- **False Positive Management**: Don't flag legitimate late-night transactions

### Key Performance Indicators

**Fraud Detection Success Metrics**:
- **Card Testing Detection**: >95% (should catch 475+ of 500 tests)
- **Account Takeover Detection**: >85% (17+ of 20 large transfers)
- **Overall Detection Rate**: >90% across all attack phases
- **Response Time**: Fraud alerts within 5 seconds of detection

**System Performance Under Attack**:
- **API Latency**: May increase to 100-200ms during peak attack
- **Error Rate**: Should remain <1% even during attack volume
- **TPS Handling**: System should sustain 20+ TPS during attack window

### Fraud Patterns to Observe

#### Card Testing Pattern
```json
{
  "transaction_sequence": [
    {"amount": 1.00, "merchant": "test_merchant_1", "result": "decline"},
    {"amount": 0.50, "merchant": "test_merchant_2", "result": "approve"}, 
    {"amount": 2.00, "merchant": "test_merchant_3", "result": "approve"},
    {"amount": 5.00, "merchant": "test_merchant_1", "result": "approve"}
  ],
  "pattern_detection": "velocity + small_amounts + multi_merchant"
}
```

#### Account Takeover Pattern  
```json
{
  "preconditions": "successful_card_testing",
  "delay_minutes": 30,
  "transaction_pattern": {
    "amount": "$8,000 (80% of $10,000 balance)",
    "type": "transfer", 
    "destination": "external_account",
    "risk_factors": ["large_amount", "unusual_time", "new_destination"]
  }
}
```

### Use Cases
- **Attack Simulation Training**: Train security teams on attack patterns
- **Detection Algorithm Testing**: Validate ML model performance
- **Incident Response Testing**: Practice response to real attacks  
- **System Stress Testing**: Ensure system stability under attack load

### What to Watch For
- **Fraud Score Spikes**: Scores should jump to 0.8+ during attacks
- **Alert Generation**: Dashboard should show red alerts during attack window
- **System Stability**: No crashes or significant performance degradation
- **Recovery Time**: System should return to normal after attack ends

---

## peak_load.yaml - High-Volume Stress Test

### Overview
Simulates Black Friday or major shopping event with extremely high transaction volume. Tests system performance, scaling, and reliability under sustained load.

### What It Simulates
- **Event**: Black Friday shopping rush
- **Duration**: 2 hours of peak activity
- **Volume**: 50+ TPS sustained (vs 10 TPS normal)
- **Customer Behavior**: Impulse buying, large purchases, mobile payments
- **Fraud Opportunity**: Higher fraud rate (0.3%) due to rushed transactions

### Load Profile

#### Transaction Volume Curve
```
Time     | TPS  | Cumulative | Load Level
---------|------|------------|------------
0-15min  | 20   | 18,000     | Warm-up
15-30min | 35   | 48,600     | Early rush
30-60min | 50   | 138,600    | Peak load
60-90min | 45   | 219,600    | Sustained high
90-120min| 30   | 273,600    | Wind down
```

#### Customer Behavior Changes
- **Purchase Frequency**: 3x normal rate
- **Transaction Amounts**: 2x larger on average
- **Payment Methods**: Heavy mobile/online usage
- **Geographic Spread**: Wider location distribution
- **Time Sensitivity**: Rapid successive purchases

### Expected Results

#### Performance Benchmarks
- **Target TPS**: 50 transactions per second sustained
- **API Response Time**: Should remain <200ms even at peak
- **Error Rate**: Must stay <2% throughout the test
- **Memory Usage**: May reach 1GB+ with high customer volume
- **Database Performance**: Connection pool pressure, query optimization critical

#### System Behavior Under Load
```
Metric               | Normal   | Peak Load | Alert Threshold
---------------------|----------|-----------|------------------
TPS                  | 10       | 50        | >60 (overload)
API Latency (P95)    | 50ms     | 150ms     | >500ms
Memory Usage         | 200MB    | 800MB     | >2GB  
CPU Usage            | 15%      | 60%       | >90%
Database Connections | 5        | 25        | >50
```

### Fraud Patterns Under Load

#### Increased Fraud Opportunities
- **Transaction Rush Masking**: Fraudsters hide in legitimate volume
- **System Stress Exploitation**: Target overloaded fraud detection
- **Customer Confusion**: Rushed customers less likely to notice fraud

#### Expected Fraud Types
- **Card Not Present**: Online shopping surge creates CNP fraud
- **Account Takeover**: Customers using weak passwords on mobile
- **Velocity Attacks**: Legitimate high velocity masks fraud velocity
- **Large Amount**: Big ticket items provide cover for fraud

### Performance Testing Checklist

#### Before Running Peak Load
```bash
# 1. Ensure sufficient system resources
free -h  # Check available RAM
df -h    # Check disk space
ulimit -n  # Check file descriptor limits

# 2. Optimize scenario settings for performance
customers: 1000         # Reduce if memory constrained
accounts_per_customer: 2  # Keep reasonable  
metrics:
  retention_minutes: 30  # Reduce retention
  export_csv: false     # Disable during load test

# 3. Pre-warm external systems
curl http://localhost:8090/health  # Nexum ready
curl http://localhost:8080/health  # Bastion ready
```

#### During Peak Load Test
Monitor these metrics continuously:
- **Dashboard responsiveness**: Should update smoothly
- **API error rates**: Watch for timeout/connection errors
- **Memory growth**: Ensure no memory leaks
- **CPU utilization**: Should not max out at 100%

#### After Peak Load Test
```bash
# Check for any errors or warnings
grep -i "error\|warning" banking_simulator.log | tail -50

# Verify transaction counts match expectations  
grep "Transactions processed" banking_simulator.log | tail -1

# Check resource cleanup
ps aux | grep python  # No zombie processes
netstat -an | grep CLOSE_WAIT  # No stuck connections
```

### Use Cases
- **Capacity Planning**: Determine maximum system throughput
- **Black Friday Preparation**: Test before actual high-load events
- **Infrastructure Validation**: Verify scaling mechanisms work
- **Performance Regression Testing**: Catch performance degradations

### What to Watch For
- **Linear TPS scaling** as load increases
- **Stable API latency** even at peak volume  
- **No memory leaks** during sustained load
- **Graceful degradation** if limits are reached
- **Quick recovery** when load returns to normal

---

## mule_network.yaml - Money Laundering Detection

### Overview
Advanced scenario simulating sophisticated money laundering operations using money mule networks. Tests the system's ability to detect complex financial crime patterns that span multiple accounts and time periods.

### What It Simulates
- **Duration**: 48 hours (2 days) for pattern development
- **Criminal Organization**: Network of 20+ money mule accounts
- **Laundering Techniques**: Layering, structuring, smurfing
- **Legitimate Cover**: Normal customer activity to provide cover

### Money Laundering Techniques

#### 1. Layering (Transaction Chain Obfuscation)
- **Pattern**: A→B→C→D→E→F (6-hop money movement)
- **Timing**: Rapid succession (completed within 2 hours)
- **Amounts**: Gradually decreasing to suggest legitimacy
- **Detection Challenge**: Individual transactions look normal

```
Example Layering Chain:
Account A: $50,000 → Account B: $48,500 → Account C: $46,000 → 
Account D: $43,500 → Account E: $41,000 → Account F: $38,500
(Final destination: Criminal account with "clean" money)
```

#### 2. Structuring (Under-Reporting Avoidance)
- **Pattern**: Breaking $50,000 into multiple sub-$10,000 transactions
- **Timing**: Spread across multiple days to avoid detection
- **Accounts**: Uses different accounts and locations
- **Detection Challenge**: Each transaction is below reporting thresholds

```
Example Structuring:
Day 1: $9,500 + $9,200 + $9,800 + $9,100 (4 transactions = $37,600)
Day 2: $8,900 + $9,300 + $9,700 + $9,400 (4 transactions = $37,300)  
Total: $74,900 across 8 transactions, all under $10,000
```

#### 3. Smurfing (Multiple Person Coordination)
- **Pattern**: 10+ people making coordinated small deposits
- **Timing**: Same time window (e.g., all within 1 hour)
- **Amounts**: Various small amounts ($500-$3,000)
- **Detection Challenge**: Requires pattern analysis across customers

### Expected Results

#### Money Laundering Metrics
```
Technique    | Transactions | Amount Moved | Detection Rate Target
-------------|-------------|--------------|---------------------
Layering     | 120         | $2,500,000   | >80% (network analysis)
Structuring  | 200         | $1,800,000   | >70% (amount patterns)
Smurfing     | 300         | $750,000     | >85% (timing correlation)
Combined     | 620         | $5,050,000   | >75% overall
```

#### Detection Challenges by Technique

**Layering Detection Requirements**:
- Transaction graph analysis
- Temporal correlation (rapid sequence detection)
- Amount flow tracking across multiple hops
- Account relationship mapping

**Structuring Detection Requirements**:
- Amount pattern recognition (just under thresholds)
- Cross-day transaction aggregation
- Same-customer behavior analysis
- Regulatory reporting threshold awareness

**Smurfing Detection Requirements**:
- Cross-customer correlation analysis
- Timing pattern recognition
- Geographic clustering detection
- Small amount aggregation

### Advanced Fraud Patterns

#### Network Analysis Requirements
```json
{
  "money_mule_network": {
    "central_accounts": ["acc_001", "acc_045", "acc_089"],
    "mule_accounts": ["acc_002", "acc_003", "acc_004", "...acc_025"],
    "relationships": [
      {"from": "acc_001", "to": "acc_002", "frequency": "high"},
      {"from": "acc_002", "to": "acc_003", "relationship": "layering"},
      {"from": "acc_003", "to": "acc_004", "pattern": "rapid_succession"}
    ],
    "red_flags": [
      "account_opened_recently",
      "no_prior_banking_history", 
      "unusual_geographic_activity",
      "transaction_timing_correlation"
    ]
  }
}
```

#### Behavioral Indicators
- **Account Age**: Newly opened accounts with immediate high activity
- **Geographic Anomalies**: Transactions from unusual locations
- **Timing Patterns**: Coordinated activity across multiple accounts
- **Amount Patterns**: Mathematically precise amount distributions

### Key Performance Indicators

#### Detection Algorithm Success Metrics
- **Network Detection**: Identify 80%+ of connected account clusters
- **Pattern Recognition**: Catch 70%+ of structuring attempts
- **Timing Analysis**: Detect 85%+ of coordinated smurfing
- **False Positive Rate**: <10% (don't flag legitimate business relationships)

#### System Performance Requirements
- **Graph Analysis**: Complex relationship queries complete within 5 seconds
- **Historical Analysis**: Pattern detection across 48-hour windows
- **Cross-Customer Correlation**: Real-time analysis of multi-customer patterns
- **Memory Usage**: Graph algorithms may require 1GB+ for network analysis

### Use Cases
- **AML Compliance Testing**: Validate Anti-Money Laundering capabilities
- **Regulatory Preparedness**: Test reporting and detection requirements
- **Advanced Analytics**: Validate graph analysis and pattern recognition
- **Investigator Training**: Provide realistic money laundering scenarios

### What to Watch For
- **Network Visualization**: Dashboard should show account relationship graphs
- **Pattern Alerts**: Multiple related alerts for connected transactions
- **Investigation Tools**: Ability to trace money flow through multiple accounts
- **Compliance Reports**: Automated generation of suspicious activity reports

---

## onboarding.yaml - Customer Growth Simulation

### Overview
Simulates a bank's customer acquisition campaign with mass customer onboarding. Tests customer creation processes, initial account setup, and early customer behavior patterns.

### What It Simulates
- **Growth Event**: Major marketing campaign driving new customer signups
- **Duration**: 8 hours of intensive onboarding
- **Volume**: 2,000 new customers (250 customers/hour)
- **Verification Challenges**: Identity verification bottlenecks
- **Early Activity**: New customer transaction patterns

### Customer Onboarding Pipeline

#### Phase 1: Registration Surge (Hours 1-2)
- **Rate**: 400 customers/hour
- **Pattern**: Marketing campaign response
- **Geographic**: Concentrated in target demographics
- **Challenges**: System load, verification backlogs

#### Phase 2: Account Setup (Hours 3-4)
- **Activity**: Initial deposits, card activation
- **Volume**: 1,500+ account creation transactions
- **Pattern**: Small initial deposits ($100-$1,000)
- **Verification**: Identity document processing

#### Phase 3: Early Usage (Hours 5-8)
- **Behavior**: First real transactions
- **Pattern**: ATM usage, small purchases
- **Learning**: New customers figuring out the system
- **Risk**: Higher error rates, confusion

### Expected Results

#### Customer Creation Metrics
```
Time Period | New Customers | Accounts | Initial Deposits | Avg Deposit
------------|---------------|----------|------------------|------------
Hour 1      | 400           | 500      | $287,500         | $575
Hour 2      | 350           | 425      | $198,250         | $467
Hour 3      | 300           | 375      | $156,000         | $416
Hour 4      | 250           | 312      | $124,800         | $400
Hours 5-8   | 700           | 875      | $350,000         | $400
Total       | 2,000         | 2,487    | $1,116,550       | $456 avg
```

#### System Load Patterns
- **Database Growth**: 2,000+ new customer records
- **API Volume**: Customer creation endpoints heavily utilized  
- **Storage**: Identity documents, profile photos
- **Network**: Video calls for identity verification

### Identity Verification Challenges

#### Common Verification Issues
- **Document Quality**: Poor photo uploads requiring retries
- **Name Mismatches**: Slight differences in legal vs provided names
- **Address Verification**: New addresses not yet in verification databases
- **Identity Theft Attempts**: Fraudulent identity document submissions

#### Expected Fraud During Onboarding
- **Synthetic Identity**: 0.2% (4 attempts per 2,000 customers)  
- **Identity Theft**: 0.1% (2 attempts per 2,000 customers)
- **Application Fraud**: 0.3% (6 attempts with false information)
- **Account Takeover Setup**: Setting up accounts for later compromise

### Performance Implications

#### Database Performance
```sql
-- Heavy INSERT activity on customer tables
INSERT INTO customers (name, email, phone, ...) VALUES (...);
INSERT INTO accounts (customer_id, account_type, ...) VALUES (...);
INSERT INTO verification_documents (...) VALUES (...);

-- Index performance critical for:
SELECT * FROM customers WHERE email = ?  -- Duplicate checking
SELECT * FROM verification_queue WHERE status = 'pending'  -- Processing queue
```

#### API Load Distribution
- **Customer Creation API**: 250 requests/hour
- **Account Setup API**: 300 requests/hour  
- **Document Upload API**: 500 requests/hour
- **Verification Status API**: 1,000 requests/hour (polling)

### Customer Behavior Patterns

#### New Customer Transaction Characteristics
- **First Week**: 2-3 transactions per day (learning period)
- **Transaction Amounts**: Lower than experienced customers
- **Channel Preference**: Heavy mobile app usage
- **Error Rate**: 3x higher due to unfamiliarity

#### Early Warning Signs
- **Immediate Large Transfers**: Suspicious for new accounts
- **Unusual Geographic Activity**: Account opened in one state, used in another
- **Rapid Account Closure**: Sign of fraudulent intent

### Use Cases
- **Growth Planning**: Test system capacity for customer acquisition campaigns
- **Onboarding Process Optimization**: Identify bottlenecks in customer setup
- **Fraud Prevention**: Test new customer fraud detection
- **Customer Experience**: Validate smooth onboarding flow

### What to Watch For
- **API Performance**: Customer creation endpoints under sustained load
- **Database Performance**: Large number of INSERT operations
- **Queue Management**: Verification backlog not growing uncontrollably
- **Error Handling**: Graceful handling of verification failures
- **Fraud Detection**: Early detection of suspicious new accounts

---

## Creating Custom Scenarios

### Scenario Design Best Practices

#### 1. Start with Clear Objectives
- **Performance Testing**: High volume, simple patterns
- **Fraud Detection**: Complex patterns, varied techniques  
- **User Training**: Realistic but observable patterns
- **Compliance Testing**: Regulatory-focused scenarios

#### 2. Balance Realism and Observability
- **Realistic**: Patterns match real-world behavior
- **Observable**: Results clearly visible in dashboard
- **Measurable**: Clear success/failure criteria
- **Actionable**: Clear next steps based on results

#### 3. Consider System Limitations
- **Memory Constraints**: Large customer sets require more RAM
- **API Rate Limits**: External systems may have throughput caps
- **Network Bandwidth**: High-frequency scenarios need good connectivity
- **Storage Space**: Long scenarios generate large log files

### Custom Scenario Template

```yaml
name: "Custom Scenario Name"
description: "What this scenario tests and why"
duration_hours: 8
speed_multiplier: 100
customers: 500
accounts_per_customer: 2
initial_balance: 5000.00

# Transaction generation
transaction_rate:
  peak_tps: 15
  off_peak_tps: 3
  business_hours: [9, 17]
  
# Fraud configuration
fraud:
  rate: 0.002  # 0.2% fraud rate
  patterns:
    - type: your_fraud_type
      weight: 0.5
      intensity: 1.0
      
# System connections
connections:
  nexum_url: "http://localhost:8090"
  bastion_url: "http://localhost:8080"
  timeout_seconds: 30
  
# Performance settings
dashboard:
  enabled: true
  port: 8095
  
metrics:
  enabled: true
  collect_interval_seconds: 1
  retention_minutes: 60
  export_csv: true
```

### Testing Your Custom Scenario

```bash
# 1. Validate the YAML syntax
python run.py --validate-scenario scenarios/my_custom_scenario.yaml

# 2. Test with minimal load
python run.py --scenario scenarios/my_custom_scenario.yaml --customers 5 --speed 100 --dry-run

# 3. Test with dashboard
python run.py --scenario scenarios/my_custom_scenario.yaml --customers 50 --speed 200 --dashboard

# 4. Full test run
python run.py --scenario scenarios/my_custom_scenario.yaml --dashboard
```