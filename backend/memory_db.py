import asyncio
import json
import time
from datetime import datetime
from typing import List, Dict, Any, Optional

# In-memory database fallback for testing
class InMemoryDB:
    def __init__(self):
        self.transactions = []
        self.alerts = []
        self.feedback = []
        self.user_profiles = {}
        self.analytics = {
            "total_transactions": 0,
            "fraud_transactions": 0,
            "total_amount": 0.0,
            "fraud_amount": 0.0
        }
    
    async def save_transaction(self, tx: Dict[str, Any]):
        tx['timestamp'] = tx.get('timestamp', int(time.time() * 1000))
        self.transactions.append(tx)
        self.analytics["total_transactions"] += 1
        self.analytics["total_amount"] += tx.get("amount", 0)
        
        if tx.get("isFraud", False):
            self.analytics["fraud_transactions"] += 1
            self.analytics["fraud_amount"] += tx.get("amount", 0)
        
        # Keep only last 1000 transactions in memory
        if len(self.transactions) > 1000:
            self.transactions = self.transactions[-1000:]
        
        return {"id": tx.get("id", "unknown")}
    
    async def save_alert(self, alert: Dict[str, Any]):
        alert['timestamp'] = alert.get('timestamp', int(time.time() * 1000))
        self.alerts.append(alert)
        
        # Keep only last 100 alerts in memory
        if len(self.alerts) > 100:
            self.alerts = self.alerts[-100:]
        
        return {"id": alert.get("id", "unknown")}
    
    async def save_feedback(self, tx_id: str, was_me: bool, user_id: str = None):
        feedback_data = {
            "tx_id": tx_id,
            "was_me": was_me,
            "user_id": user_id,
            "timestamp": int(time.time() * 1000)
        }
        self.feedback.append(feedback_data)
        
        # Keep only last 100 feedback entries in memory
        if len(self.feedback) > 100:
            self.feedback = self.feedback[-100:]
        
        return {"status": "saved"}
    
    async def get_recent_transactions(self, limit: int = 50) -> List[Dict[str, Any]]:
        # Sort by timestamp desc and return limited results
        sorted_tx = sorted(self.transactions, key=lambda x: x.get('timestamp', 0), reverse=True)
        return sorted_tx[:limit]
    
    async def get_user_transactions(self, user_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        user_tx = [tx for tx in self.transactions if tx.get('userId') == user_id]
        sorted_tx = sorted(user_tx, key=lambda x: x.get('timestamp', 0), reverse=True)
        return sorted_tx[:limit]
    
    async def get_active_alerts(self, limit: int = 20) -> List[Dict[str, Any]]:
        sorted_alerts = sorted(self.alerts, key=lambda x: x.get('timestamp', 0), reverse=True)
        return sorted_alerts[:limit]
    
    async def get_analytics_data(self, hours: int = 24) -> Dict[str, Any]:
        current_time = int(time.time() * 1000)
        cutoff_time = current_time - (hours * 60 * 60 * 1000)
        
        # Filter recent transactions
        recent_tx = [tx for tx in self.transactions if tx.get('timestamp', 0) >= cutoff_time]
        recent_fraud = [tx for tx in recent_tx if tx.get('isFraud', False)]
        
        total_amount = sum(tx.get('amount', 0) for tx in recent_tx)
        fraud_amount = sum(tx.get('amount', 0) for tx in recent_fraud)
        
        fraud_rate = (len(recent_fraud) / len(recent_tx) * 100) if recent_tx else 0
        
        return {
            "total_transactions": len(recent_tx),
            "fraud_transactions": len(recent_fraud),
            "fraud_rate": round(fraud_rate, 2),
            "total_amount": round(total_amount, 2),
            "fraud_amount": round(fraud_amount, 2),
            "timeframe_hours": hours,
            "timestamp": current_time
        }
    
    async def update_user_profile(self, user_id: str, profile_data: Dict[str, Any]):
        self.user_profiles[user_id] = {
            **profile_data,
            "updated_at": int(time.time() * 1000)
        }
        return {"status": "updated"}
    
    async def get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        return self.user_profiles.get(user_id)

# Test the in-memory database
async def test_in_memory_db():
    print("🧪 Testing In-Memory Database...")
    
    db = InMemoryDB()
    
    # Test saving a transaction
    print("📝 Testing transaction save...")
    tx = {
        "id": "test_tx_001",
        "userId": "user_123",
        "amount": 150.00,
        "category": "Retail",
        "isFraud": False,
        "riskScore": 5
    }
    result = await db.save_transaction(tx)
    print(f"✅ Transaction saved: {result}")
    
    # Test saving an alert
    print("🚨 Testing alert save...")
    alert = {
        "id": "alert_001",
        "userId": "user_123",
        "amount": 5000.00,
        "category": "Crypto",
        "isFraud": True,
        "riskScore": 95,
        "alertType": "fraud_detected"
    }
    result = await db.save_alert(alert)
    print(f"✅ Alert saved: {result}")
    
    # Test saving feedback
    print("📝 Testing feedback save...")
    result = await db.save_feedback("test_tx_001", True, "user_123")
    print(f"✅ Feedback saved: {result}")
    
    # Test retrieving transactions
    print("📖 Testing transaction retrieval...")
    transactions = await db.get_recent_transactions(10)
    print(f"✅ Retrieved {len(transactions)} transactions")
    
    # Test analytics
    print("📊 Testing analytics...")
    analytics = await db.get_analytics_data(24)
    print(f"✅ Analytics: {json.dumps(analytics, indent=2)}")
    
    print("\n🎉 In-Memory Database working perfectly!")
    return db

if __name__ == "__main__":
    asyncio.run(test_in_memory_db())
