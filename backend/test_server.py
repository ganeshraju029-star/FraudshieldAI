import requests
import json

# Test all available endpoints
BASE_URL = "http://localhost:8000"

def test_all_endpoints():
    print("🛡️  FraudShield AI - Server Test")
    print("=" * 50)
    
    # Test 1: Root endpoint
    print("1. 🏠 Testing Root Endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ {data['message']}")
            print(f"   📊 Status: {data['status']}")
            print(f"   📦 Version: {data['version']}")
        else:
            print(f"   ❌ Status Code: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print()
    
    # Test 2: Health endpoint
    print("2. 🏥 Testing Health Endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/api/health")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Status: {data['status']}")
            print(f"   📦 Version: {data['version']}")
            print(f"   🤖 Models Loaded: {data['models_loaded']}")
        else:
            print(f"   ❌ Status Code: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print()
    
    # Test 3: API Documentation
    print("3. 📖 Testing API Documentation...")
    try:
        response = requests.get(f"{BASE_URL}/docs")
        if response.status_code == 200:
            print(f"   ✅ API Docs Available: {BASE_URL}/docs")
            print("   🌐 Open this URL in your browser for interactive API testing")
        else:
            print(f"   ❌ Status Code: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print()
    
    # Test 4: Authentication
    print("4. 🔐 Testing Authentication...")
    try:
        login_data = {"username": "admin", "password": "admin123"}
        response = requests.post(f"{BASE_URL}/api/auth/login", json=login_data)
        if response.status_code == 200:
            data = response.json()
            token = data['access_token']
            print(f"   ✅ Login Successful!")
            print(f"   🔑 Token: {token[:50]}...")
            return token
        else:
            print(f"   ❌ Status Code: {response.status_code}")
            print(f"   📄 Response: {response.text}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    return None

def test_with_token(token):
    print("5. 📊 Testing Protected Endpoints...")
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test Analytics
    try:
        response = requests.get(f"{BASE_URL}/api/analytics", headers=headers)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Analytics: {data.get('total_transactions', 0)} transactions")
            print(f"   🚨 Fraud Rate: {data.get('fraud_rate', 0)}%")
        else:
            print(f"   ❌ Analytics Status: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Analytics Error: {e}")
    
    print()
    print("🎉 All tests completed!")
    print()
    print("🌐 What you can do now:")
    print(f"   1. Open {BASE_URL}/docs in your browser")
    print("   2. Use the interactive API interface")
    print("   3. Test transactions with real-time fraud detection")
    print("   4. View live analytics and alerts")

if __name__ == "__main__":
    token = test_all_endpoints()
    if token:
        test_with_token(token)
    else:
        print("\n💡 If you see errors, make sure:")
        print("   ✅ Server is running on http://localhost:8000")
        print("   ✅ No firewall blocking the connection")
        print("   ✅ Try opening http://localhost:8000/docs directly in browser")
