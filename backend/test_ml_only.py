import requests
import json

# Test the FraudShield AI Backend (without Firebase dependencies)
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

def test_transaction_ml_only(token):
    """Test transaction processing without database"""
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test a normal transaction
    tx_data = {
        "user_id": "test_user_001",
        "amount": 150.00,
        "location": "New York, USA",
        "category": "Retail"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/transaction", json=tx_data, headers=headers, timeout=5)
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
    except requests.exceptions.Timeout:
        print("⏰ Transaction timed out (Firebase issue)")
    except Exception as e:
        print(f"❌ Transaction error: {e}")
    print()

def test_high_risk_transaction_ml_only(token):
    """Test a high-risk transaction without database"""
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test a suspicious transaction
    tx_data = {
        "user_id": "test_user_001",
        "amount": 15000.00,
        "location": "Lagos, Nigeria",
        "category": "Crypto"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/transaction", json=tx_data, headers=headers, timeout=5)
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
    except requests.exceptions.Timeout:
        print("⏰ High-risk transaction timed out (Firebase issue)")
    except Exception as e:
        print(f"❌ High-risk transaction error: {e}")
    print()

def test_ml_engine_directly():
    """Test ML engine directly"""
    print("Testing ML Engine directly...")
    try:
        from ml_engine import engine
        
        # Test normal transaction
        is_fraud, risk_score, flag_reason = engine.evaluate_transaction(
            amount=150.00,
            category="Retail",
            lat=40.7128,
            lng=-74.0060,
            user_id="test_user_001"
        )
        
        print(f"✅ ML Engine working!")
        print(f"Normal Transaction - Risk Score: {risk_score}, Is Fraud: {is_fraud}")
        
        # Test high-risk transaction
        is_fraud, risk_score, flag_reason = engine.evaluate_transaction(
            amount=15000.00,
            category="Crypto",
            lat=6.5244,
            lng=3.3792,
            user_id="test_user_001"
        )
        
        print(f"High-Risk Transaction - Risk Score: {risk_score}, Is Fraud: {is_fraud}")
        print(f"Flag Reason: {flag_reason}")
        
    except Exception as e:
        print(f"❌ ML Engine error: {e}")
    print()

if __name__ == "__main__":
    print("🧪 Testing FraudShield AI Backend (ML Focus)")
    print("=" * 55)
    
    # Test health
    test_health()
    
    # Test ML engine directly
    test_ml_engine_directly()
    
    # Test authentication
    token = test_auth()
    
    if token:
        # Test transactions (may timeout due to Firebase)
        test_transaction_ml_only(token)
        test_high_risk_transaction_ml_only(token)
    
    print("🏁 Testing completed!")
    print()
    print("📝 Note: Firebase Firestore API needs to be enabled for full functionality")
    print("🔗 Enable at: https://console.developers.google.com/apis/api/firestore.googleapis.com/overview?project=fraudshieldai-f2a10")
