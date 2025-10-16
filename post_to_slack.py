#!/usr/bin/env python3
"""
Automatically post CODE7 results to Slack
"""

import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

SLACK_ACCESS_TOKEN = os.getenv('SLACK_ACCESS_TOKEN')
CHANNEL = '#mytests'  # Test channel first

def post_to_slack(message):
    """Post message to Slack channel"""
    
    if not SLACK_ACCESS_TOKEN:
        print("❌ No SLACK_ACCESS_TOKEN found!")
        print("Set it in .env file")
        return False
    
    url = 'https://slack.com/api/chat.postMessage'
    headers = {
        'Authorization': f'Bearer {SLACK_ACCESS_TOKEN}',
        'Content-Type': 'application/json'
    }
    
    data = {
        'channel': CHANNEL,
        'text': message,
        'unfurl_links': False,
        'unfurl_media': False
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=10)
        result = response.json()
        
        if result.get('ok'):
            print(f"✅ Posted to {CHANNEL}")
            return True
        else:
            print(f"❌ Error: {result.get('error')}")
            return False
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

# Test message
if __name__ == '__main__':
    test_message = f"""🤖 **CODE7 Test Post**

⚠️ No Transactions - {datetime.now().strftime('%A, %B %d, %Y')}
📊 Weekend/Holiday
✅ Automated posting works!

_This is a test from CODE7 automation_
"""
    
    print("📤 Posting to Slack...")
    post_to_slack(test_message)




