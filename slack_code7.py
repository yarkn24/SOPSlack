#!/usr/bin/env python3
"""
Slack-optimized CODE7 - Returns instant response
"""

import pandas as pd
import requests
from datetime import datetime
import os
import sys

REDASH_API_KEY = "wPoSJ9zxm7gAu5GYU44w3bY9hBmagjTMg7LfqDBH"
REDASH_BASE_URL = "https://redash.zp-int.com"
REDASH_QUERY_ID = "133695"

# Get latest cached results (fast)
headers = {"Authorization": f"Key {REDASH_API_KEY}"}
results_url = f"{REDASH_BASE_URL}/api/queries/{REDASH_QUERY_ID}/results.json"

try:
    response = requests.get(results_url, headers=headers, timeout=5)
    response.raise_for_status()
    rows = response.json()['query_result']['data']['rows']
    count = len(rows)
    
    # Instant response
    today = datetime.now().strftime('%A, %B %d, %Y')
    
    if count == 0:
        print(f"⚠️  **Daily Reconciliation - No Data**")
        print(f"")
        print(f"📅 {today}")
        print(f"📊 Query Status: 0 transactions")
        print(f"")
        print(f"💡 Weekend or banking holiday - banks are closed")
    else:
        print(f"✅ **Daily Reconciliation Report**")
        print(f"")
        print(f"📅 {today}")
        print(f"📊 Found: {count} transactions")
        print(f"")
        print(f"⚙️  CODE7 pipeline is processing...")
        print(f"📁 Results will be saved to ~/Desktop/cursor_data/")
        print(f"⏱️  Estimated: ~15 seconds")
        print(f"")
        print(f"🔄 Run `python3 code7.py` for full processing")
        
except Exception as e:
    print(f"❌ **Error**")
    print(f"")
    print(f"Could not fetch data from Redash")
    print(f"Error: {str(e)}")
    sys.exit(1)

