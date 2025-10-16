"""
Vercel Serverless Function for Transaction Analysis with Gemini AI
"""

from http.server import BaseHTTPRequestHandler
import json
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

try:
    import google.generativeai as genai
    from complete_sop_mapping import COMPLETE_SOP_MAPPING
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    COMPLETE_SOP_MAPPING = {}

# Initialize Gemini
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
if GEMINI_API_KEY and GEMINI_AVAILABLE:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-flash-latest')

def ask_gemini_about_transaction(question):
    """
    Chat mode: Answer questions about transactions using Gemini
    """
    if not GEMINI_API_KEY or not GEMINI_AVAILABLE:
        return {
            'response': 'Gemini is not configured. Please check API key.',
            'suggested_label': None
        }
    
    # Build prompt with SOP context
    agent_list = ', '.join(sorted(set(COMPLETE_SOP_MAPPING.keys())))
    
    prompt = f"""You are an expert bank reconciliation assistant for Gusto. Answer this question about bank transactions:

Question: {question}

Context:
- Available agent labels: {agent_list}
- You should suggest ONE specific agent label if the question is about a transaction
- Reference SOPs when appropriate
- Keep answers concise and actionable

Instructions:
1. If the question includes a transaction, analyze it and suggest the correct agent label
2. Explain WHY that label is correct
3. Provide reconciliation guidance if relevant
4. Keep response under 200 words

Response:"""

    try:
        response = model.generate_content(prompt)
        result_text = response.text.strip()
        
        # Try to extract suggested label from response
        suggested_label = None
        for agent in COMPLETE_SOP_MAPPING.keys():
            if agent.upper() in result_text.upper():
                suggested_label = agent
                break
        
        # Get SOP info if label found
        sop_info = {}
        if suggested_label and suggested_label in COMPLETE_SOP_MAPPING:
            sop_data = COMPLETE_SOP_MAPPING[suggested_label]
            sop_info = {
                'sop_title': sop_data.get('sop_page', ''),
                'sop_link': sop_data.get('sop_link', '')
            }
        
        return {
            'response': result_text,
            'suggested_label': suggested_label,
            'confidence': 'High' if suggested_label else 'Medium',
            **sop_info
        }
        
    except Exception as e:
        return {
            'response': f'Error: {str(e)}',
            'suggested_label': None
        }

def predict_label_rule_based(transaction):
    """Rule-based prediction (same as static-predictor.js)"""
    desc = (transaction.get('description', '')).upper()
    account = (transaction.get('origination_account_id', '')).upper()
    amount = float((transaction.get('amount', '0')).replace('$', '').replace(',', '')) if transaction.get('amount') else 0
    method = (transaction.get('payment_method', '')).lower()
    
    # Account-based rules
    if 'PNC WIRE IN' in account or 'CHASE WIRE IN' in account:
        return 'Risk', 'rule-based', 'Account is PNC Wire In or Chase Wire In'
    
    if 'CHASE PAYROLL INCOMING WIRES' in account:
        return 'Risk', 'rule-based', 'Account is Chase Payroll Incoming Wires'
    
    if 'CHASE RECOVERY' in account:
        return 'Recovery Wire', 'rule-based', 'Account is Chase Recovery'
    
    # Payment method
    if 'check' in method:
        return 'Check', 'rule-based', "Payment method is 'Check'"
    
    # Description-based
    if 'NYS DTF WT' in desc:
        return 'NY WH', 'rule-based', "Description contains 'NYS DTF WT'"
    
    if 'OH WH TAX' in desc:
        return 'OH WH', 'rule-based', "Description contains 'OH WH TAX'"
    
    if 'JPMORGAN ACCESS TRANSFER' in desc:
        return 'ICP Funding', 'rule-based', "Description contains 'JPMORGAN ACCESS TRANSFER'"
    
    if 'CSC' in desc:
        return 'CSC', 'rule-based', "Description contains 'CSC'"
    
    if 'ACH RETURN SETTLEMENT' in desc or 'CREDIT MEMO' in desc:
        return 'LOI', 'rule-based', 'Description indicates LOI'
    
    if 'LOCKBOX' in desc:
        return 'Lockbox', 'rule-based', "Description contains 'LOCKBOX'"
    
    if amount < 1.0 and amount > 0:
        return 'Bad Debt', 'rule-based', 'Amount less than $1.00'
    
    return 'Unknown', 'rule-based', 'No matching rule found'

def predict_with_gemini(transaction):
    """Use Gemini AI to predict label"""
    if not GEMINI_API_KEY or not GEMINI_AVAILABLE:
        return 'Unknown', 'ml-based', 'Gemini not available'
    
    prompt = f"""Analyze this bank transaction and predict the most appropriate label.

Transaction:
- Amount: {transaction.get('amount')}
- Account: {transaction.get('origination_account_id')}
- Method: {transaction.get('payment_method')}
- Description: {transaction.get('description')}

Available Labels: {', '.join(COMPLETE_SOP_MAPPING.keys())}

Respond with ONLY the label name, nothing else."""

    try:
        response = model.generate_content(prompt)
        label = response.text.strip()
        
        # Validate label
        if label in COMPLETE_SOP_MAPPING:
            return label, 'ml-based (Gemini Pro)', f'AI predicted based on pattern analysis'
        else:
            return 'Unknown', 'ml-based', f'AI suggested: {label} (not in valid labels)'
            
    except Exception as e:
        return 'Unknown', 'ml-based', f'AI error: {str(e)}'

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        """Handle POST requests"""
        try:
            # Read request body
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            # Check if this is a chat mode request
            if data.get('mode') == 'chat':
                question = data.get('question', '')
                if not question:
                    self.send_error(400, 'No question provided')
                    return
                
                # Ask Gemini
                result = ask_gemini_about_transaction(question)
                
                # Send response
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                
                self.wfile.write(json.dumps(result).encode())
                return
            
            # Normal transaction analysis mode
            transactions = data.get('transactions', [])
            use_ai = data.get('use_ai', True)
            
            if not transactions:
                self.send_error(400, 'No transactions provided')
                return
            
            results = []
            
            for txn in transactions:
                # Try rule-based first
                label, method, reason = predict_label_rule_based(txn)
                
                # If Unknown and AI enabled, try Gemini
                if label == 'Unknown' and use_ai:
                    label, method, reason = predict_with_gemini(txn)
                
                # Get SOP content
                sop_content = COMPLETE_SOP_MAPPING.get(label, {})
                
                result = {
                    'transaction_id': txn.get('transaction_id', 'N/A'),
                    'amount': txn.get('amount', 'N/A'),
                    'account': txn.get('origination_account_id', 'N/A'),
                    'description': txn.get('description', 'N/A')[:100] + '...',
                    'label': label,
                    'method': method,
                    'reason': reason,
                    'sop_content': sop_content
                }
                
                results.append(result)
            
            # Send response
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            response = {
                'success': True,
                'count': len(results),
                'results': results,
                'ai_enabled': bool(GEMINI_API_KEY and GEMINI_AVAILABLE)
            }
            
            self.wfile.write(json.dumps(response).encode())
            
        except Exception as e:
            self.send_error(500, str(e))
    
    def do_OPTIONS(self):
        """Handle CORS preflight"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def do_GET(self):
        """Handle GET for health check"""
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        response = {
            'status': 'healthy',
            'gemini_configured': bool(GEMINI_API_KEY),
            'gemini_available': GEMINI_AVAILABLE
        }
        
        self.wfile.write(json.dumps(response).encode())

