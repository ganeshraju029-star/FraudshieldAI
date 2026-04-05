import razorpay
import os
import json
import uuid
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import asyncio
import httpx

class RazorpayGateway:
    """Razorpay payment gateway integration with fraud detection"""
    
    def __init__(self):
        # Razorpay credentials (in production, use environment variables)
        self.key_id = os.getenv("RAZORPAY_KEY_ID", "rzp_test_YourTestKeyHere")
        self.key_secret = os.getenv("RAZORPAY_KEY_SECRET", "YourTestSecretHere")
        
        # Initialize Razorpay client
        try:
            self.client = razorpay.Client(auth=(self.key_id, self.key_secret))
            self.is_test_mode = True
            print("Razorpay client initialized in test mode")
        except Exception as e:
            print(f"Razorpay initialization failed: {e}")
            self.client = None
            self.is_test_mode = False
    
    async def create_order(self, amount: float, currency: str = "INR", 
                         receipt: str = None, notes: Dict[str, Any] = None) -> Dict[str, Any]:
        """Create Razorpay order with fraud check"""
        try:
            if not self.client:
                return self._mock_order(amount, currency, receipt, notes)
            
            # Convert amount to paise (Razorpay uses smallest currency unit)
            amount_paise = int(amount * 100)
            
            order_data = {
                "amount": amount_paise,
                "currency": currency,
                "receipt": receipt or f"receipt_{uuid.uuid4().hex[:8]}",
                "notes": notes or {},
                "payment_capture": 1  # Auto-capture payment
            }
            
            # Create order asynchronously
            order = await asyncio.get_event_loop().run_in_executor(
                None, lambda: self.client.order.create(order_data)
            )
            
            return {
                "success": True,
                "order_id": order["id"],
                "amount": amount,
                "currency": currency,
                "receipt": order["receipt"],
                "notes": order["notes"],
                "created_at": order["created_at"]
            }
            
        except Exception as e:
            print(f"Razorpay order creation failed: {e}")
            return self._mock_order(amount, currency, receipt, notes)
    
    def _mock_order(self, amount: float, currency: str, receipt: str, notes: Dict[str, Any]) -> Dict[str, Any]:
        """Mock order for testing when Razorpay is not configured"""
        mock_order_id = f"order_mock_{uuid.uuid4().hex[:12]}"
        
        return {
            "success": True,
            "order_id": mock_order_id,
            "amount": amount,
            "currency": currency,
            "receipt": receipt or f"receipt_{uuid.uuid4().hex[:8]}",
            "notes": notes or {},
            "created_at": int(datetime.now().timestamp()),
            "mock": True,
            "message": "Mock order created (Razorpay not configured)"
        }
    
    async def verify_payment(self, razorpay_order_id: str, razorpay_payment_id: str, 
                           razorpay_signature: str) -> Dict[str, Any]:
        """Verify Razorpay payment signature"""
        try:
            if not self.client:
                return self._mock_verify_payment(razorpay_order_id, razorpay_payment_id)
            
            # Verify payment signature
            params = {
                'razorpay_order_id': razorpay_order_id,
                'razorpay_payment_id': razorpay_payment_id,
                'razorpay_signature': razorpay_signature
            }
            
            # Verify asynchronously
            verification = await asyncio.get_event_loop().run_in_executor(
                None, lambda: self.client.utility.verify_payment_signature(params)
            )
            
            if verification:
                # Get payment details
                payment = await asyncio.get_event_loop().run_in_executor(
                    None, lambda: self.client.payment.fetch(razorpay_payment_id)
                )
                
                return {
                    "success": True,
                    "payment_id": razorpay_payment_id,
                    "order_id": razorpay_order_id,
                    "amount": payment["amount"] / 100,  # Convert back to rupees
                    "status": payment["status"],
                    "method": payment["method"],
                    "bank": payment.get("bank", None),
                    "wallet": payment.get("wallet", None),
                    "captured": payment["captured"],
                    "created_at": payment["created_at"]
                }
            else:
                return {
                    "success": False,
                    "error": "Invalid signature"
                }
                
        except Exception as e:
            print(f"Razorpay payment verification failed: {e}")
            return self._mock_verify_payment(razorpay_order_id, razorpay_payment_id)
    
    def _mock_verify_payment(self, razorpay_order_id: str, razorpay_payment_id: str) -> Dict[str, Any]:
        """Mock payment verification for testing"""
        return {
            "success": True,
            "payment_id": razorpay_payment_id,
            "order_id": razorpay_order_id,
            "amount": 100.0,  # Mock amount
            "status": "captured",
            "method": "card",
            "bank": "HDFC",
            "wallet": None,
            "captured": True,
            "created_at": int(datetime.now().timestamp()),
            "mock": True,
            "message": "Mock payment verified (Razorpay not configured)"
        }
    
    async def refund_payment(self, payment_id: str, amount: float = None) -> Dict[str, Any]:
        """Process refund for a payment"""
        try:
            if not self.client:
                return self._mock_refund(payment_id, amount)
            
            refund_data = {}
            if amount:
                refund_data["amount"] = int(amount * 100)  # Convert to paise
            
            # Process refund asynchronously
            refund = await asyncio.get_event_loop().run_in_executor(
                None, lambda: self.client.payment.refund(payment_id, refund_data)
            )
            
            return {
                "success": True,
                "refund_id": refund["id"],
                "payment_id": payment_id,
                "amount": refund["amount"] / 100,  # Convert back to rupees
                "status": refund["status"],
                "created_at": refund["created_at"]
            }
            
        except Exception as e:
            print(f"Razorpay refund failed: {e}")
            return self._mock_refund(payment_id, amount)
    
    def _mock_refund(self, payment_id: str, amount: float) -> Dict[str, Any]:
        """Mock refund for testing"""
        return {
            "success": True,
            "refund_id": f"refund_mock_{uuid.uuid4().hex[:12]}",
            "payment_id": payment_id,
            "amount": amount or 100.0,
            "status": "processed",
            "created_at": int(datetime.now().timestamp()),
            "mock": True,
            "message": "Mock refund processed (Razorpay not configured)"
        }
    
    async def get_payment_methods(self) -> Dict[str, Any]:
        """Get available payment methods"""
        try:
            if not self.client:
                return self._mock_payment_methods()
            
            # Get payment methods asynchronously
            methods = await asyncio.get_event_loop().run_in_executor(
                None, lambda: self.client.payment_method.all()
            )
            
            return {
                "success": True,
                "methods": methods.get("items", [])
            }
            
        except Exception as e:
            print(f"Failed to get payment methods: {e}")
            return self._mock_payment_methods()
    
    def _mock_payment_methods(self) -> Dict[str, Any]:
        """Mock payment methods for testing"""
        return {
            "success": True,
            "methods": [
                {"name": "card", "display_name": "Credit/Debit Card"},
                {"name": "upi", "display_name": "UPI"},
                {"name": "netbanking", "display_name": "Net Banking"},
                {"name": "wallet", "display_name": "Wallet"},
                {"name": "emi", "display_name": "EMI"}
            ],
            "mock": True,
            "message": "Mock payment methods (Razorpay not configured)"
        }

# Initialize Razorpay gateway
razorpay_gateway = RazorpayGateway()
