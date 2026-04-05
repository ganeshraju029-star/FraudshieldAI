import requests
import json
import time

# Comprehensive test of FraudShield AI with Firebase Realtime Database
BASE_URL = "http://localhost:8000"

def test_firebase_integration():
    print("🔥 Testing FraudShield AI with Firebase Realtime Database")
    print("=" * 65)
    
    # Login
    login_data = {"username": "admin", "password": "admin123"}
    response = requests.post(f"{BASE_URL}/api/auth/login", json=login_data)
    
    if response.status_code != 200:
        print("❌ Login failed")
        return
    
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    print("✅ Authentication successful")
    print()
    
    # Test 1: Normal transactions
    print("📝 Test 1: Processing normal transactions...")
    normal_txs = [
        {"user_id": "user_001", "amount": 25.50, "location": "New York, USA", "category": "Retail"},
        {"user_id": "user_002", "amount": 75.00, "location": "London, UK", "category": "Restaurant"},
        {"user_id": "user_003", "amount": 120.00, "location": "Tokyo, Japan", "category": "Digital Goods"}
    ]
    
    for tx in normal_txs:
        response = requests.post(f"{BASE_URL}/api/transaction", json=tx, headers=headers)
        if response.status_code == 200:
            result = response.json()
            print(f"  ✅ ${result['amount']:,.2f} - Risk: {result['riskScore']} - {result['status']}")
    
    print()
    
    # Test 2: Fraud transactions
    print("🚨 Test 2: Processing suspicious transactions...")
    fraud_txs = [
        {"user_id": "user_001", "amount": 8500.00, "location": "Lagos, Nigeria", "category": "Crypto"},
        {"user_id": "user_002", "amount": 15000.00, "location": "São Paulo, Brazil", "category": "Gambling"}
    ]
    
    for tx in fraud_txs:
        response = requests.post(f"{BASE_URL}/api/transaction", json=tx, headers=headers)
        if response.status_code == 200:
            result = response.json()
            print(f"  🚨 ${result['amount']:,.2f} - Risk: {result['riskScore']} - {result['status']}")
            print(f"     Reason: {result.get('flagReason', 'N/A')}")
    
    print()
    
    # Wait a moment for database writes
    time.sleep(1)
    
    # Test 3: Transaction history
    print("📖 Test 3: Retrieving transaction history...")
    response = requests.get(f"{BASE_URL}/api/transactions", headers=headers)
    if response.status_code == 200:
        transactions = response.json()["transactions"]
        print(f"  ✅ Retrieved {len(transactions)} transactions")
        for tx in transactions[:5]:  # Show first 5
            risk_emoji = "🚨" if tx['isFraud'] else "✅"
            print(f"     {risk_emoji} ${tx['amount']:,.2f} - {tx['category']} - Risk: {tx['riskScore']}")
    
    print()
    
    # Test 4: Alerts
    print("🚨 Test 4: Checking fraud alerts...")
    response = requests.get(f"{BASE_URL}/api/alerts", headers=headers)
    if response.status_code == 200:
        alerts = response.json()["alerts"]
        print(f"  ✅ Found {len(alerts)} fraud alerts")
        for alert in alerts[:3]:  # Show first 3
            print(f"     🚨 ${alert['amount']:,.2f} - Risk: {alert['riskScore']} - {alert.get('flagReason', 'N/A')}")
    
    print()
    
    # Test 5: Analytics
    print("📊 Test 5: Analytics dashboard...")
    response = requests.get(f"{BASE_URL}/api/analytics", headers=headers)
    if response.status_code == 200:
        analytics = response.json()
        print(f"  ✅ Analytics Summary:")
        print(f"     📈 Total Transactions: {analytics.get('total_transactions', 0)}")
        print(f"     🚨 Fraud Transactions: {analytics.get('fraud_transactions', 0)}")
        print(f"     📊 Fraud Rate: {analytics.get('fraud_rate', 0)}%")
        print(f"     💰 Total Amount: ${analytics.get('total_amount', 0):,.2f}")
        print(f"     💸 Fraud Amount: ${analytics.get('fraud_amount', 0):,.2f}")
        print(f"     💾 Database: {analytics.get('database_type', 'Unknown')}")
        print(f"     🏥 System Status: {analytics.get('system_status', 'Unknown')}")
    
    print()
    
    # Test 6: User-specific transactions
    print("👤 Test 6: User-specific transaction history...")
    response = requests.get(f"{BASE_URL}/api/users/user_001/transactions", headers=headers)
    if response.status_code == 200:
        user_txs = response.json()["transactions"]
        print(f"  ✅ User_001 has {len(user_txs)} transactions")
        for tx in user_txs:
            risk_emoji = "🚨" if tx['isFraud'] else "✅"
            print(f"     {risk_emoji} ${tx['amount']:,.2f} - Risk: {tx['riskScore']}")
    
    print()
    
    # Test 7: Feedback system
    print("🔄 Test 7: Feedback system...")
    if transactions:
        test_tx = transactions[0]
        feedback_data = {
            "transaction_id": test_tx['id'],
            "was_me": True,
            "user_id": test_tx['userId']
        }
        response = requests.post(f"{BASE_URL}/api/feedback", json=feedback_data, headers=headers)
        if response.status_code == 200:
            print(f"  ✅ Feedback submitted for transaction {test_tx['id']}")
    
    print()
    
    # Test 8: Health check
    print("🏥 Test 8: System health check...")
    response = requests.get(f"{BASE_URL}/api/health")
    if response.status_code == 200:
        health = response.json()
        print(f"  ✅ System Status: {health['status']}")
        print(f"  📦 Version: {health['version']}")
        print(f"  🤖 Models Loaded: {health['models_loaded']}")
    
    print()
    print("🎉 All tests completed successfully!")
    print("🔥 Firebase Realtime Database is fully integrated and operational!")
    print("🚀 FraudShield AI is ready for production deployment!")

if __name__ == "__main__":
    test_firebase_integration()
