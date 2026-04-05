# Quick test to verify server is running
import requests

# Test health endpoint
try:
    response = requests.get("http://localhost:8000/api/health")
    if response.status_code == 200:
        health = response.json()
        print("✅ Server is running!")
        print(f"📊 Status: {health['status']}")
        print(f"📦 Version: {health['version']}")
        print(f"🤖 Models: {health['models_loaded']}")
        print(f"🔗 Database: Firebase Realtime Database")
    else:
        print("❌ Server not responding")
except requests.exceptions.ConnectionError:
    print("❌ Cannot connect to server")
    print("💡 Make sure server is running on http://localhost:8000")
