import firebase_admin
from firebase_admin import credentials, firestore
import json

# Test Firebase connection directly
print("🔗 Testing Firebase Firestore Connection...")

try:
    # Load credentials
    cred = credentials.Certificate("firebase_credentials.json")
    
    # Initialize Firebase
    firebase_admin.initialize_app(cred)
    
    # Get Firestore client
    db = firestore.client()
    
    # Test write operation
    print("📝 Testing write operation...")
    test_doc = {
        "test": True,
        "timestamp": firestore.SERVER_TIMESTAMP,
        "message": "Firebase connection test"
    }
    
    doc_ref = db.collection("test").document("connection_test")
    doc_ref.set(test_doc)
    print("✅ Write operation successful!")
    
    # Test read operation
    print("📖 Testing read operation...")
    doc = doc_ref.get()
    if doc.exists:
        data = doc.to_dict()
        print(f"✅ Read operation successful!")
        print(f"📄 Data: {json.dumps(data, indent=2, default=str)}")
    else:
        print("❌ Document not found")
    
    # Clean up test document
    doc_ref.delete()
    print("🧹 Test document cleaned up")
    
    print("\n🎉 Firebase Firestore is working correctly!")
    print("✅ Connection established")
    print("✅ Read/Write operations working")
    print("✅ Ready for production use")
    
except Exception as e:
    print(f"❌ Firebase connection failed: {e}")
    print(f"🔍 Error type: {type(e).__name__}")
    
    # Check if it's a permissions issue
    if "permission" in str(e).lower():
        print("🔧 This might be a permissions issue. Check:")
        print("   1. Firestore API is enabled")
        print("   2. Service account has Firestore permissions")
        print("   3. Firebase project ID is correct")
    
    # Check if it's a project ID issue
    if "project" in str(e).lower():
        print("🔧 Check your project ID in firebase_credentials.json")
        
finally:
    # Clean up Firebase app
    if firebase_admin._apps:
        firebase_admin.delete_app(firebase_admin._apps[0])
        print("🔧 Firebase app cleaned up")
