"""FastAPI dashboard server for banking simulation.

Provides REST API endpoints and WebSocket support for the real-time
simulation dashboard. Serves static files and handles dashboard control.
"""

import asyncio
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from .ws import websocket_manager
from ..config import DashboardConfig
from ..engine import SimulationEngine
from ..metrics import MetricsCollector


logger = logging.getLogger(__name__)


class DashboardServer:
    """FastAPI-based dashboard server"""
    
    def __init__(self, config: DashboardConfig, simulation_engine: Optional[SimulationEngine] = None,
                 metrics_collector: Optional[MetricsCollector] = None):
        self.config = config
        self.simulation_engine = simulation_engine
        self.metrics_collector = metrics_collector
        
        # Create FastAPI app
        self.app = FastAPI(
            title="Banking Simulator Dashboard",
            description="Real-time dashboard for banking simulation monitoring and control",
            version="1.0.0",
            docs_url="/api/docs",
            redoc_url="/api/redoc"
        )
        
        # Add CORS middleware
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],  # Configure appropriately for production
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Setup routes
        self._setup_routes()
        
        # Setup static file serving
        self._setup_static_files()
        
        # Dashboard statistics
        self.stats = {
            "server_start_time": datetime.now(),
            "total_requests": 0,
            "websocket_connections": 0,
            "errors": 0
        }
        
    def _setup_routes(self):
        """Setup API routes"""
        
        @self.app.get("/", response_class=HTMLResponse)
        async def dashboard_home():
            """Serve the main dashboard page"""
            try:
                static_path = Path(self.config.static_path)
                index_file = static_path / "index.html"
                
                if index_file.exists():
                    return HTMLResponse(content=index_file.read_text(), status_code=200)
                else:
                    # Return a basic HTML page if index.html doesn't exist
                    return HTMLResponse(content=self._get_default_dashboard_html(), status_code=200)
                    
            except Exception as e:
                logger.error(f"Error serving dashboard: {e}")
                self.stats["errors"] += 1
                raise HTTPException(status_code=500, detail="Dashboard not available")
                
        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            """WebSocket endpoint for real-time updates"""
            client_info = {
                "client_ip": websocket.client.host if websocket.client else "unknown",
                "user_agent": websocket.headers.get("user-agent", "unknown")
            }
            
            await websocket_manager.connect(websocket, client_info)
            self.stats["websocket_connections"] += 1
            
            try:
                while True:
                    # Receive messages from client
                    message = await websocket.receive_text()
                    
                    # Handle client message and get any actions to perform
                    actions = await websocket_manager.handle_client_message(websocket, message)
                    
                    # Process actions
                    if actions.get("action") == "get_status":
                        await self._send_current_status(websocket)
                    elif actions.get("action") == "get_metrics":
                        await self._send_current_metrics(websocket)
                        
            except WebSocketDisconnect:
                await websocket_manager.disconnect(websocket)
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
                await websocket_manager.disconnect(websocket)
                
        @self.app.get("/api/health")
        async def health_check():
            """Health check endpoint"""
            self.stats["total_requests"] += 1
            
            return {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "dashboard_config": {
                    "port": self.config.port,
                    "host": self.config.host
                },
                "simulation_connected": self.simulation_engine is not None,
                "metrics_connected": self.metrics_collector is not None,
                "websocket_connections": len(websocket_manager.active_connections)
            }
            
        @self.app.get("/api/status")
        async def get_simulation_status():
            """Get current simulation status"""
            self.stats["total_requests"] += 1
            
            if not self.simulation_engine:
                raise HTTPException(status_code=503, detail="Simulation engine not available")
                
            try:
                status = self.simulation_engine.get_status()
                return {
                    "status": "ok",
                    "data": status,
                    "timestamp": datetime.now().isoformat()
                }
            except Exception as e:
                logger.error(f"Error getting simulation status: {e}")
                self.stats["errors"] += 1
                raise HTTPException(status_code=500, detail=str(e))
                
        @self.app.get("/api/metrics")
        async def get_current_metrics():
            """Get current simulation metrics"""
            self.stats["total_requests"] += 1
            
            if not self.metrics_collector:
                raise HTTPException(status_code=503, detail="Metrics collector not available")
                
            try:
                metrics = self.metrics_collector.get_dashboard_data()
                return {
                    "status": "ok",
                    "data": metrics,
                    "timestamp": datetime.now().isoformat()
                }
            except Exception as e:
                logger.error(f"Error getting metrics: {e}")
                self.stats["errors"] += 1
                raise HTTPException(status_code=500, detail=str(e))
                
        @self.app.get("/api/metrics/timeseries/{metric_name}")
        async def get_metric_timeseries(metric_name: str, minutes: int = 10):
            """Get time series data for a specific metric"""
            self.stats["total_requests"] += 1
            
            if not self.metrics_collector:
                raise HTTPException(status_code=503, detail="Metrics collector not available")
                
            try:
                data = self.metrics_collector.get_time_series_data(metric_name, minutes)
                return {
                    "status": "ok",
                    "metric": metric_name,
                    "data": data,
                    "timestamp": datetime.now().isoformat()
                }
            except Exception as e:
                logger.error(f"Error getting time series data: {e}")
                self.stats["errors"] += 1
                raise HTTPException(status_code=500, detail=str(e))
                
        @self.app.post("/api/control/pause")
        async def pause_simulation():
            """Pause the simulation"""
            self.stats["total_requests"] += 1
            
            if not self.simulation_engine:
                raise HTTPException(status_code=503, detail="Simulation engine not available")
                
            try:
                self.simulation_engine.pause()
                
                # Broadcast system event
                await websocket_manager.broadcast_system_event("simulation_paused", {
                    "timestamp": datetime.now().isoformat(),
                    "action": "pause"
                })
                
                return {"status": "ok", "message": "Simulation paused"}
            except Exception as e:
                logger.error(f"Error pausing simulation: {e}")
                self.stats["errors"] += 1
                raise HTTPException(status_code=500, detail=str(e))
                
        @self.app.post("/api/control/resume")
        async def resume_simulation():
            """Resume the simulation"""
            self.stats["total_requests"] += 1
            
            if not self.simulation_engine:
                raise HTTPException(status_code=503, detail="Simulation engine not available")
                
            try:
                self.simulation_engine.resume()
                
                # Broadcast system event
                await websocket_manager.broadcast_system_event("simulation_resumed", {
                    "timestamp": datetime.now().isoformat(),
                    "action": "resume"
                })
                
                return {"status": "ok", "message": "Simulation resumed"}
            except Exception as e:
                logger.error(f"Error resuming simulation: {e}")
                self.stats["errors"] += 1
                raise HTTPException(status_code=500, detail=str(e))
                
        @self.app.post("/api/control/stop")
        async def stop_simulation():
            """Stop the simulation"""
            self.stats["total_requests"] += 1
            
            if not self.simulation_engine:
                raise HTTPException(status_code=503, detail="Simulation engine not available")
                
            try:
                self.simulation_engine.stop()
                
                # Broadcast system event
                await websocket_manager.broadcast_system_event("simulation_stopped", {
                    "timestamp": datetime.now().isoformat(),
                    "action": "stop"
                })
                
                return {"status": "ok", "message": "Simulation stopped"}
            except Exception as e:
                logger.error(f"Error stopping simulation: {e}")
                self.stats["errors"] += 1
                raise HTTPException(status_code=500, detail=str(e))
                
        @self.app.post("/api/control/speed")
        async def set_simulation_speed(request: Request):
            """Set simulation speed multiplier"""
            self.stats["total_requests"] += 1
            
            if not self.simulation_engine:
                raise HTTPException(status_code=503, detail="Simulation engine not available")
                
            try:
                body = await request.json()
                multiplier = body.get("multiplier")
                
                if not multiplier or not isinstance(multiplier, (int, float)) or multiplier <= 0:
                    raise HTTPException(status_code=400, detail="Invalid speed multiplier")
                    
                self.simulation_engine.set_speed(float(multiplier))
                
                # Broadcast system event
                await websocket_manager.broadcast_system_event("speed_changed", {
                    "timestamp": datetime.now().isoformat(),
                    "action": "speed_change",
                    "new_multiplier": multiplier
                })
                
                return {"status": "ok", "message": f"Speed set to {multiplier}x"}
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error setting simulation speed: {e}")
                self.stats["errors"] += 1
                raise HTTPException(status_code=500, detail=str(e))
                
        @self.app.post("/api/start")
        async def start_simulation(request: Request):
            """Start simulation with optional parameters"""
            self.stats["total_requests"] += 1
            
            if not self.simulation_engine:
                raise HTTPException(status_code=503, detail="Simulation engine not available")
                
            try:
                body = await request.json() if request.headers.get("content-type") == "application/json" else {}
                scenario = body.get("scenario", "normal_day")
                
                self.simulation_engine.start(scenario)
                
                # Broadcast system event
                await websocket_manager.broadcast_system_event("simulation_started", {
                    "timestamp": datetime.now().isoformat(),
                    "action": "start",
                    "scenario": scenario
                })
                
                return {"status": "ok", "message": f"Simulation started with scenario: {scenario}"}
            except Exception as e:
                logger.error(f"Error starting simulation: {e}")
                self.stats["errors"] += 1
                raise HTTPException(status_code=500, detail=str(e))
                
        @self.app.get("/api/scenarios")
        async def get_scenarios():
            """Get available simulation scenarios"""
            self.stats["total_requests"] += 1
            
            try:
                # Import scenarios dynamically to avoid circular imports
                from ..scenarios import get_available_scenarios
                scenarios = get_available_scenarios()
                
                return {
                    "status": "ok",
                    "data": scenarios,
                    "timestamp": datetime.now().isoformat()
                }
            except Exception as e:
                logger.error(f"Error getting scenarios: {e}")
                self.stats["errors"] += 1
                # Return default scenarios if the function doesn't exist
                return {
                    "status": "ok", 
                    "data": [
                        {"name": "normal_day", "description": "Normal banking day simulation"},
                        {"name": "fraud_attack", "description": "High fraud activity simulation"},
                        {"name": "peak_hours", "description": "Peak transaction volume simulation"},
                        {"name": "holiday_rush", "description": "Holiday shopping rush simulation"},
                        {"name": "system_stress", "description": "System stress test simulation"}
                    ],
                    "timestamp": datetime.now().isoformat()
                }
                
        @self.app.get("/api/customers")
        async def get_customers():
            """Get list of generated customers"""
            self.stats["total_requests"] += 1
            
            try:
                customers = []
                if self.simulation_engine:
                    # Get customers from simulation engine if available
                    customers = getattr(self.simulation_engine, 'get_customers', lambda: [])()
                
                return {
                    "status": "ok",
                    "data": customers,
                    "count": len(customers),
                    "timestamp": datetime.now().isoformat()
                }
            except Exception as e:
                logger.error(f"Error getting customers: {e}")
                self.stats["errors"] += 1
                raise HTTPException(status_code=500, detail=str(e))
                
        @self.app.get("/api/transactions")
        async def get_transactions(limit: int = 100):
            """Get recent transactions"""
            self.stats["total_requests"] += 1
            
            try:
                transactions = []
                if self.simulation_engine:
                    # Get recent transactions from simulation engine
                    transactions = getattr(self.simulation_engine, 'get_recent_transactions', lambda x: [])(limit)
                
                return {
                    "status": "ok",
                    "data": transactions,
                    "count": len(transactions),
                    "limit": limit,
                    "timestamp": datetime.now().isoformat()
                }
            except Exception as e:
                logger.error(f"Error getting transactions: {e}")
                self.stats["errors"] += 1
                raise HTTPException(status_code=500, detail=str(e))
                
        @self.app.get("/api/results")
        async def get_simulation_results():
            """Get simulation results and summary statistics"""
            self.stats["total_requests"] += 1
            
            try:
                results = {}
                if self.simulation_engine:
                    results = getattr(self.simulation_engine, 'get_results', lambda: {})()
                if self.metrics_collector:
                    metrics = self.metrics_collector.get_summary_stats()
                    results.update(metrics)
                
                return {
                    "status": "ok",
                    "data": results,
                    "timestamp": datetime.now().isoformat()
                }
            except Exception as e:
                logger.error(f"Error getting results: {e}")
                self.stats["errors"] += 1
                raise HTTPException(status_code=500, detail=str(e))
                
        @self.app.get("/api/stats")
        async def get_dashboard_stats():
            """Get dashboard server statistics"""
            self.stats["total_requests"] += 1
            
            uptime = (datetime.now() - self.stats["server_start_time"]).total_seconds()
            
            return {
                "status": "ok",
                "stats": {
                    "uptime_seconds": uptime,
                    "total_requests": self.stats["total_requests"],
                    "websocket_connections": self.stats["websocket_connections"],
                    "active_websockets": len(websocket_manager.active_connections),
                    "errors": self.stats["errors"],
                    "websocket_stats": websocket_manager.get_stats()
                },
                "timestamp": datetime.now().isoformat()
            }
            
    def _setup_static_files(self):
        """Setup static file serving"""
        static_path = Path(self.config.static_path)
        
        if static_path.exists() and static_path.is_dir():
            # Mount static files
            self.app.mount("/static", StaticFiles(directory=str(static_path)), name="static")
        else:
            logger.warning(f"Static path not found: {static_path}")
            
    def _get_default_dashboard_html(self) -> str:
        """Get default dashboard HTML when static files are not available"""
        return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Banking Simulator Dashboard</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; }
        .header { background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .status { background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .error { color: #d32f2f; background: #ffebee; padding: 15px; border-radius: 4px; margin: 10px 0; }
        .info { color: #1976d2; background: #e3f2fd; padding: 15px; border-radius: 4px; margin: 10px 0; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Banking Simulator Dashboard</h1>
            <p>Real-time monitoring and control for banking simulation</p>
        </div>
        <div class="status">
            <h2>Dashboard Status</h2>
            <div class="info">Dashboard server is running, but static files are not available.</div>
            <div class="info">API endpoints are available at /api/</div>
            <p><strong>Available endpoints:</strong></p>
            <ul>
                <li>GET /api/health - Health check</li>
                <li>GET /api/status - Simulation status</li>
                <li>GET /api/metrics - Current metrics</li>
                <li>WebSocket /ws - Real-time updates</li>
                <li>POST /api/control/pause - Pause simulation</li>
                <li>POST /api/control/resume - Resume simulation</li>
                <li>POST /api/control/stop - Stop simulation</li>
            </ul>
        </div>
    </div>
</body>
</html>
"""
        
    async def _send_current_status(self, websocket: WebSocket):
        """Send current simulation status to WebSocket client"""
        if self.simulation_engine:
            try:
                status = self.simulation_engine.get_status()
                await websocket_manager.send_to_client(websocket, {
                    "type": "status_response",
                    "data": status,
                    "timestamp": datetime.now().isoformat()
                })
            except Exception as e:
                await websocket_manager.send_error_to_client(websocket, str(e), "STATUS_ERROR")
        else:
            await websocket_manager.send_error_to_client(websocket, "Simulation engine not available", "NO_ENGINE")
            
    async def _send_current_metrics(self, websocket: WebSocket):
        """Send current metrics to WebSocket client"""
        if self.metrics_collector:
            try:
                metrics = self.metrics_collector.get_dashboard_data()
                await websocket_manager.send_to_client(websocket, {
                    "type": "metrics_response",
                    "data": metrics,
                    "timestamp": datetime.now().isoformat()
                })
            except Exception as e:
                await websocket_manager.send_error_to_client(websocket, str(e), "METRICS_ERROR")
        else:
            await websocket_manager.send_error_to_client(websocket, "Metrics collector not available", "NO_METRICS")
            
    def set_simulation_engine(self, engine: SimulationEngine):
        """Set the simulation engine reference"""
        self.simulation_engine = engine
        
    def set_metrics_collector(self, collector: MetricsCollector):
        """Set the metrics collector reference"""
        self.metrics_collector = collector
        
        # Add callback for real-time metrics broadcasting
        collector.add_update_callback(self._broadcast_metrics_update)
        
    async def _broadcast_metrics_update(self, metrics_data: Dict[str, Any]):
        """Callback for broadcasting metrics updates"""
        try:
            await websocket_manager.broadcast_metrics(metrics_data)
        except Exception as e:
            logger.error(f"Error broadcasting metrics update: {e}")
            
    async def start_websocket_manager(self):
        """Start the WebSocket manager"""
        await websocket_manager.start_periodic_broadcasting()
        
    async def stop_websocket_manager(self):
        """Stop the WebSocket manager"""
        await websocket_manager.stop_periodic_broadcasting()
        await websocket_manager.close_all_connections()
        
    def get_stats(self) -> Dict[str, Any]:
        """Get dashboard server statistics"""
        uptime = (datetime.now() - self.stats["server_start_time"]).total_seconds()
        
        return {
            "uptime_seconds": uptime,
            "total_requests": self.stats["total_requests"],
            "websocket_connections": self.stats["websocket_connections"],
            "active_websockets": len(websocket_manager.active_connections),
            "errors": self.stats["errors"],
            "config": {
                "host": self.config.host,
                "port": self.config.port,
                "static_path": self.config.static_path
            }
        }


def create_dashboard_app(config: DashboardConfig, simulation_engine: Optional[SimulationEngine] = None,
                        metrics_collector: Optional[MetricsCollector] = None) -> DashboardServer:
    """Create and configure dashboard server"""
    return DashboardServer(config, simulation_engine, metrics_collector)