from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, EmailStr
from jose import JWTError, jwt
import hashlib
import secrets
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import asyncio
import json
import random
import uuid
import time
import os
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import numpy as np

from ml_engine import engine, LOCATIONS, CATEGORIES, HIGH_RISK_CATEGORIES
from database import db
from memory_db import InMemoryDB
from razorpay_gateway import razorpay_gateway
from graph_engine import graph_engine

# Initialize fallback database
memory_db = InMemoryDB()
firebase_available = True

# Test Firebase connection on startup
async def test_firebase_connection():
    global firebase_available
    try:
        # Try a simple Firebase operation
        await db.save_transaction({"test": True, "timestamp": int(time.time() * 1000)})
        print("Firebase Firestore connected successfully!")
        return True
    except Exception as e:
        print(f"Firebase not available: {e}")
        print("Using in-memory database as fallback")
        firebase_available = False
        return False

# Database wrapper function
async def save_to_database(data_type: str, data: dict):
    """Save to Firebase if available, otherwise use in-memory database"""
    global firebase_available
    if firebase_available:
        try:
            if data_type == "transaction":
                return await db.save_transaction(data)
            elif data_type == "alert":
                return await db.save_alert(data)
            elif data_type == "feedback":
                return await db.save_feedback(data.get("tx_id"), data.get("was_me"), data.get("user_id"))
        except Exception as e:
            print(f"Firebase error, falling back to memory: {e}")
            firebase_available = False
    
    # Fallback to in-memory database
    if data_type == "transaction":
        return await memory_db.save_transaction(data)
    elif data_type == "alert":
        return await memory_db.save_alert(data)
    elif data_type == "feedback":
        return await memory_db.save_feedback(data.get("tx_id"), data.get("was_me"), data.get("user_id"))

async def get_from_database(data_type: str, **kwargs):
    """Get from Firebase if available, otherwise use in-memory database"""
    global firebase_available
    if firebase_available:
        try:
            if data_type == "transactions":
                return await db.get_recent_transactions(kwargs.get("limit", 50))
            elif data_type == "user_transactions":
                return await db.get_user_transactions(kwargs.get("user_id"), kwargs.get("limit", 20))
            elif data_type == "alerts":
                return await db.get_active_alerts(kwargs.get("limit", 20))
            elif data_type == "analytics":
                return await db.get_analytics_data(kwargs.get("hours", 24))
        except Exception as e:
            print(f"Firebase error, falling back to memory: {e}")
            firebase_available = False
    
    # Fallback to in-memory database
    if data_type == "transactions":
        return await memory_db.get_recent_transactions(kwargs.get("limit", 50))
    elif data_type == "user_transactions":
        return await memory_db.get_user_transactions(kwargs.get("user_id"), kwargs.get("limit", 20))
    elif data_type == "alerts":
        return await memory_db.get_active_alerts(kwargs.get("limit", 20))
    elif data_type == "analytics":
        return await memory_db.get_analytics_data(kwargs.get("hours", 24))

# Security Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-here-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Rate Limiting
limiter = Limiter(key_func=get_remote_address)
app = FastAPI(title="FraudShield AI Backend")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Security
security = HTTPBearer()

def hash_password(password: str) -> str:
    """Simple password hashing using SHA-256 with salt"""
    salt = secrets.token_hex(16)
    return hashlib.sha256(f"{salt}{password}".encode()).hexdigest() + ":" + salt

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    try:
        hash_part, salt = hashed_password.split(":")
        return hash_part == hashlib.sha256(f"{salt}{plain_password}".encode()).hexdigest()
    except:
        return False

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        token = credentials.credentials
        if token in blacklisted_tokens:
            raise credentials_exception
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = users_db.get(username)
    if user is None:
        raise credentials_exception
    return user

# Models
class TransactionRequest(BaseModel):
    user_id: str
    amount: float
    location: str
    category: str
    target_account: Optional[str] = None
    device_id: Optional[str] = None
    biometrics: Optional[Dict[str, Any]] = None

class FeedbackRequest(BaseModel):
    transaction_id: str
    was_me: bool
    user_id: Optional[str] = None

class PaymentRequest(BaseModel):
    amount: float
    currency: str = "INR"
    receipt: Optional[str] = None
    notes: Optional[Dict[str, Any]] = None
    user_id: str
    location: str
    category: str
    target_account: Optional[str] = None
    device_id: Optional[str] = None
    biometrics: Optional[Dict[str, Any]] = None

class PaymentVerification(BaseModel):
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str

class RefundRequest(BaseModel):
    payment_id: str
    amount: Optional[float] = None
    reason: Optional[str] = None

class UserLogin(BaseModel):
    username: str
    password: str

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

# In-memory user store (in production, use database)
users_db = {}
blacklisted_tokens = set()

# WebSockets Manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []
        self.authenticated_connections: Dict[WebSocket, str] = {}

    async def connect(self, websocket: WebSocket, token: Optional[str] = None):
        await websocket.accept()
        
        # Validate token if provided
        if token:
            try:
                payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
                username = payload.get("sub")
                if username and username in users_db:
                    self.authenticated_connections[websocket] = username
            except JWTError:
                pass
        
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        if websocket in self.authenticated_connections:
            del self.authenticated_connections[websocket]

    async def broadcast(self, message: dict):
        dead_connections = []
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(message))
            except Exception:
                dead_connections.append(connection)
        for dc in dead_connections:
            self.disconnect(dc)

    async def broadcast_authenticated(self, message: dict):
        """Broadcast only to authenticated connections"""
        dead_connections = []
        for connection, username in self.authenticated_connections.items():
            try:
                await connection.send_text(json.dumps(message))
            except Exception:
                dead_connections.append(connection)
        for dc in dead_connections:
            self.disconnect(dc)

manager = ConnectionManager()

# Authentication Routes
@app.post("/api/auth/register")
@limiter.limit("5/minute")
async def register(request: Request, user: UserCreate):
    if user.username in users_db:
        raise HTTPException(
            status_code=400,
            detail="Username already registered"
        )
    
    hashed_password = get_password_hash(user.password)
    users_db[user.username] = {
        "username": user.username,
        "email": user.email,
        "hashed_password": hashed_password,
        "created_at": datetime.now()
    }
    
    return {"message": "User registered successfully"}

@app.post("/api/auth/login")
@limiter.limit("10/minute")
async def login(request: Request, user_credentials: UserLogin):
    user = users_db.get(user_credentials.username)
    if not user or not verify_password(user_credentials.password, user["hashed_password"]):
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user_credentials.username}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/api/auth/logout")
async def logout(current_user: dict = Depends(get_current_user)):
    # In a real implementation, you'd blacklist the token
    return {"message": "Successfully logged out"}

# Transaction Processing
@app.post("/api/transaction")
@limiter.limit("100/minute")
async def process_transaction(request: Request, req: TransactionRequest):
    # Input validation
    if req.amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")
    
    if req.category not in CATEGORIES:
        raise HTTPException(status_code=400, detail=f"Invalid category. Must be one of: {CATEGORIES}")
    
    # Lookup lat lng from location name
    lat, lng = 0.0, 0.0
    location_found = False
    for loc in LOCATIONS:
        if loc['name'] == req.location:
            lat, lng = loc['lat'], loc['lng']
            location_found = True
            break
    
    if not location_found:
        raise HTTPException(status_code=400, detail="Invalid location")
    
    # Process through ML engine normally
    is_fraud, risk_score, flag_reason = engine.evaluate_transaction(
        amount=req.amount,
        category=req.category,
        lat=lat,
        lng=lng,
        user_id=req.user_id,
        device_id=req.device_id,
        biometrics=req.biometrics
    )

    # Hard-coded rules for Target Account tracking the user request
    import re
    if req.target_account:
        target = req.target_account.strip()
        # Basic validation: either an account number matching 9-18 digits, or a valid UPI format pattern (user@bank)
        is_upi = "@" in target
        is_valid_account = bool(re.match(r'^\d{9,18}$', target))
        is_valid_upi = bool(re.match(r'^[a-zA-Z0-9.\-_]{2,256}@[a-zA-Z]{2,64}$', target))
        
        if not (is_valid_account or is_valid_upi):
            is_fraud = True
            risk_score = 99
            flag_reason = "Invalid Destination Account / UPI Format"

    tx_doc = {
        "id": f"tx_{uuid.uuid4().hex[:8]}",
        "userId": req.user_id,
        "amount": req.amount,
        "location": req.location,
        "lat": lat,
        "lng": lng,
        "category": req.category,
        "target_account": req.target_account,
        "device_id": req.device_id,
        "timestamp": int(time.time() * 1000),
        "riskScore": risk_score,
        "isFraud": bool(is_fraud),
        "status": 'fraud' if is_fraud else ('suspicious' if risk_score > 50 else 'safe'),
        "flagReason": flag_reason if is_fraud else None
    }

    # Save to database
    await save_to_database("transaction", tx_doc)
    
    # Create alert if fraud detected
    if is_fraud:
        alert_doc = tx_doc.copy()
        alert_doc["alertType"] = "fraud_detected"
        alert_doc["severity"] = "high" if risk_score > 90 else "medium"
        await save_to_database("alert", alert_doc)
        
        # Broadcast fraud alert
        await manager.broadcast({
            "type": "fraud_alert",
            "data": alert_doc
        })
    
    # Broadcast transaction to all connections
    await manager.broadcast({
        "type": "transaction",
        "data": tx_doc
    })
    
    return tx_doc

@app.post("/api/feedback")
@limiter.limit("50/minute")
async def process_feedback(request: Request, req: FeedbackRequest):
    await save_to_database("feedback", {
        "tx_id": req.transaction_id,
        "was_me": req.was_me,
        "user_id": req.user_id
    })
    
    # Adaptive learning
    if req.user_id:
        engine.adaptive_learning_update(req.transaction_id, req.was_me, req.user_id)
    
    return {"status": "feedback logged"}

# Data Retrieval Endpoints
@app.get("/api/transactions")
@limiter.limit("30/minute")
async def get_transactions(request: Request, limit: int = 50, current_user: dict = Depends(get_current_user)):
    transactions = await get_from_database("transactions", limit=limit)
    return {"transactions": transactions}

@app.get("/api/users/{user_id}/transactions")
@limiter.limit("20/minute")
async def get_user_transactions(request: Request, user_id: str, limit: int = 20, current_user: dict = Depends(get_current_user)):
    transactions = await get_from_database("user_transactions", user_id=user_id, limit=limit)
    return {"transactions": transactions}

@app.get("/api/alerts")
@limiter.limit("30/minute")
async def get_alerts(request: Request, limit: int = 20, current_user: dict = Depends(get_current_user)):
    alerts = await get_from_database("alerts", limit=limit)
    return {"alerts": alerts}

@app.get("/api/analytics")
@limiter.limit("10/minute")
async def get_analytics(request: Request, hours: int = 24, current_user: dict = Depends(get_current_user)):
    analytics_data = await get_from_database("analytics", hours=hours)
    
    # Add additional analytics
    analytics_data.update({
        "total_users": len(engine.user_history),
        "model_weights": engine.model_weights,
        "high_risk_categories": HIGH_RISK_CATEGORIES,
        "system_status": "healthy",
        "database_type": "Firebase" if firebase_available else "In-Memory"
    })
    
    return analytics_data

# Payment Processing Endpoints
@app.post("/api/payment/create-order")
@limiter.limit("30/minute")
async def create_payment_order(request: Request, payment_req: PaymentRequest):
    """Create Razorpay order with fraud detection"""
    # Input validation
    if payment_req.amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")
    
    if payment_req.category not in CATEGORIES:
        raise HTTPException(status_code=400, detail=f"Invalid category. Must be one of: {CATEGORIES}")
    
    # Lookup lat lng from location name
    lat, lng = 0.0, 0.0
    location_found = False
    for loc in LOCATIONS:
        if loc['name'] == payment_req.location:
            lat, lng = loc['lat'], loc['lng']
            location_found = True
            break
    
    if not location_found:
        raise HTTPException(status_code=400, detail="Invalid location")
    
    # Process through ML engine for fraud detection
    is_fraud, risk_score, flag_reason = engine.evaluate_transaction(
        amount=payment_req.amount,
        category=payment_req.category,
        lat=lat,
        lng=lng,
        user_id=payment_req.user_id,
        device_id=payment_req.device_id,
        biometrics=payment_req.biometrics
    )

    # Hard-coded rules for Target Account tracking
    import re
    if payment_req.target_account:
        target = payment_req.target_account.strip()
        # Basic validation: either an account number matching 9-18 digits, or a valid UPI format pattern (user@bank)
        is_upi = "@" in target
        is_valid_account = bool(re.match(r'^\d{9,18}$', target))
        is_valid_upi = bool(re.match(r'^[a-zA-Z0-9.\-_]{2,256}@[a-zA-Z]{2,64}$', target))
        
        if not (is_valid_account or is_valid_upi):
            is_fraud = True
            risk_score = 99
            flag_reason = "Invalid Destination Account / UPI Format"

    # If fraud detected, block payment creation
    if is_fraud and risk_score > 80:
        # Save fraud attempt
        fraud_attempt = {
            "id": f"fraud_{uuid.uuid4().hex[:8]}",
            "userId": payment_req.user_id,
            "amount": payment_req.amount,
            "location": payment_req.location,
            "lat": lat,
            "lng": lng,
            "category": payment_req.category,
            "target_account": payment_req.target_account,
            "device_id": payment_req.device_id,
            "timestamp": int(time.time() * 1000),
            "riskScore": risk_score,
            "isFraud": True,
            "status": 'blocked',
            "flagReason": flag_reason,
            "payment_status": "blocked_by_fraud_detection"
        }
        
        await save_to_database("transaction", fraud_attempt)
        
        # Create fraud alert
        alert_doc = fraud_attempt.copy()
        alert_doc["alertType"] = "payment_blocked"
        alert_doc["severity"] = "high"
        await save_to_database("alert", alert_doc)
        
        # Broadcast fraud alert
        await manager.broadcast({
            "type": "fraud_alert",
            "data": alert_doc
        })
        
        raise HTTPException(
            status_code=403,
            detail={
                "error": "Payment blocked due to fraud detection",
                "risk_score": risk_score,
                "flag_reason": flag_reason,
                "suggestion": "Please verify your transaction details or contact support"
            }
        )
    
    # Prepare notes for Razorpay
    notes = payment_req.notes or {}
    notes.update({
        "user_id": payment_req.user_id,
        "location": payment_req.location,
        "category": payment_req.category,
        "target_account": payment_req.target_account,
        "device_id": payment_req.device_id,
        "fraud_risk_score": risk_score,
        "fraud_check_passed": True
    })
    
    # Create Razorpay order
    try:
        order = await razorpay_gateway.create_order(
            amount=payment_req.amount,
            currency=payment_req.currency,
            receipt=payment_req.receipt,
            notes=notes
        )
        
        # Save order details to database
        order_doc = {
            "id": order["order_id"],
            "userId": payment_req.user_id,
            "amount": payment_req.amount,
            "currency": payment_req.currency,
            "location": payment_req.location,
            "lat": lat,
            "lng": lng,
            "category": payment_req.category,
            "target_account": payment_req.target_account,
            "device_id": payment_req.device_id,
            "timestamp": int(time.time() * 1000),
            "riskScore": risk_score,
            "isFraud": False,
            "status": 'order_created',
            "payment_status": "pending",
            "razorpay_order_id": order["order_id"],
            "notes": notes
        }
        
        await save_to_database("transaction", order_doc)
        
        return {
            "success": True,
            "order": order,
            "fraud_check": {
                "passed": True,
                "risk_score": risk_score,
                "status": "safe"
            },
            "next_steps": {
                "frontend": "Use order_id and key_id to initialize Razorpay checkout",
                "backend": "Verify payment signature after completion"
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Payment order creation failed: {str(e)}")

@app.post("/api/payment/verify")
@limiter.limit("50/minute")
async def verify_payment(request: Request, verification: PaymentVerification):
    """Verify Razorpay payment and update transaction status"""
    try:
        # Verify payment with Razorpay
        payment_result = await razorpay_gateway.verify_payment(
            verification.razorpay_order_id,
            verification.razorpay_payment_id,
            verification.razorpay_signature
        )
        
        if not payment_result["success"]:
            raise HTTPException(status_code=400, detail="Payment verification failed")
        
        # Update transaction in database
        transaction_update = {
            "payment_id": payment_result["payment_id"],
            "payment_status": "verified",
            "payment_method": payment_result.get("method"),
            "payment_bank": payment_result.get("bank"),
            "payment_wallet": payment_result.get("wallet"),
            "status": "completed" if payment_result.get("captured") else "pending",
            "updated_at": int(time.time() * 1000)
        }
        
        # Find and update the transaction
        transactions = await get_from_database("transactions", limit=100)
        for tx in transactions:
            if tx.get("razorpay_order_id") == verification.razorpay_order_id:
                # Update transaction
                tx.update(transaction_update)
                await save_to_database("transaction", tx)
                
                # Broadcast successful payment
                await manager.broadcast({
                    "type": "payment_completed",
                    "data": tx
                })
                
                return {
                    "success": True,
                    "message": "Payment verified successfully",
                    "transaction": tx,
                    "payment_details": payment_result
                }
        
        raise HTTPException(status_code=404, detail="Transaction not found")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Payment verification failed: {str(e)}")

@app.post("/api/payment/refund")
@limiter.limit("20/minute")
async def process_refund(request: Request, refund_req: RefundRequest, current_user: dict = Depends(get_current_user)):
    """Process refund for a payment"""
    try:
        # Process refund with Razorpay
        refund_result = await razorpay_gateway.refund_payment(
            refund_req.payment_id,
            refund_req.amount
        )
        
        if not refund_result["success"]:
            raise HTTPException(status_code=400, detail="Refund processing failed")
        
        # Update transaction status
        transactions = await get_from_database("transactions", limit=100)
        for tx in transactions:
            if tx.get("payment_id") == refund_req.payment_id:
                # Update transaction with refund details
                refund_update = {
                    "refund_id": refund_result["refund_id"],
                    "refund_amount": refund_result["amount"],
                    "refund_status": refund_result["status"],
                    "status": "refunded",
                    "updated_at": int(time.time() * 1000),
                    "refund_reason": refund_req.reason
                }
                
                tx.update(refund_update)
                await save_to_database("transaction", tx)
                
                # Broadcast refund notification
                await manager.broadcast({
                    "type": "payment_refunded",
                    "data": tx
                })
                
                return {
                    "success": True,
                    "message": "Refund processed successfully",
                    "refund_details": refund_result,
                    "transaction": tx
                }
        
        raise HTTPException(status_code=404, detail="Transaction not found")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Refund processing failed: {str(e)}")

@app.get("/api/payment/methods")
@limiter.limit("10/minute")
async def get_payment_methods(request: Request):
    """Get available payment methods"""
    try:
        methods = await razorpay_gateway.get_payment_methods()
        return methods
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get payment methods: {str(e)}")

@app.get("/api/payment/transactions")
@limiter.limit("30/minute")
async def get_payment_transactions(request: Request, limit: int = 20, current_user: dict = Depends(get_current_user)):
    """Get payment transactions"""
    transactions = await get_from_database("transactions", limit=limit)
    
    # Filter only payment transactions (those with razorpay_order_id)
    payment_transactions = [
        tx for tx in transactions 
        if tx.get("razorpay_order_id") or tx.get("payment_id")
    ]
    
    return {
        "transactions": payment_transactions,
        "total": len(payment_transactions)
    }

@app.get("/api/xai/explain/{tx_id}")
@limiter.limit("20/minute")
async def get_xai_explanation(request: Request, tx_id: str):
    transactions = await get_from_database("transactions", limit=100)
    tx = next((t for t in transactions if t.get("id") == tx_id or t.get("razorpay_order_id") == tx_id), None)
    if not tx:
        return {"explanation": "Transaction not found or too old to analyze."}
    
    explanation = engine.generate_xai_explanation(tx, tx.get("riskScore", 0), tx.get("flagReason"))
    return {"explanation": explanation}

is_chaos_running = False

@app.post("/api/admin/chaos-mode")
async def trigger_chaos_mode(request: Request):
    global is_chaos_running
    is_chaos_running = True
    async def run_chaos():
        global is_chaos_running
        for _ in range(5): # Decreased to 5 transactions
            if not is_chaos_running:
                break
            await asyncio.sleep(random.uniform(0.2, 0.6))
            loc = random.choice(LOCATIONS)
            cat = random.choice(CATEGORIES)
            amt = random.uniform(5000, 50000)
            uid = f"usr_chaos_{random.randint(1, 5)}"
            device_id = f"device_chaos_{random.randint(1, 3)}"
            target_account = f"account_{random.randint(1, 5)}"
            
            is_fraud, risk, flag = engine.evaluate_transaction(
                amt, cat, loc['lat'], loc['lng'], uid, device_id, 
                biometrics={"typingSpeedMs": 5, "mouseJitter": 0.1}
            )
            
            tx_doc = {
                "id": f"tx_chaos_{uuid.uuid4().hex[:8]}",
                "userId": uid,
                "amount": amt,
                "location": loc['name'],
                "lat": loc['lat'],
                "lng": loc['lng'],
                "category": cat,
                "target_account": target_account,
                "device_id": device_id,
                "timestamp": int(time.time() * 1000),
                "riskScore": risk,
                "isFraud": bool(is_fraud),
                "status": 'fraud',
                "flagReason": flag,
                "simulated": True,
                "is_chaos": True
            }
            
            await save_to_database("transaction", tx_doc)
            
            alert_doc = tx_doc.copy()
            alert_doc["alertType"] = "chaos_fraud_detected"
            alert_doc["severity"] = "high"
            await save_to_database("alert", alert_doc)
            
            await manager.broadcast({"type": "fraud_alert", "data": alert_doc})
            await manager.broadcast({"type": "transaction", "data": tx_doc})
        
        is_chaos_running = False

    asyncio.create_task(run_chaos())
    return {"status": "Chaos mode launched"}

@app.post("/api/admin/chaos-mode/stop")
async def stop_chaos_mode(request: Request):
    global is_chaos_running
    is_chaos_running = False
    return {"status": "Chaos mode stopped"}

@app.get("/api/analytics/graph")
@limiter.limit("100/minute")
async def get_topology_graph(request: Request):
    transactions = await get_from_database("transactions", limit=200)
    graph_data = graph_engine.evaluate_topology(transactions)
    return graph_data

@app.post("/api/payment/pre-flight")
@limiter.limit("30/minute")
async def pre_flight_check(request: Request, body: Dict[str, Any]):
    biometrics = body.get("biometrics", {})
    typing_speed = biometrics.get('typingSpeedMs', 100)
    mouse_jitter = biometrics.get('mouseJitter', 10)
    
    allow_all = True
    if typing_speed < 20 or mouse_jitter < 0.5:
        allow_all = False
        
    return {"allowed_methods": ["upi", "netbanking"] if not allow_all else ["card", "upi", "netbanking", "wallet"]}

@app.get("/")
async def root():
    """Root endpoint - serve frontend dashboard"""
    return {
        "message": "FraudShield AI - Real-time Fraud Detection API",
        "status": "running",
        "version": "1.0.0",
        "frontend": "/static/index.html",
        "api_docs": "/docs",
        "endpoints": {
            "documentation": "/docs",
            "health": "/api/health",
            "auth": "/api/auth/login",
            "transactions": "/api/transaction",
            "payment_create": "/api/payment/create-order",
            "payment_verify": "/api/payment/verify",
            "payment_refund": "/api/payment/refund",
            "payment_methods": "/api/payment/methods",
            "analytics": "/api/analytics",
            "websocket": "/ws/stream?token=<jwt>"
        },
        "quick_start": {
            "login": {
                "url": "/api/auth/login",
                "method": "POST",
                "body": {"username": "admin", "password": "admin123"}
            },
            "test_payment": {
                "url": "/api/payment/create-order", 
                "method": "POST",
                "headers": {"Authorization": "Bearer <token>"},
                "body": {"amount": 100.0, "user_id": "test_user", "location": "New York, USA", "category": "Retail"}
            }
        }
    }

@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": int(time.time() * 1000),
        "version": "1.0.0",
        "models_loaded": engine.xgb is not None and engine.iforest is not None
    }

# WebSocket endpoint
@app.websocket("/ws/stream")
async def websocket_endpoint(websocket: WebSocket):
    # Get token from query params
    token = websocket.query_params.get("token")
    await manager.connect(websocket, token)
    
    try:
        while True:
            # Keep connection alive and handle incoming messages
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                
                # Handle different message types
                if message.get("type") == "ping":
                    await websocket.send_text(json.dumps({"type": "pong"}))
                elif message.get("type") == "subscribe_alerts":
                    # Send recent alerts to new subscriber
                    if websocket in manager.authenticated_connections:
                        alerts = await db.get_active_alerts(10)
                        await websocket.send_text(json.dumps({
                            "type": "initial_alerts",
                            "data": alerts
                        }))
                        
            except json.JSONDecodeError:
                pass  # Ignore invalid JSON
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# Background simulation
async def simulate_global_transactions():
    """Background task to simulate realistic transaction traffic"""
    while True:
        await asyncio.sleep(random.uniform(1.0, 4.0))  # Variable interval
        
        # Generate realistic transaction
        loc = random.choice(LOCATIONS)
        cat = random.choice(CATEGORIES)
        
        # Realistic amount distribution
        if random.random() < 0.7:  # 70% normal transactions
            amt = np.random.lognormal(mean=4, sigma=1.5)
            amt = max(1, min(amt, 2000))
        else:  # 30% higher amounts
            amt = random.uniform(500, 5000)
        
        uid = f"usr_{random.randint(1, 200)}"
        device_id = f"device_{random.randint(1, 100)}"
        
        # Process through engine
        is_fraud, risk, flag = engine.evaluate_transaction(amt, cat, loc['lat'], loc['lng'], uid, device_id)
        
        # Occasionally force fraud for testing
        if random.random() < 0.02:  # 2% forced fraud
            amt = random.uniform(10000, 30000)
            is_fraud, risk, flag = engine.evaluate_transaction(amt, cat, loc['lat'], loc['lng'], uid, device_id)
        
        tx_doc = {
            "id": f"tx_sim_{uuid.uuid4().hex[:8]}",
            "userId": uid,
            "amount": amt,
            "location": loc['name'],
            "lat": loc['lat'],
            "lng": loc['lng'],
            "category": cat,
            "device_id": device_id,
            "timestamp": int(time.time() * 1000),
            "riskScore": risk,
            "isFraud": bool(is_fraud),
            "status": 'fraud' if is_fraud else ('suspicious' if risk > 50 else 'safe'),
            "flagReason": flag if is_fraud else None,
            "simulated": True
        }
        
        # Broadcast simulation
        await manager.broadcast({
            "type": "transaction",
            "data": tx_doc
        })

@app.on_event("startup")
async def startup_event():
    # Test Firebase connection
    await test_firebase_connection()
    
    # Initialize admin user if not exists
    if "admin" not in users_db:
        users_db["admin"] = {
            "username": "admin",
            "email": "admin@fraudshield.ai",
            "hashed_password": hash_password("admin123"),
            "created_at": datetime.now()
        }
    
    # Start background simulation
    asyncio.create_task(simulate_global_transactions())
    
    print("FraudShield AI Backend started successfully!")
    print("Default admin credentials: admin / admin123")
    print("WebSocket endpoint: ws://localhost:8000/ws/stream?token=<jwt_token>")
    print("API Documentation: http://localhost:8000/docs")
    print(f"Database: {'Firebase Firestore' if firebase_available else 'In-Memory (Fallback)'}")
    if not firebase_available:
        print("Firebase API still propagating. System will auto-switch when available.")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
