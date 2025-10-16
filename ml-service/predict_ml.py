"""
ML Prediction Microservice
Only XGBoost prediction, called by main app
"""

from http.server import BaseHTTPRequestHandler
import json
import os
import pickle
import re
from scipy.sparse import hstack
import numpy as np

# Load ML models
MODEL_DIR = os.path.dirname(__file__)
ML_MODEL = None
TFIDF = None
LABEL_ENCODER = None

try:
    with open(os.path.join(MODEL_DIR, 'ultra_fast_model.pkl'), 'rb') as f:
        ML_MODEL = pickle.load(f, encoding='latin1')
    with open(os.path.join(MODEL_DIR, 'ultra_fast_tfidf.pkl'), 'rb') as f:
        TFIDF = pickle.load(f, encoding='latin1')
    with open(os.path.join(MODEL_DIR, 'ultra_fast_agent_encoder.pkl'), 'rb') as f:
        LABEL_ENCODER = pickle.load(f, encoding='latin1')
    print("✅ ML Models loaded (XGBoost)")
except Exception as e:
    print(f"❌ ML Model load error: {e}")

def clean_text(text):
    """Clean text for ML"""
    if not text:
        return ""
    text = str(text).upper()
    text = re.sub(r'[^\w\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def predict_ml(transaction):
    """ML prediction using XGBoost"""
    if not ML_MODEL or not TFIDF or not LABEL_ENCODER:
        return None, 0.0
    
    try:
        # Features
        desc = clean_text(transaction.get('description', ''))
        account = clean_text(transaction.get('origination_account_id', ''))
        amount = float(str(transaction.get('amount', '0')).replace('$', '').replace(',', '')) if transaction.get('amount') else 0
        method_map = {'wire in': 0, 'ach': 1, 'ach external': 2, 'check': 3, 'ach transaction': 4}
        method = method_map.get((transaction.get('payment_method', '')).lower(), -1)
        
        # TF-IDF
        X_tfidf = TFIDF.transform([desc])
        
        # Extra features
        X_ex = np.array([[method, 0, amount, np.log1p(amount)]])
        
        # Combine
        X = hstack([X_tfidf, X_ex])
        
        # Predict
        prediction = ML_MODEL.predict(X)
        proba = ML_MODEL.predict_proba(X)
        
        label = LABEL_ENCODER.inverse_transform(prediction)[0]
        confidence = float(proba.max())
        
        return label, confidence
        
    except Exception as e:
        print(f"ML prediction error: {e}")
        return None, 0.0

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        """Handle ML prediction requests"""
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            transaction = data.get('transaction', {})
            
            if not transaction:
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({'error': 'No transaction provided'}).encode())
                return
            
            # Predict
            label, confidence = predict_ml(transaction)
            
            response = {
                'label': label,
                'confidence': confidence,
                'method': 'Trained Model (XGBoost)'
            }
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode())
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({'error': str(e)}).encode())
    
    def do_OPTIONS(self):
        """Handle CORS preflight"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

