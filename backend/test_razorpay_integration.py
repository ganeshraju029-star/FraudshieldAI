import requests
import json

# Test Razorpay integration with FraudShield AI
BASE_URL = "http://localhost:8000"

def test_razorpay_integration():
    print("💳 Testing Razorpay + FraudShield AI Integration")
    print("=" * 55)
    
    # Step 1: Login
    print("1. 🔐 Authenticating...")
    login_data = {"username": "admin", "password": "admin123"}
    response = requests.post(f"{BASE_URL}/api/auth/login", json=login_data)
    
    if response.status_code != 200:
        print("❌ Login failed")
        return
    
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("✅ Authentication successful")
    
    # Step 2: Test payment methods
    print("\n2. 💳 Getting payment methods...")
    response = requests.get(f"{BASE_URL}/api/payment/methods")
    if response.status_code == 200:
        methods = response.json()
        print(f"✅ Payment methods available: {len(methods.get('methods', []))}")
        for method in methods.get('methods', []):
            print(f"   - {method.get('display_name', method.get('name'))}")
    else:
        print("❌ Failed to get payment methods")
    
    # Step 3: Test safe payment
    print("\n3. ✅ Testing safe payment...")
    safe_payment = {
        "amount": 500.00,
        "user_id": "user_safe_001",
        "location": "New York, USA",
        "category": "Retail",
        "target_account": "987654321098765432"
    }
    
    response = requests.post(f"{BASE_URL}/api/payment/create-order", json=safe_payment, headers=headers)
    if response.status_code == 200:
        order = response.json()
        print(f"✅ Safe payment order created: {order['order']['order_id']}")
        print(f"   Risk Score: {order['fraud_check']['risk_score']}")
        print(f"   Status: {order['fraud_check']['status']}")
    else:
        print(f"❌ Safe payment failed: {response.status_code}")
        print(f"   Error: {response.text}")
    
    # Step 4: Test suspicious payment
    print("\n4. 🚨 Testing suspicious payment...")
    suspicious_payment = {
        "amount": 15000.00,
        "user_id": "user_suspicious_001",
        "location": "Lagos, Nigeria",
        "category": "Crypto",
        "target_account": "invalid@format"
    }
    
    response = requests.post(f"{BASE_URL}/api/payment/create-order", json=suspicious_payment, headers=headers)
    if response.status_code == 403:
        error = response.json()
        print(f"✅ Suspicious payment blocked!")
        print(f"   Risk Score: {error['detail']['risk_score']}")
        print(f"   Reason: {error['detail']['flag_reason']}")
        print(f"   Suggestion: {error['detail']['suggestion']}")
    elif response.status_code == 200:
        order = response.json()
        print(f"⚠️ Suspicious payment passed: {order['order']['order_id']}")
        print(f"   Risk Score: {order['fraud_check']['risk_score']}")
    else:
        print(f"❌ Suspicious payment error: {response.status_code}")
        print(f"   Error: {response.text}")
    
    # Step 5: Test high-risk payment
    print("\n5. 🚨 Testing high-risk payment...")
    high_risk_payment = {
        "amount": 50000.00,
        "user_id": "user_highrisk_001",
        "location": "São Paulo, Brazil",
        "category": "Gambling",
        "target_account": "123456789"  # Invalid format
    }
    
    response = requests.post(f"{BASE_URL}/api/payment/create-order", json=high_risk_payment, headers=headers)
    if response.status_code == 403:
        error = response.json()
        print(f"✅ High-risk payment blocked!")
        print(f"   Risk Score: {error['detail']['risk_score']}")
        print(f"   Reason: {error['detail']['flag_reason']}")
    elif response.status_code == 200:
        order = response.json()
        print(f"⚠️ High-risk payment passed: {order['order']['order_id']}")
    else:
        print(f"❌ High-risk payment error: {response.status_code}")
    
    # Step 6: Check payment transactions
    print("\n6. 📋 Checking payment transactions...")
    response = requests.get(f"{BASE_URL}/api/payment/transactions", headers=headers)
    if response.status_code == 200:
        transactions = response.json()
        print(f"✅ Found {transactions['total']} payment transactions")
        for tx in transactions['transactions'][:3]:
            status = "🚨" if tx.get('isFraud') else "✅"
            print(f"   {status} ₹{tx.get('amount', 0):,.2f} - {tx.get('category')} - Risk: {tx.get('riskScore', 0)}")
    else:
        print("❌ Failed to get payment transactions")
    
    # Step 7: Check analytics
    print("\n7. 📊 Checking analytics...")
    response = requests.get(f"{BASE_URL}/api/analytics", headers=headers)
    if response.status_code == 200:
        analytics = response.json()
        print(f"✅ Analytics Summary:")
        print(f"   Total Transactions: {analytics.get('total_transactions', 0)}")
        print(f"   Fraud Rate: {analytics.get('fraud_rate', 0)}%")
        print(f"   Database: {analytics.get('database_type', 'Unknown')}")
    else:
        print("❌ Failed to get analytics")
    
    print("\n🎉 Razorpay + FraudShield AI Integration Test Complete!")
    print("\n🌐 Frontend Dashboard: http://localhost:8000/static/index.html")
    print("📖 API Documentation: http://localhost:8000/docs")

if __name__ == "__main__":
    test_razorpay_integration()
