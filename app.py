#!/usr/bin/env python3
"""
Flask backend for Bank Transaction Analyzer
Integrates with Gemini Pro and OpenAI GPT for ML predictions
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import json
from dotenv import load_dotenv
import google.generativeai as genai
from openai import OpenAI

# Load environment variables
load_dotenv()

# Import our prediction logic
from final_predictor import predict_label
from complete_sop_mapping import COMPLETE_SOP_MAPPING

app = Flask(__name__, static_folder='.')
CORS(app)

# Initialize AI clients
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    gemini_model = genai.GenerativeModel('gemini-pro')
    print("✅ Gemini Pro initialized")

if OPENAI_API_KEY:
    openai_client = OpenAI(api_key=OPENAI_API_KEY)
    print("✅ OpenAI GPT initialized")

def predict_with_ai(transaction, ai_provider='gemini'):
    """
    Use AI to predict label when rule-based prediction returns Unknown
    """
    
    # Prepare prompt with transaction details
    prompt = f"""You are a bank transaction labeling expert. Analyze this transaction and predict the most appropriate label.

Transaction Details:
- Amount: {transaction.get('amount', 'N/A')}
- Date: {transaction.get('date', 'N/A')}
- Payment Method: {transaction.get('payment_method', 'N/A')}
- Account: {transaction.get('origination_account_id', 'N/A')}
- Description: {transaction.get('description', 'N/A')}

Available Labels:
{', '.join(COMPLETE_SOP_MAPPING.keys())}

Based on the transaction details, predict the most appropriate label. Respond with ONLY the label name, nothing else.
If you're uncertain, respond with "Unknown".

Label:"""

    try:
        if ai_provider == 'gemini' and GEMINI_API_KEY:
            response = gemini_model.generate_content(prompt)
            predicted_label = response.text.strip()
            return predicted_label, 'ml-based (Gemini Pro)'
            
        elif ai_provider == 'openai' and OPENAI_API_KEY:
            response = openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a bank transaction labeling expert. Respond with only the label name."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=50
            )
            predicted_label = response.choices[0].message.content.strip()
            return predicted_label, 'ml-based (GPT-4)'
            
        else:
            return "Unknown", "rule-based (AI not configured)"
            
    except Exception as e:
        print(f"AI prediction error: {e}")
        return "Unknown", "rule-based (AI error)"

@app.route('/')
def index():
    """Serve the main HTML page"""
    return send_from_directory('.', 'index.html')

@app.route('/sop_data.json')
def sop_data():
    """Serve SOP data"""
    return jsonify(COMPLETE_SOP_MAPPING)

@app.route('/api/analyze', methods=['POST'])
def analyze_transactions():
    """
    Analyze one or more transactions
    """
    try:
        data = request.json
        transactions = data.get('transactions', [])
        ai_provider = data.get('ai_provider', 'gemini')  # 'gemini' or 'openai'
        
        if not transactions:
            return jsonify({'error': 'No transactions provided'}), 400
        
        results = []
        
        for txn in transactions:
            # First try rule-based prediction
            label, method, reason = predict_label(txn)
            
            # If Unknown, try AI prediction
            if label == "Unknown" and (GEMINI_API_KEY or OPENAI_API_KEY):
                ai_label, ai_method = predict_with_ai(txn, ai_provider)
                if ai_label != "Unknown" and ai_label in COMPLETE_SOP_MAPPING:
                    label = ai_label
                    method = ai_method
                    reason = f"AI predicted based on transaction pattern"
            
            # Get SOP content
            sop_content = COMPLETE_SOP_MAPPING.get(label, {})
            
            result = {
                'transaction_id': txn.get('transaction_id', 'N/A'),
                'amount': txn.get('amount', 'N/A'),
                'account': txn.get('origination_account_id', 'N/A'),
                'description': txn.get('description', 'N/A')[:100] + '...' if len(txn.get('description', '')) > 100 else txn.get('description', 'N/A'),
                'label': label,
                'method': method,
                'reason': reason,
                'sop_content': sop_content
            }
            
            results.append(result)
        
        return jsonify({
            'success': True,
            'count': len(results),
            'results': results
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'gemini_configured': bool(GEMINI_API_KEY),
        'openai_configured': bool(OPENAI_API_KEY)
    })

if __name__ == '__main__':
    print("\n" + "="*80)
    print("🏦 Bank Transaction Analyzer API")
    print("="*80)
    print(f"✅ Gemini Pro: {'Configured' if GEMINI_API_KEY else 'Not configured'}")
    print(f"✅ OpenAI GPT: {'Configured' if OPENAI_API_KEY else 'Not configured'}")
    print("="*80)
    print("\nStarting server at http://localhost:5000")
    print("="*80 + "\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000)

