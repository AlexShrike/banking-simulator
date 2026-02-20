"""Main simulation engine for the banking simulator.

Orchestrates the entire simulation including customer generation, transaction
processing, fraud detection, metrics collection, and real-time dashboard updates.
Supports time acceleration and various scenario execution modes.
"""

import asyncio
import logging
import random
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass
from collections import defaultdict

from .config import SimulationConfig, RuntimeStats
from .scenarios import ScenarioLoader
from .generators.customers import CustomerGenerator, CustomerProfile
from .generators.transactions import TransactionGenerator, PendingTransaction
from .generators.fraud import FraudGenerator, FraudProfile, FraudType
from .generators.events import LifeEventGenerator, LifeEvent
from .connectors.nexum import NexumConnector, MockNexumConnector
from .connectors.bastion import BastionConnector, MockBastionConnector
from .connectors.kafka import KafkaConnector, MockKafkaConnector
from .metrics import MetricsCollector


logger = logging.getLogger(__name__)


@dataclass
class SimulationState:
    """Current state of the simulation"""
    is_running: bool = False
    is_paused: bool = False
    start_time: Optional[datetime] = None
    current_sim_time: Optional[datetime] = None
    customers: List[CustomerProfile] = None
    customer_accounts: Dict[str, List[str]] = None
    active_fraud_profiles: List[FraudProfile] = None
    active_life_events: List[LifeEvent] = None
    pending_transactions: List[PendingTransaction] = None
    
    def __post_init__(self):
        if self.customers is None:
            self.customers = []
        if self.customer_accounts is None:
            self.customer_accounts = {}
        if self.active_fraud_profiles is None:
            self.active_fraud_profiles = []
        if self.active_life_events is None:
            self.active_life_events = []
        if self.pending_transactions is None:
            self.pending_transactions = []


class SimulationClock:
    """Manages simulation time with acceleration support"""
    
    def __init__(self, speed_multiplier: float = 1.0):
        self.speed_multiplier = speed_multiplier
        self.real_start_time = datetime.now()
        self.sim_start_time = datetime.now()
        self.paused = False
        self.pause_duration = timedelta(0)
        self.pause_start = None
        
    def get_current_sim_time(self) -> datetime:
        """Get current simulation time with acceleration"""
        if self.paused:
            return self.sim_start_time
            
        real_elapsed = datetime.now() - self.real_start_time - self.pause_duration
        sim_elapsed = real_elapsed * self.speed_multiplier
        return self.sim_start_time + sim_elapsed
        
    def pause(self):
        """Pause the simulation clock"""
        if not self.paused:
            self.pause_start = datetime.now()
            self.paused = True
            
    def resume(self):
        """Resume the simulation clock"""
        if self.paused and self.pause_start:
            self.pause_duration += datetime.now() - self.pause_start
            self.paused = False
            self.pause_start = None
            
    def set_speed(self, multiplier: float):
        """Change simulation speed"""
        # Adjust start times to maintain continuity
        current_sim = self.get_current_sim_time()
        self.real_start_time = datetime.now() - self.pause_duration
        self.sim_start_time = current_sim
        self.speed_multiplier = multiplier
        
    def sleep_for_sim_time(self, sim_duration: timedelta) -> float:
        """Calculate real sleep time for a simulation duration"""
        return sim_duration.total_seconds() / self.speed_multiplier


class SimulationEngine:
    """Main banking simulation engine"""
    
    def __init__(self, config: SimulationConfig):
        self.config = config
        self.state = SimulationState()
        
        # Initialize components
        self.customer_generator = CustomerGenerator(config.seed)
        self.transaction_generator = TransactionGenerator(config.seed)
        self.fraud_generator = FraudGenerator(config.seed)
        self.life_event_generator = LifeEventGenerator(config.seed)
        self.metrics_collector = MetricsCollector(config.metrics)
        
        # Initialize simulation clock
        self.clock = SimulationClock(config.speed_multiplier)
        
        # Initialize connectors
        if config.dry_run:
            self.nexum_connector = MockNexumConnector(config.connections)
            self.bastion_connector = MockBastionConnector(config.connections)
            self.kafka_connector = MockKafkaConnector(config.connections) if config.connections.kafka_bootstrap_servers else None
        else:
            self.nexum_connector = NexumConnector(config.connections)
            self.bastion_connector = BastionConnector(config.connections)
            if config.connections.kafka_bootstrap_servers:
                self.kafka_connector = KafkaConnector(config.connections)
            else:
                self.kafka_connector = None
                
        # Runtime statistics
        self.runtime_stats = RuntimeStats(start_time=datetime.now())
        
        # Control flags
        self._stop_requested = False
        self._pause_requested = False
        
        # Background tasks
        self.background_tasks: Set[asyncio.Task] = set()
        
    async def __aenter__(self):
        """Async context manager entry"""
        # Initialize all connectors
        await self.nexum_connector.__aenter__()
        await self.bastion_connector.__aenter__()
        if self.kafka_connector:
            await self.kafka_connector.__aenter__()
            
        # Start metrics collector
        await self.metrics_collector.start()
        
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        # Cancel background tasks
        for task in self.background_tasks:
            task.cancel()
            
        await self._wait_for_tasks()
        
        # Stop components
        await self.metrics_collector.stop()
        
        if self.kafka_connector:
            await self.kafka_connector.__aexit__(exc_type, exc_val, exc_tb)
        await self.bastion_connector.__aexit__(exc_type, exc_val, exc_tb)
        await self.nexum_connector.__aexit__(exc_type, exc_val, exc_tb)
        
    async def _wait_for_tasks(self):
        """Wait for all background tasks to complete"""
        if self.background_tasks:
            await asyncio.gather(*self.background_tasks, return_exceptions=True)
            
    async def run_scenario(self, scenario_name: Optional[str] = None) -> RuntimeStats:
        """Run a complete simulation scenario"""
        try:
            # Load scenario if specified
            if scenario_name:
                loader = ScenarioLoader()
                self.config = loader.load_scenario(scenario_name)
                
            logger.info(f"Starting simulation: {self.config.name}")
            logger.info(f"Duration: {self.config.duration_hours} hours (accelerated {self.config.speed_multiplier}x)")
            logger.info(f"Customers: {self.config.customers}, Fraud rate: {self.config.fraud.rate:.1%}")
            
            # Setup phase
            await self.setup()
            
            # Main execution phase
            await self.execute()
            
            # Generate final report
            await self.generate_report()
            
            return self.runtime_stats
            
        except KeyboardInterrupt:
            logger.info("Simulation interrupted by user")
            self._stop_requested = True
            return self.runtime_stats
        except Exception as e:
            logger.error(f"Simulation error: {e}")
            self.runtime_stats.errors += 1
            raise
        finally:
            self.state.is_running = False
            self.runtime_stats.end_time = datetime.now()
            
    async def setup(self):
        """Setup phase: create customers, accounts, and initial balances"""
        logger.info("Setting up simulation...")
        setup_start = time.time()
        
        # Health check external systems
        await self._health_check_systems()
        
        # Generate customers
        logger.info(f"Creating {self.config.customers} customers...")
        self.state.customers = self.customer_generator.generate_customers(self.config.customers)
        
        # Create customers in Nexum
        customer_tasks = []
        for customer in self.state.customers:
            task = self._create_customer(customer)
            customer_tasks.append(task)
            
        await asyncio.gather(*customer_tasks, return_exceptions=True)
        
        # Create accounts for each customer
        logger.info("Creating accounts...")
        account_tasks = []
        for customer in self.state.customers:
            for i in range(self.config.accounts_per_customer):
                task = self._create_account(customer, i)
                account_tasks.append(task)
                
        await asyncio.gather(*account_tasks, return_exceptions=True)
        
        # Seed initial balances
        logger.info("Seeding initial balances...")
        balance_tasks = []
        for customer_id, account_ids in self.state.customer_accounts.items():
            for account_id in account_ids:
                task = self._seed_initial_balance(account_id)
                balance_tasks.append(task)
                
        await asyncio.gather(*balance_tasks, return_exceptions=True)
        
        # Generate life events for the simulation period
        logger.info("Generating life events...")
        all_life_events = []
        for customer in self.state.customers:
            events = self.life_event_generator.generate_life_events(
                customer, self.clock.sim_start_time, 
                int(self.config.duration_hours * 24)
            )
            all_life_events.extend(events)
            
        self.state.active_life_events = all_life_events
        
        # Pre-generate fraud profiles based on scenario
        logger.info("Initializing fraud patterns...")
        await self._setup_fraud_patterns()
        
        setup_duration = time.time() - setup_start
        logger.info(f"Setup completed in {setup_duration:.2f} seconds")
        
        # Update runtime stats
        self.runtime_stats.customers_created = len(self.state.customers)
        self.runtime_stats.accounts_created = sum(len(accounts) for accounts in self.state.customer_accounts.values())
        
        # Update metrics
        self.metrics_collector.record_gauge("customers_created", self.runtime_stats.customers_created)
        self.metrics_collector.record_gauge("accounts_created", self.runtime_stats.accounts_created)
        
    async def execute(self):
        """Main execution phase: run simulation with transaction generation"""
        logger.info("Starting transaction simulation...")
        
        self.state.is_running = True
        self.state.start_time = datetime.now()
        self.clock.real_start_time = self.state.start_time
        self.clock.sim_start_time = self.state.start_time
        
        # Start background tasks
        self.background_tasks.add(asyncio.create_task(self._transaction_generation_loop()))
        self.background_tasks.add(asyncio.create_task(self._fraud_detection_loop()))
        self.background_tasks.add(asyncio.create_task(self._metrics_reporting_loop()))
        
        if self.kafka_connector:
            self.background_tasks.add(asyncio.create_task(self._kafka_publishing_loop()))
            
        # Main execution loop
        end_time = self.state.start_time + timedelta(hours=self.config.duration_hours)
        
        while self.state.is_running and not self._stop_requested:
            current_time = datetime.now()
            
            # Check if simulation should end
            sim_time = self.clock.get_current_sim_time()
            if sim_time >= end_time:
                logger.info("Simulation duration completed")
                break
                
            # Handle pause requests
            if self._pause_requested:
                self.state.is_paused = True
                self.clock.pause()
                logger.info("Simulation paused")
                
                while self._pause_requested and not self._stop_requested:
                    await asyncio.sleep(0.1)
                    
                self.clock.resume()
                self.state.is_paused = False
                logger.info("Simulation resumed")
                
            # Update current simulation time
            self.state.current_sim_time = sim_time
            
            # Brief sleep to prevent excessive CPU usage
            await asyncio.sleep(0.1)
            
        # Signal all tasks to stop
        self.state.is_running = False
        
        # Wait for background tasks to complete
        logger.info("Waiting for background tasks to complete...")
        await self._wait_for_tasks()
        
        logger.info("Transaction simulation completed")
        
    async def _transaction_generation_loop(self):
        """Background loop for generating transactions"""
        try:
            while self.state.is_running:
                if self.state.is_paused:
                    await asyncio.sleep(0.1)
                    continue
                    
                current_sim_time = self.clock.get_current_sim_time()
                
                # Generate transactions for each customer
                batch_transactions = []
                
                for customer in self.state.customers:
                    # Apply life event effects
                    active_events = [
                        event for event in self.state.active_life_events
                        if event.customer_id == customer.customer_id and event.is_active(current_sim_time)
                    ]
                    
                    if active_events:
                        modified_customer = self.life_event_generator.apply_event_effects(customer, active_events)
                    else:
                        modified_customer = customer
                        
                    # Determine if customer should generate transactions now
                    if self._should_generate_transactions(modified_customer, current_sim_time):
                        account_ids = self.state.customer_accounts.get(customer.customer_id, [])
                        if account_ids:
                            # Generate 1-3 transactions for this customer
                            num_transactions = random.randint(1, 3)
                            for _ in range(num_transactions):
                                transaction = self._generate_single_transaction(
                                    modified_customer, account_ids, current_sim_time
                                )
                                if transaction:
                                    batch_transactions.append(transaction)
                                    
                # Process batch of transactions
                if batch_transactions:
                    await self._process_transaction_batch(batch_transactions)
                    
                # Sleep based on simulation speed
                sleep_time = self.clock.sleep_for_sim_time(timedelta(seconds=10))  # 10 sim seconds
                await asyncio.sleep(max(0.01, sleep_time))  # At least 10ms real time
                
        except asyncio.CancelledError:
            logger.info("Transaction generation loop cancelled")
        except Exception as e:
            logger.error(f"Transaction generation loop error: {e}")
            
    async def _fraud_detection_loop(self):
        """Background loop for processing fraud patterns"""
        try:
            while self.state.is_running:
                if self.state.is_paused:
                    await asyncio.sleep(0.1)
                    continue
                    
                current_sim_time = self.clock.get_current_sim_time()
                
                # Process active fraud profiles
                active_profiles = self.fraud_generator.get_active_fraud_profiles(current_sim_time)
                
                for profile in active_profiles:
                    # Generate fraud transactions for this profile
                    fraud_transactions = self.fraud_generator.generate_fraud_transactions(profile, current_sim_time)
                    
                    if fraud_transactions:
                        await self._process_fraud_transactions(fraud_transactions)
                        
                # Check for new fraud patterns to activate
                await self._activate_scheduled_fraud()
                
                # Sleep
                sleep_time = self.clock.sleep_for_sim_time(timedelta(seconds=30))  # 30 sim seconds
                await asyncio.sleep(max(0.1, sleep_time))
                
        except asyncio.CancelledError:
            logger.info("Fraud detection loop cancelled")
        except Exception as e:
            logger.error(f"Fraud detection loop error: {e}")
            
    async def _metrics_reporting_loop(self):
        """Background loop for metrics reporting"""
        try:
            while self.state.is_running:
                if self.state.is_paused:
                    await asyncio.sleep(1)
                    continue
                    
                # Update simulation metrics
                self.metrics_collector.record_gauge("simulation_time_multiplier", self.config.speed_multiplier)
                
                # Calculate current rates
                if self.runtime_stats.duration_seconds > 0:
                    tps = self.runtime_stats.transactions_processed / self.runtime_stats.duration_seconds
                    self.metrics_collector.record_gauge("current_tps", tps)
                    
                # Update API statistics from connectors
                nexum_stats = self.nexum_connector.get_stats()
                bastion_stats = self.bastion_connector.get_connector_stats()
                
                if nexum_stats["total_requests"] > 0:
                    self.metrics_collector.record_gauge("nexum_success_rate", nexum_stats["success_rate"])
                    self.metrics_collector.record_gauge("nexum_avg_latency", nexum_stats["average_latency_ms"])
                    
                if bastion_stats["total_requests"] > 0:
                    self.metrics_collector.record_gauge("bastion_success_rate", bastion_stats["success_rate"])
                    self.metrics_collector.record_gauge("bastion_avg_latency", bastion_stats["average_latency_ms"])
                    self.metrics_collector.record_gauge("avg_risk_score", bastion_stats["average_risk_score"])
                    
                await asyncio.sleep(5)  # Report every 5 seconds
                
        except asyncio.CancelledError:
            logger.info("Metrics reporting loop cancelled")
        except Exception as e:
            logger.error(f"Metrics reporting loop error: {e}")
            
    async def _kafka_publishing_loop(self):
        """Background loop for Kafka message publishing"""
        if not self.kafka_connector:
            return
            
        try:
            while self.state.is_running:
                if self.state.is_paused:
                    await asyncio.sleep(1)
                    continue
                    
                # Publish simulation metrics to Kafka
                dashboard_data = self.metrics_collector.get_dashboard_data()
                await self.kafka_connector.publish_metrics(dashboard_data)
                
                await asyncio.sleep(10)  # Publish every 10 seconds
                
        except asyncio.CancelledError:
            logger.info("Kafka publishing loop cancelled")
        except Exception as e:
            logger.error(f"Kafka publishing loop error: {e}")
            
    async def _health_check_systems(self):
        """Check health of external systems"""
        logger.info("Checking system health...")
        
        # Check Nexum
        try:
            health = await self.nexum_connector.health_check()
            if health.get("status") == "healthy":
                logger.info("✅ Nexum is healthy")
            else:
                logger.warning(f"⚠️ Nexum health check: {health}")
        except Exception as e:
            logger.error(f"❌ Nexum health check failed: {e}")
            if not self.config.dry_run:
                raise
                
        # Check Bastion
        try:
            health = await self.bastion_connector.health_check()
            if health.get("status") == "healthy":
                logger.info("✅ Bastion is healthy")
            else:
                logger.warning(f"⚠️ Bastion health check: {health}")
        except Exception as e:
            logger.error(f"❌ Bastion health check failed: {e}")
            if not self.config.dry_run:
                raise
                
        # Check Kafka if enabled
        if self.kafka_connector:
            try:
                health = await self.kafka_connector.health_check()
                if health.get("status") == "healthy":
                    logger.info("✅ Kafka is healthy")
                else:
                    logger.warning(f"⚠️ Kafka health check: {health}")
            except Exception as e:
                logger.warning(f"⚠️ Kafka health check failed: {e}")
                
    async def _create_customer(self, customer: CustomerProfile):
        """Create a customer in Nexum"""
        try:
            address = {
                "line1": customer.address_line1,
                "city": customer.city,
                "state": customer.state,
                "postal_code": customer.postal_code,
                "country": customer.country
            }
            
            result = await self.nexum_connector.create_customer(
                first_name=customer.first_name,
                last_name=customer.last_name,
                email=customer.email,
                phone=customer.phone,
                date_of_birth=customer.date_of_birth.isoformat(),
                address=address
            )
            
            # Update customer ID from Nexum if different
            if "customer_id" in result:
                customer.customer_id = result["customer_id"]
                
        except Exception as e:
            logger.error(f"Failed to create customer {customer.customer_id}: {e}")
            self.runtime_stats.errors += 1
            
    async def _create_account(self, customer: CustomerProfile, account_index: int):
        """Create an account for a customer"""
        try:
            # Determine account type
            account_types = ["savings", "checking"]
            if account_index < 2:
                product_type = account_types[account_index]
            else:
                product_type = random.choice(["savings", "checking", "credit_line"])
                
            account_name = f"{product_type.title()} Account"
            
            result = await self.nexum_connector.create_account(
                customer_id=customer.customer_id,
                product_type=product_type,
                currency=self.config.currency,
                name=account_name
            )
            
            if "account_id" in result:
                account_id = result["account_id"]
                
                # Store account mapping
                if customer.customer_id not in self.state.customer_accounts:
                    self.state.customer_accounts[customer.customer_id] = []
                self.state.customer_accounts[customer.customer_id].append(account_id)
                
        except Exception as e:
            logger.error(f"Failed to create account for {customer.customer_id}: {e}")
            self.runtime_stats.errors += 1
            
    async def _seed_initial_balance(self, account_id: str):
        """Seed initial balance in an account"""
        try:
            amount = self.config.initial_balance + random.uniform(-1000, 1000)  # Some variation
            amount = max(0, amount)  # Don't go negative
            
            await self.nexum_connector.deposit(
                account_id=account_id,
                amount=amount,
                description="Initial balance seed",
                channel="system"
            )
            
        except Exception as e:
            logger.error(f"Failed to seed balance for account {account_id}: {e}")
            self.runtime_stats.errors += 1
            
    async def _setup_fraud_patterns(self):
        """Setup fraud patterns based on configuration"""
        fraud_config = self.config.fraud
        
        for pattern_config in fraud_config.patterns:
            # Create fraud profiles for each pattern type
            fraud_type = FraudType(pattern_config.type)
            
            # Select target customers for this fraud type
            num_targets = max(1, int(len(self.state.customers) * pattern_config.weight))
            target_customers = random.sample(self.state.customers, num_targets)
            
            # Schedule fraud attacks throughout the simulation
            for i, customer in enumerate(target_customers):
                # Random timing within fraud attack window if specified
                if fraud_config.attack_window:
                    start_hour, end_hour = fraud_config.attack_window
                    attack_time = self.clock.sim_start_time + timedelta(
                        hours=random.uniform(start_hour, end_hour)
                    )
                else:
                    # Random time during simulation
                    attack_time = self.clock.sim_start_time + timedelta(
                        hours=random.uniform(1, self.config.duration_hours - 1)
                    )
                    
                fraud_profile = self.fraud_generator.generate_fraud_attack(
                    fraud_type=fraud_type,
                    target_customers=[customer],
                    account_mapping=self.state.customer_accounts,
                    start_time=attack_time,
                    intensity=pattern_config.intensity
                )
                
                self.fraud_generator.add_fraud_profile(fraud_profile)
                
    def _should_generate_transactions(self, customer: CustomerProfile, current_time: datetime) -> bool:
        """Determine if a customer should generate transactions now"""
        # Base probability based on customer transaction frequency
        base_prob_per_hour = customer.transaction_frequency / (7 * 24)  # Weekly to hourly
        
        # Adjust for time of day
        hour = current_time.hour
        time_multiplier = 1.0
        
        # Business hours are busier
        if 8 <= hour <= 18:
            time_multiplier = 1.5
        elif 22 <= hour or hour <= 6:
            time_multiplier = 0.3  # Quiet hours
            
        # Weekend adjustment
        if current_time.weekday() >= 5:
            time_multiplier *= 0.7
            
        adjusted_prob = base_prob_per_hour * time_multiplier
        
        # Convert to probability for this time tick (every ~10 sim seconds)
        tick_prob = adjusted_prob / 360  # 360 ticks per hour
        
        return random.random() < tick_prob
        
    def _generate_single_transaction(self, customer: CustomerProfile, account_ids: List[str], 
                                   current_time: datetime) -> Optional[PendingTransaction]:
        """Generate a single transaction for a customer"""
        try:
            # Use transaction generator to create realistic transaction
            transactions = self.transaction_generator.generate_transactions_for_customer(
                customer, account_ids, current_time, 0.1  # Short duration for single transaction
            )
            
            if transactions:
                return transactions[0]  # Return first transaction
                
        except Exception as e:
            logger.error(f"Error generating transaction for {customer.customer_id}: {e}")
            
        return None
        
    async def _process_transaction_batch(self, transactions: List[PendingTransaction]):
        """Process a batch of legitimate transactions"""
        try:
            for transaction in transactions:
                await self._process_single_transaction(transaction)
                
        except Exception as e:
            logger.error(f"Error processing transaction batch: {e}")
            
    async def _process_fraud_transactions(self, fraud_transactions: List[PendingTransaction]):
        """Process fraud transactions"""
        try:
            for transaction in fraud_transactions:
                # Mark as fraud for metrics
                transaction.metadata["is_fraud"] = True
                await self._process_single_transaction(transaction, is_fraud=True)
                
        except Exception as e:
            logger.error(f"Error processing fraud transactions: {e}")
            
    async def _process_single_transaction(self, transaction: PendingTransaction, is_fraud: bool = False):
        """Process a single transaction through Nexum and Bastion"""
        start_time = time.time()
        
        try:
            # Record transaction metrics
            self.metrics_collector.record_transaction(is_fraud)
            
            # Submit to Nexum
            nexum_start = time.time()
            nexum_result = await self._submit_to_nexum(transaction)
            nexum_latency = (time.time() - nexum_start) * 1000
            
            self.metrics_collector.record_nexum_request(nexum_latency, nexum_result.get("success", True))
            
            # Submit to Bastion for fraud scoring
            bastion_start = time.time()
            fraud_score_result = await self._submit_to_bastion(transaction)
            bastion_latency = (time.time() - bastion_start) * 1000
            
            risk_score = fraud_score_result.get("risk_score", 0.0)
            decision = fraud_score_result.get("action", "APPROVE").upper()
            
            self.metrics_collector.record_bastion_request(bastion_latency, risk_score, True)
            
            # Record fraud detection accuracy
            predicted_fraud = decision in ["REVIEW", "DECLINE"]
            actual_fraud = transaction.metadata.get("is_fraud", False)
            self.metrics_collector.record_fraud_decision(predicted_fraud, actual_fraud)
            
            # Publish to Kafka if enabled
            if self.kafka_connector:
                await self.kafka_connector.publish_transaction(transaction.__dict__)
                await self.kafka_connector.publish_fraud_decision(fraud_score_result)
                
            # Update runtime stats
            self.runtime_stats.transactions_processed += 1
            if is_fraud:
                self.runtime_stats.fraud_transactions += 1
                
        except Exception as e:
            logger.error(f"Error processing transaction {transaction.transaction_id}: {e}")
            self.runtime_stats.errors += 1
            
    async def _submit_to_nexum(self, transaction: PendingTransaction) -> Dict[str, Any]:
        """Submit transaction to Nexum core banking"""
        try:
            if transaction.transaction_type.value == "deposit":
                result = await self.nexum_connector.deposit(
                    account_id=transaction.to_account_id,
                    amount=transaction.amount,
                    description=transaction.description,
                    channel=transaction.channel.value,
                    reference=transaction.reference
                )
            elif transaction.transaction_type.value == "withdrawal":
                result = await self.nexum_connector.withdraw(
                    account_id=transaction.from_account_id,
                    amount=transaction.amount,
                    description=transaction.description,
                    channel=transaction.channel.value,
                    reference=transaction.reference
                )
            elif transaction.transaction_type.value == "transfer":
                result = await self.nexum_connector.transfer(
                    from_account_id=transaction.from_account_id,
                    to_account_id=transaction.to_account_id,
                    amount=transaction.amount,
                    description=transaction.description,
                    channel=transaction.channel.value,
                    reference=transaction.reference
                )
            else:
                # For other transaction types, default to withdrawal
                result = await self.nexum_connector.withdraw(
                    account_id=transaction.from_account_id or transaction.to_account_id,
                    amount=transaction.amount,
                    description=transaction.description,
                    channel=transaction.channel.value,
                    reference=transaction.reference
                )
                
            result["success"] = True
            return result
            
        except Exception as e:
            logger.error(f"Nexum submission error: {e}")
            return {"success": False, "error": str(e)}
            
    async def _submit_to_bastion(self, transaction: PendingTransaction) -> Dict[str, Any]:
        """Submit transaction to Bastion for fraud scoring"""
        try:
            result = await self.bastion_connector.score_transaction(
                transaction_id=getattr(transaction, 'transaction_id', f"TXN_{int(time.time())}"),
                cif_id=transaction.from_account_id or transaction.to_account_id or "unknown",
                amount=transaction.amount,
                currency=transaction.currency,
                merchant_id=transaction.merchant_id or "",
                merchant_category=transaction.merchant_category or "",
                channel=transaction.channel.value,
                country=transaction.metadata.get("customer_location", "US").split(",")[-1].strip(),
                timestamp=transaction.timestamp.timestamp(),
                metadata=transaction.metadata
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Bastion scoring error: {e}")
            return {"risk_score": 0.0, "action": "APPROVE", "error": str(e)}
            
    async def _activate_scheduled_fraud(self):
        """Activate scheduled fraud patterns"""
        # This would activate fraud patterns based on timing
        # For now, fraud patterns are pre-generated in setup
        pass
        
    async def generate_report(self):
        """Generate final simulation report"""
        logger.info("Generating simulation report...")
        
        # Update final runtime stats
        self.runtime_stats.end_time = datetime.now()
        
        # Get final metrics
        final_metrics = self.metrics_collector.get_current_metrics()
        nexum_stats = self.nexum_connector.get_stats()
        bastion_stats = self.bastion_connector.get_connector_stats()
        
        # Log summary
        logger.info("=== SIMULATION COMPLETED ===")
        logger.info(f"Duration: {self.runtime_stats.duration_seconds:.1f} seconds")
        logger.info(f"Customers: {self.runtime_stats.customers_created}")
        logger.info(f"Accounts: {self.runtime_stats.accounts_created}")
        logger.info(f"Transactions: {self.runtime_stats.transactions_processed}")
        logger.info(f"Fraud transactions: {self.runtime_stats.fraud_transactions}")
        logger.info(f"Average TPS: {self.runtime_stats.actual_tps:.2f}")
        logger.info(f"Nexum API calls: {nexum_stats['total_requests']}")
        logger.info(f"Bastion API calls: {bastion_stats['total_requests']}")
        logger.info(f"Errors: {self.runtime_stats.errors}")
        
        if bastion_stats["total_requests"] > 0:
            logger.info(f"Average risk score: {bastion_stats['average_risk_score']:.3f}")
            logger.info(f"Fraud decisions: {bastion_stats['decisions']}")
            
    # Control methods
    def pause(self):
        """Pause the simulation"""
        self._pause_requested = True
        
    def resume(self):
        """Resume the simulation"""
        self._pause_requested = False
        
    def stop(self):
        """Stop the simulation"""
        self._stop_requested = True
        
    def set_speed(self, multiplier: float):
        """Change simulation speed"""
        self.config.speed_multiplier = multiplier
        self.clock.set_speed(multiplier)
        
    def get_status(self) -> Dict[str, Any]:
        """Get current simulation status"""
        return {
            "is_running": self.state.is_running,
            "is_paused": self.state.is_paused,
            "current_time": self.state.current_sim_time.isoformat() if self.state.current_sim_time else None,
            "elapsed_seconds": (datetime.now() - self.state.start_time).total_seconds() if self.state.start_time else 0,
            "speed_multiplier": self.config.speed_multiplier,
            "customers": len(self.state.customers),
            "accounts": sum(len(accounts) for accounts in self.state.customer_accounts.values()),
            "transactions_processed": self.runtime_stats.transactions_processed,
            "fraud_transactions": self.runtime_stats.fraud_transactions,
            "errors": self.runtime_stats.errors
        }