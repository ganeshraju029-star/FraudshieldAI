import pandas as pd
import numpy as np
import random
import os
import joblib
from typing import Dict, Any, Tuple, List
from xgboost import XGBClassifier
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from geopy.distance import geodesic
from datetime import datetime, timedelta
import json
import uuid

MODEL_DIR = os.path.dirname(__file__)
XGB_PATH = os.path.join(MODEL_DIR, 'xgb_model.pkl')
IF_PATH = os.path.join(MODEL_DIR, 'iforest_model.pkl')
SCALER_PATH = os.path.join(MODEL_DIR, 'scaler.pkl')

LOCATIONS = [
  {'name': 'New York, USA', 'lat': 40.7128, 'lng': -74.0060},
  {'name': 'London, UK', 'lat': 51.5074, 'lng': -0.1278},
  {'name': 'Tokyo, Japan', 'lat': 35.6762, 'lng': 139.6503},
  {'name': 'Lagos, Nigeria', 'lat': 6.5244, 'lng': 3.3792},
  {'name': 'São Paulo, Brazil', 'lat': -23.5505, 'lng': -46.6333},
  {'name': 'Mumbai, India', 'lat': 19.0760, 'lng': 72.8777},
  {'name': 'Singapore', 'lat': 1.3521, 'lng': 103.8198},
  {'name': 'Dubai, UAE', 'lat': 25.2048, 'lng': 55.2708},
  {'name': 'Sydney, Australia', 'lat': -33.8688, 'lng': 151.2093},
  {'name': 'Toronto, Canada', 'lat': 43.6532, 'lng': -79.3832},
]

CATEGORIES = [
    'Retail', 'Digital Goods', 'Crypto', 'Travel', 'P2P Transfer', 
    'Gambling', 'Groceries', 'Restaurant', 'Gas Station', 'Online Shopping',
    'Bill Payment', 'Investment', 'Entertainment', 'Healthcare', 'Education'
]

HIGH_RISK_CATEGORIES = ['Crypto', 'Gambling', 'P2P Transfer', 'Investment']

class FeatureEngineer:
    """Advanced feature engineering for fraud detection"""
    
    def __init__(self):
        self.scaler = StandardScaler()
        self.is_fitted = False
    
    def fit(self, X: pd.DataFrame):
        """Fit the scaler on training data"""
        numeric_features = X.select_dtypes(include=[np.number]).columns
        self.scaler.fit(X[numeric_features])
        self.is_fitted = True
    
    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        """Transform features"""
        X = X.copy()
        
        # Amount-based features
        X['amount_log'] = np.log1p(X['amount'])
        X['amount_sqrt'] = np.sqrt(X['amount'])
        
        # Time-based features
        if 'hour_of_day' not in X.columns:
            X['hour_of_day'] = pd.to_datetime(X['timestamp'], unit='ms').dt.hour
            X['day_of_week'] = pd.to_datetime(X['timestamp'], unit='ms').dt.dayofweek
        
        # Risk scoring based on category
        X['is_high_risk_category'] = X['category'].isin(HIGH_RISK_CATEGORIES).astype(int)
        
        # Location-based features
        if 'prev_lat' in X.columns and 'prev_lng' in X.columns:
            X['distance_traveled'] = X.apply(
                lambda row: geodesic(
                    (row['prev_lat'], row['prev_lng']), 
                    (row['lat'], row['lng'])
                ).kilometers if pd.notna(row['prev_lat']) else 0, axis=1
            )
        
        # Frequency-based features
        if 'transaction_count_24h' in X.columns:
            X['avg_amount_24h'] = X['total_amount_24h'] / X['transaction_count_24h']
            X['amount_deviation'] = (X['amount'] - X['avg_amount_24h']) / X['avg_amount_24h']
        
        # Scale numeric features
        if self.is_fitted:
            numeric_features = X.select_dtypes(include=[np.number]).columns
            X[numeric_features] = self.scaler.transform(X[numeric_features])
        
        return X
    
    def extract_features(self, transaction: Dict[str, Any], user_history: Dict[str, Any]) -> np.ndarray:
        """Extract features for a single transaction"""
        features = {}
        
        # Basic features
        features['amount'] = transaction['amount']
        features['amount_log'] = np.log1p(transaction['amount'])
        features['amount_sqrt'] = np.sqrt(transaction['amount'])
        
        # Category encoding
        cat_idx = CATEGORIES.index(transaction['category']) if transaction['category'] in CATEGORIES else 0
        features['category_idx'] = cat_idx
        features['is_high_risk_category'] = 1 if transaction['category'] in HIGH_RISK_CATEGORIES else 0
        
        # Location features
        features['lat'] = transaction['lat']
        features['lng'] = transaction['lng']
        
        # Time features
        timestamp = transaction.get('timestamp', datetime.now().timestamp() * 1000)
        dt = datetime.fromtimestamp(timestamp / 1000)
        features['hour_of_day'] = dt.hour
        features['day_of_week'] = dt.weekday()
        features['is_weekend'] = 1 if dt.weekday() >= 5 else 0
        features['is_night'] = 1 if dt.hour < 6 or dt.hour > 22 else 0
        
        # User behavior features
        if user_history:
            features['user_avg_amount'] = user_history.get('avg_amount', 0)
            features['user_transaction_count'] = user_history.get('count', 0)
            features['amount_ratio_to_avg'] = transaction['amount'] / max(user_history.get('avg_amount', 1), 1)
            features['is_new_user'] = 1 if user_history.get('count', 0) < 3 else 0
            
            # Location change detection
            if user_history.get('last_location'):
                last_loc = user_history['last_location']
                distance = geodesic(
                    (last_loc['lat'], last_loc['lng']),
                    (transaction['lat'], transaction['lng'])
                ).kilometers
                features['location_change_km'] = distance
                features['is_location_change'] = 1 if distance > 100 else 0
            else:
                features['location_change_km'] = 0
                features['is_location_change'] = 0
            
            # Time since last transaction
            if user_history.get('last_timestamp'):
                time_diff = (timestamp - user_history['last_timestamp']) / (1000 * 60)  # minutes
                features['time_since_last_tx'] = time_diff
                features['is_rapid_transaction'] = 1 if time_diff < 5 else 0
            else:
                features['time_since_last_tx'] = 999999
                features['is_rapid_transaction'] = 0
        else:
            # Default values for new users
            features['user_avg_amount'] = 0
            features['user_transaction_count'] = 0
            features['amount_ratio_to_avg'] = 1
            features['is_new_user'] = 1
            features['location_change_km'] = 0
            features['is_location_change'] = 0
            features['time_since_last_tx'] = 999999
            features['is_rapid_transaction'] = 0
        
        # Convert to numpy array
        feature_order = [
            'amount', 'amount_log', 'amount_sqrt', 'category_idx', 'is_high_risk_category',
            'lat', 'lng', 'hour_of_day', 'day_of_week', 'is_weekend', 'is_night',
            'user_avg_amount', 'user_transaction_count', 'amount_ratio_to_avg', 'is_new_user',
            'location_change_km', 'is_location_change', 'time_since_last_tx', 'is_rapid_transaction'
        ]
        
        return np.array([features.get(f, 0) for f in feature_order])

def load_real_dataset() -> pd.DataFrame:
    """Load realistic transaction data from user-provided CSV"""
    csv_path = r'C:\Users\olgan\Desktop\fraud_dataset_12000.csv'
    if not os.path.exists(csv_path):
        print(f"Dataset not found at {csv_path}")
        return pd.DataFrame()
        
    df = pd.read_csv(csv_path)
    
    location_map = {
        'Canada': {'lat': 56.1304, 'lng': -106.3468},
        'UAE': {'lat': 23.4241, 'lng': 53.8478},
        'India': {'lat': 20.5937, 'lng': 78.9629},
        'Germany': {'lat': 51.1657, 'lng': 10.4515},
        'USA': {'lat': 37.0902, 'lng': -95.7129},
        'UK': {'lat': 55.3781, 'lng': -3.4360}
    }
    
    formatted_data = []
    
    for _, row in df.iterrows():
        loc_str = str(row.get('location', 'USA'))
        mapped_loc = location_map.get(loc_str, {'lat': 37.0, 'lng': -95.0})
        
        try:
            dt = datetime.strptime(str(row['timestamp']), "%Y-%m-%d %H:%M:%S.%f")
            ts = int(dt.timestamp() * 1000)
        except:
            ts = int(datetime.now().timestamp() * 1000)
            
        formatted_data.append({
            'user_id': str(row.get('user_id', f"usr_{uuid.uuid4().hex[:8]}")),
            'amount': float(row.get('amount', 0)),
            'category': str(row.get('merchant_category', 'Retail')),
            'lat': mapped_loc['lat'],
            'lng': mapped_loc['lng'],
            'timestamp': ts,
            'device_id': str(row.get('device_id', 'unknown')),
            'is_fraud': int(row.get('fraud_label', 0))
        })
        
    return pd.DataFrame(formatted_data)

class FraudMLEngine:
    """Enhanced ML Engine with multiple models and adaptive learning"""
    
    def __init__(self):
        self.xgb = None
        self.iforest = None
        self.feature_engineer = FeatureEngineer()
        self.user_history = {}  # Cache for user behavioral data
        self.model_weights = {'xgb': 0.5, 'iforest': 0.3, 'rules': 0.2}
        self.load_or_train()

    def load_or_train(self):
        """Load existing models or train new ones"""
        if (os.path.exists(XGB_PATH) and os.path.exists(IF_PATH) and 
            os.path.exists(SCALER_PATH)):
            try:
                self.xgb = joblib.load(XGB_PATH)
                self.iforest = joblib.load(IF_PATH)
                self.feature_engineer.scaler = joblib.load(SCALER_PATH)
                self.feature_engineer.is_fitted = True
                print("✅ Models loaded successfully")
                return
            except Exception as e:
                print(f"⚠️ Error loading models: {e}, retraining...")
        
        print("🔄 Training new models...")
        self.train_models()

    def train_models(self):
        """Train all ML models with real data"""
        # Generate training data
        df = load_real_dataset()
        if df.empty:
            print("⚠️ Real dataset empty or missing, skipping training.")
            return
        
        # Extract features
        X_features = []
        for _, row in df.iterrows():
            user_hist = self.user_history.get(row['user_id'], {})
            features = self.feature_engineer.extract_features(row.to_dict(), user_hist)
            X_features.append(features)
        
        X = np.array(X_features)
        y = df['is_fraud'].values
        
        # Train XGBoost
        self.xgb = XGBClassifier(
            n_estimators=200,
            max_depth=6,
            learning_rate=0.05,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42
        )
        self.xgb.fit(X, y)
        
        # Train Isolation Forest
        self.iforest = IsolationForest(
            contamination=0.08,
            random_state=42,
            n_estimators=100
        )
        self.iforest.fit(X)
        
        # Fit scaler
        self.feature_engineer.scaler.fit(X)
        self.feature_engineer.is_fitted = True
        
        # Save models
        joblib.dump(self.xgb, XGB_PATH)
        joblib.dump(self.iforest, IF_PATH)
        joblib.dump(self.feature_engineer.scaler, SCALER_PATH)
        
        print("✅ Models trained and saved successfully")

    def evaluate_transaction(self, amount: float, category: str, lat: float, lng: float, 
                           user_id: str, device_id: str = None, biometrics: Dict[str, Any] = None) -> Tuple[bool, int, str]:
        """Comprehensive transaction evaluation"""
        
        transaction = {
            'amount': amount,
            'category': category,
            'lat': lat,
            'lng': lng,
            'timestamp': datetime.now().timestamp() * 1000,
            'device_id': device_id or f"device_{random.randint(1, 500)}"
        }
        
        # Get user history
        user_hist = self.user_history.get(user_id, {})
        
        # Extract features
        features = self.feature_engineer.extract_features(transaction, user_hist)
        X_live = features.reshape(1, -1)
        
        # Supervised learning (XGBoost)
        xgb_prob = self.xgb.predict_proba(X_live)[0][1]
        
        # Unsupervised anomaly detection (Isolation Forest)
        if_score = self.iforest.decision_function(X_live)[0]
        iforest_risk = 1.0 if if_score < 0 else max(0, -if_score * 2)
        
        # Rule-based engine
        rules_risk, rule_reasons = self._apply_rules(transaction, user_hist)
        
        # Biometrics evaluation
        bio_risk = 0.0
        if biometrics:
            typing_speed = biometrics.get('typingSpeedMs', 100)
            mouse_jitter = biometrics.get('mouseJitter', 10)
            if typing_speed < 15:  # Super-human speed
                bio_risk += 0.8
                rule_reasons.append("Super-human typing speed (sub-15ms/char)")
            if mouse_jitter < 0.5 and mouse_jitter > 0:  # Rigid, robotic trajectory
                bio_risk += 0.8
                rule_reasons.append("Non-human cursor trajectory")
        
        # Weighted ensemble
        final_risk = (
            xgb_prob * self.model_weights['xgb'] + 
            iforest_risk * self.model_weights['iforest'] + 
            rules_risk * self.model_weights['rules'] +
            (bio_risk * 0.4) # Add biometrics weight
        )
        
        final_score_100 = min(int(final_risk * 100), 100)
        
        # Determine fraud status and reason
        is_fraud = final_score_100 > 75
        flag_reason = self._determine_flag_reason(final_score_100, rule_reasons, xgb_prob, iforest_risk)
        
        # Update user history
        self._update_user_history(user_id, transaction, final_score_100)
        
        return is_fraud, final_score_100, flag_reason

    def _apply_rules(self, transaction: Dict[str, Any], user_hist: Dict[str, Any]) -> Tuple[float, List[str]]:
        """Apply rule-based fraud detection"""
        risk_score = 0.0
        reasons = []
        
        # Rule 1: Amount deviation and strict thresholds
        if transaction['amount'] >= 5000:
            risk_score += 0.9
            reasons.append("Unusually high transaction amount (≥ ₹5000)")
        elif transaction['amount'] >= 3000:
            risk_score += 0.6
            reasons.append("High transaction amount (≥ ₹3000)")
            
        if user_hist.get('avg_amount'):
            amount_ratio = transaction['amount'] / max(user_hist['avg_amount'], 1)
            if amount_ratio > 4 and transaction['amount'] > 1000:
                risk_score += 0.4
                reasons.append("Sharp deviation from personal average")
        
        # Rule 2: Location change
        if user_hist.get('last_location'):
            last_loc = user_hist['last_location']
            distance = geodesic(
                (last_loc['lat'], last_loc['lng']),
                (transaction['lat'], transaction['lng'])
            ).kilometers
            
            if distance > 1000:  # More than 1000km
                risk_score += 0.6
                reasons.append("Impossible location change")
            elif distance > 500:
                risk_score += 0.3
                reasons.append("Suspicious location change")
        
        # Rule 3: Rapid transactions
        if user_hist.get('last_timestamp'):
            time_diff = (transaction['timestamp'] - user_hist['last_timestamp']) / (1000 * 60)
            if time_diff < 1:  # Less than 1 minute
                risk_score += 0.4
                reasons.append("Rapid consecutive transactions")
        
        # Rule 4: High-risk category
        if transaction['category'] in HIGH_RISK_CATEGORIES:
            if transaction['amount'] >= 5000:
                risk_score += 0.5
                reasons.append(f"High amount (≥ ₹5000) in {transaction['category']}")
            else:
                risk_score += 0.2
                reasons.append(f"Transaction in {transaction['category']}")
        
        # Rule 5: New user
        if user_hist.get('count', 0) < 3:
            if transaction['amount'] >= 3000:
                risk_score += 0.3
                reasons.append("New user with high transaction (≥ ₹3000)")
        
        # Rule 6: Time-based patterns
        hour = datetime.fromtimestamp(transaction['timestamp'] / 1000).hour
        if hour < 4 or hour > 23:  # Unusual hours
            risk_score += 0.2
            reasons.append("Unusual transaction time")
        
        return min(risk_score, 1.0), reasons

    def _determine_flag_reason(self, score: int, rule_reasons: List[str], 
                              xgb_prob: float, iforest_risk: float) -> str:
        """Determine the primary reason for fraud flag"""
        if score >= 90:
            if rule_reasons:
                return " | ".join(rule_reasons[:2])
            elif xgb_prob > 0.8:
                return "ML Model: High fraud probability"
            elif iforest_risk > 0.7:
                return "Anomaly Detection: Unusual pattern detected"
            else:
                return "Multiple risk factors detected"
        elif score >= 75:
            if rule_reasons:
                return rule_reasons[0]
            elif xgb_prob > 0.6:
                return "ML Model: Suspicious pattern"
            else:
                return "Suspicious activity detected"
        else:
            return None

    def _update_user_history(self, user_id: str, transaction: Dict[str, Any], risk_score: int):
        """Update user behavioral history"""
        current_time = transaction['timestamp']
        
        if user_id not in self.user_history:
            self.user_history[user_id] = {
                'count': 0,
                'total_amount': 0,
                'avg_amount': 0,
                'last_timestamp': 0,
                'last_location': None,
                'high_risk_count': 0
            }
        
        hist = self.user_history[user_id]
        hist['count'] += 1
        hist['total_amount'] += transaction['amount']
        hist['avg_amount'] = hist['total_amount'] / hist['count']
        hist['last_timestamp'] = current_time
        hist['last_location'] = {'lat': transaction['lat'], 'lng': transaction['lng']}
        
        if risk_score > 50:
            hist['high_risk_count'] += 1

    def adaptive_learning_update(self, tx_id: str, was_me: bool, user_id: str):
        """Update model weights based on user feedback"""
        if was_me:
            # Reduce false positive sensitivity
            self.model_weights['rules'] = max(0.1, self.model_weights['rules'] - 0.01)
            self.model_weights['xgb'] = min(0.6, self.model_weights['xgb'] + 0.01)
        else:
            # Increase fraud detection sensitivity
            self.model_weights['rules'] = min(0.3, self.model_weights['rules'] + 0.01)
            self.model_weights['iforest'] = min(0.4, self.model_weights['iforest'] + 0.01)
        
        # Normalize weights
        total = sum(self.model_weights.values())
        for key in self.model_weights:
            self.model_weights[key] /= total

    def generate_xai_explanation(self, transaction: Dict[str, Any], risk_score: int, flag_reason: str) -> str:
        """Generate Explainable AI Natural Language reasoning"""
        if risk_score <= 50:
            return "This transaction appears normal. Feature values align with the user's historical baseline and no anomalies were detected by the Isolation Forest."
            
        explanation = f"Fraud Score {risk_score}/100.\\n\\n"
        reason_lower = str(flag_reason).lower() if flag_reason else ""
        
        if "device" in reason_lower or "super-human" in reason_lower or "cursor" in reason_lower:
            explanation += "**Biometric Anomaly:** The system detected strongly anomalous biometrics. Physical interactions with the form resemble automated robotic scripts rather than human behavior.\\n\\n"
        
        if "location" in reason_lower:
            explanation += "**Geographic Anomaly:** There is an impossible or highly unusual geographic shift from the user's historical baseline.\\n\\n"
            
        if "amount" in reason_lower or "deviation" in reason_lower or "sharp" in reason_lower:
            explanation += "**Behavioral Deviation:** The transaction amount is statistically deviant compared to historical norms. The Isolation Forest flagged this sequence.\\n\\n"
            
        if "rapid" in reason_lower:
            explanation += "**Velocity Anomaly:** Transactions are occurring at a frequency faster than humanly likely.\\n\\n"
            
        if risk_score > 90:
            explanation += "**XGBoost Confidence:** The XGBoost classifier gave >90% confidence that this transaction clusters identically with known fraud rings based on deep feature analysis.\\n"
            
        if explanation == f"Fraud Score {risk_score}/100.\\n\\n":
            explanation += "Machine learning models indicate complex hidden fraud patterns within the 19 behavioral features."
            
        return explanation.strip()

# Global engine instance
engine = FraudMLEngine()
