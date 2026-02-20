"""Nexum Core Banking System connector.

Provides REST API client for Nexum core banking system running on port 8090.
Handles customer management, account operations, and transaction processing.
"""

import httpx
import asyncio
import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from decimal import Decimal

from ..config import ConnectionConfig


logger = logging.getLogger(__name__)


class NexumError(Exception):
    """Base exception for Nexum API errors"""
    pass


class NexumConnectionError(NexumError):
    """Connection error with Nexum API"""
    pass


class NexumAPIError(NexumError):
    """API error response from Nexum"""
    def __init__(self, status_code: int, message: str, details: Optional[Dict] = None):
        self.status_code = status_code
        self.message = message
        self.details = details or {}
        super().__init__(f"Nexum API Error {status_code}: {message}")


class NexumConnector:
    """REST API connector for Nexum core banking system"""
    
    def __init__(self, config: ConnectionConfig):
        self.base_url = config.nexum_url.rstrip('/')
        self.timeout = config.timeout_seconds
        self.max_retries = config.max_retries
        self.jwt_token = config.jwt_token
        
        # Statistics tracking
        self.stats = {
            "requests_sent": 0,
            "requests_successful": 0,
            "requests_failed": 0,
            "total_latency_ms": 0,
            "errors": []
        }
        
        # HTTP client with connection pooling
        self._client = None
        
    async def __aenter__(self):
        """Async context manager entry"""
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(self.timeout),
            limits=httpx.Limits(max_connections=20, max_keepalive_connections=5)
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
        """Make HTTP request to Nexum API with error handling and retries"""
        if not self._client:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(self.timeout),
                limits=httpx.Limits(max_connections=20, max_keepalive_connections=5)
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
                        raise NexumAPIError(response.status_code, error_detail.get("detail", "Unknown error"), error_detail)
                        
                    # Retry for 5xx errors
                    if response.status_code >= 500:
                        await asyncio.sleep(2 ** attempt)  # Exponential backoff
                        continue
                    else:
                        # Don't retry 4xx errors
                        self.stats["requests_failed"] += 1
                        raise NexumAPIError(response.status_code, error_detail.get("detail", "Client error"), error_detail)
                        
            except httpx.TimeoutException:
                if attempt == self.max_retries:
                    self.stats["requests_failed"] += 1
                    self.stats["errors"].append({
                        "endpoint": endpoint,
                        "error": "timeout",
                        "timestamp": datetime.now().isoformat()
                    })
                    raise NexumConnectionError(f"Timeout connecting to Nexum at {url}")
                await asyncio.sleep(2 ** attempt)
                
            except httpx.ConnectError:
                if attempt == self.max_retries:
                    self.stats["requests_failed"] += 1
                    self.stats["errors"].append({
                        "endpoint": endpoint,
                        "error": "connection_error", 
                        "timestamp": datetime.now().isoformat()
                    })
                    raise NexumConnectionError(f"Cannot connect to Nexum at {url}")
                await asyncio.sleep(2 ** attempt)
                
        # Should not reach here
        raise NexumConnectionError("Max retries exceeded")
        
    async def health_check(self) -> Dict[str, Any]:
        """Check if Nexum API is healthy"""
        try:
            return await self._make_request("GET", "/health")
        except Exception as e:
            logger.warning(f"Nexum health check failed: {e}")
            return {"status": "unhealthy", "error": str(e)}
            
    # Customer Management
    async def create_customer(self, first_name: str, last_name: str, email: str,
                            phone: Optional[str] = None, date_of_birth: Optional[str] = None,
                            address: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Create a new customer"""
        data = {
            "first_name": first_name,
            "last_name": last_name,
            "email": email
        }
        
        if phone:
            data["phone"] = phone
        if date_of_birth:
            data["date_of_birth"] = date_of_birth
        if address:
            data["address"] = address
            
        return await self._make_request("POST", "/customers", data)
        
    async def get_customer(self, customer_id: str) -> Dict[str, Any]:
        """Get customer details"""
        return await self._make_request("GET", f"/customers/{customer_id}")
        
    async def update_customer(self, customer_id: str, **updates) -> Dict[str, Any]:
        """Update customer information"""
        return await self._make_request("PUT", f"/customers/{customer_id}", updates)
        
    async def update_kyc_status(self, customer_id: str, status: str, tier: Optional[str] = None,
                              documents: Optional[List[str]] = None) -> Dict[str, Any]:
        """Update customer KYC status"""
        data = {"status": status}
        if tier:
            data["tier"] = tier
        if documents:
            data["documents"] = documents
            
        return await self._make_request("PUT", f"/customers/{customer_id}/kyc", data)
        
    # Account Management
    async def create_account(self, customer_id: str, product_type: str, currency: str, name: str,
                           account_number: Optional[str] = None, interest_rate: Optional[str] = None,
                           credit_limit: Optional[Dict[str, str]] = None,
                           minimum_balance: Optional[Dict[str, str]] = None,
                           daily_transaction_limit: Optional[Dict[str, str]] = None,
                           monthly_transaction_limit: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Create a new account"""
        data = {
            "customer_id": customer_id,
            "product_type": product_type,
            "currency": currency,
            "name": name
        }
        
        # Add optional parameters
        if account_number:
            data["account_number"] = account_number
        if interest_rate:
            data["interest_rate"] = interest_rate
        if credit_limit:
            data["credit_limit"] = credit_limit
        if minimum_balance:
            data["minimum_balance"] = minimum_balance
        if daily_transaction_limit:
            data["daily_transaction_limit"] = daily_transaction_limit
        if monthly_transaction_limit:
            data["monthly_transaction_limit"] = monthly_transaction_limit
            
        return await self._make_request("POST", "/accounts", data)
        
    async def get_account(self, account_id: str) -> Dict[str, Any]:
        """Get account details"""
        return await self._make_request("GET", f"/accounts/{account_id}")
        
    async def get_customer_accounts(self, customer_id: str) -> Dict[str, Any]:
        """Get all accounts for a customer"""
        return await self._make_request("GET", f"/customers/{customer_id}/accounts")
        
    async def get_account_balance(self, account_id: str) -> Dict[str, Any]:
        """Get account balance (included in get_account response)"""
        account_info = await self.get_account(account_id)
        return {
            "book_balance": account_info.get("book_balance"),
            "available_balance": account_info.get("available_balance")
        }
        
    # Transaction Operations
    async def deposit(self, account_id: str, amount: Union[float, str], description: str,
                     channel: str = "online", reference: Optional[str] = None) -> Dict[str, Any]:
        """Make a deposit"""
        data = {
            "account_id": account_id,
            "amount": {
                "amount": str(amount),
                "currency": "USD"
            },
            "description": description,
            "channel": channel
        }
        
        if reference:
            data["reference"] = reference
            
        return await self._make_request("POST", "/transactions/deposit", data)
        
    async def withdraw(self, account_id: str, amount: Union[float, str], description: str,
                      channel: str = "online", reference: Optional[str] = None) -> Dict[str, Any]:
        """Make a withdrawal"""
        data = {
            "account_id": account_id,
            "amount": {
                "amount": str(amount),
                "currency": "USD"
            },
            "description": description,
            "channel": channel
        }
        
        if reference:
            data["reference"] = reference
            
        return await self._make_request("POST", "/transactions/withdraw", data)
        
    async def transfer(self, from_account_id: str, to_account_id: str, amount: Union[float, str], 
                      description: str, channel: str = "online", reference: Optional[str] = None) -> Dict[str, Any]:
        """Transfer between accounts"""
        data = {
            "from_account_id": from_account_id,
            "to_account_id": to_account_id,
            "amount": {
                "amount": str(amount),
                "currency": "USD"
            },
            "description": description,
            "channel": channel
        }
        
        if reference:
            data["reference"] = reference
            
        return await self._make_request("POST", "/transactions/transfer", data)
        
    async def get_account_transactions(self, account_id: str, skip: int = 0, limit: int = 50) -> Dict[str, Any]:
        """Get transaction history for account"""
        params = {"skip": skip, "limit": limit}
        return await self._make_request("GET", f"/accounts/{account_id}/transactions", params=params)
        
    async def get_transaction(self, transaction_id: str) -> Dict[str, Any]:
        """Get transaction details (if endpoint exists)"""
        try:
            return await self._make_request("GET", f"/transactions/{transaction_id}")
        except NexumAPIError as e:
            if e.status_code == 404:
                logger.warning(f"Transaction endpoint not found: {transaction_id}")
                return {"error": "endpoint_not_found"}
            raise
            
    # Credit and Loans
    async def make_credit_payment(self, account_id: str, amount: Union[float, str],
                                 payment_date: Optional[str] = None) -> Dict[str, Any]:
        """Make a credit card payment"""
        data = {
            "account_id": account_id,
            "amount": {
                "amount": str(amount),
                "currency": "USD"
            }
        }
        
        if payment_date:
            data["payment_date"] = payment_date
            
        return await self._make_request("POST", "/credit/payment", data)
        
    async def create_loan(self, customer_id: str, loan_terms: Dict[str, Any], currency: str = "USD") -> Dict[str, Any]:
        """Create a new loan"""
        data = {
            "customer_id": customer_id,
            "terms": loan_terms,
            "currency": currency
        }
        
        return await self._make_request("POST", "/loans", data)
        
    async def make_loan_payment(self, loan_id: str, amount: Union[float, str],
                               payment_date: Optional[str] = None,
                               source_account_id: Optional[str] = None) -> Dict[str, Any]:
        """Make a loan payment"""
        data = {
            "loan_id": loan_id,
            "amount": {
                "amount": str(amount),
                "currency": "USD"
            }
        }
        
        if payment_date:
            data["payment_date"] = payment_date
        if source_account_id:
            data["source_account_id"] = source_account_id
            
        return await self._make_request("POST", "/loans/payment", data)
        
    # Statistics and monitoring
    def get_stats(self) -> Dict[str, Any]:
        """Get connector statistics"""
        total_requests = self.stats["requests_sent"]
        if total_requests > 0:
            avg_latency = self.stats["total_latency_ms"] / total_requests
            success_rate = self.stats["requests_successful"] / total_requests
        else:
            avg_latency = 0
            success_rate = 0
            
        return {
            "total_requests": total_requests,
            "successful_requests": self.stats["requests_successful"],
            "failed_requests": self.stats["requests_failed"],
            "success_rate": success_rate,
            "average_latency_ms": avg_latency,
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
            "errors": []
        }


class MockNexumConnector(NexumConnector):
    """Mock implementation of Nexum connector for dry-run mode"""
    
    def __init__(self, config: ConnectionConfig):
        super().__init__(config)
        self.customers = {}
        self.accounts = {}
        self.transactions = {}
        self.next_customer_id = 1
        self.next_account_id = 1
        self.next_transaction_id = 1
        
    async def __aenter__(self):
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass
        
    async def _make_request(self, method: str, endpoint: str, 
                          data: Optional[Dict] = None, params: Optional[Dict] = None) -> Dict[str, Any]:
        """Mock request - simulate realistic response times"""
        await asyncio.sleep(0.01 + random.uniform(0, 0.05))  # 10-60ms latency
        
        self.stats["requests_sent"] += 1
        self.stats["requests_successful"] += 1
        
        # Route to mock implementations
        if endpoint == "/health":
            return {"status": "healthy", "timestamp": datetime.now().isoformat(), "mode": "mock"}
        elif endpoint == "/customers" and method == "POST":
            return self._mock_create_customer(data)
        elif endpoint.startswith("/customers/") and method == "GET":
            customer_id = endpoint.split("/")[-1]
            return self._mock_get_customer(customer_id)
        elif endpoint == "/accounts" and method == "POST":
            return self._mock_create_account(data)
        elif endpoint.startswith("/accounts/") and not endpoint.endswith("/transactions"):
            account_id = endpoint.split("/")[-1]
            return self._mock_get_account(account_id)
        elif endpoint.startswith("/customers/") and endpoint.endswith("/accounts"):
            customer_id = endpoint.split("/")[-2]
            return self._mock_get_customer_accounts(customer_id)
        elif endpoint == "/transactions/deposit":
            return self._mock_deposit(data)
        elif endpoint == "/transactions/withdraw":
            return self._mock_withdraw(data)
        elif endpoint == "/transactions/transfer":
            return self._mock_transfer(data)
        else:
            return {"status": "ok", "message": f"Mock response for {method} {endpoint}", "data": data}
            
    def _mock_create_customer(self, data: Dict[str, Any]) -> Dict[str, Any]:
        customer_id = f"CUST_{self.next_customer_id:06d}"
        self.next_customer_id += 1
        
        self.customers[customer_id] = {
            "id": customer_id,
            "first_name": data["first_name"],
            "last_name": data["last_name"],
            "email": data["email"],
            "phone": data.get("phone"),
            "kyc_status": "pending",
            "kyc_tier": "tier_0",
            "is_active": True,
            "created_at": datetime.now().isoformat()
        }
        
        return {"customer_id": customer_id, "message": "Customer created successfully"}
        
    def _mock_get_customer(self, customer_id: str) -> Dict[str, Any]:
        if customer_id not in self.customers:
            raise NexumAPIError(404, "Customer not found")
        return self.customers[customer_id]
        
    def _mock_create_account(self, data: Dict[str, Any]) -> Dict[str, Any]:
        account_id = f"ACC_{self.next_account_id:06d}"
        account_number = f"{random.randint(100000000, 999999999)}"
        self.next_account_id += 1
        
        self.accounts[account_id] = {
            "id": account_id,
            "account_number": account_number,
            "customer_id": data["customer_id"],
            "product_type": data["product_type"],
            "currency": data["currency"],
            "name": data["name"],
            "state": "active",
            "book_balance": {"amount": "0.00", "currency": data["currency"]},
            "available_balance": {"amount": "0.00", "currency": data["currency"]},
            "created_at": datetime.now().isoformat()
        }
        
        return {
            "account_id": account_id,
            "account_number": account_number,
            "message": "Account created successfully"
        }
        
    def _mock_get_account(self, account_id: str) -> Dict[str, Any]:
        if account_id not in self.accounts:
            raise NexumAPIError(404, "Account not found")
        return self.accounts[account_id]
        
    def _mock_get_customer_accounts(self, customer_id: str) -> Dict[str, Any]:
        customer_accounts = [
            account for account in self.accounts.values()
            if account["customer_id"] == customer_id
        ]
        return {"accounts": customer_accounts}
        
    def _mock_deposit(self, data: Dict[str, Any]) -> Dict[str, Any]:
        transaction_id = f"TXN_{self.next_transaction_id:06d}"
        self.next_transaction_id += 1
        
        # Update account balance
        account_id = data["account_id"]
        if account_id in self.accounts:
            current_balance = float(self.accounts[account_id]["book_balance"]["amount"])
            amount = float(data["amount"]["amount"])
            new_balance = current_balance + amount
            
            self.accounts[account_id]["book_balance"]["amount"] = f"{new_balance:.2f}"
            self.accounts[account_id]["available_balance"]["amount"] = f"{new_balance:.2f}"
            
        return {
            "transaction_id": transaction_id,
            "state": "processed",
            "message": "Deposit processed successfully"
        }
        
    def _mock_withdraw(self, data: Dict[str, Any]) -> Dict[str, Any]:
        transaction_id = f"TXN_{self.next_transaction_id:06d}"
        self.next_transaction_id += 1
        
        # Update account balance
        account_id = data["account_id"]
        if account_id in self.accounts:
            current_balance = float(self.accounts[account_id]["book_balance"]["amount"])
            amount = float(data["amount"]["amount"])
            
            if current_balance >= amount:
                new_balance = current_balance - amount
                self.accounts[account_id]["book_balance"]["amount"] = f"{new_balance:.2f}"
                self.accounts[account_id]["available_balance"]["amount"] = f"{new_balance:.2f}"
                state = "processed"
            else:
                state = "declined"
        else:
            state = "declined"
            
        return {
            "transaction_id": transaction_id,
            "state": state,
            "message": f"Withdrawal {state}"
        }
        
    def _mock_transfer(self, data: Dict[str, Any]) -> Dict[str, Any]:
        transaction_id = f"TXN_{self.next_transaction_id:06d}"
        self.next_transaction_id += 1
        
        from_account_id = data["from_account_id"]
        to_account_id = data["to_account_id"]
        amount = float(data["amount"]["amount"])
        
        # Check balances and update
        if (from_account_id in self.accounts and 
            (to_account_id in self.accounts or to_account_id is None)):
            
            from_balance = float(self.accounts[from_account_id]["book_balance"]["amount"])
            
            if from_balance >= amount:
                # Debit from account
                new_from_balance = from_balance - amount
                self.accounts[from_account_id]["book_balance"]["amount"] = f"{new_from_balance:.2f}"
                self.accounts[from_account_id]["available_balance"]["amount"] = f"{new_from_balance:.2f}"
                
                # Credit to account (if internal transfer)
                if to_account_id and to_account_id in self.accounts:
                    to_balance = float(self.accounts[to_account_id]["book_balance"]["amount"])
                    new_to_balance = to_balance + amount
                    self.accounts[to_account_id]["book_balance"]["amount"] = f"{new_to_balance:.2f}"
                    self.accounts[to_account_id]["available_balance"]["amount"] = f"{new_to_balance:.2f}"
                    
                state = "processed"
            else:
                state = "declined"
        else:
            state = "declined"
            
        return {
            "transaction_id": transaction_id,
            "state": state,
            "message": f"Transfer {state}"
        }


# Import here to avoid circular imports
import random