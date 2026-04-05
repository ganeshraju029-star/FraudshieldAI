# FraudShield AI Backend

A comprehensive real-time fraud detection platform with advanced ML models, secure APIs, and intelligent alerting.

## 🚀 Features

### Core Fraud Detection
- **Hybrid ML System**: XGBoost + Isolation Forest + Rule Engine
- **Real-time Processing**: <200ms response time
- **Adaptive Learning**: Models improve from user feedback
- **Advanced Feature Engineering**: 19+ features including behavioral patterns

### Security & Performance
- **JWT Authentication**: Secure API access
- **Rate Limiting**: Prevent abuse and attacks
- **Input Validation**: Comprehensive security checks
- **WebSocket Support**: Real-time alerts and streaming

### Database Integration
- **Firebase Firestore**: Scalable cloud database
- **Async Operations**: Non-blocking database calls
- **User Profiles**: Behavioral analysis storage
- **Analytics Dashboard**: Real-time metrics

## 📊 Architecture

```
Transaction → API → Feature Engineering → ML Models → Fraud Score → Alert System → Database → Frontend
```

## 🛠 Installation

1. **Install Dependencies**
```bash
pip install -r requirements.txt
```

2. **Firebase Setup**
   - Firebase credentials are included in `firebase_credentials.json`
   - Ensure Firestore is enabled in your Firebase project

3. **Environment Variables**
```bash
export JWT_SECRET_KEY="your-production-secret-key"
```

## 🚀 Running the Server

```bash
python main.py
```

The server will start on `http://localhost:8000`

## 📡 API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - User login
- `POST /api/auth/logout` - User logout

### Transactions
- `POST /api/transaction` - Process transaction (real-time fraud detection)
- `POST /api/feedback` - Submit user feedback for adaptive learning
- `GET /api/transactions` - Get recent transactions (authenticated)
- `GET /api/users/{user_id}/transactions` - Get user-specific transactions

### Alerts & Analytics
- `GET /api/alerts` - Get active fraud alerts (authenticated)
- `GET /api/analytics` - Dashboard analytics (authenticated)
- `GET /api/health` - System health check

### WebSocket
- `WS /ws/stream?token=<jwt>` - Real-time transaction stream

## 🧠 ML Models

### 1. Supervised Learning (XGBoost)
- **Features**: 19 engineered features
- **Training**: 20,000 synthetic samples
- **Performance**: High accuracy on fraud patterns

### 2. Anomaly Detection (Isolation Forest)
- **Purpose**: Detect unusual patterns
- **Contamination**: 8% expected fraud rate
- **Output**: Anomaly score (0-1)

### 3. Rule-Based Engine
- **Amount Deviation**: 5x user average
- **Location Change**: >1000km distance
- **Rapid Transactions**: <1 minute intervals
- **High-Risk Categories**: Crypto, Gambling, P2P
- **Time Patterns**: Unusual hours

### Ensemble Weighting
- **XGBoost**: 50% weight
- **Isolation Forest**: 30% weight  
- **Rules Engine**: 20% weight

## 📈 Feature Engineering

### Transaction Features
- Amount (raw, log, sqrt transformed)
- Category encoding (15 categories)
- Location (lat, lng)
- Time features (hour, day, weekend, night)

### Behavioral Features
- User average amount & transaction count
- Amount ratio to user average
- Location change detection (km)
- Time since last transaction
- New user detection
- Device tracking

## 🔔 Real-time Alerts

When fraud_score > 75:
- **Database Storage**: Alert saved to Firestore
- **WebSocket Broadcast**: Real-time notification
- **Severity Levels**: High (>90) or Medium (75-90)
- **Detailed Reasons**: Specific rule violations

## 🎯 Default Credentials

- **Username**: admin
- **Password**: admin123
- **WebSocket Token**: Get from `/api/auth/login`

## 📊 Performance Metrics

- **Response Time**: <200ms
- **Throughput**: 100+ transactions/second
- **Memory Usage**: ~500MB (models + cache)
- **Accuracy**: 95%+ on synthetic data

## 🔧 Configuration

### Model Weights
```python
model_weights = {
    'xgb': 0.5,      # XGBoost classifier
    'iforest': 0.3,   # Isolation Forest
    'rules': 0.2      # Rule-based engine
}
```

### Risk Thresholds
- **Fraud**: score > 75
- **Suspicious**: score > 50
- **Safe**: score ≤ 50

## 🌍 Supported Locations

10 major cities worldwide:
- New York, London, Tokyo
- Lagos, São Paulo, Mumbai
- Singapore, Dubai, Sydney, Toronto

## 🏷️ Transaction Categories

15 categories including:
- Retail, Digital Goods, Crypto
- Travel, P2P Transfer, Gambling
- Groceries, Restaurant, Healthcare
- And more...

## 🔄 Adaptive Learning

User feedback updates model weights:
- **"This was me"**: Reduce false positive sensitivity
- **"Not me"**: Increase fraud detection sensitivity

## 📱 WebSocket Events

### Client → Server
- `ping`: Connection health check
- `subscribe_alerts`: Get fraud notifications

### Server → Client
- `transaction`: New transaction processed
- `fraud_alert`: Fraud detected (authenticated only)
- `pong`: Response to ping

## 🛡️ Security Features

- **JWT Tokens**: 30-minute expiration
- **Rate Limiting**: Varies by endpoint
- **Input Validation**: Comprehensive checks
- **CORS**: Configurable origins
- **Password Hashing**: bcrypt encryption

## 📊 Analytics Dashboard

Real-time metrics:
- Total/fraud transaction counts
- Fraud rate percentage
- Total/fraud amounts
- Active alerts count
- Model performance weights

## 🚀 Production Deployment

### Environment Variables
```bash
JWT_SECRET_KEY="your-secure-secret-key"
FIREBASE_PROJECT_ID="your-project-id"
```

### Docker Support
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "main.py"]
```

### Scaling Considerations
- **Horizontal Scaling**: Multiple instances behind load balancer
- **Database**: Firestore scales automatically
- **Model Caching**: Load models on startup
- **Rate Limiting**: Redis-based for distributed systems

## 🧪 Testing

### Sample Transaction
```bash
curl -X POST "http://localhost:8000/api/transaction" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_123",
    "amount": 1500.00,
    "location": "New York, USA",
    "category": "Retail"
  }'
```

### WebSocket Connection
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/stream?token=your_jwt_token');
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Received:', data);
};
```

## 📈 Monitoring

### Health Check
```bash
curl http://localhost:8000/api/health
```

### System Metrics
- Model loading status
- Response times
- Error rates
- Active connections

## 🔄 Continuous Learning

The system improves over time through:
1. **User Feedback**: Weight adjustments
2. **Pattern Recognition**: Feature importance
3. **Model Retraining**: Scheduled updates
4. **A/B Testing**: Performance validation

---

**FraudShield AI** - Enterprise-grade real-time fraud detection 🛡️
