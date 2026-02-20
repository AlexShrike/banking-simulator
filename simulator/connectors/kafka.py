"""Kafka connector for real-time message streaming.

Optional Kafka integration for publishing transaction events and consuming
fraud decisions. Useful for event-driven architectures and real-time monitoring.
"""

import json
import asyncio
import logging
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime

try:
    from aiokafka import AIOKafkaProducer, AIOKafkaConsumer
    from aiokafka.errors import KafkaError, KafkaConnectionError
    HAS_KAFKA = True
except ImportError:
    HAS_KAFKA = False

from ..config import ConnectionConfig


logger = logging.getLogger(__name__)


class KafkaConnectorError(Exception):
    """Base exception for Kafka connector errors"""
    pass


class KafkaConnectionError(KafkaConnectorError):
    """Connection error with Kafka brokers"""
    pass


class KafkaConnector:
    """Kafka connector for real-time message streaming"""
    
    def __init__(self, config: ConnectionConfig):
        if not HAS_KAFKA:
            raise KafkaConnectorError("aiokafka not installed. Run: pip install aiokafka")
            
        self.bootstrap_servers = config.kafka_bootstrap_servers or "localhost:9092"
        self.timeout = config.timeout_seconds
        
        # Topic configuration
        self.topics = {
            "transactions": "nexum.transactions",
            "fraud_decisions": "bastion.fraud.decisions",
            "customer_events": "nexum.customer.events",
            "account_events": "nexum.account.events",
            "simulation_metrics": "simulator.metrics"
        }
        
        # Kafka clients
        self.producer = None
        self.consumers = {}
        self.consumer_tasks = {}
        
        # Statistics
        self.stats = {
            "messages_produced": 0,
            "messages_consumed": 0,
            "producer_errors": 0,
            "consumer_errors": 0,
            "bytes_sent": 0,
            "bytes_received": 0,
            "last_activity": None
        }
        
    async def __aenter__(self):
        """Async context manager entry"""
        await self.initialize()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()
        
    async def initialize(self):
        """Initialize Kafka producer and consumers"""
        try:
            # Initialize producer
            self.producer = AIOKafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                value_serializer=self._serialize_json,
                key_serializer=lambda key: key.encode('utf-8') if key else None,
                compression_type='gzip',
                request_timeout_ms=self.timeout * 1000,
                retry_backoff_ms=1000,
                max_in_flight_requests_per_connection=5
            )
            
            await self.producer.start()
            logger.info(f"Kafka producer initialized: {self.bootstrap_servers}")
            
        except Exception as e:
            logger.error(f"Failed to initialize Kafka producer: {e}")
            raise KafkaConnectionError(f"Cannot initialize Kafka producer: {e}")
            
    async def close(self):
        """Close Kafka connections"""
        # Stop all consumers
        for task in self.consumer_tasks.values():
            task.cancel()
            
        for consumer in self.consumers.values():
            try:
                await consumer.stop()
            except:
                pass
                
        # Stop producer
        if self.producer:
            try:
                await self.producer.stop()
            except:
                pass
                
        logger.info("Kafka connections closed")
        
    def _serialize_json(self, value: Any) -> bytes:
        """JSON serializer for Kafka messages"""
        return json.dumps(value, default=str).encode('utf-8')
        
    def _deserialize_json(self, value: bytes) -> Any:
        """JSON deserializer for Kafka messages"""
        return json.loads(value.decode('utf-8'))
        
    # Producer methods
    async def publish_transaction(self, transaction_data: Dict[str, Any]) -> bool:
        """Publish transaction event to Kafka"""
        try:
            key = transaction_data.get("transaction_id", "")
            message = {
                "event_type": "transaction_created",
                "timestamp": datetime.now().isoformat(),
                "data": transaction_data
            }
            
            await self.producer.send_and_wait(
                topic=self.topics["transactions"],
                key=key,
                value=message
            )
            
            self.stats["messages_produced"] += 1
            self.stats["bytes_sent"] += len(json.dumps(message))
            self.stats["last_activity"] = datetime.now()
            
            logger.debug(f"Published transaction: {key}")
            return True
            
        except Exception as e:
            self.stats["producer_errors"] += 1
            logger.error(f"Failed to publish transaction {key}: {e}")
            return False
            
    async def publish_fraud_decision(self, decision_data: Dict[str, Any]) -> bool:
        """Publish fraud decision to Kafka"""
        try:
            key = decision_data.get("transaction_id", "")
            message = {
                "event_type": "fraud_decision",
                "timestamp": datetime.now().isoformat(),
                "data": decision_data
            }
            
            await self.producer.send_and_wait(
                topic=self.topics["fraud_decisions"],
                key=key,
                value=message
            )
            
            self.stats["messages_produced"] += 1
            self.stats["bytes_sent"] += len(json.dumps(message))
            self.stats["last_activity"] = datetime.now()
            
            return True
            
        except Exception as e:
            self.stats["producer_errors"] += 1
            logger.error(f"Failed to publish fraud decision {key}: {e}")
            return False
            
    async def publish_customer_event(self, customer_id: str, event_type: str, event_data: Dict[str, Any]) -> bool:
        """Publish customer lifecycle event"""
        try:
            message = {
                "event_type": event_type,
                "customer_id": customer_id,
                "timestamp": datetime.now().isoformat(),
                "data": event_data
            }
            
            await self.producer.send_and_wait(
                topic=self.topics["customer_events"],
                key=customer_id,
                value=message
            )
            
            self.stats["messages_produced"] += 1
            self.stats["bytes_sent"] += len(json.dumps(message))
            self.stats["last_activity"] = datetime.now()
            
            return True
            
        except Exception as e:
            self.stats["producer_errors"] += 1
            logger.error(f"Failed to publish customer event {customer_id}: {e}")
            return False
            
    async def publish_account_event(self, account_id: str, event_type: str, event_data: Dict[str, Any]) -> bool:
        """Publish account lifecycle event"""
        try:
            message = {
                "event_type": event_type,
                "account_id": account_id,
                "timestamp": datetime.now().isoformat(),
                "data": event_data
            }
            
            await self.producer.send_and_wait(
                topic=self.topics["account_events"],
                key=account_id,
                value=message
            )
            
            self.stats["messages_produced"] += 1
            self.stats["bytes_sent"] += len(json.dumps(message))
            self.stats["last_activity"] = datetime.now()
            
            return True
            
        except Exception as e:
            self.stats["producer_errors"] += 1
            logger.error(f"Failed to publish account event {account_id}: {e}")
            return False
            
    async def publish_metrics(self, metrics_data: Dict[str, Any]) -> bool:
        """Publish simulation metrics"""
        try:
            message = {
                "event_type": "simulation_metrics",
                "timestamp": datetime.now().isoformat(),
                "data": metrics_data
            }
            
            await self.producer.send_and_wait(
                topic=self.topics["simulation_metrics"],
                value=message
            )
            
            self.stats["messages_produced"] += 1
            self.stats["bytes_sent"] += len(json.dumps(message))
            self.stats["last_activity"] = datetime.now()
            
            return True
            
        except Exception as e:
            self.stats["producer_errors"] += 1
            logger.error(f"Failed to publish metrics: {e}")
            return False
            
    # Consumer methods
    async def start_consumer(self, topic: str, handler: Callable[[Dict[str, Any]], None],
                           consumer_group: str = "banking_simulator") -> bool:
        """Start a consumer for a specific topic"""
        try:
            if topic in self.consumers:
                logger.warning(f"Consumer for topic {topic} already running")
                return False
                
            consumer = AIOKafkaConsumer(
                topic,
                bootstrap_servers=self.bootstrap_servers,
                group_id=consumer_group,
                value_deserializer=self._deserialize_json,
                auto_offset_reset='latest',
                enable_auto_commit=True,
                request_timeout_ms=self.timeout * 1000
            )
            
            await consumer.start()
            self.consumers[topic] = consumer
            
            # Start consumer task
            task = asyncio.create_task(self._consume_messages(consumer, handler))
            self.consumer_tasks[topic] = task
            
            logger.info(f"Started Kafka consumer for topic: {topic}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start consumer for {topic}: {e}")
            return False
            
    async def _consume_messages(self, consumer: 'AIOKafkaConsumer', handler: Callable[[Dict[str, Any]], None]):
        """Internal method to consume messages"""
        try:
            async for message in consumer:
                try:
                    # Update statistics
                    self.stats["messages_consumed"] += 1
                    self.stats["bytes_received"] += len(message.value)
                    self.stats["last_activity"] = datetime.now()
                    
                    # Call handler
                    await asyncio.get_event_loop().run_in_executor(None, handler, message.value)
                    
                except Exception as e:
                    self.stats["consumer_errors"] += 1
                    logger.error(f"Error processing message: {e}")
                    
        except asyncio.CancelledError:
            logger.info("Consumer task cancelled")
        except Exception as e:
            self.stats["consumer_errors"] += 1
            logger.error(f"Consumer error: {e}")
            
    async def stop_consumer(self, topic: str):
        """Stop a consumer for a specific topic"""
        if topic in self.consumer_tasks:
            self.consumer_tasks[topic].cancel()
            del self.consumer_tasks[topic]
            
        if topic in self.consumers:
            await self.consumers[topic].stop()
            del self.consumers[topic]
            
        logger.info(f"Stopped consumer for topic: {topic}")
        
    # Convenience methods for simulation
    async def start_transaction_consumer(self, handler: Callable[[Dict[str, Any]], None]) -> bool:
        """Start consumer for transaction events"""
        return await self.start_consumer(self.topics["transactions"], handler)
        
    async def start_fraud_decision_consumer(self, handler: Callable[[Dict[str, Any]], None]) -> bool:
        """Start consumer for fraud decisions"""
        return await self.start_consumer(self.topics["fraud_decisions"], handler)
        
    # Health and monitoring
    async def health_check(self) -> Dict[str, Any]:
        """Check Kafka connection health"""
        try:
            if self.producer:
                # Try to get metadata as health check
                metadata = await self.producer.client.fetch_metadata()
                brokers = len(metadata.brokers)
                topics = len(metadata.topics)
                
                return {
                    "status": "healthy",
                    "brokers": brokers,
                    "topics": topics,
                    "producer_connected": True,
                    "active_consumers": len(self.consumers),
                    "bootstrap_servers": self.bootstrap_servers
                }
            else:
                return {
                    "status": "not_initialized",
                    "producer_connected": False,
                    "active_consumers": 0
                }
                
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "producer_connected": False,
                "active_consumers": len(self.consumers)
            }
            
    def get_stats(self) -> Dict[str, Any]:
        """Get Kafka connector statistics"""
        return {
            "messages_produced": self.stats["messages_produced"],
            "messages_consumed": self.stats["messages_consumed"],
            "producer_errors": self.stats["producer_errors"],
            "consumer_errors": self.stats["consumer_errors"],
            "bytes_sent": self.stats["bytes_sent"],
            "bytes_received": self.stats["bytes_received"],
            "active_consumers": len(self.consumers),
            "last_activity": self.stats["last_activity"].isoformat() if self.stats["last_activity"] else None,
            "bootstrap_servers": self.bootstrap_servers,
            "topics": self.topics
        }
        
    def reset_stats(self):
        """Reset statistics counters"""
        self.stats = {
            "messages_produced": 0,
            "messages_consumed": 0,
            "producer_errors": 0,
            "consumer_errors": 0,
            "bytes_sent": 0,
            "bytes_received": 0,
            "last_activity": None
        }


class MockKafkaConnector(KafkaConnector):
    """Mock implementation of Kafka connector for testing and dry-run mode"""
    
    def __init__(self, config: ConnectionConfig):
        # Don't call parent __init__ to avoid Kafka dependency
        self.bootstrap_servers = config.kafka_bootstrap_servers or "localhost:9092"
        self.timeout = config.timeout_seconds
        
        # Mock storage for messages
        self.message_store = {
            "transactions": [],
            "fraud_decisions": [],
            "customer_events": [],
            "account_events": [],
            "simulation_metrics": []
        }
        
        # Statistics
        self.stats = {
            "messages_produced": 0,
            "messages_consumed": 0,
            "producer_errors": 0,
            "consumer_errors": 0,
            "bytes_sent": 0,
            "bytes_received": 0,
            "last_activity": None
        }
        
        # Consumer handlers
        self.consumer_handlers = {}
        
    async def __aenter__(self):
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass
        
    async def initialize(self):
        """Mock initialization"""
        logger.info("Mock Kafka connector initialized")
        
    async def close(self):
        """Mock close"""
        logger.info("Mock Kafka connector closed")
        
    # Mock producer methods
    async def publish_transaction(self, transaction_data: Dict[str, Any]) -> bool:
        """Mock publish transaction"""
        message = {
            "event_type": "transaction_created",
            "timestamp": datetime.now().isoformat(),
            "data": transaction_data
        }
        
        self.message_store["transactions"].append(message)
        self.stats["messages_produced"] += 1
        self.stats["bytes_sent"] += len(json.dumps(message))
        self.stats["last_activity"] = datetime.now()
        
        # If there's a consumer handler, simulate message delivery
        if "transactions" in self.consumer_handlers:
            try:
                handler = self.consumer_handlers["transactions"]
                await asyncio.get_event_loop().run_in_executor(None, handler, message)
                self.stats["messages_consumed"] += 1
            except Exception as e:
                self.stats["consumer_errors"] += 1
                logger.error(f"Mock consumer error: {e}")
        
        return True
        
    async def publish_fraud_decision(self, decision_data: Dict[str, Any]) -> bool:
        """Mock publish fraud decision"""
        message = {
            "event_type": "fraud_decision",
            "timestamp": datetime.now().isoformat(),
            "data": decision_data
        }
        
        self.message_store["fraud_decisions"].append(message)
        self.stats["messages_produced"] += 1
        self.stats["bytes_sent"] += len(json.dumps(message))
        self.stats["last_activity"] = datetime.now()
        
        # Simulate consumer delivery
        if "fraud_decisions" in self.consumer_handlers:
            try:
                handler = self.consumer_handlers["fraud_decisions"]
                await asyncio.get_event_loop().run_in_executor(None, handler, message)
                self.stats["messages_consumed"] += 1
            except Exception as e:
                self.stats["consumer_errors"] += 1
                
        return True
        
    async def publish_customer_event(self, customer_id: str, event_type: str, event_data: Dict[str, Any]) -> bool:
        """Mock publish customer event"""
        message = {
            "event_type": event_type,
            "customer_id": customer_id,
            "timestamp": datetime.now().isoformat(),
            "data": event_data
        }
        
        self.message_store["customer_events"].append(message)
        self.stats["messages_produced"] += 1
        self.stats["last_activity"] = datetime.now()
        return True
        
    async def publish_account_event(self, account_id: str, event_type: str, event_data: Dict[str, Any]) -> bool:
        """Mock publish account event"""
        message = {
            "event_type": event_type,
            "account_id": account_id,
            "timestamp": datetime.now().isoformat(),
            "data": event_data
        }
        
        self.message_store["account_events"].append(message)
        self.stats["messages_produced"] += 1
        self.stats["last_activity"] = datetime.now()
        return True
        
    async def publish_metrics(self, metrics_data: Dict[str, Any]) -> bool:
        """Mock publish metrics"""
        message = {
            "event_type": "simulation_metrics",
            "timestamp": datetime.now().isoformat(),
            "data": metrics_data
        }
        
        self.message_store["simulation_metrics"].append(message)
        self.stats["messages_produced"] += 1
        self.stats["last_activity"] = datetime.now()
        return True
        
    # Mock consumer methods
    async def start_consumer(self, topic: str, handler: Callable[[Dict[str, Any]], None],
                           consumer_group: str = "banking_simulator") -> bool:
        """Mock start consumer"""
        self.consumer_handlers[topic] = handler
        logger.info(f"Mock consumer started for topic: {topic}")
        return True
        
    async def stop_consumer(self, topic: str):
        """Mock stop consumer"""
        if topic in self.consumer_handlers:
            del self.consumer_handlers[topic]
        logger.info(f"Mock consumer stopped for topic: {topic}")
        
    async def start_transaction_consumer(self, handler: Callable[[Dict[str, Any]], None]) -> bool:
        """Mock start transaction consumer"""
        return await self.start_consumer("transactions", handler)
        
    async def start_fraud_decision_consumer(self, handler: Callable[[Dict[str, Any]], None]) -> bool:
        """Mock start fraud decision consumer"""
        return await self.start_consumer("fraud_decisions", handler)
        
    async def health_check(self) -> Dict[str, Any]:
        """Mock health check"""
        return {
            "status": "healthy",
            "mode": "mock",
            "brokers": 1,
            "topics": 5,
            "producer_connected": True,
            "active_consumers": len(self.consumer_handlers),
            "bootstrap_servers": self.bootstrap_servers
        }
        
    def get_message_store(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get stored messages for testing"""
        return self.message_store.copy()
        
    def clear_message_store(self):
        """Clear stored messages"""
        for topic_messages in self.message_store.values():
            topic_messages.clear()