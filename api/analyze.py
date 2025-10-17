"""
Vercel Serverless Function for Transaction Analysis with Gemini AI
SIMPLIFIED VERSION - NO TOKEN TRACKING
"""

from http.server import BaseHTTPRequestHandler
import json
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

try:
    import google.generativeai as genai
    from api.complete_sop_mapping import COMPLETE_SOP_MAPPING
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
    """Chat mode: Answer questions about transactions using Gemini"""
    if not GEMINI_API_KEY or not GEMINI_AVAILABLE:
        return {
            'response': 'Gemini is not configured.',
            'suggested_label': None
        }
    
    # Build SOP context
    agent_list = ', '.join(sorted(set(COMPLETE_SOP_MAPPING.keys())))
    
    sop_context = "Available transaction labels (agents):\n"
    for agent, info in sorted(COMPLETE_SOP_MAPPING.items())[:10]:
        labeling = info.get('labeling', 'N/A')[:100]
        sop_context += f"- {agent}: {labeling}\n"
    
    prompt = f"""You are a transaction reconciliation expert for Gusto's Platform Operations team.

{sop_context}

IMPORTANT: Use ONLY the internal SOP information provided above. If information is not in the SOPs, clearly state: "This information is not in our SOPs" and then provide general banking knowledge as a helpful reference, suggesting to consult a team lead.

Available labels: {agent_list}

Question: {question}

Provide a clear, concise answer. If suggesting a label, explain why."""
    
    try:
        response = model.generate_content(prompt)
        return {
            'response': response.text,
            'suggested_label': None
        }
    except Exception as e:
        return {
            'response': f'Error: {str(e)}',
            'suggested_label': None
        }

class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        """Handle preflight requests"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')
        self.end_headers()
    
    def do_GET(self):
        """Handle GET requests"""
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')
        self.send_header('Pragma', 'no-cache')
        self.end_headers()
        
        response = {
            'status': 'ok',
            'endpoint': '/api/analyze',
            'description': 'Chat mode for transaction questions'
        }
        self.wfile.write(json.dumps(response).encode('utf-8'))
    
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
                self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')
                self.send_header('Pragma', 'no-cache')
                self.end_headers()
                
                self.wfile.write(json.dumps(result).encode('utf-8'))
            else:
                self.send_error(400, 'Invalid mode. Use mode=chat')
                
        except Exception as e:
            self.send_error(500, str(e))
