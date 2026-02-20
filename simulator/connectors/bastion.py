"""Bastion Fraud Detection System connector.

Provides REST API client for Bastion fraud detection system running on port 8080.
Handles transaction scoring, rule management, and case management.
"""

import httpx
import asyncio
import logging
import random
from typing import Dict, List, Optional, Any, Union
from datetime import datetime

from ..config import ConnectionConfig


logger = logging.getLogger(__name__)


class BastionError(Exception):
    """Base exception for Bastion API errors"""
    pass


class BastionConnectionError(BastionError):
    """Connection error with Bastion API"""
    pass


class BastionAPIError(BastionError):
    """API error response from Bastion"""
    def __init__(self, status_code: int, message: str, details: Optional[Dict] = None):
        self.status_code = status_code
        self.message = message
        self.details = details or {}
        super().__init__(f"Bastion API Error {status_code}: {message}")


class BastionConnector:
    """REST API connector for Bastion fraud detection system"""
    
    def __init__(self, config: ConnectionConfig):
        self.base_url = config.bastion_url.rstrip('/')
        self.timeout = config.timeout_seconds
        self.max_retries = config.max_retries
        self.jwt_token = config.jwt_token
        
        # Statistics tracking
        self.stats = {
            "requests_sent": 0,
            "requests_successful": 0,
            "requests_failed": 0,
            "total_latency_ms": 0,
            "total_score_time_ms": 0,
            "transactions_scored": 0,
            "avg_risk_score": 0.0,
            "decisions": {"approve": 0, "review": 0, "decline": 0},
            "errors": []
        }
        
        # HTTP client
        self._client = None
        
    async def __aenter__(self):
        """Async context manager entry"""
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(self.timeout),
            limits=httpx.Limits(max_connections=10, max_keepalive_connections=5)
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self._client:
            await self._client.aclose()
            
    def _get_headers(self) -> Dict[str, str]:
        """Get HTTP headers for requests"""
        headers = {"Content-Type": "application/json"}
        if self.jwt_token:
            headers["Authorization"] = f"Bearer {self.jwt_token}"
        return headers
        
    async def _make_request(self, method: str, endpoint: str, 
                          data: Optional[Dict] = None, params: Optional[Dict] = None) -> Dict[str, Any]:
        """Make HTTP request to Bastion API with error handling and retries"""
        if not self._client:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(self.timeout),
                limits=httpx.Limits(max_connections=10, max_keepalive_connections=5)
            )
            
        url = f"{self.base_url}{endpoint}"
        headers = self._get_headers()
        
        self.stats["requests_sent"] += 1
        start_time = datetime.now()
        
        for attempt in range(self.max_retries + 1):
            try:
                response = await self._client.request(
                    method=method,
                    url=url,
                    json=data,
                    params=params,
                    headers=headers
                )
                
                # Calculate latency
                latency_ms = (datetime.now() - start_time).total_seconds() * 1000
                self.stats["total_latency_ms"] += latency_ms
                
                if response.status_code == 200 or response.status_code == 201:
                    self.stats["requests_successful"] += 1
                    return response.json()
                elif response.status_code >= 400:
                    error_detail = {}
                    try:
                        error_detail = response.json()
                    except:
                        error_detail = {"detail": response.text}
                        
                    if attempt == self.max_retries:
                        self.stats["requests_failed"] += 1
                        self.stats["errors"].append({
                            "endpoint": endpoint,
                            "status_code": response.status_code,
                            "error": error_detail,
                            "timestamp": datetime.now().isoformat()
                        })
                        raise BastionAPIError(response.status_code, error_detail.get("detail", "Unknown error"), error_detail)
                        
                    # Retry for 5xx errors
                    if response.status_code >= 500:
                        await asyncio.sleep(2 ** attempt)  # Exponential backoff
                        continue
                    else:
                        # Don't retry 4xx errors
                        self.stats["requests_failed"] += 1
                        raise BastionAPIError(response.status_code, error_detail.get("detail", "Client error"), error_detail)
                        
            except httpx.TimeoutException:
                if attempt == self.max_retries:
                    self.stats["requests_failed"] += 1
                    self.stats["errors"].append({
                        "endpoint": endpoint,
                        "error": "timeout",
                        "timestamp": datetime.now().isoformat()
                    })
                    raise BastionConnectionError(f"Timeout connecting to Bastion at {url}")
                await asyncio.sleep(2 ** attempt)
                
            except httpx.ConnectError:
                if attempt == self.max_retries:
                    self.stats["requests_failed"] += 1
                    self.stats["errors"].append({
                        "endpoint": endpoint,
                        "error": "connection_error",
                        "timestamp": datetime.now().isoformat()
                    })
                    raise BastionConnectionError(f"Cannot connect to Bastion at {url}")
                await asyncio.sleep(2 ** attempt)
                
        # Should not reach here
        raise BastionConnectionError("Max retries exceeded")
        
    async def health_check(self) -> Dict[str, Any]:
        """Check if Bastion API is healthy"""
        try:
            return await self._make_request("GET", "/health")
        except Exception as e:
            logger.warning(f"Bastion health check failed: {e}")
            return {"status": "unhealthy", "error": str(e)}
            
    # Core Fraud Detection
    async def score_transaction(self, transaction_id: str, cif_id: str, amount: float,
                               currency: str = "USD", merchant_id: str = "",
                               merchant_category: str = "", channel: str = "card",
                               country: str = "", timestamp: Optional[float] = None,
                               metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Score a single transaction for fraud"""
        start_time = datetime.now()
        
        data = {
            "transaction_id": transaction_id,
            "cif_id": cif_id,
            "amount": amount,
            "currency": currency,
            "merchant_id": merchant_id,
            "merchant_category": merchant_category,
            "channel": channel,
            "country": country,
            "timestamp": timestamp or datetime.now().timestamp(),
            "metadata": metadata or {}
        }
        
        result = await self._make_request("POST", "/score", data)
        
        # Track scoring statistics
        scoring_latency = (datetime.now() - start_time).total_seconds() * 1000
        self.stats["total_score_time_ms"] += scoring_latency
        self.stats["transactions_scored"] += 1
        
        # Update decision counts and risk score averages
        if "action" in result:
            action = result["action"].lower()
            if action in self.stats["decisions"]:
                self.stats["decisions"][action] += 1
                
        if "risk_score" in result:
            risk_score = result["risk_score"]
            current_avg = self.stats["avg_risk_score"]
            count = self.stats["transactions_scored"]
            self.stats["avg_risk_score"] = ((current_avg * (count - 1)) + risk_score) / count
            
        return result
        
    async def score_batch(self, transactions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Score multiple transactions in batch"""
        data = {"transactions": transactions}
        
        start_time = datetime.now()
        results = await self._make_request("POST", "/score/batch", data)
        
        # Update batch statistics
        batch_latency = (datetime.now() - start_time).total_seconds() * 1000
        self.stats["total_score_time_ms"] += batch_latency
        self.stats["transactions_scored"] += len(transactions)
        
        # Update decision and risk score stats
        for result in results:
            if "action" in result:
                action = result["action"].lower()
                if action in self.stats["decisions"]:
                    self.stats["decisions"][action] += 1
                    
            if "risk_score" in result:
                risk_score = result["risk_score"]
                current_avg = self.stats["avg_risk_score"]
                count = self.stats["transactions_scored"]
                self.stats["avg_risk_score"] = ((current_avg * (count - 1)) + risk_score) / count
                
        return results
        
    # Transaction Explanation
    async def explain_transaction(self, transaction_id: str, transaction_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get explanation for a transaction decision"""
        return await self._make_request("POST", f"/explain/{transaction_id}", transaction_data)
        
    # Rule Management
    async def list_rules(self) -> Dict[str, Any]:
        """Get list of active fraud rules"""
        return await self._make_request("GET", "/rules")
        
    async def add_rule(self, name: str, priority: int, conditions: List[Dict], action: str,
                      reason: str = "", score_adjustment: float = 0.0) -> Dict[str, Any]:
        """Add a new fraud rule"""
        data = {
            "name": name,
            "priority": priority,
            "conditions": conditions,
            "action": action,
            "reason": reason,
            "score_adjustment": score_adjustment
        }
        
        return await self._make_request("POST", "/rules", data)
        
    async def remove_rule(self, rule_name: str) -> Dict[str, Any]:
        """Remove a fraud rule"""
        return await self._make_request("DELETE", f"/rules/{rule_name}")
        
    # System Statistics
    async def get_stats(self) -> Dict[str, Any]:
        """Get Bastion engine statistics"""
        return await self._make_request("GET", "/stats")
        
    # Case Management (if available)
    async def list_cases(self, status: Optional[str] = None, priority: Optional[str] = None,
                        assigned_to: Optional[str] = None, skip: int = 0, limit: int = 100) -> Dict[str, Any]:
        """List fraud cases"""
        params = {"skip": skip, "limit": limit}
        if status:
            params["status"] = status
        if priority:
            params["priority"] = priority
        if assigned_to:
            params["assigned_to"] = assigned_to
            
        return await self._make_request("GET", "/cases", params=params)
        
    async def get_case(self, case_id: str) -> Dict[str, Any]:
        """Get case details"""
        return await self._make_request("GET", f"/cases/{case_id}")
        
    async def add_case_note(self, case_id: str, author: str, content: str, note_type: str = "COMMENT") -> Dict[str, Any]:
        """Add note to case"""
        data = {
            "author": author,
            "content": content,
            "note_type": note_type
        }
        
        return await self._make_request("POST", f"/cases/{case_id}/note", data)
        
    async def resolve_case(self, case_id: str, resolution: str, actor: str, notes: str = "") -> Dict[str, Any]:
        """Resolve a fraud case"""
        data = {
            "resolution": resolution,
            "actor": actor,
            "notes": notes
        }
        
        return await self._make_request("POST", f"/cases/{case_id}/resolve", data)
        
    # Authentication
    async def login(self, username: str, password: str) -> Dict[str, Any]:
        """Authenticate with Bastion and get JWT token"""
        data = {"username": username, "password": password}
        return await self._make_request("POST", "/auth/login", data)
        
    # Feedback Management (if available)
    async def submit_feedback(self, transaction_id: str, actual_fraud: bool, analyst_decision: str,
                            confidence: float, notes: str = "") -> Dict[str, Any]:
        """Submit feedback for model training"""
        data = {
            "transaction_id": transaction_id,
            "actual_fraud": actual_fraud,
            "analyst_decision": analyst_decision,
            "confidence": confidence,
            "notes": notes
        }
        
        try:
            return await self._make_request("POST", "/feedback", data)
        except BastionAPIError as e:
            if e.status_code == 404:
                logger.warning("Feedback endpoint not available")
                return {"status": "feedback_not_supported"}
            raise
            
    # Statistics and monitoring
    def get_connector_stats(self) -> Dict[str, Any]:
        """Get connector statistics"""
        total_requests = self.stats["requests_sent"]
        if total_requests > 0:
            avg_latency = self.stats["total_latency_ms"] / total_requests
            success_rate = self.stats["requests_successful"] / total_requests
        else:
            avg_latency = 0
            success_rate = 0
            
        scored_transactions = self.stats["transactions_scored"]
        if scored_transactions > 0:
            avg_scoring_latency = self.stats["total_score_time_ms"] / scored_transactions
        else:
            avg_scoring_latency = 0
            
        return {
            "total_requests": total_requests,
            "successful_requests": self.stats["requests_successful"],
            "failed_requests": self.stats["requests_failed"],
            "success_rate": success_rate,
            "average_latency_ms": avg_latency,
            "transactions_scored": scored_transactions,
            "average_scoring_latency_ms": avg_scoring_latency,
            "average_risk_score": self.stats["avg_risk_score"],
            "decisions": self.stats["decisions"].copy(),
            "recent_errors": self.stats["errors"][-10:],  # Last 10 errors
            "base_url": self.base_url
        }
        
    def reset_stats(self):
        """Reset statistics counters"""
        self.stats = {
            "requests_sent": 0,
            "requests_successful": 0,
            "requests_failed": 0,
            "total_latency_ms": 0,
            "total_score_time_ms": 0,
            "transactions_scored": 0,
            "avg_risk_score": 0.0,
            "decisions": {"approve": 0, "review": 0, "decline": 0},
            "errors": []
        }


class MockBastionConnector(BastionConnector):
    """Mock implementation of Bastion connector for dry-run mode"""
    
    def __init__(self, config: ConnectionConfig):
        super().__init__(config)
        self.rules = []
        self.cases = {}
        self.next_case_id = 1
        
        # Mock fraud detection parameters
        self.base_risk_scores = {
            "low": (0.0, 0.3),
            "medium": (0.3, 0.7),
            "high": (0.7, 1.0)
        }
        
    async def __aenter__(self):
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass
        
    async def _make_request(self, method: str, endpoint: str, 
                          data: Optional[Dict] = None, params: Optional[Dict] = None) -> Dict[str, Any]:
        """Mock request - simulate realistic response times"""
        # Simulate scoring latency (10-100ms for fraud detection)
        if endpoint == "/score":
            await asyncio.sleep(random.uniform(0.01, 0.1))
        else:
            await asyncio.sleep(random.uniform(0.005, 0.02))
            
        self.stats["requests_sent"] += 1
        self.stats["requests_successful"] += 1
        
        # Route to mock implementations
        if endpoint == "/health":
            return {"status": "healthy", "timestamp": datetime.now().isoformat(), "mode": "mock"}
        elif endpoint == "/score":
            return self._mock_score_transaction(data)
        elif endpoint == "/score/batch":
            return self._mock_score_batch(data)
        elif endpoint == "/rules" and method == "GET":
            return self._mock_list_rules()
        elif endpoint == "/rules" and method == "POST":
            return self._mock_add_rule(data)
        elif endpoint == "/stats":
            return self._mock_get_stats()
        else:
            return {"status": "ok", "message": f"Mock response for {method} {endpoint}"}
            
    def _mock_score_transaction(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Mock transaction scoring with realistic fraud detection logic"""
        transaction_id = data["transaction_id"]
        amount = data["amount"]
        merchant_category = data.get("merchant_category", "")
        channel = data.get("channel", "card")
        country = data.get("country", "US")
        metadata = data.get("metadata", {})
        
        # Base risk calculation
        risk_score = 0.1  # Base risk
        triggered_rules = []
        
        # Amount-based risk
        if amount > 10000:
            risk_score += 0.4
            triggered_rules.append("large_amount")
        elif amount < 1:
            risk_score += 0.3
            triggered_rules.append("micro_transaction")
            
        # Location-based risk
        high_risk_countries = ["RU", "NG", "RO", "CN"]
        if country in high_risk_countries:
            risk_score += 0.5
            triggered_rules.append("high_risk_country")
            
        # Time-based risk (if it's unusual hours)
        current_hour = datetime.now().hour
        if current_hour < 6 or current_hour > 23:
            risk_score += 0.2
            triggered_rules.append("unusual_hours")
            
        # Channel risk
        if channel == "wire":
            risk_score += 0.1
        elif channel == "atm" and current_hour < 6:
            risk_score += 0.3
            triggered_rules.append("night_atm")
            
        # Fraud metadata
        if metadata.get("is_fraud", False):
            # This is a known fraud transaction - make sure it scores high
            risk_score = max(risk_score, 0.8)
            fraud_type = metadata.get("fraud_type", "unknown")
            if fraud_type == "card_testing":
                risk_score = min(risk_score + 0.2, 1.0)
            elif fraud_type == "velocity_attack":
                risk_score = min(risk_score + 0.3, 1.0)
                triggered_rules.append("velocity_fraud")
            elif fraud_type == "layering":
                risk_score = min(risk_score + 0.1, 1.0)  # Harder to detect
                
        # Add some randomness but bias towards fraud if marked
        if metadata.get("is_fraud", False):
            risk_score += random.uniform(-0.1, 0.2)  # Slight positive bias
        else:
            risk_score += random.uniform(-0.2, 0.2)  # Neutral
            
        risk_score = max(0.0, min(1.0, risk_score))
        
        # Determine action
        if risk_score >= 0.8:
            action = "DECLINE"
        elif risk_score >= 0.5:
            action = "REVIEW"
        else:
            action = "APPROVE"
            
        # Track statistics
        self.stats["transactions_scored"] += 1
        self.stats["decisions"][action.lower()] = self.stats["decisions"].get(action.lower(), 0) + 1
        
        # Update average risk score
        current_avg = self.stats["avg_risk_score"]
        count = self.stats["transactions_scored"]
        self.stats["avg_risk_score"] = ((current_avg * (count - 1)) + risk_score) / count
        
        # Create realistic response
        return {
            "transaction_id": transaction_id,
            "risk_score": round(risk_score, 3),
            "action": action,
            "reason": f"Risk score: {risk_score:.3f}",
            "rule_hits": triggered_rules,
            "model_scores": {
                "amount_model": round(random.uniform(0.1, 0.8), 3),
                "velocity_model": round(random.uniform(0.0, 0.6), 3),
                "location_model": round(random.uniform(0.1, 0.5), 3)
            },
            "features": {
                "amount": amount,
                "merchant_category": merchant_category,
                "channel": channel,
                "country": country,
                "hour_of_day": current_hour
            },
            "processing_time_ms": round(random.uniform(10, 100), 2),
            "model_version": "mock_v1.0",
            "timestamp": datetime.now().isoformat()
        }
        
    def _mock_score_batch(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Mock batch transaction scoring"""
        transactions = data["transactions"]
        results = []
        
        for txn in transactions:
            result = self._mock_score_transaction(txn)
            results.append(result)
            
        return results
        
    def _mock_list_rules(self) -> Dict[str, Any]:
        """Mock rule listing"""
        return {
            "rules": [
                {
                    "name": "large_amount",
                    "priority": 100,
                    "action": "REVIEW",
                    "reason": "Large transaction amount",
                    "enabled": True,
                    "conditions": [{"field": "amount", "op": ">", "value": 10000}]
                },
                {
                    "name": "high_risk_country",
                    "priority": 90,
                    "action": "DECLINE",
                    "reason": "Transaction from high-risk country",
                    "enabled": True,
                    "conditions": [{"field": "country", "op": "in", "value": ["RU", "NG", "RO"]}]
                },
                {
                    "name": "velocity_check",
                    "priority": 80,
                    "action": "REVIEW",
                    "reason": "High transaction velocity",
                    "enabled": True,
                    "conditions": [{"field": "velocity_5min", "op": ">", "value": 5}]
                }
            ]
        }
        
    def _mock_add_rule(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Mock adding a new rule"""
        rule_name = data["name"]
        self.rules.append(data)
        return {"status": "ok", "rule": rule_name}
        
    def _mock_get_stats(self) -> Dict[str, Any]:
        """Mock Bastion engine statistics"""
        return {
            "transactions_processed": self.stats["transactions_scored"],
            "average_processing_time_ms": random.uniform(15, 45),
            "rules_active": 3,
            "model_version": "mock_v1.0",
            "uptime_seconds": random.randint(3600, 86400),
            "decisions": self.stats["decisions"].copy(),
            "fraud_detection_rate": random.uniform(0.02, 0.08),
            "false_positive_rate": random.uniform(0.001, 0.005)
        }