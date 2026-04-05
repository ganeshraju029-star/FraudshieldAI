import requests
import json

# Test the FraudShield AI Backend
BASE_URL = "http://localhost:8000"

def test_health():
    """Test health endpoint"""
    response = requests.get(f"{BASE_URL}/api/health")
    print("Health Check:", response.status_code)
    print(response.json())
    print()

def test_auth():
    """Test authentication"""
    # Login
    login_data = {"username": "admin", "password": "admin123"}
    response = requests.post(f"{BASE_URL}/api/auth/login", json=login_data)
    print("Login:", response.status_code)
    
    if response.status_code == 200:
        token = response.json()["access_token"]
        print("✅ Login successful!")
        print(f"Token: {token[:50]}...")
        print()
        return token
    else:
        print("❌ Login failed")
        print(response.text)
        return None

def test_transaction(token):
    """Test transaction processing"""
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test a normal transaction
    tx_data = {
        "user_id": "test_user_001",
        "amount": 150.00,
        "location": "New York, USA",
        "category": "Retail"
    }
    
    response = requests.post(f"{BASE_URL}/api/transaction", json=tx_data, headers=headers)
    print("Transaction:", response.status_code)
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Transaction processed!")
        print(f"Risk Score: {result['riskScore']}")
        print(f"Status: {result['status']}")
        print(f"Is Fraud: {result['isFraud']}")
    else:
        print("❌ Transaction failed")
        print(response.text)
    print()

def test_high_risk_transaction(token):
    """Test a high-risk transaction"""
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test a suspicious transaction
    tx_data = {
        "user_id": "test_user_001",
        "amount": 15000.00,
        "location": "Lagos, Nigeria",
        "category": "Crypto"
    }
    
    response = requests.post(f"{BASE_URL}/api/transaction", json=tx_data, headers=headers)
    print("High-Risk Transaction:", response.status_code)
    if response.status_code == 200:
        result = response.json()
        print(f"✅ High-risk transaction processed!")
        print(f"Risk Score: {result['riskScore']}")
        print(f"Status: {result['status']}")
        print(f"Is Fraud: {result['isFraud']}")
        print(f"Flag Reason: {result.get('flagReason', 'None')}")
    else:
        print("❌ High-risk transaction failed")
        print(response.text)
    print()

def test_analytics(token):
    """Test analytics endpoint"""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/api/analytics", headers=headers)
    print("Analytics:", response.status_code)
    if response.status_code == 200:
        data = response.json()
        print("✅ Analytics retrieved!")
        print(f"Total Transactions: {data.get('total_transactions', 0)}")
        print(f"Fraud Rate: {data.get('fraud_rate', 0)}%")
        print(f"System Status: {data.get('system_status', 'unknown')}")
    else:
        print("❌ Analytics failed")
        print(response.text)
    print()

if __name__ == "__main__":
    print("🧪 Testing FraudShield AI Backend")
    print("=" * 50)
    
    # Test health
    test_health()
    
    # Test authentication
    token = test_auth()
    
    if token:
        # Test transactions
        test_transaction(token)
        test_high_risk_transaction(token)
        
        # Test analytics
        test_analytics(token)
    
    print("🏁 Testing completed!")
