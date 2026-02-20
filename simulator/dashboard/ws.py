"""WebSocket handler for real-time dashboard updates.

Manages WebSocket connections for pushing live simulation metrics
and status updates to connected dashboard clients.
"""

import asyncio
import json
import logging
from typing import Set, Dict, Any, Optional
from datetime import datetime
from fastapi import WebSocket, WebSocketDisconnect


logger = logging.getLogger(__name__)


class WebSocketManager:
    """Manages WebSocket connections for real-time updates"""
    
    def __init__(self):
        # Active WebSocket connections
        self.active_connections: Set[WebSocket] = set()
        
        # Connection metadata
        self.connection_info: Dict[WebSocket, Dict[str, Any]] = {}
        
        # Statistics
        self.stats = {
            "total_connections": 0,
            "active_connections": 0,
            "messages_sent": 0,
            "messages_failed": 0,
            "bytes_sent": 0
        }
        
        # Background broadcasting task
        self.broadcast_task: Optional[asyncio.Task] = None
        self.running = False
        
    async def connect(self, websocket: WebSocket, client_info: Optional[Dict[str, Any]] = None):
        """Accept a WebSocket connection"""
        await websocket.accept()
        
        self.active_connections.add(websocket)
        self.connection_info[websocket] = {
            "connected_at": datetime.now(),
            "client_info": client_info or {},
            "messages_sent": 0,
            "last_activity": datetime.now()
        }
        
        self.stats["total_connections"] += 1
        self.stats["active_connections"] = len(self.active_connections)
        
        logger.info(f"WebSocket connected. Active connections: {self.stats['active_connections']}")
        
        # Send initial connection confirmation
        await self.send_to_client(websocket, {
            "type": "connection_established",
            "timestamp": datetime.now().isoformat(),
            "client_id": id(websocket)
        })
        
    async def disconnect(self, websocket: WebSocket):
        """Handle WebSocket disconnection"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            
        if websocket in self.connection_info:
            del self.connection_info[websocket]
            
        self.stats["active_connections"] = len(self.active_connections)
        
        logger.info(f"WebSocket disconnected. Active connections: {self.stats['active_connections']}")
        
    async def send_to_client(self, websocket: WebSocket, message: Dict[str, Any]) -> bool:
        """Send message to a specific client"""
        try:
            message_str = json.dumps(message, default=str)
            await websocket.send_text(message_str)
            
            # Update statistics
            self.stats["messages_sent"] += 1
            self.stats["bytes_sent"] += len(message_str)
            
            if websocket in self.connection_info:
                self.connection_info[websocket]["messages_sent"] += 1
                self.connection_info[websocket]["last_activity"] = datetime.now()
                
            return True
            
        except Exception as e:
            logger.error(f"Failed to send message to client: {e}")
            self.stats["messages_failed"] += 1
            
            # Remove disconnected client
            if websocket in self.active_connections:
                await self.disconnect(websocket)
                
            return False
            
    async def broadcast(self, message: Dict[str, Any]):
        """Broadcast message to all connected clients"""
        if not self.active_connections:
            return
            
        # Add timestamp if not present
        if "timestamp" not in message:
            message["timestamp"] = datetime.now().isoformat()
            
        # Send to all clients concurrently
        tasks = []
        for websocket in self.active_connections.copy():  # Use copy to avoid modification during iteration
            task = asyncio.create_task(self.send_to_client(websocket, message))
            tasks.append(task)
            
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            successful = sum(1 for result in results if result is True)
            logger.debug(f"Broadcast sent to {successful}/{len(tasks)} clients")
            
    async def broadcast_metrics(self, metrics_data: Dict[str, Any]):
        """Broadcast simulation metrics update"""
        message = {
            "type": "metrics_update",
            "data": metrics_data,
            "timestamp": datetime.now().isoformat()
        }
        
        await self.broadcast(message)
        
    async def broadcast_status(self, status_data: Dict[str, Any]):
        """Broadcast simulation status update"""
        message = {
            "type": "status_update",
            "data": status_data,
            "timestamp": datetime.now().isoformat()
        }
        
        await self.broadcast(message)
        
    async def broadcast_transaction_feed(self, transaction_data: Dict[str, Any]):
        """Broadcast live transaction feed"""
        message = {
            "type": "transaction_feed",
            "data": transaction_data,
            "timestamp": datetime.now().isoformat()
        }
        
        await self.broadcast(message)
        
    async def broadcast_fraud_alert(self, fraud_data: Dict[str, Any]):
        """Broadcast fraud detection alert"""
        message = {
            "type": "fraud_alert",
            "data": fraud_data,
            "timestamp": datetime.now().isoformat(),
            "priority": "high"
        }
        
        await self.broadcast(message)
        
    async def broadcast_system_event(self, event_type: str, event_data: Dict[str, Any]):
        """Broadcast system event (start, stop, pause, etc.)"""
        message = {
            "type": "system_event",
            "event": event_type,
            "data": event_data,
            "timestamp": datetime.now().isoformat()
        }
        
        await self.broadcast(message)
        
    async def send_error_to_client(self, websocket: WebSocket, error_message: str, error_code: Optional[str] = None):
        """Send error message to specific client"""
        message = {
            "type": "error",
            "message": error_message,
            "code": error_code,
            "timestamp": datetime.now().isoformat()
        }
        
        await self.send_to_client(websocket, message)
        
    async def handle_client_message(self, websocket: WebSocket, message: str) -> Dict[str, Any]:
        """Handle incoming message from client"""
        try:
            data = json.loads(message)
            message_type = data.get("type", "unknown")
            
            logger.debug(f"Received client message: {message_type}")
            
            # Handle different message types
            if message_type == "ping":
                # Respond to ping with pong
                await self.send_to_client(websocket, {
                    "type": "pong",
                    "timestamp": datetime.now().isoformat()
                })
                
            elif message_type == "subscribe":
                # Handle subscription requests
                topics = data.get("topics", [])
                await self._handle_subscription(websocket, topics)
                
            elif message_type == "get_status":
                # Client requesting current status
                return {"action": "get_status"}
                
            elif message_type == "get_metrics":
                # Client requesting current metrics
                return {"action": "get_metrics"}
                
            else:
                await self.send_error_to_client(websocket, f"Unknown message type: {message_type}")
                
        except json.JSONDecodeError:
            await self.send_error_to_client(websocket, "Invalid JSON message", "INVALID_JSON")
        except Exception as e:
            logger.error(f"Error handling client message: {e}")
            await self.send_error_to_client(websocket, "Internal server error", "INTERNAL_ERROR")
            
        return {}
        
    async def _handle_subscription(self, websocket: WebSocket, topics: list):
        """Handle subscription to specific topics"""
        # Store subscription preferences in connection info
        if websocket in self.connection_info:
            self.connection_info[websocket]["subscriptions"] = topics
            
        await self.send_to_client(websocket, {
            "type": "subscription_confirmed",
            "topics": topics,
            "timestamp": datetime.now().isoformat()
        })
        
    async def start_periodic_broadcasting(self, interval_seconds: int = 5):
        """Start periodic broadcasting of connection stats"""
        self.running = True
        self.broadcast_task = asyncio.create_task(self._periodic_broadcast_loop(interval_seconds))
        
    async def stop_periodic_broadcasting(self):
        """Stop periodic broadcasting"""
        self.running = False
        if self.broadcast_task:
            self.broadcast_task.cancel()
            try:
                await self.broadcast_task
            except asyncio.CancelledError:
                pass
                
    async def _periodic_broadcast_loop(self, interval_seconds: int):
        """Periodic loop for broadcasting stats"""
        try:
            while self.running:
                # Broadcast connection statistics
                if self.active_connections:
                    stats_message = {
                        "type": "connection_stats",
                        "data": {
                            "active_connections": self.stats["active_connections"],
                            "total_connections": self.stats["total_connections"],
                            "messages_sent": self.stats["messages_sent"],
                            "uptime_seconds": self._get_uptime_seconds()
                        }
                    }
                    
                    await self.broadcast(stats_message)
                    
                await asyncio.sleep(interval_seconds)
                
        except asyncio.CancelledError:
            logger.info("Periodic broadcast loop cancelled")
        except Exception as e:
            logger.error(f"Error in periodic broadcast loop: {e}")
            
    def _get_uptime_seconds(self) -> float:
        """Calculate WebSocket manager uptime"""
        # This is a simple implementation - could be enhanced with actual start time tracking
        return sum(
            (datetime.now() - info["connected_at"]).total_seconds()
            for info in self.connection_info.values()
        ) / max(1, len(self.connection_info))
        
    def get_stats(self) -> Dict[str, Any]:
        """Get WebSocket manager statistics"""
        return {
            "active_connections": self.stats["active_connections"],
            "total_connections": self.stats["total_connections"],
            "messages_sent": self.stats["messages_sent"],
            "messages_failed": self.stats["messages_failed"],
            "bytes_sent": self.stats["bytes_sent"],
            "average_messages_per_connection": (
                self.stats["messages_sent"] / max(1, self.stats["total_connections"])
            ),
            "connection_info": {
                str(id(ws)): {
                    "connected_at": info["connected_at"].isoformat(),
                    "messages_sent": info["messages_sent"],
                    "last_activity": info["last_activity"].isoformat(),
                    "client_info": info["client_info"]
                }
                for ws, info in self.connection_info.items()
            }
        }
        
    async def cleanup_stale_connections(self, max_idle_minutes: int = 30):
        """Clean up connections that have been idle too long"""
        cutoff_time = datetime.now() - timedelta(minutes=max_idle_minutes)
        stale_connections = []
        
        for websocket, info in self.connection_info.items():
            if info["last_activity"] < cutoff_time:
                stale_connections.append(websocket)
                
        for websocket in stale_connections:
            logger.info("Cleaning up stale WebSocket connection")
            await self.disconnect(websocket)
            
    async def close_all_connections(self):
        """Close all active WebSocket connections"""
        disconnect_tasks = []
        
        for websocket in self.active_connections.copy():
            try:
                await websocket.close()
            except Exception:
                pass
                
        self.active_connections.clear()
        self.connection_info.clear()
        self.stats["active_connections"] = 0
        
        logger.info("All WebSocket connections closed")


# Global WebSocket manager instance
websocket_manager = WebSocketManager()


# Import here to avoid circular imports
from datetime import timedelta