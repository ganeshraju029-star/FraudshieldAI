import firebase_admin
from firebase_admin import credentials, db
import asyncio
import json
import time
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor

# Initialize Firebase with Realtime Database
cred = credentials.Certificate("firebase_credentials.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://fraudshieldai-f2a10-default-rtdb.firebaseio.com/'
})

# Get Realtime Database reference
database_ref = db.reference()

class FirebaseDB:
    def __init__(self):
        self.database = database_ref
        self.executor = ThreadPoolExecutor(max_workers=4)
    
    async def save_transaction(self, tx: Dict[str, Any]):
        """Save transaction to Firebase Realtime Database"""
        try:
            # Generate unique ID if not provided
            if 'id' not in tx:
                tx['id'] = f"tx_{int(time.time() * 1000)}_{hash(str(tx)) % 10000}"
            
            # Save to transactions collection
            tx_ref = self.database.child('transactions').child(tx['id'])
            tx_ref.set(tx)
            return {"id": tx['id']}
        except Exception as e:
            print(f"Error saving transaction: {e}")
            raise
    
    async def save_alert(self, alert: Dict[str, Any]):
        """Save alert to Firebase Realtime Database"""
        try:
            # Generate unique ID if not provided
            if 'id' not in alert:
                alert['id'] = f"alert_{int(time.time() * 1000)}_{hash(str(alert)) % 10000}"
            
            # Save to alerts collection
            alert_ref = self.database.child('alerts').child(alert['id'])
            alert_ref.set(alert)
            return {"id": alert['id']}
        except Exception as e:
            print(f"Error saving alert: {e}")
            raise
    
    async def save_feedback(self, tx_id: str, was_me: bool, user_id: str = None):
        """Save feedback to Firebase Realtime Database"""
        try:
            feedback_data = {
                "tx_id": tx_id,
                "was_me": was_me,
                "user_id": user_id,
                "timestamp": int(time.time() * 1000)
            }
            
            # Save to feedback collection
            feedback_ref = self.database.child('feedback').push()
            feedback_ref.set(feedback_data)
            return {"status": "saved"}
        except Exception as e:
            print(f"Error saving feedback: {e}")
            raise
    
    async def get_recent_transactions(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent transactions from Firebase Realtime Database"""
        try:
            transactions_ref = self.database.child('transactions').limit_to_last(limit)
            transactions = transactions_ref.get()
            
            if not transactions:
                return []
            
            # Convert to list and sort by timestamp
            tx_list = []
            for tx_id, tx_data in transactions.items():
                tx_data['id'] = tx_id
                tx_list.append(tx_data)
            
            # Sort by timestamp descending
            tx_list.sort(key=lambda x: x.get('timestamp', 0), reverse=True)
            return tx_list
        except Exception as e:
            print(f"Error getting transactions: {e}")
            return []
    
    async def get_user_transactions(self, user_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Get transactions for specific user"""
        try:
            transactions_ref = self.database.child('transactions').order_by_child('userId').equal_to(user_id).limit_to_last(limit)
            transactions = transactions_ref.get()
            
            if not transactions:
                return []
            
            # Convert to list and sort by timestamp
            tx_list = []
            for tx_id, tx_data in transactions.items():
                tx_data['id'] = tx_id
                tx_list.append(tx_data)
            
            # Sort by timestamp descending
            tx_list.sort(key=lambda x: x.get('timestamp', 0), reverse=True)
            return tx_list
        except Exception as e:
            print(f"Error getting user transactions: {e}")
            return []
    
    async def get_active_alerts(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get active alerts from Firebase Realtime Database"""
        try:
            alerts_ref = self.database.child('alerts').limit_to_last(limit)
            alerts = alerts_ref.get()
            
            if not alerts:
                return []
            
            # Convert to list and sort by timestamp
            alert_list = []
            for alert_id, alert_data in alerts.items():
                alert_data['id'] = alert_id
                alert_list.append(alert_data)
            
            # Sort by timestamp descending
            alert_list.sort(key=lambda x: x.get('timestamp', 0), reverse=True)
            return alert_list
        except Exception as e:
            print(f"Error getting alerts: {e}")
            return []
    
    async def get_analytics_data(self, hours: int = 24) -> Dict[str, Any]:
        """Get analytics data from Firebase Realtime Database"""
        try:
            current_time = int(time.time() * 1000)
            cutoff_time = current_time - (hours * 60 * 60 * 1000)
            
            # Get recent transactions
            transactions_ref = self.database.child('transactions')
            all_transactions = transactions_ref.get()
            
            if not all_transactions:
                return {
                    "total_transactions": 0,
                    "fraud_transactions": 0,
                    "fraud_rate": 0.0,
                    "total_amount": 0.0,
                    "fraud_amount": 0.0,
                    "timeframe_hours": hours,
                    "timestamp": current_time
                }
            
            # Filter and analyze recent transactions
            recent_tx = []
            fraud_tx = []
            total_amount = 0.0
            fraud_amount = 0.0
            
            for tx_id, tx_data in all_transactions.items():
                tx_time = tx_data.get('timestamp', 0)
                if tx_time >= cutoff_time:
                    recent_tx.append(tx_data)
                    amount = tx_data.get('amount', 0)
                    total_amount += amount
                    
                    if tx_data.get('isFraud', False):
                        fraud_tx.append(tx_data)
                        fraud_amount += amount
            
            fraud_rate = (len(fraud_tx) / len(recent_tx) * 100) if recent_tx else 0
            
            return {
                "total_transactions": len(recent_tx),
                "fraud_transactions": len(fraud_tx),
                "fraud_rate": round(fraud_rate, 2),
                "total_amount": round(total_amount, 2),
                "fraud_amount": round(fraud_amount, 2),
                "timeframe_hours": hours,
                "timestamp": current_time
            }
        except Exception as e:
            print(f"Error getting analytics: {e}")
            return {
                "total_transactions": 0,
                "fraud_transactions": 0,
                "fraud_rate": 0.0,
                "total_amount": 0.0,
                "fraud_amount": 0.0,
                "timeframe_hours": hours,
                "timestamp": int(time.time() * 1000)
            }
    
    async def update_user_profile(self, user_id: str, profile_data: Dict[str, Any]):
        """Update user profile in Firebase Realtime Database"""
        try:
            profile_ref = self.database.child('users').child(user_id)
            profile_ref.update(profile_data)
            return {"status": "updated"}
        except Exception as e:
            print(f"Error updating user profile: {e}")
            raise
    
    async def get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user profile from Firebase Realtime Database"""
        try:
            profile_ref = self.database.child('users').child(user_id)
            profile = profile_ref.get()
            return profile
        except Exception as e:
            print(f"Error getting user profile: {e}")
            return None

# Test connection
try:
    test_ref = database_ref.child('test')
    test_ref.set({"connected": True, "timestamp": int(time.time() * 1000)})
    test_ref.delete()
    print("✅ Firebase Realtime Database connected successfully!")
except Exception as e:
    print(f"❌ Firebase Realtime Database connection failed: {e}")

# Create database instance
db = FirebaseDB()
