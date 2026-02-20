# Custom Scenarios Guide

This guide provides comprehensive documentation for creating your own banking simulation scenarios, including YAML schema reference, configuration options, and advanced patterns.

## Table of Contents

1. [Quick Start](#quick-start)
2. [YAML Schema Reference](#yaml-schema-reference)
3. [Configuration Fields](#configuration-fields)
4. [Transaction Rate Patterns](#transaction-rate-patterns)
5. [Fraud Pattern Types](#fraud-pattern-types)
6. [Advanced Features](#advanced-features)
7. [Example Scenarios](#example-scenarios)
8. [Testing & Validation](#testing--validation)
9. [Best Practices](#best-practices)

---

## Quick Start

### Creating Your First Custom Scenario

1. **Copy an existing scenario as a template:**
```bash
cd /Users/alexshrike/.openclaw/workspace/banking-simulator/scenarios
cp normal_day.yaml my_scenario.yaml
```

2. **Edit the basic parameters:**
```yaml
name: "My Custom Scenario"
description: "Testing custom transaction patterns"
duration_hours: 2  # Shorter for quick testing
speed_multiplier: 300  # Faster execution
customers: 100  # Smaller dataset
```

3. **Validate your scenario:**
```bash
python run.py --validate-scenario scenarios/my_scenario.yaml
```

4. **Test with dry run:**
```bash
python run.py --scenario scenarios/my_scenario.yaml --dry-run --dashboard
```

---

## YAML Schema Reference

### Complete Schema Structure

```yaml
# Required fields
name: string                    # Display name for the scenario
description: string            # What this scenario simulates
duration_hours: number         # Simulation duration in hours
speed_multiplier: number       # Time acceleration factor

# Customer generation
customers: number              # Number of customer profiles to create
accounts_per_customer: number  # Bank accounts per customer (1-5)
initial_balance: number        # Starting balance per account
currency: string              # Currency code (USD, EUR, GBP, etc.)

# Transaction patterns  
transaction_rate:
  peak_tps: number            # Peak transactions per second
  off_peak_tps: number       # Off-peak transactions per second
  business_hours: [number, number]  # Peak hours [start, end] (24h format)
  weekend_multiplier: number  # Weekend activity reduction (0.0-1.0)

# Fraud configuration
fraud:
  rate: number               # Base fraud rate (0.001 = 0.1%)
  attack_window: [number, number]  # Optional concentrated attack hours
  patterns: []               # Array of fraud pattern definitions

# System connections
connections:
  nexum_url: string         # Nexum API endpoint
  bastion_url: string       # Bastion API endpoint
  kafka_bootstrap_servers: string  # Kafka brokers (optional)
  timeout_seconds: number   # API timeout
  max_retries: number      # API retry attempts

# Dashboard settings
dashboard:
  enabled: boolean          # Enable dashboard
  port: number             # Dashboard port
  host: string             # Dashboard bind address

# Metrics collection
metrics:
  enabled: boolean                  # Enable metrics collection
  collect_interval_seconds: number # Metrics collection frequency
  retention_minutes: number        # Memory retention time
  export_csv: boolean              # Export metrics to CSV files
```

---

## Configuration Fields

### Basic Scenario Configuration

#### Name & Description
```yaml
name: "Production Load Test"
description: "Simulates Black Friday shopping load with 50+ TPS sustained throughput"
```

**Best Practices:**
- Use descriptive names that indicate the scenario's purpose
- Include key metrics in the description (TPS, fraud rate, duration)
- Mention any special requirements or setup needed

#### Duration & Speed
```yaml
duration_hours: 24          # Real-world time being simulated
speed_multiplier: 100       # Acceleration factor (100x = 24h in ~14min)
```

**Speed Multiplier Guidelines:**
- `1`: Real-time (use for production testing)
- `10-50`: Slow demo (observable patterns)
- `100-500`: Standard testing (good balance)
- `1000+`: Fast testing (stress test mode)

**Duration Considerations:**
- Short scenarios (1-4 hours): Good for specific event testing
- Medium scenarios (8-24 hours): Full business day simulation
- Long scenarios (48+ hours): Multi-day pattern analysis

### Customer Configuration

```yaml
customers: 500                    # Total customer profiles
accounts_per_customer: 2          # Average accounts per customer
initial_balance: 5000.00         # Starting balance in accounts
currency: "USD"                  # Account currency
```

**Customer Count Guidelines:**
- Small (10-100): Development and debugging
- Medium (100-1000): Standard testing
- Large (1000+): Load testing (requires more memory)

**Account Structure:**
- 1 account/customer: Simple scenarios
- 2-3 accounts/customer: Realistic (checking + savings)
- 4+ accounts/customer: Complex scenarios (business customers)

### Advanced Customer Configuration

```yaml
# Advanced customer generation options
customer_demographics:
  age_distribution:
    min_age: 18
    max_age: 80
    median_age: 35
  
  income_distribution:
    type: "log_normal"           # normal, log_normal, uniform
    median_income: 55000
    income_std_dev: 25000
    
  geographic_distribution:
    regions: ["west_coast", "east_coast", "midwest", "south"]
    weights: [0.3, 0.3, 0.2, 0.2]
    
  customer_types:
    - type: "standard"
      weight: 0.8
      transaction_multiplier: 1.0
    - type: "premium"  
      weight: 0.15
      transaction_multiplier: 2.5
    - type: "business"
      weight: 0.05
      transaction_multiplier: 5.0
```

---

## Transaction Rate Patterns

### Basic Rate Configuration

```yaml
transaction_rate:
  peak_tps: 15              # Peak transactions per second
  off_peak_tps: 3           # Off-peak transactions per second
  business_hours: [9, 17]   # 9am-5pm peak activity
  weekend_multiplier: 0.4   # 40% of weekday activity
```

### Advanced Rate Patterns

#### Hourly Multipliers
```yaml
transaction_rate:
  peak_tps: 20
  off_peak_tps: 2
  business_hours: [8, 18]
  
  # Custom multiplier for each hour of the day
  hourly_multipliers:
    0: 0.1    # Midnight: 10% of base rate
    1: 0.05   # 1 AM: 5% of base rate  
    6: 0.3    # 6 AM: 30% (early morning)
    8: 1.2    # 8 AM: 120% (morning rush)
    12: 1.8   # Noon: 180% (lunch peak)
    17: 1.5   # 5 PM: 150% (evening rush)
    20: 0.8   # 8 PM: 80% (evening activity)
    23: 0.2   # 11 PM: 20% (late night)
```

#### Day-of-Week Variations
```yaml
transaction_rate:
  # ... base configuration ...
  
  weekday_multipliers:
    monday: 1.1      # 10% higher (Monday blues = more spending?)
    tuesday: 1.0     # Normal
    wednesday: 1.0   # Normal  
    thursday: 1.1    # 10% higher
    friday: 1.3      # 30% higher (TGIF spending)
    saturday: 0.6    # 40% lower (weekend)
    sunday: 0.4      # 60% lower (quiet Sunday)
```

#### Seasonal Patterns
```yaml
transaction_rate:
  # ... base configuration ...
  
  # Monthly multipliers for seasonal effects
  seasonal_multipliers:
    1: 0.8     # January: 20% lower (post-holiday)
    2: 0.9     # February: 10% lower
    3: 1.0     # March: Normal
    11: 1.4    # November: 40% higher (Black Friday prep)
    12: 1.6    # December: 60% higher (Holiday shopping)
```

#### Special Event Patterns
```yaml
transaction_rate:
  # ... base configuration ...
  
  # Special event spikes
  special_events:
    - name: "Black Friday"
      start_hour: 480    # Hour 480 of simulation (day 20, 8am)
      duration_hours: 8
      multiplier: 3.0    # 300% increase
      
    - name: "Cyber Monday" 
      start_hour: 552    # Hour 552 (day 23, 8am)
      duration_hours: 12
      multiplier: 2.5    # 250% increase
      transaction_types: ["online_purchase"]  # Only affects online purchases
```

### Complex Rate Patterns

#### Multi-Phase Load Pattern
```yaml
transaction_rate:
  # Multi-phase load testing pattern
  phases:
    - name: "warm_up"
      start_hour: 0
      duration_hours: 1  
      tps: 5
      
    - name: "ramp_up"
      start_hour: 1
      duration_hours: 2
      tps_start: 5
      tps_end: 25       # Gradually increase to 25 TPS
      
    - name: "sustained_load"
      start_hour: 3
      duration_hours: 4
      tps: 25           # Hold at 25 TPS
      
    - name: "peak_burst"
      start_hour: 7
      duration_hours: 1
      tps: 50           # Spike to 50 TPS
      
    - name: "cool_down"  
      start_hour: 8
      duration_hours: 2
      tps_start: 50
      tps_end: 5        # Gradually decrease
```

#### Realistic Business Patterns
```yaml
transaction_rate:
  # Simulate realistic business day patterns
  business_patterns:
    - pattern_type: "retail_bank"
      morning_rush:
        hours: [8, 10]
        multiplier: 1.5
        types: ["atm_withdrawal", "branch_deposit"]
        
      lunch_peak:
        hours: [12, 14] 
        multiplier: 2.0
        types: ["card_purchase", "online_transfer"]
        
      evening_rush:
        hours: [17, 19]
        multiplier: 1.8
        types: ["card_purchase", "bill_payment"]
        
    - pattern_type: "online_bank"
      # Different pattern for online-only bank
      activity_curve: "flat_with_peaks"
      peak_hours: [12, 14, 20, 22]  # Lunch and evening
      base_multiplier: 0.8
      peak_multiplier: 1.5
```

---

## Fraud Pattern Types

### Basic Fraud Configuration

```yaml
fraud:
  rate: 0.002                 # 0.2% base fraud rate
  patterns:
    - type: card_testing
      weight: 0.4            # 40% of fraud attempts
      intensity: 1.0         # Standard intensity
```

### Comprehensive Fraud Pattern Types

#### Card Testing Attacks

```yaml
fraud:
  patterns:
    - type: card_testing
      weight: 0.3
      intensity: 1.5                    # 50% more aggressive than normal
      
      # Specific configuration
      transaction_count: 50             # Exact number of test transactions
      duration_minutes: 5               # Complete within 5 minutes
      amount_range: [0.01, 2.00]       # Test amounts between $0.01-$2.00
      
      # Merchant targeting
      merchant_types: ["gas_station", "convenience_store", "fast_food"]
      merchant_selection: "random"      # random, sequential, targeted
      
      # Timing patterns
      burst_pattern: true              # Rapid succession vs spread out
      inter_transaction_delay: [10, 30] # 10-30 seconds between attempts
      
      # Success criteria (when does attack succeed?)
      success_threshold: 0.1           # 10% approval rate = successful test
      escalation:                      # What happens after successful test
        delay_minutes: 30              # Wait 30 minutes
        follow_up_pattern: "account_takeover"
```

#### Account Takeover Attacks

```yaml
fraud:
  patterns:  
    - type: account_takeover
      weight: 0.2
      intensity: 2.0
      
      # Prerequisites
      requires_successful: "card_testing"  # Must follow successful card testing
      prerequisite_delay: [15, 60]        # 15-60 minutes after prerequisite
      
      # Target selection
      target_criteria:
        min_balance: 1000               # Only target accounts with $1000+
        account_age_days: 30            # Only established accounts
        customer_type: ["premium", "business"]  # High-value targets
        
      # Attack characteristics
      transaction_pattern:
        initial_probe: 
          amount_percent: 0.05          # Start with 5% of balance
        escalation:
          amount_percent: 0.8           # Then take 80% if probe succeeds
          
      # Evasion techniques
      location_spoofing: true           # Spoof user's known locations
      device_mimicking: true            # Mimic user's device characteristics
      timing_mimicking: true            # Mimic user's transaction timing patterns
```

#### Velocity Attacks

```yaml
fraud:
  patterns:
    - type: velocity_attack
      weight: 0.25
      intensity: 1.8
      
      # Velocity characteristics
      transaction_burst:
        count: 25                      # 25 transactions in rapid succession
        time_window_seconds: 120       # Within 2 minutes
        amount_pattern: "increasing"   # Start small, increase amounts
        
      # Cross-merchant pattern
      merchant_hopping: true           # Use different merchants
      merchant_count: 8                # Across 8 different merchants
      
      # Amount progression
      amount_progression:
        start_amount: 50
        increment: 25                  # Increase by $25 each transaction
        max_amount: 500
        
      # Geographic spread
      location_spread:
        radius_km: 10                  # Within 10km radius
        impossible_travel: false       # Don't use impossible travel times
```

#### Money Laundering Patterns

```yaml
fraud:
  patterns:
    - type: money_laundering
      weight: 0.1
      intensity: 1.0
      
      # Layering configuration
      layering:
        chain_length: [5, 10]          # 5-10 transaction hops
        amount_degradation: 0.03       # 3% lost per hop (fees/conversion)
        time_spacing: [30, 120]        # 30-120 minutes between hops
        
        # Account network
        mule_account_count: 15         # Use 15 money mule accounts
        final_destination: "offshore"   # offshore, crypto, cash_equivalent
        
      # Structuring configuration  
      structuring:
        target_amount: 25000           # Total amount to launder
        transaction_limit: 9500        # Keep below $10k reporting limit
        time_spread_hours: 48          # Spread over 48 hours
        account_spread: 5              # Use 5 different accounts
        
      # Smurfing configuration
      smurfing:
        smurf_count: 12               # 12 different people involved
        coordination_window: 60        # All deposit within 1 hour
        amount_range: [500, 3000]     # Individual amounts $500-$3000
        location_clustering: true      # All in same geographic area
```

#### Advanced ML Evasion

```yaml
fraud:
  patterns:
    - type: ml_evasion
      weight: 0.15
      intensity: 2.5
      
      # Adaptive behavior
      detection_learning: true         # Learn from detection patterns
      evasion_adaptation: 
        detection_threshold: 0.7       # If fraud score > 0.7, adapt
        adaptation_methods:
          - "amount_perturbation"      # Slightly modify amounts
          - "timing_jitter"            # Add random timing noise  
          - "merchant_rotation"        # Switch merchant categories
          
      # Anti-pattern techniques
      legitimacy_mimicking:
        copy_user_patterns: true       # Copy legitimate user behavior
        historical_analysis_days: 30   # Analyze 30 days of user history
        pattern_confidence: 0.8        # 80% confidence in pattern match
        
      # Advanced evasion
      ensemble_attack:
        combine_patterns: ["card_testing", "velocity_attack"]
        pattern_weights: [0.3, 0.7]    # 30% card testing, 70% velocity
        synchronization: true          # Coordinate multiple attack types
```

### Multi-Phase Fraud Scenarios

```yaml
fraud:
  # Complex multi-phase attack scenario
  coordinated_attack:
    phases:
      - name: "reconnaissance"
        start_hour: 2
        duration_hours: 1
        patterns:
          - type: small_probe
            count: 20
            intensity: 0.5
            
      - name: "vulnerability_mapping"  
        start_hour: 3
        duration_hours: 2
        patterns:
          - type: card_testing
            count: 100
            intensity: 1.0
            success_threshold: 0.15
            
      - name: "exploitation"
        start_hour: 5
        duration_hours: 1
        patterns:
          - type: account_takeover
            count: 15
            intensity: 3.0
            requires_successful: "card_testing"
            
      - name: "money_movement"
        start_hour: 6  
        duration_hours: 3
        patterns:
          - type: money_laundering
            target_amount: 100000
            urgency: "high"             # Fast money movement
            
      - name: "cleanup"
        start_hour: 9
        duration_hours: 1
        patterns:
          - type: evidence_erasure
            clear_transaction_history: true
            create_false_trails: true
```

---

## Advanced Features

### Dynamic Scenario Adjustment

```yaml
# Scenarios can adjust based on real-time conditions
dynamic_adjustments:
  enabled: true
  
  # Adjust based on API response times
  api_performance_scaling:
    latency_threshold_ms: 200
    high_latency_action:
      reduce_tps_by: 0.3              # Reduce TPS by 30%
      extend_duration: 1.2            # Extend duration by 20%
      
  # Adjust based on error rates
  error_rate_scaling:
    error_threshold: 0.05             # 5% error rate
    high_error_action:
      enable_circuit_breaker: true
      fallback_to_mock: true
      
  # Adjust fraud rates based on detection success
  fraud_adaptation:
    detection_success_threshold: 0.9  # If 90%+ fraud detected
    adaptation_action:
      increase_evasion: 1.5           # Make fraud 50% more sophisticated
      reduce_fraud_rate: 0.8          # But reduce overall rate by 20%
```

### Custom Business Rules

```yaml
# Custom business logic for transaction validation
business_rules:
  # Daily limits per customer
  daily_limits:
    standard_customer: 5000
    premium_customer: 25000
    business_customer: 100000
    
  # Velocity limits
  velocity_limits:
    transactions_per_hour: 10
    transactions_per_minute: 3
    amount_per_hour: 2000
    
  # Geographic restrictions
  geographic_rules:
    restricted_countries: ["XX", "YY"]  # ISO country codes
    high_risk_regions: ["Region1"]
    additional_verification_required: true
    
  # Time-based restrictions  
  time_restrictions:
    large_transfer_hours: [8, 18]      # Large transfers only 8am-6pm
    weekend_transfer_limit: 1000       # Lower limits on weekends
    
# Custom validation logic
validation_rules:
  - name: "suspicious_round_numbers"
    condition: "amount % 100 == 0 and amount > 1000"  # Round hundreds over $1000
    action: "flag_for_review"
    risk_score_increase: 0.2
    
  - name: "rapid_geographic_change"
    condition: "distance_from_last_transaction > 100km and time_diff < 1hour"
    action: "require_additional_auth"
    risk_score_increase: 0.5
```

### Integration Testing Features

```yaml
# Features for testing integration with external systems
integration_testing:
  # Chaos engineering
  chaos_engineering:
    enabled: true
    failure_scenarios:
      - type: "api_timeout"
        probability: 0.02             # 2% chance per transaction
        duration_seconds: 30
        
      - type: "database_connection_loss"
        probability: 0.001            # 0.1% chance  
        duration_seconds: 120
        
      - type: "kafka_broker_down"
        probability: 0.005
        duration_seconds: 60
        
  # Load testing
  load_testing:
    gradual_ramp_up: true
    ramp_duration_minutes: 10
    sustained_load_minutes: 30
    ramp_down_minutes: 5
    
  # A/B testing support
  ab_testing:
    enabled: true
    variants:
      - name: "control"
        weight: 0.5
        fraud_detection_threshold: 0.7
        
      - name: "experimental"  
        weight: 0.5
        fraud_detection_threshold: 0.6  # Lower threshold
```

---

## Example Scenarios

### Example 1: E-Commerce Peak Season

```yaml
name: "E-Commerce Holiday Rush"
description: "Black Friday through Cyber Monday shopping simulation with coordinated fraud attacks"
duration_hours: 120  # 5 days
speed_multiplier: 150
customers: 2000
accounts_per_customer: 2
initial_balance: 3000.00
currency: "USD"

transaction_rate:
  peak_tps: 35
  off_peak_tps: 8
  business_hours: [6, 23]  # Extended shopping hours
  
  # Special event spikes
  special_events:
    - name: "Black Friday"
      start_hour: 72    # Day 3 (Friday)
      duration_hours: 12
      multiplier: 4.0   # 400% increase
      
    - name: "Cyber Monday"
      start_hour: 120   # Day 5 (Monday)  
      duration_hours: 8
      multiplier: 3.5

fraud:
  rate: 0.008  # Higher fraud rate during shopping season
  patterns:
    - type: card_testing
      weight: 0.4
      intensity: 2.0
      # Attackers know people are shopping, less likely to notice small charges
      
    - type: account_takeover
      weight: 0.3  
      intensity: 1.8
      # Target accounts with high balances for shopping
      
    - type: velocity_attack
      weight: 0.3
      intensity: 1.5
      # Blend in with legitimate shopping sprees

connections:
  nexum_url: "http://localhost:8090"
  bastion_url: "http://localhost:8080"
  timeout_seconds: 45  # Higher timeout for peak load

dashboard:
  enabled: true
  port: 8095

metrics:
  enabled: true
  collect_interval_seconds: 2  # More frequent collection during peaks
  retention_minutes: 180       # Keep 3 hours of data
  export_csv: true
```

### Example 2: Money Laundering Investigation

```yaml
name: "Money Laundering Network Investigation"
description: "Sophisticated money laundering operation for AML testing"
duration_hours: 168  # 1 week
speed_multiplier: 50  # Slower to observe patterns
customers: 500
accounts_per_customer: 3  # More accounts for complex laundering
initial_balance: 15000.00

transaction_rate:
  peak_tps: 8   # Lower volume to focus on pattern quality
  off_peak_tps: 3
  business_hours: [8, 18]

fraud:
  rate: 0.05  # 5% - high proportion of suspicious activity
  patterns:
    - type: money_laundering
      weight: 0.6
      intensity: 1.5
      
      layering:
        chain_length: [7, 12]
        amount_degradation: 0.02
        mule_account_count: 25
        
      structuring:
        target_amount: 50000
        transaction_limit: 9800  # Just under $10k limit
        time_spread_hours: 72    # 3 days
        
    - type: smurfing
      weight: 0.4
      intensity: 1.2
      smurf_count: 20
      coordination_window: 120  # 2 hours
      amount_range: [800, 2500]

# Custom AML detection rules
business_rules:
  aml_rules:
    structuring_detection:
      amount_threshold: 9000
      time_window_hours: 24
      transaction_count_threshold: 3
      
    layering_detection:
      max_hops: 5
      time_window_minutes: 180
      amount_threshold: 1000

connections:
  nexum_url: "http://localhost:8090"
  bastion_url: "http://localhost:8080"
  
dashboard:
  enabled: true
  port: 8095

metrics:
  enabled: true
  collect_interval_seconds: 1
  retention_minutes: 240  # Keep 4 hours for pattern analysis
  export_csv: true
```

### Example 3: API Load Testing

```yaml
name: "API Performance Load Test"
description: "Sustained high-volume load test for API performance validation"
duration_hours: 4
speed_multiplier: 1  # Real-time for accurate load testing
customers: 10000
accounts_per_customer: 2
initial_balance: 2000.00

transaction_rate:
  # Graduated load test
  phases:
    - name: "baseline"
      start_hour: 0
      duration_hours: 0.5
      tps: 10
      
    - name: "ramp_up"
      start_hour: 0.5
      duration_hours: 1
      tps_start: 10
      tps_end: 100
      
    - name: "sustained_load"
      start_hour: 1.5
      duration_hours: 2
      tps: 100  # Target load
      
    - name: "ramp_down"
      start_hour: 3.5
      duration_hours: 0.5
      tps_start: 100
      tps_end: 10

fraud:
  rate: 0.001  # Minimal fraud to focus on performance
  patterns:
    - type: card_testing
      weight: 1.0
      intensity: 0.5  # Low intensity

# Chaos engineering for resilience testing
chaos_engineering:
  enabled: true
  failure_scenarios:
    - type: "network_latency"
      start_hour: 2
      duration_minutes: 5
      latency_ms: 200
      
    - type: "api_error_injection"
      start_hour: 2.5
      duration_minutes: 2
      error_rate: 0.1  # 10% error rate

connections:
  nexum_url: "http://localhost:8090"
  bastion_url: "http://localhost:8080"
  timeout_seconds: 10  # Aggressive timeout for load testing
  max_retries: 1       # Minimal retries

dashboard:
  enabled: true
  port: 8095

metrics:
  enabled: true
  collect_interval_seconds: 1
  retention_minutes: 60
  export_csv: true
  
  # Additional performance metrics
  performance_metrics:
    percentiles: [50, 75, 90, 95, 99]
    error_tracking: true
    throughput_tracking: true
```

---

## Testing & Validation

### Scenario Validation Process

#### 1. YAML Syntax Validation
```bash
# Check YAML syntax
python -c "import yaml; yaml.safe_load(open('scenarios/my_scenario.yaml'))"

# Use built-in validator
python run.py --validate-scenario scenarios/my_scenario.yaml
```

#### 2. Logic Validation
```bash
# Test with minimal parameters first
python run.py --scenario scenarios/my_scenario.yaml --customers 5 --speed 1000 --dry-run --verbose
```

#### 3. Integration Testing
```bash
# Test with external systems
python run.py --scenario scenarios/my_scenario.yaml --customers 10 --dashboard
```

### Common Validation Errors

#### YAML Syntax Errors
```
Error: YAML syntax error at line 15: expected <block end>, but found '<scalar>'
```
**Solution**: Check indentation, missing colons, incorrect list formatting

#### Configuration Logic Errors
```
Error: transaction_rate.peak_tps must be greater than off_peak_tps
```
**Solution**: Ensure peak_tps > off_peak_tps

#### Resource Constraint Errors
```
Error: Requested 50000 customers exceeds memory limits
```
**Solution**: Reduce customer count or increase available memory

### Testing Checklist

#### Pre-Deployment Testing
- [ ] YAML syntax validates correctly
- [ ] Scenario loads without configuration errors
- [ ] Dry run completes successfully  
- [ ] Dashboard loads and updates properly
- [ ] All fraud patterns trigger as expected
- [ ] Metrics collection works correctly
- [ ] CSV export functions (if enabled)

#### Performance Testing
- [ ] Achieves target TPS without errors
- [ ] API latency remains within acceptable bounds
- [ ] Memory usage stays within limits
- [ ] No connection pool exhaustion
- [ ] Error rates remain below 1%

#### Functional Testing
- [ ] Transaction patterns match expectations
- [ ] Fraud detection triggers appropriately  
- [ ] Time acceleration works correctly
- [ ] All business rules enforced properly
- [ ] Dashboard displays accurate information

---

## Best Practices

### Scenario Design Guidelines

#### 1. Start Simple, Iterate
```yaml
# Start with basic parameters
name: "Basic Test v1"
duration_hours: 1
customers: 10
transaction_rate:
  peak_tps: 2
  off_peak_tps: 1

# Then gradually add complexity
# v2: Add fraud patterns
# v3: Add advanced timing
# v4: Add business rules
```

#### 2. Use Descriptive Names and Documentation
```yaml
name: "Load Test - 100 TPS Sustained for API Performance Validation"
description: |
  Tests Nexum API performance under sustained 100 TPS load.
  Expected outcomes:
  - API latency < 100ms P95
  - Error rate < 1%
  - No memory leaks
  - Stable performance for 2 hours
  
  Prerequisites:
  - Nexum running on dedicated test server
  - Database connection pool configured for high load
  - Monitoring enabled
```

#### 3. Realistic Parameter Selection

**Transaction Rates:**
- Don't exceed realistic API capacity (test gradually)
- Consider downstream system limits
- Account for network latency

**Customer Counts:**
- More customers = more memory usage
- Balance realism with resource constraints
- Use customer count appropriate for scenario duration

**Fraud Rates:**
- Real-world fraud rates: 0.1-0.5% typically
- Higher rates (1-5%) for focused fraud testing
- Very high rates (10%+) only for attack simulations

### Performance Optimization

#### Memory Management
```yaml
# For large simulations, optimize memory usage
customers: 5000
accounts_per_customer: 2  # Don't exceed 3 unless necessary

metrics:
  retention_minutes: 30   # Reduce retention for large simulations
  collect_interval_seconds: 5  # Less frequent collection
  export_csv: false      # Disable if not needed

# Consider running multiple smaller scenarios instead of one large one
```

#### API Optimization
```yaml
connections:
  timeout_seconds: 30    # Reasonable timeout
  max_retries: 3        # Allow for transient failures
  
# For high-load scenarios:
  timeout_seconds: 10    # Faster failure detection
  max_retries: 1        # Fewer retries
```

### Documentation Standards

#### Scenario Comments
```yaml
# Always include scenario metadata
name: "Scenario Name"
description: |
  Multi-line description explaining:
  - What this scenario simulates
  - Expected outcomes
  - Prerequisites
  - Success criteria
  
# Comment complex configurations
transaction_rate:
  peak_tps: 50        # Chosen based on API capacity testing
  off_peak_tps: 10    # Maintains realistic 5:1 peak ratio
  business_hours: [8, 20]  # Extended hours for retail bank simulation
```

#### Version Control
```bash
# Use descriptive commit messages
git add scenarios/my_scenario.yaml
git commit -m "scenarios: add e-commerce load test scenario

- 100 TPS sustained load over 4 hours
- Realistic shopping patterns with evening peaks  
- Coordinated fraud attacks during peak hours
- Validates API performance under holiday load"
```

### Error Handling

#### Graceful Degradation
```yaml
# Configure fallback behavior
fallback_options:
  on_api_failure:
    action: "continue_with_mock"  # Don't stop entire simulation
    log_failures: true
    
  on_high_error_rate:
    threshold: 0.05              # 5% error rate
    action: "reduce_load"        # Automatically reduce TPS
    reduction_factor: 0.5        # Cut load in half
    
  on_memory_pressure:
    threshold_mb: 1500           # 1.5GB memory usage
    action: "reduce_retention"   # Reduce metrics retention
    min_retention_minutes: 5     # Don't go below 5 minutes
```

### Testing Strategy

#### Progressive Testing Approach
1. **Syntax Validation**: YAML parsing and configuration validation
2. **Dry Run Testing**: Mock mode with minimal resources
3. **Integration Testing**: Real APIs with small dataset
4. **Load Testing**: Gradually increase to target parameters
5. **Stress Testing**: Push beyond normal parameters
6. **Failure Testing**: Test error conditions and recovery

#### Scenario Testing Matrix
```bash
# Test matrix for comprehensive validation
for customers in 10 100 1000; do
  for speed in 100 500 1000; do
    echo "Testing: customers=$customers, speed=$speed"
    python run.py --scenario my_scenario.yaml \
      --customers $customers --speed $speed \
      --dry-run --timeout 60
  done
done
```

This comprehensive guide should enable you to create sophisticated, realistic banking simulation scenarios tailored to your specific testing requirements.