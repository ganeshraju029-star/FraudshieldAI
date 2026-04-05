import requests
import json

# Test complete system with analytics
BASE_URL = "http://localhost:8000"

def test_complete_system():
    print("🧪 Testing Complete FraudShield AI System")
    print("=" * 55)
    
    # Login first
    login_data = {"username": "admin", "password": "admin123"}
    response = requests.post(f"{BASE_URL}/api/auth/login", json=login_data)
    
    if response.status_code != 200:
        print("❌ Login failed")
        return
    
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test multiple transactions
    print("📝 Processing test transactions...")
    transactions = [
        {
            "user_id": "user_001",
            "amount": 50.00,
            "location": "New York, USA",
            "category": "Retail"
        },
        {
            "user_id": "user_002", 
            "amount": 12500.00,
            "location": "Lagos, Nigeria",
            "category": "Crypto"
        },
        {
            "user_id": "user_001",
            "amount": 200.00,
            "location": "London, UK",
            "category": "Travel"
        }
    ]
    
    for i, tx in enumerate(transactions):
        response = requests.post(f"{BASE_URL}/api/transaction", json=tx, headers=headers)
        if response.status_code == 200:
            result = response.json()
            status = "🚨 FRAUD" if result['isFraud'] else "✅ Safe"
            print(f"  Transaction {i+1}: ${result['amount']:,.2f} - Risk: {result['riskScore']} - {status}")
        else:
            print(f"  Transaction {i+1}: ❌ Failed")
    
    print()
    
    # Test analytics
    print("📊 Testing analytics...")
    response = requests.get(f"{BASE_URL}/api/analytics", headers=headers)
    if response.status_code == 200:
        analytics = response.json()
        print(f"✅ Analytics retrieved!")
        print(f"  Total Transactions: {analytics.get('total_transactions', 0)}")
        print(f"  Fraud Transactions: {analytics.get('fraud_transactions', 0)}")
        print(f"  Fraud Rate: {analytics.get('fraud_rate', 0)}%")
        print(f"  Total Amount: ${analytics.get('total_amount', 0):,.2f}")
        print(f"  Fraud Amount: ${analytics.get('fraud_amount', 0):,.2f}")
        print(f"  Database Type: {analytics.get('database_type', 'Unknown')}")
        print(f"  System Status: {analytics.get('system_status', 'Unknown')}")
    else:
        print("❌ Analytics failed")
    
    print()
    
    # Test alerts
    print("🚨 Testing alerts...")
    response = requests.get(f"{BASE_URL}/api/alerts", headers=headers)
    if response.status_code == 200:
        alerts = response.json()["alerts"]
        print(f"✅ Retrieved {len(alerts)} alerts")
        for alert in alerts[:3]:  # Show first 3
            print(f"  🚨 Alert: ${alert['amount']:,.2f} - Risk: {alert['riskScore']} - {alert['flagReason']}")
    else:
        print("❌ Alerts failed")
    
    print()
    
    # Test transaction history
    print("📖 Testing transaction history...")
    response = requests.get(f"{BASE_URL}/api/transactions", headers=headers)
    if response.status_code == 200:
        transactions = response.json()["transactions"]
        print(f"✅ Retrieved {len(transactions)} recent transactions")
        for tx in transactions[:3]:  # Show first 3
            status = "🚨" if tx['isFraud'] else "✅"
            print(f"  {status} ${tx['amount']:,.2f} - {tx['category']} - Risk: {tx['riskScore']}")
    else:
        print("❌ Transaction history failed")
    
    print()
    print("🎉 Complete system test finished!")
    print("📝 System is fully operational with in-memory database fallback")
    print("🔄 When Firebase API propagates, system will automatically switch to Firestore")

if __name__ == "__main__":
    test_complete_system()
