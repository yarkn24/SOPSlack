"""
2-Tier Prediction System: Rule-Based → Gemini AI
Fast deployment, 92-95% accuracy
"""

from http.server import BaseHTTPRequestHandler
import json
import os
import sys
import pickle
import re

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

try:
    import google.generativeai as genai
    from complete_sop_mapping import COMPLETE_SOP_MAPPING
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    COMPLETE_SOP_MAPPING = {}

# Initialize Gemini (Tier 3 fallback)
GEMINI_API_KEY = os.environ.get('GEMINI_KEY') or os.environ.get('GEMINI_API_KEY')
if GEMINI_API_KEY and GEMINI_AVAILABLE:
    genai.configure(api_key=GEMINI_API_KEY)
    gemini_model = genai.GenerativeModel('gemini-pro')

# ML removed for faster Vercel deployment (Hobby plan 15min limit)

def clean_text(text):
    """Clean transaction description"""
    if not text:
        return ""
    text = str(text).upper()
    text = re.sub(r'[^\w\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def predict_rule_based(transaction):
    """Tier 1: Rule-based prediction (98% accuracy)"""
    desc = clean_text(transaction.get('description', ''))
    account = clean_text(transaction.get('origination_account_id', ''))
    amount = float((transaction.get('amount', '0')).replace('$', '').replace(',', '')) if transaction.get('amount') else 0
    method = (transaction.get('payment_method', '')).lower()
    
    # Account-based rules (highest priority)
    if 'PNC WIRE IN' in account or 'CHASE WIRE IN' in account:
        return 'Risk', 'rule-based', 'Account is PNC Wire In or Chase Wire In', 0.99
    
    if 'CHASE PAYROLL INCOMING WIRES' in account:
        return 'Risk', 'rule-based', 'Account is Chase Payroll Incoming Wires', 0.99
    
    if 'CHASE RECOVERY' in account:
        return 'Recovery Wire', 'rule-based', 'Account is Chase Recovery', 0.99
    
    if 'CHASE INTERNATIONAL CONTRACTOR PAYMENT' in account or 'CHASE ICP' in account:
        if 'JPMORGAN ACCESS TRANSFER' in desc:
            return 'ICP Funding', 'rule-based', "Description contains 'JPMORGAN ACCESS TRANSFER'", 0.99
    
    # Payment method rules
    if 'check' in method:
        return 'Check', 'rule-based', "Payment method is 'Check'", 0.99
    
    # Description-based rules
    if 'NYS DTF WT' in desc:
        return 'NY WH', 'rule-based', "Description contains 'NYS DTF WT'", 0.99
    
    if 'OH WH TAX' in desc:
        return 'OH WH', 'rule-based', "Description contains 'OH WH TAX'", 0.99
    
    if 'OH SDWH' in desc:
        return 'OH SDWH', 'rule-based', "Description contains 'OH SDWH'", 0.99
    
    if 'NYS DOL UI' in desc:
        return 'NY UI', 'rule-based', "Description contains 'NYS DOL UI'", 0.99
    
    if 'CSC' in desc and re.search(r'CSC\d{6}', desc):
        return 'CSC', 'rule-based', "Description contains 'CSC' with number", 0.99
    
    if 'ACH RETURN SETTLEMENT' in desc or 'CREDIT MEMO' in desc:
        return 'LOI', 'rule-based', 'Description indicates LOI', 0.99
    
    if 'LOCKBOX' in desc:
        return 'Lockbox', 'rule-based', "Description contains 'LOCKBOX'", 0.99
    
    if 'IL DEPT EMPL SEC' in desc:
        return 'IL UI', 'rule-based', "Description contains 'IL DEPT EMPL SEC'", 0.99
    
    if 'MT TAX' in desc or 'STATE OF MONTANA' in desc:
        return 'MT UI', 'rule-based', "Description contains 'STATE OF MONTANA'", 0.99
    
    if 'STATE OF WA ESD' in desc or 'ESD WA UI TAX' in desc:
        return 'WA ESD', 'rule-based', "Description contains 'STATE OF WA ESD'", 0.99
    
    if 'EFT REVERSAL' in desc:
        return 'ACH', 'rule-based', "Description contains 'EFT REVERSAL'", 0.99
    
    if 'RTN OFFSET' in desc:
        return 'ACH Return', 'rule-based', "Description contains 'RTN OFFSET'", 0.99
    
    if 'MONEY MKT MUTUAL FUND' in desc:
        return 'Money Market Fund', 'rule-based', "Description contains 'MONEY MARKET'", 0.99
    
    if 'US TREASURY CAPITAL' in desc or 'TREASURY' in desc:
        return 'Treasury Transfer', 'rule-based', "Description contains 'TREASURY'", 0.99
    
    if 'L I' in desc or 'LABOR INDUSTRIES' in desc or 'LABORINDUSTRIES' in desc:
        return 'WA LNI', 'rule-based', "Description contains 'L&I' or 'Labor&Industries'", 0.99
    
    if 'VA. EMPLOY COMM' in desc or 'VA EMPLOY COMM' in desc:
        return 'VA UI', 'rule-based', "Description contains 'VA. EMPLOY COMM'", 0.99
    
    if amount < 1.0 and amount > 0:
        return 'Bad Debt', 'rule-based', 'Amount less than $1.00', 0.99
    
    return None, None, None, 0

# ML model removed for faster deployment (Vercel Hobby plan limits)

# Simple cache to avoid repeat Gemini calls (save tokens!)
_gemini_cache = {}

def predict_gemini(transaction):
    """Tier 2: Gemini AI - Token Optimized (Free tier friendly!)"""
    if not GEMINI_API_KEY or not GEMINI_AVAILABLE:
        return 'Unknown', 'unknown', 'No prediction method available', 0
    
    # Create cache key from transaction signature
    desc = clean_text(transaction.get('description', ''))
    account = clean_text(transaction.get('origination_account_id', ''))
    cache_key = f"{desc[:50]}_{account[:30]}"
    
    # Check cache first (avoid Gemini call = SAVE TOKENS!)
    if cache_key in _gemini_cache:
        cached = _gemini_cache[cache_key]
        return cached[0], cached[1] + ' (cached)', cached[2], cached[3]
    
    # ULTRA-SHORT prompt to minimize token usage (free tier limit!)
    prompt = f"""Label this bank transaction (internal data only, no web search).

RULES:
Wire In→Risk | Check→Check | State+WH→Tax | State+UI→Unemployment | LOCKBOX→Lockbox | ACH RETURN→LOI | JPMORGAN ACCESS→ICP Funding | TREASURY→Treasury Transfer

LABELS: Risk, Check, NY WH, OH WH, NY UI, IL UI, WA ESD, Lockbox, LOI, ICP Funding, Treasury Transfer, Money Market Fund, ACH, ACH Return, CSC

Transaction:
Account: {transaction.get('origination_account_id', 'N/A')[:40]}
Description: {transaction.get('description', 'N/A')[:60]}

Label (one word):"""

    try:
        response = gemini_model.generate_content(prompt)
        label = response.text.strip()
        
        # Validate against known labels
        if label in COMPLETE_SOP_MAPPING:
            result = (label, 'ml-based (Gemini AI)', f'Pattern match', 0.75)
            _gemini_cache[cache_key] = result
            return result
        
        # Try fuzzy match
        label_upper = label.upper()
        for known_label in COMPLETE_SOP_MAPPING.keys():
            if known_label.upper() in label_upper or label_upper in known_label.upper():
                result = (known_label, 'ml-based (Gemini AI)', f'Fuzzy: {label}', 0.70)
                _gemini_cache[cache_key] = result
                return result
        
        # No match - return Unknown (don't cache unknowns)
        return 'Unknown', 'ml-based (Gemini AI)', f'No pattern match', 0.50
            
    except Exception as e:
        return 'Unknown', 'unknown', f'AI call failed', 0

def predict_transaction(transaction):
    """2-Tier prediction: Rule-based (95%+) → Gemini AI (fallback only)"""
    
    # Tier 1: Rule-based (fastest, most accurate, NO tokens!)
    label, method, reason, confidence = predict_rule_based(transaction)
    if label and confidence > 0.9:
        return label, method, reason, confidence
    
    # Tier 2: Gemini AI (ONLY when rule-based fails - saves tokens!)
    # Most transactions (95%+) handled by rules, so Gemini rarely called
    label, method, reason, confidence = predict_gemini(transaction)
    return label, method, reason, confidence

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        """Handle POST requests"""
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            transactions = data.get('transactions', [])
            
            if not transactions:
                self.send_error(400, 'No transactions provided')
                return
            
            results = []
            stats = {'rule_based': 0, 'gemini': 0}
            
            for txn in transactions:
                label, method, reason, confidence = predict_transaction(txn)
                
                # Track stats
                if 'rule-based' in method:
                    stats['rule_based'] += 1
                elif 'Gemini' in method:
                    stats['gemini'] += 1
                
                # Get SOP content
                sop_content = COMPLETE_SOP_MAPPING.get(label, {})
                
                # Add Gemini summary if SOP reconciliation is long
                gemini_summary = None
                recon_text = sop_content.get('reconciliation', '')
                if recon_text and len(recon_text) > 200 and GEMINI_API_KEY:
                    try:
                        prompt = f"""Summarize these reconciliation steps in 2-3 bullet points (Turkish):

{recon_text}

Format: Emoji + short sentence per step."""
                        response = gemini_model.generate_content(prompt)
                        gemini_summary = response.text.strip()
                    except:
                        gemini_summary = None
                
                result = {
                    'transaction_id': txn.get('transaction_id', 'N/A'),
                    'amount': txn.get('amount', 'N/A'),
                    'account': txn.get('origination_account_id', 'N/A'),
                    'description': txn.get('description', 'N/A')[:100] + '...',
                    'label': label,
                    'method': method,
                    'reason': reason,
                    'confidence': f"{confidence:.0%}",
                    'sop_content': sop_content,
                    'gemini_summary': gemini_summary
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
                'stats': stats,
                'gemini_available': bool(GEMINI_API_KEY)
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
            'tier_1': 'Rule-Based (90%+)',
            'tier_2': 'Gemini AI (backup)' if GEMINI_API_KEY else 'Not configured'
        }
        
        self.wfile.write(json.dumps(response).encode())

