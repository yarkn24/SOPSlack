"""
Gemini-powered Smart Transaction Parser
Parses any format transaction input into structured data
"""

from http.server import BaseHTTPRequestHandler
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

# Initialize Gemini
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
if GEMINI_API_KEY and GEMINI_AVAILABLE:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-pro')

def parse_with_gemini(raw_text):
    """
    Use Gemini to intelligently parse any transaction format
    """
    if not GEMINI_API_KEY or not GEMINI_AVAILABLE:
        return None, "Gemini not configured"
    
    prompt = f"""You are a bank transaction parser. Extract structured data from this transaction text.

Transaction text:
{raw_text}

Extract these fields (if present):
- transaction_id: The transaction/claim ID number
- amount: Dollar amount (keep $ sign)
- date: Transaction date
- payment_method: Method like "wire in", "ach", "check", etc.
- origination_account_id: Bank account name (e.g., "Chase Wire In", "Chase Operations")
- description: Full transaction description/details

**IMPORTANT:** 
- If a field is not present, set it to "unknown"
- Return ONLY valid JSON, no explanation
- Use exact field names as shown above

Example format:
{{
  "transaction_id": "59316175",
  "amount": "$80.76",
  "date": "10/15/2025",
  "payment_method": "ach transaction",
  "origination_account_id": "Grasshopper Operations",
  "description": "vendor description: GUSTO, receiver id number: null"
}}

Now parse the transaction above:"""

    try:
        response = model.generate_content(prompt)
        result_text = response.text.strip()
        
        # Extract JSON from response (Gemini sometimes adds markdown)
        if '```json' in result_text:
            result_text = result_text.split('```json')[1].split('```')[0].strip()
        elif '```' in result_text:
            result_text = result_text.split('```')[1].split('```')[0].strip()
        
        # Parse JSON
        parsed_data = json.loads(result_text)
        
        # Validate and normalize required fields
        required_fields = ['transaction_id', 'amount', 'date', 'payment_method', 'origination_account_id', 'description']
        for field in required_fields:
            if field not in parsed_data:
                parsed_data[field] = 'unknown'
        
        # Normalize payment method
        parsed_data['payment_method'] = normalize_payment_method(parsed_data.get('payment_method', 'unknown'))
        
        # Clean transaction ID (remove "claim_" prefix)
        parsed_data['transaction_id'] = str(parsed_data.get('transaction_id', '')).replace('claim_', '').replace('claim', '').strip()
        
        return parsed_data, None
        
    except json.JSONDecodeError as e:
        return None, f"Failed to parse Gemini response as JSON: {str(e)}"
    except Exception as e:
        return None, f"Gemini parsing error: {str(e)}"

def normalize_payment_method(method):
    """
    Normalize payment method to standard format
    """
    method = str(method).lower().strip()
    
    # Common mappings
    if 'ach' in method:
        return 'ach'
    elif 'wire' in method:
        return 'wire in'
    elif 'check' in method:
        return 'check'
    elif 'card' in method or 'credit' in method or 'debit' in method:
        return 'card'
    else:
        return method

def parse_csv(raw_text):
    """
    Parse CSV format (tab or comma separated)
    """
    try:
        lines = raw_text.strip().split('\n')
        transactions = []
        
        for line in lines:
            if not line.strip():
                continue
            
            # Try tab-separated first
            if '\t' in line:
                parts = [p.strip() for p in line.split('\t')]
            # Then comma-separated
            elif ',' in line:
                parts = [p.strip() for p in line.split(',')]
            else:
                continue
            
            # Need at least 5 columns
            if len(parts) >= 5:
                transactions.append({
                    'transaction_id': parts[0].replace('claim_', '').replace('claim', '').strip(),
                    'amount': parts[1] if parts[1] else 'unknown',
                    'date': parts[2] if len(parts) > 2 else 'unknown',
                    'payment_method': normalize_payment_method(parts[3]) if len(parts) > 3 else 'unknown',
                    'origination_account_id': parts[4] if len(parts) > 4 else 'unknown',
                    'description': ' '.join(parts[5:]) if len(parts) > 5 else 'unknown'
                })
        
        return transactions if transactions else (None, "No valid CSV data found")
        
    except Exception as e:
        return None, str(e)

def parse_traditional(raw_text):
    """
    Fallback: Traditional parsing for standard format
    Format: ID | Amount | Date | Method | Account | Description
    """
    try:
        # First try CSV format
        result = parse_csv(raw_text)
        if result and not isinstance(result, tuple):
            return result, None
        
        # Then try pipe-separated
        lines = raw_text.strip().split('\n')
        transactions = []
        
        for line in lines:
            if not line.strip():
                continue
            
            # Try pipe-separated format
            if '|' in line:
                parts = [p.strip() for p in line.split('|')]
                if len(parts) >= 6:
                    transactions.append({
                        'transaction_id': parts[0].replace('claim_', '').replace('claim', '').strip(),
                        'amount': parts[1],
                        'date': parts[2],
                        'payment_method': normalize_payment_method(parts[3]),
                        'origination_account_id': parts[4],
                        'description': ' '.join(parts[5:])
                    })
            else:
                # Single transaction, try Gemini
                return None, "Use Gemini for non-standard format"
        
        return transactions if transactions else (None, "No valid data found"), None
        
    except Exception as e:
        return None, str(e)

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        """Handle POST requests for transaction parsing"""
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            raw_text = data.get('raw_text', '').strip()
            use_gemini = data.get('use_gemini', True)
            
            if not raw_text:
                self.send_error(400, 'No transaction text provided')
                return
            
            parsed_transactions = []
            parsing_method = 'unknown'
            
            # Try traditional parsing first (fast)
            transactions, error = parse_traditional(raw_text)
            
            if transactions:
                parsed_transactions = transactions
                parsing_method = 'traditional'
            elif use_gemini:
                # Use Gemini for intelligent parsing
                parsed_data, error = parse_with_gemini(raw_text)
                if parsed_data:
                    parsed_transactions = [parsed_data]
                    parsing_method = 'gemini'
                else:
                    self.send_error(400, f'Parsing failed: {error}')
                    return
            else:
                self.send_error(400, f'Parsing failed: {error}')
                return
            
            # Send response
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            response = {
                'success': True,
                'count': len(parsed_transactions),
                'transactions': parsed_transactions,
                'parsing_method': parsing_method,
                'gemini_available': bool(GEMINI_API_KEY and GEMINI_AVAILABLE)
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
            'service': 'Smart Transaction Parser',
            'gemini_available': bool(GEMINI_API_KEY and GEMINI_AVAILABLE),
            'features': [
                'Traditional format (pipe-separated)',
                'Gemini AI smart parsing (any format)',
                'Automatic format detection'
            ]
        }
        
        self.wfile.write(json.dumps(response).encode())

