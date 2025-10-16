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
GEMINI_API_KEY = os.environ.get('GEMINI_KEY') or os.environ.get('GEMINI_API_KEY')
if GEMINI_API_KEY and GEMINI_AVAILABLE:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-pro')

def parse_with_gemini(raw_text, force_single=False):
    """
    Use Gemini to intelligently parse any transaction format (single or multiple)
    Can handle messy/incomplete data and convert to structured format
    """
    if not GEMINI_API_KEY or not GEMINI_AVAILABLE:
        return None, "Gemini not configured"
    
    # Check if multiple transactions (multiple lines with "claim" prefix)
    lines = raw_text.strip().split('\n')
    is_multiple = len(lines) > 1 and sum(1 for line in lines if 'claim' in line.lower()) > 1
    
    # Force single transaction mode if requested (for fallback scenarios)
    if force_single:
        is_multiple = False
    
    if is_multiple:
        prompt = f"""You are an expert bank transaction parser. Extract structured data from MULTIPLE transactions.

Transaction data (multiple lines):
{raw_text}

For EACH transaction, extract:
- transaction_id: The transaction/claim/BT ID (remove "claim_" or "claim" prefix)
- amount: Dollar amount (keep $ sign, e.g., "$80.76")
- date: Transaction date
- payment_method: MUST be one of: "wire in", "ach", "check", "wire out", "ach external", "card", "ach return", "zero balance transfer", "check paid"
- origination_account_id: Bank account name (e.g., "PNC Operations", "Chase Wire In")
- description: Full transaction details

**CRITICAL RULES:**
- Return a JSON ARRAY of transaction objects
- One object per transaction line
- Remove "claim_" or "claim" prefix from transaction_id
- Keep account names like "PNC Operations", "Chase Wire In" intact
- For payment_method, look at the 5th column
- Return ONLY valid JSON array, no markdown

Example input:
claim	59392989	$463.54	10/15/2025	check paid	PNC Operations
CHECK 884892943
claim	59370967	$841,340.16	10/15/2025	zero balance transfer	Chase Wire In
CASH CONCENTRATION TRANSFER

Example output:
[
  {{
    "transaction_id": "59392989",
    "amount": "$463.54",
    "date": "10/15/2025",
    "payment_method": "check paid",
    "origination_account_id": "PNC Operations",
    "description": "CHECK 884892943"
  }},
  {{
    "transaction_id": "59370967",
    "amount": "$841,340.16",
    "date": "10/15/2025",
    "payment_method": "zero balance transfer",
    "origination_account_id": "Chase Wire In",
    "description": "CASH CONCENTRATION TRANSFER"
  }}
]

Now parse ALL transactions above:"""
    else:
        prompt = f"""You are an expert bank transaction parser. Extract structured data from this transaction text. The input may be incomplete, messy, or just a description - do your best to infer the correct fields.

Transaction text:
{raw_text}

Extract these fields (infer if not explicitly stated):
- transaction_id: The transaction/claim/BT ID number (use "unknown" if not provided)
- amount: Dollar amount with $ sign (e.g., "$80.76", use "unknown" if not stated)
- date: Transaction date (use "unknown" if not stated)
- payment_method: MUST be one of: "wire in", "ach", "check", "wire out", "ach external", "card", "ach return", "zero balance transfer", "check paid"
  * Look for keywords: "wire" → "wire in", "check" → "check", "ach" → "ach", "interest" → "ach external"
- origination_account_id: Bank account name
  * Look for: "Chase Wire In", "PNC Wire In", "Chase Recovery", "PNC Operations", "Grasshopper Operations"
  * If you see "chase" + "wire" → "Chase Wire In"
  * If you see "pnc" + "wire" → "PNC Wire In"
  * Use "unknown" if unclear
- description: Full transaction details (everything that doesn't fit other fields)

**CRITICAL PAYMENT METHOD RULES:**
- If you see "wire", "wire transfer", "wire in" → use "wire in"
- If you see "ach", "ach transaction", "ach external" → use "ach"  
- If you see "check", "check paid" → use "check"
- Default to "wire in" if unclear

**CRITICAL ACCOUNT RULES:**
- Look for bank names: Chase, PNC, Grasshopper, Blueridge, etc.
- Common accounts: "Chase Wire In", "Chase Operations", "PNC Wire In", "Chase Payroll Incoming Wires"
- Keep the FULL account name including bank + type
- If you see "Chase" + "wire" → "Chase Wire In"
- If you see "PNC" + "wire" → "PNC Wire In"

**IMPORTANT:** 
- Remove "claim_" or "claim" prefix from transaction_id
- If a field is not clear, set it to "unknown"
- Return ONLY valid JSON, no explanation
- Use exact field names as shown above

Example 1:
Input: "59316175 $80.76 10/15/2025 ach transaction Grasshopper Operations vendor: GUSTO"
Output:
{{
  "transaction_id": "59316175",
  "amount": "$80.76",
  "date": "10/15/2025",
  "payment_method": "ach",
  "origination_account_id": "Grasshopper Operations",
  "description": "vendor: GUSTO"
}}

Example 2:
Input: "claim_59315257 $5,100.00 10/14/2025 wire in Chase Wire In YOUR REF=POH OF 25/10/14"
Output:
{{
  "transaction_id": "59315257",
  "amount": "$5,100.00",
  "date": "10/14/2025",
  "payment_method": "wire in",
  "origination_account_id": "Chase Wire In",
  "description": "YOUR REF=POH OF 25/10/14"
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
        
        # Check if it's a list (multiple transactions) or dict (single)
        if isinstance(parsed_data, list):
            # Multiple transactions
            transactions = []
            for txn in parsed_data:
                # Validate and normalize
                required_fields = ['transaction_id', 'amount', 'date', 'payment_method', 'origination_account_id', 'description']
                for field in required_fields:
                    if field not in txn:
                        txn[field] = 'unknown'
                
                # Normalize payment method
                txn['payment_method'] = normalize_payment_method(txn.get('payment_method', 'unknown'))
                
                # Clean transaction ID
                txn['transaction_id'] = str(txn.get('transaction_id', '')).replace('claim_', '').replace('claim', '').strip()
                
                transactions.append(txn)
            
            return transactions, None
        else:
            # Single transaction
            required_fields = ['transaction_id', 'amount', 'date', 'payment_method', 'origination_account_id', 'description']
            for field in required_fields:
                if field not in parsed_data:
                    parsed_data[field] = 'unknown'
            
            # Normalize payment method
            parsed_data['payment_method'] = normalize_payment_method(parsed_data.get('payment_method', 'unknown'))
            
            # Clean transaction ID (remove "claim_" prefix)
            parsed_data['transaction_id'] = str(parsed_data.get('transaction_id', '')).replace('claim_', '').replace('claim', '').strip()
            
            return [parsed_data], None
        
    except json.JSONDecodeError as e:
        return None, f"Failed to parse Gemini response as JSON: {str(e)}"
    except Exception as e:
        return None, f"Gemini parsing error: {str(e)}"

def normalize_payment_method(method):
    """
    Normalize payment method to standard format
    IMPORTANT: Keep different ACH types separate!
    """
    method = str(method).lower().strip()
    
    # Exact matches first (most specific)
    if method in ['ach external', 'ach_external']:
        return 'ach external'
    elif method in ['ach transaction', 'ach_transaction', 'ach']:
        return 'ach'
    elif method in ['wire in', 'wire_in', 'wirein', 'wire transfer']:
        return 'wire in'
    elif method in ['wire out', 'wire_out', 'wireout']:
        return 'wire out'
    elif method in ['check', 'check paid', 'check_paid']:
        return 'check'
    elif 'card' in method or 'credit' in method or 'debit' in method:
        return 'card'
    else:
        # Return as-is if no match
        return method

def parse_redash_format(raw_text):
    """
    Parse Redash queue format (tab-separated with specific structure)
    Format: [claim]\tID\t$amount\tdate\tmethod\taccount\t\t\t\tdescription
    """
    try:
        lines = raw_text.strip().split('\n')
        transactions = []
        current_transaction = None
        
        for line in lines:
            if not line.strip():
                continue
            
            # Check if this is a transaction line (has multiple tabs)
            if '\t' in line:
                parts = line.split('\t')
                
                # Filter out empty strings
                non_empty_parts = [p.strip() for p in parts if p.strip()]
                
                # Check if this looks like a transaction line (has at least ID, amount, date)
                if len(non_empty_parts) >= 4:
                    # First part might be "claim" or the ID
                    if non_empty_parts[0].lower() == 'claim':
                        # Format: claim \t ID \t amount \t date \t method \t account \t ... \t description
                        if len(non_empty_parts) >= 6:
                            transaction_id = non_empty_parts[1]
                            amount = non_empty_parts[2]
                            date = non_empty_parts[3]
                            method = non_empty_parts[4]
                            account = non_empty_parts[5]
                            description = ' '.join(non_empty_parts[6:]) if len(non_empty_parts) > 6 else ''
                        else:
                            continue
                    else:
                        # Format: ID \t amount \t date \t method \t account \t ... \t description
                        transaction_id = non_empty_parts[0]
                        amount = non_empty_parts[1] if len(non_empty_parts) > 1 else 'unknown'
                        date = non_empty_parts[2] if len(non_empty_parts) > 2 else 'unknown'
                        method = non_empty_parts[3] if len(non_empty_parts) > 3 else 'unknown'
                        account = non_empty_parts[4] if len(non_empty_parts) > 4 else 'unknown'
                        description = ' '.join(non_empty_parts[5:]) if len(non_empty_parts) > 5 else ''
                    
                    # Clean transaction ID
                    transaction_id = transaction_id.replace('claim_', '').replace('claim', '').strip()
                    
                    # Save previous transaction if exists
                    if current_transaction:
                        transactions.append(current_transaction)
                    
                    # Create new transaction
                    current_transaction = {
                        'transaction_id': transaction_id,
                        'amount': amount if amount else 'unknown',
                        'date': date if date else 'unknown',
                        'payment_method': normalize_payment_method(method) if method else 'unknown',
                        'origination_account_id': account if account else 'unknown',
                        'description': description
                    }
                elif current_transaction and len(non_empty_parts) > 0:
                    # This might be a continuation of the description
                    current_transaction['description'] += ' ' + ' '.join(non_empty_parts)
        
        # Don't forget the last transaction
        if current_transaction:
            transactions.append(current_transaction)
        
        return transactions if transactions else (None, "No valid data found")
        
    except Exception as e:
        return None, str(e)

def parse_csv(raw_text):
    """
    Parse CSV format (tab or comma separated)
    """
    try:
        # First try Redash format
        result = parse_redash_format(raw_text)
        if result and not isinstance(result, tuple):
            return result
        
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
            
            # Accept both 'text' and 'raw_text' for flexibility
            raw_text = data.get('text', data.get('raw_text', '')).strip()
            use_gemini = data.get('use_gemini', True)
            force_gemini = data.get('force_gemini', False)  # New: force Gemini even for simple inputs
            
            if not raw_text:
                self.send_error(400, 'No transaction text provided')
                return
            
            parsed_transactions = []
            parsing_method = 'unknown'
            
            # Force Gemini mode (for fallback from frontend)
            if force_gemini and use_gemini:
                parsed_data, error = parse_with_gemini(raw_text, force_single=True)
                if parsed_data:
                    parsed_transactions = parsed_data if isinstance(parsed_data, list) else [parsed_data]
                    parsing_method = 'gemini-forced'
                else:
                    self.send_error(400, f'Gemini parsing failed: {error}')
                    return
            else:
                # Try traditional parsing first (fast)
                transactions, error = parse_traditional(raw_text)
                
                if transactions:
                    parsed_transactions = transactions
                    parsing_method = 'traditional'
                elif use_gemini:
                    # Use Gemini for intelligent parsing (supports multiple transactions)
                    parsed_data, error = parse_with_gemini(raw_text)
                    if parsed_data:
                        parsed_transactions = parsed_data if isinstance(parsed_data, list) else [parsed_data]
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

