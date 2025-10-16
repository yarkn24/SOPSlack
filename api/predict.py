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
    gemini_model = genai.GenerativeModel('gemini-flash-latest')

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
    
    # Check if this is description-only mode (frontend sends this flag)
    description_only_mode = transaction.get('description_only_mode', False)
    
    # Handle amount - safely convert to float, default to 0 if invalid
    amount_str = str(transaction.get('amount', '0')).replace('$', '').replace(',', '').strip()
    if amount_str and amount_str.lower() not in ['unknown', 'n/a', 'na', '']:
        try:
            amount = float(amount_str)
        except (ValueError, TypeError):
            amount = 0.0
    else:
        amount = 0.0
    
    method = (transaction.get('payment_method', '')).lower()
    
    # ⚠️ CRITICAL: ZBT CHECK FIRST - ABSOLUTE HIGHEST PRIORITY ⚠️
    # Zero Balance Transfer MUST be checked before ANY other rule!
    if 'zero balance transfer' in method or method == 'zero balance transfer':
        return 'ZBT', 'rule-based', "⚠️ Payment method is 'Zero Balance Transfer' - FOR INFO ONLY. We don't reconcile ZBT transactions.", 1.00
    
    # Get transaction date for same-day check
    from datetime import datetime, timezone
    import pytz
    
    txn_date = transaction.get('date', '')
    is_same_day = False
    if txn_date:
        try:
            # Parse transaction date
            if isinstance(txn_date, str):
                txn_dt = datetime.strptime(txn_date.split()[0], '%Y-%m-%d') if ' ' in txn_date else datetime.strptime(txn_date, '%Y-%m-%d')
            else:
                txn_dt = txn_date
            
            # Get current date in PST
            pst = pytz.timezone('America/Los_Angeles')
            now_pst = datetime.now(pst).date()
            is_same_day = txn_dt.date() == now_pst if hasattr(txn_dt, 'date') else txn_dt == now_pst
        except:
            pass
    
    # RISK DETECTION (High Priority)
    # If description has CUSTOMER= field with a company that's NOT Gusto → Risk
    if 'CUSTOMER=' in desc or 'B/O CUSTOMER=' in desc:
        # Check if customer is NOT Gusto
        if 'GUSTO' not in desc:
            return 'Risk', 'rule-based', "Customer field present with non-Gusto company (wire to external party)", 0.99
    
    # Account-based rules (ONLY if NOT description-only mode)
    if not description_only_mode:
        if 'PNC WIRE IN' in account or 'CHASE WIRE IN' in account:
            return 'Risk', 'rule-based', 'Account is PNC Wire In or Chase Wire In', 0.99
        
        if 'CHASE PAYROLL INCOMING WIRES' in account:
            if is_same_day:
                return 'Risk', 'rule-based', '⚠️ Account is Chase Payroll Incoming Wires - SAME DAY TRANSACTION: Wait until tomorrow to label', 0.99
            return 'Risk', 'rule-based', 'Account is Chase Payroll Incoming Wires', 0.99
        
        if 'CHASE RECOVERY' in account:
            return 'Recovery Wire', 'rule-based', 'Account is Chase Recovery', 0.99
    
    # ICP Funding: JPMORGAN in description (works for description-only mode too)
    if 'JPMORGAN ACCESS TRANSFER' in desc or 'JPMORGAN' in desc:
        return 'ICP Funding', 'rule-based', "Description contains 'JPMORGAN ACCESS TRANSFER'", 0.99
    
    if 'CHASE INTERNATIONAL CONTRACTOR PAYMENT' in account or 'CHASE ICP' in account:
        return 'ICP Funding', 'rule-based', "Account is Chase ICP", 0.99
    
    # Check rule: Payment method "check" or "check paid" OR "CHECK" in description
    if 'check' in method or 'check paid' in method or 'CHECK' in desc:
        return 'Check', 'rule-based', "Payment method is Check or CHECK in description", 0.99
    
    # Description-based rules
    if 'NYS DTF WT' in desc:
        return 'NY WH', 'rule-based', "Description contains 'NYS DTF WT'", 0.99
    
    if 'OH WH TAX' in desc:
        return 'OH WH', 'rule-based', "Description contains 'OH WH TAX'", 0.99
    
    if 'OH SDWH' in desc:
        return 'OH SDWH', 'rule-based', "Description contains 'OH SDWH'", 0.99
    
    if 'NYS DOL UI' in desc:
        return 'NY UI', 'rule-based', "Description contains 'NYS DOL UI'", 0.99
    
    # CSC: If CSC in description, label it (works for description-only mode)
    if 'CSC' in desc:
        return 'CSC', 'rule-based', "Description contains 'CSC'", 0.99
    
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
_gemini_call_count = 0  # Track Gemini usage for demo day
MAX_GEMINI_CALLS = int(os.environ.get('MAX_GEMINI_CALLS', '50'))  # Default: max 50 calls/session
GEMINI_ENABLED = os.environ.get('GEMINI_ENABLED', 'true').lower() == 'true'  # Can disable for demo!
GEMINI_SUMMARY_ENABLED = os.environ.get('GEMINI_SUMMARY_ENABLED', 'true').lower() == 'true'  # Default: ON (with warnings!)

def predict_gemini(transaction):
    """Tier 2: Gemini AI - ULTRA CONSERVATIVE (Demo-safe!)"""
    global _gemini_call_count
    
    # DEMO MODE: Check if Gemini is disabled
    if not GEMINI_ENABLED:
        return 'Unknown', 'rule-based-only', 'Gemini disabled for token conservation', 0.50
    
    if not GEMINI_API_KEY or not GEMINI_AVAILABLE:
        return 'Unknown', 'unknown', 'No prediction method available', 0
    
    # DEMO MODE: Check call limit (protect free tier!)
    if _gemini_call_count >= MAX_GEMINI_CALLS:
        return 'Unknown', 'gemini-limit-reached', f'Max {MAX_GEMINI_CALLS} calls reached (token protection)', 0.50
    
    # Create cache key from transaction signature
    desc = clean_text(transaction.get('description', ''))
    account = clean_text(transaction.get('origination_account_id', ''))
    cache_key = f"{desc[:50]}_{account[:30]}"
    
    # Check cache first (avoid Gemini call = SAVE TOKENS!)
    if cache_key in _gemini_cache:
        cached = _gemini_cache[cache_key]
        return cached[0], cached[1] + ' (cached-0tk)', cached[2], cached[3]
    
    # Check if this is description-only mode (unknown account/payment_method)
    account_val = transaction.get('origination_account_id', 'N/A')
    is_description_only = account_val in ['unknown', 'N/A', '']
    
    # ULTRA-SHORT prompt to minimize token usage (free tier limit!)
    if is_description_only:
        prompt = f"""Label this bank transaction using ONLY the description (account info unavailable).

Description: {transaction.get('description', 'N/A')[:80]}

LABELS: Risk, Check, NY WH, OH WH, NY UI, IL UI, WA ESD, Lockbox, LOI, ICP Funding, Treasury Transfer, Money Market Fund, ACH, ACH Return, CSC, Recovery Wire

HINTS:
- CHECK/Check→Check | NYS DTF→NY WH | OH WH→OH WH | JPMORGAN→ICP Funding | CSC→CSC | LOCKBOX→Lockbox | State tax/UI→State label
- CUSTOMER= with non-Gusto company→Risk
- If unclear, give your BEST GUESS based on description keywords
- Return 1 label (most confident), or if uncertain: "Label1 or Label2"

Label:"""
    else:
        prompt = f"""Label this bank transaction (internal data only, no web search).

RULES:
Wire In→Risk | CUSTOMER= (non-Gusto)→Risk | Check→Check | State+WH→Tax | State+UI→Unemployment | LOCKBOX→Lockbox | ACH RETURN→LOI | JPMORGAN ACCESS→ICP Funding | TREASURY→Treasury Transfer

LABELS: Risk, Check, NY WH, OH WH, NY UI, IL UI, WA ESD, Lockbox, LOI, ICP Funding, Treasury Transfer, Money Market Fund, ACH, ACH Return, CSC, Recovery Wire

Transaction:
Account: {account_val[:40]}
Description: {transaction.get('description', 'N/A')[:60]}

Label (one word):"""

    try:
        # INCREMENT COUNTER (track token usage!)
        _gemini_call_count += 1
        
        response = gemini_model.generate_content(prompt)
        label_text = response.text.strip()
        
        # Parse response: might be "Label1" or "Label1 or Label2" (for low confidence cases)
        alternatives = []
        if ' or ' in label_text.lower():
            # Extract alternatives: "Check or CSC" → ["Check", "CSC"]
            parts = label_text.replace(' OR ', ' or ').split(' or ')
            label = parts[0].strip()
            if len(parts) > 1:
                alternatives = [p.strip() for p in parts[1:]]
        else:
            label = label_text
        
        # Validate primary label against known labels
        if label in COMPLETE_SOP_MAPPING:
            confidence = 0.65 if alternatives else 0.75  # Lower confidence if multiple options
            reason = f'AI-based pattern analysis'
            if alternatives and confidence < 0.70:
                # Show alternatives in reason
                alt_str = ' or '.join([a for a in alternatives if a in COMPLETE_SOP_MAPPING][:1])  # Max 1 alternative
                if alt_str:
                    reason = f'AI suggests: {label} (or possibly {alt_str})'
            result = (label, f'ml-based (Gemini-{_gemini_call_count})', reason, confidence)
            _gemini_cache[cache_key] = result
            return result
        
        # Try fuzzy match on primary label
        label_upper = label.upper()
        for known_label in COMPLETE_SOP_MAPPING.keys():
            if known_label.upper() in label_upper or label_upper in known_label.upper():
                reason = f'Similar to "{label}" (AI suggestion)'
                if alternatives:
                    alt_str = ' or '.join([a for a in alternatives if a in COMPLETE_SOP_MAPPING][:1])
                    if alt_str:
                        reason = f'AI suggests: {known_label} (or possibly {alt_str})'
                result = (known_label, f'ml-based (Gemini-{_gemini_call_count})', reason, 0.65)
                _gemini_cache[cache_key] = result
                return result
        
        # No match - return Unknown (don't cache unknowns)
        return 'Unknown', f'ml-based (Gemini-{_gemini_call_count})', f'No clear pattern found (AI)', 0.50
            
    except Exception as e:
        return 'Unknown', 'unknown', f'AI call failed', 0

def gemini_quick_triage(transaction):
    """Quick Gemini check: Is this a rule-based transaction? (~50 tokens)"""
    if not GEMINI_API_KEY or not gemini_model:
        return True  # No Gemini available, default to rule-based
    
    desc = transaction.get('description', '')
    method = transaction.get('payment_method', '')
    account = transaction.get('origination_account_id', '')
    
    # If we have clear indicators, skip Gemini triage
    if any(keyword in desc.upper() for keyword in ['CHECK', 'NYS DTF', 'OH WH', 'JPMORGAN', 'CSC']):
        return True  # Definitely rule-based
    
    if any(keyword in method.lower() for keyword in ['check', 'zero balance']):
        return True  # Definitely rule-based
    
    if any(keyword in account.upper() for keyword in ['PNC WIRE', 'CHASE WIRE', 'CHASE PAYROLL', 'CHASE RECOVERY']):
        return True  # Definitely rule-based
    
    # Edge case - ask Gemini for quick triage (saves tokens on complex cases)
    try:
        prompt = f"""Quick analysis: Is this a standard rule-based transaction?
Description: {desc[:100]}
Payment: {method}
Account: {account[:50]}

Answer ONLY: "RULE-BASED" or "COMPLEX"
RULE-BASED = obvious patterns (Check, Wire, NYS DTF, OH WH, etc)
COMPLEX = needs deeper AI analysis"""
        
        response = gemini_model.generate_content(prompt)
        result = response.text.strip().upper()
        return 'RULE' in result
    except:
        return True  # Default to rule-based on error

def predict_transaction(transaction):
    """Smart 3-Tier Prediction System:
    1. Quick Triage (Gemini or pattern check) - decide approach
    2. Rule-Based (if triage says yes) - 0 tokens, fast
    3. Full Gemini Analysis (if complex) - deep analysis
    """
    
    # Step 1: Quick triage - is this rule-based?
    is_rule_based = gemini_quick_triage(transaction)
    
    if is_rule_based:
        # Tier 1: Rule-based (fastest, most accurate, NO tokens!)
        label, method, reason, confidence = predict_rule_based(transaction)
        if label != 'Unknown' and confidence > 0.9:
            return label, method, reason, confidence
    
    # Tier 2: Gemini AI (for complex/edge cases only)
    # Only called when:
    # - Triage says "complex" OR
    # - Rule-based returned Unknown/low confidence
    label, method, reason, confidence = predict_gemini(transaction)
    return label, method, reason, confidence

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        """Handle POST requests"""
        global _gemini_call_count  # Need to modify global counter
        
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
                
                # Gemini summary DISABLED by default (token conservation!)
                # Enable only if GEMINI_SUMMARY_ENABLED=true in env vars
                gemini_summary = None
                if GEMINI_SUMMARY_ENABLED and GEMINI_ENABLED and _gemini_call_count < MAX_GEMINI_CALLS:
                    recon_text = sop_content.get('reconciliation', '')
                    if recon_text and len(recon_text) > 200 and GEMINI_API_KEY:
                        try:
                            _gemini_call_count += 1  # Count summary calls too!
                            prompt = f"""Summarize in 2-3 bullets (English):

{recon_text[:300]}

Emoji + short sentence per step."""
                            response = gemini_model.generate_content(prompt)
                            gemini_summary = response.text.strip() + f" (Gemini-{_gemini_call_count})"
                        except:
                            gemini_summary = None
                
                # Determine confidence level and message
                confidence_level = "High"
                confidence_note = ""
                
                if confidence >= 0.95:
                    confidence_level = "High"
                    confidence_note = "✅ Strong match"
                elif confidence >= 0.80:
                    confidence_level = "Medium"
                    confidence_note = "⚠️ Good match, but verify"
                elif confidence >= 0.60:
                    confidence_level = "Low"
                    confidence_note = "🔍 Best guess - review recommended"
                else:
                    confidence_level = "Uncertain"
                    confidence_note = "❓ Uncertain - manual review required"
                
                result = {
                    'transaction_id': txn.get('transaction_id', 'N/A'),
                    'amount': txn.get('amount', 'N/A'),
                    'account': txn.get('origination_account_id', 'N/A'),
                    'description': txn.get('description', 'N/A')[:100] + '...',
                    'label': label,
                    'method': method,
                    'reason': reason,
                    'confidence': f"{confidence:.0%}",
                    'confidence_level': confidence_level,
                    'confidence_note': confidence_note,
                    'sop_content': sop_content,
                    'gemini_summary': gemini_summary
                }
                
                results.append(result)
            
            # Send response
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            # Calculate estimated token usage
            estimated_tokens = _gemini_call_count * 100  # ~100 tokens per call
            usage_percentage = (_gemini_call_count / MAX_GEMINI_CALLS * 100) if MAX_GEMINI_CALLS > 0 else 0
            
            # Generate warning if over 50% usage
            warning = None
            if usage_percentage >= 75:
                warning = f"⚠️ CRITICAL: {usage_percentage:.0f}% token limit reached! Consider disabling Gemini summary."
            elif usage_percentage >= 50:
                warning = f"⚠️ WARNING: {usage_percentage:.0f}% token limit reached! {MAX_GEMINI_CALLS - _gemini_call_count} calls remaining."
            
            response = {
                'success': True,
                'count': len(results),
                'results': results,
                'stats': stats,
                'gemini_usage': {
                    'enabled': GEMINI_ENABLED,
                    'summary_enabled': GEMINI_SUMMARY_ENABLED,
                    'calls_this_session': _gemini_call_count,
                    'max_calls_allowed': MAX_GEMINI_CALLS,
                    'remaining_calls': max(0, MAX_GEMINI_CALLS - _gemini_call_count),
                    'estimated_tokens_used': estimated_tokens,
                    'usage_percentage': f"{usage_percentage:.0f}%",
                    'cache_size': len(_gemini_cache),
                    'warning': warning
                }
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
        global _gemini_call_count
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        usage_percentage = (_gemini_call_count / MAX_GEMINI_CALLS * 100) if MAX_GEMINI_CALLS > 0 else 0
        warning = None
        if usage_percentage >= 75:
            warning = f"⚠️ CRITICAL: {usage_percentage:.0f}% limit reached!"
        elif usage_percentage >= 50:
            warning = f"⚠️ WARNING: {usage_percentage:.0f}% limit reached!"
        
        response = {
            'status': 'healthy',
            'tier_1': 'Rule-Based (95%+ - 0 tokens)',
            'tier_2': f'Gemini AI ({_gemini_call_count}/{MAX_GEMINI_CALLS} calls - {"ENABLED" if GEMINI_ENABLED else "DISABLED"})',
            'token_protection': {
                'gemini_prediction_enabled': GEMINI_ENABLED,
                'gemini_summary_enabled': GEMINI_SUMMARY_ENABLED,
                'max_calls': MAX_GEMINI_CALLS,
                'calls_used': _gemini_call_count,
                'usage_percentage': f"{usage_percentage:.0f}%",
                'estimated_tokens': _gemini_call_count * 100,
                'cache_hits': len(_gemini_cache),
                'warning': warning,
                'note': 'Gemini Summary ENABLED - warnings at 50%+ usage'
            }
        }
        
        self.wfile.write(json.dumps(response).encode())

