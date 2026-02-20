#!/usr/bin/env python3
"""
Banking Simulator CLI

Command-line interface for running banking simulation scenarios.
Supports standalone mode, full integration with Nexum/Bastion, and dashboard.
"""

import argparse
import asyncio
import logging
import sys
import signal
from pathlib import Path
from typing import Optional

# Add simulator to path
sys.path.insert(0, str(Path(__file__).parent))

from simulator.config import SimulationConfig, ConnectionConfig, DashboardConfig, MetricsConfig
from simulator.scenarios import ScenarioLoader, get_builtin_scenario
from simulator.engine import SimulationEngine
from simulator.dashboard.app import create_dashboard_app
from simulator.dashboard.ws import websocket_manager

import uvicorn


# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('banking_simulator.log')
    ]
)

logger = logging.getLogger(__name__)


class SimulationRunner:
    """Main simulation runner that coordinates engine and dashboard"""
    
    def __init__(self, config: SimulationConfig):
        self.config = config
        self.simulation_engine = None
        self.dashboard_server = None
        self.dashboard_task = None
        self.simulation_task = None
        self._shutdown_event = asyncio.Event()
        
    async def run(self):
        """Run the complete simulation with optional dashboard"""
        try:
            # Create simulation engine
            logger.info("Initializing simulation engine...")
            async with SimulationEngine(self.config) as engine:
                self.simulation_engine = engine
                
                # Start dashboard if enabled
                if self.config.dashboard.enabled:
                    await self._start_dashboard()
                    
                # Run simulation
                logger.info("Starting simulation...")
                
                # Setup signal handlers for graceful shutdown
                self._setup_signal_handlers()
                
                # Start simulation in background
                self.simulation_task = asyncio.create_task(
                    engine.run_scenario(None)  # Config already loaded
                )
                
                # Wait for simulation to complete or shutdown signal
                await asyncio.gather(
                    self.simulation_task,
                    self._shutdown_event.wait(),
                    return_exceptions=True
                )
                
                logger.info("Simulation completed")
                
        except KeyboardInterrupt:
            logger.info("Interrupted by user")
        except Exception as e:
            logger.error(f"Simulation failed: {e}")
            raise
        finally:
            await self._cleanup()
            
    async def _start_dashboard(self):
        """Start the dashboard server"""
        try:
            logger.info(f"Starting dashboard on http://{self.config.dashboard.host}:{self.config.dashboard.port}")
            
            self.dashboard_server = create_dashboard_app(
                self.config.dashboard,
                self.simulation_engine,
                self.simulation_engine.metrics_collector if self.simulation_engine else None
            )
            
            # Start WebSocket manager
            await self.dashboard_server.start_websocket_manager()
            
            # Start dashboard server
            config = uvicorn.Config(
                app=self.dashboard_server.app,
                host=self.config.dashboard.host,
                port=self.config.dashboard.port,
                log_level="warning",  # Reduce uvicorn logging
                access_log=False
            )
            
            server = uvicorn.Server(config)
            self.dashboard_task = asyncio.create_task(server.serve())
            
            logger.info("Dashboard started successfully")
            
        except Exception as e:
            logger.error(f"Failed to start dashboard: {e}")
            
    def _setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, shutting down...")
            self._shutdown_event.set()
            
            # Stop simulation
            if self.simulation_engine:
                self.simulation_engine.stop()
                
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
    async def _cleanup(self):
        """Cleanup resources"""
        # Stop dashboard
        if self.dashboard_task:
            self.dashboard_task.cancel()
            try:
                await self.dashboard_task
            except asyncio.CancelledError:
                pass
                
        if self.dashboard_server:
            await self.dashboard_server.stop_websocket_manager()
            
        logger.info("Cleanup completed")


async def run_simulation(args):
    """Main simulation runner"""
    try:
        # Load or create configuration
        if args.scenario.endswith('.yaml') or args.scenario.endswith('.yml'):
            # Load from file
            loader = ScenarioLoader()
            config = loader.load_scenario(args.scenario)
            logger.info(f"Loaded scenario from {args.scenario}")
        else:
            # Load built-in scenario
            config = get_builtin_scenario(args.scenario)
            logger.info(f"Using built-in scenario: {args.scenario}")
            
        # Override configuration with command-line arguments
        if args.speed is not None:
            config.speed_multiplier = args.speed
            
        if args.customers is not None:
            config.customers = args.customers
            
        if args.nexum_url:
            config.connections.nexum_url = args.nexum_url
            
        if args.bastion_url:
            config.connections.bastion_url = args.bastion_url
            
        if args.dashboard:
            config.dashboard.enabled = True
            
        if args.dashboard_port:
            config.dashboard.port = args.dashboard_port
            
        if args.no_kafka:
            config.connections.kafka_bootstrap_servers = None
            
        if args.dry_run:
            config.dry_run = True
            logger.info("Running in dry-run mode (mock connectors)")
            
        # Print configuration summary
        logger.info("=== Simulation Configuration ===")
        logger.info(f"Scenario: {config.name}")
        logger.info(f"Description: {config.description}")
        logger.info(f"Duration: {config.duration_hours} hours")
        logger.info(f"Speed: {config.speed_multiplier}x")
        logger.info(f"Customers: {config.customers}")
        logger.info(f"Fraud rate: {config.fraud.rate:.1%}")
        logger.info(f"Nexum: {config.connections.nexum_url}")
        logger.info(f"Bastion: {config.connections.bastion_url}")
        logger.info(f"Dashboard: {'enabled' if config.dashboard.enabled else 'disabled'}")
        logger.info(f"Dry run: {'yes' if config.dry_run else 'no'}")
        logger.info("=" * 32)
        
        # Run simulation
        runner = SimulationRunner(config)
        await runner.run()
        
    except KeyboardInterrupt:
        logger.info("Simulation interrupted")
    except Exception as e:
        logger.error(f"Simulation failed: {e}")
        sys.exit(1)


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Banking Simulator - Flight simulator for testing Nexum and Bastion",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run normal day scenario with dashboard
  python run.py --scenario normal_day --dashboard
  
  # Run fraud attack scenario at 200x speed
  python run.py --scenario fraud_attack --speed 200
  
  # Run custom scenario from file
  python run.py --scenario my_scenario.yaml --dashboard-port 8080
  
  # Test setup without external dependencies
  python run.py --scenario normal_day --dry-run --dashboard
  
Built-in scenarios:
  - normal_day: Typical business day with 0.1% fraud
  - fraud_attack: Coordinated fraud attack scenario  
  - peak_load: High volume stress test
  - mule_network: Money laundering detection
  - onboarding: New customer onboarding wave
"""
    )
    
    # Scenario selection
    parser.add_argument(
        "--scenario", 
        default="normal_day",
        help="Scenario name or YAML file path (default: normal_day)"
    )
    
    # Simulation parameters
    parser.add_argument(
        "--speed", 
        type=float,
        help="Speed multiplier for time acceleration (default: from scenario)"
    )
    
    parser.add_argument(
        "--customers", 
        type=int,
        help="Number of customers to create (default: from scenario)"
    )
    
    # External system URLs
    parser.add_argument(
        "--nexum-url", 
        default="http://localhost:8090",
        help="Nexum core banking API URL"
    )
    
    parser.add_argument(
        "--bastion-url", 
        default="http://localhost:8080",
        help="Bastion fraud detection API URL"
    )
    
    # Dashboard options
    parser.add_argument(
        "--dashboard", 
        action="store_true",
        help="Launch real-time dashboard"
    )
    
    parser.add_argument(
        "--dashboard-port", 
        type=int, 
        default=8095,
        help="Dashboard server port (default: 8095)"
    )
    
    # Optional features
    parser.add_argument(
        "--no-kafka", 
        action="store_true",
        help="Disable Kafka message publishing"
    )
    
    parser.add_argument(
        "--dry-run", 
        action="store_true",
        help="Use mock connectors instead of real APIs"
    )
    
    # Utility commands
    parser.add_argument(
        "--list-scenarios", 
        action="store_true",
        help="List available scenarios and exit"
    )
    
    parser.add_argument(
        "--validate-scenario",
        help="Validate a scenario file and exit"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        
    # Handle utility commands
    if args.list_scenarios:
        loader = ScenarioLoader()
        print("Built-in scenarios:")
        from simulator.scenarios import BUILTIN_SCENARIOS
        for name, config in BUILTIN_SCENARIOS.items():
            print(f"  {name}: {config.get('description', 'No description')}")
            
        print("\nScenario files:")
        scenarios = loader.list_scenarios()
        if scenarios:
            for scenario in scenarios:
                print(f"  {scenario}.yaml")
        else:
            print("  (no scenario files found)")
        sys.exit(0)
        
    if args.validate_scenario:
        try:
            loader = ScenarioLoader()
            config = loader.load_scenario(args.validate_scenario)
            print(f"✅ Scenario '{args.validate_scenario}' is valid")
            print(f"   Name: {config.name}")
            print(f"   Description: {config.description}")
            print(f"   Duration: {config.duration_hours} hours")
            print(f"   Customers: {config.customers}")
            print(f"   Fraud rate: {config.fraud.rate:.1%}")
        except Exception as e:
            print(f"❌ Scenario validation failed: {e}")
            sys.exit(1)
        sys.exit(0)
        
    # Run simulation
    try:
        asyncio.run(run_simulation(args))
    except KeyboardInterrupt:
        print("\nSimulation interrupted by user")
        sys.exit(1)


if __name__ == "__main__":
    main()