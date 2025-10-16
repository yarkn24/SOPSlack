#!/usr/bin/env python3
"""
Fetch RAW data from Redash and save to CSV
"""

import pandas as pd
import requests
import time

REDASH_API_KEY = "wPoSJ9zxm7gAu5GYU44w3bY9hBmagjTMg7LfqDBH"
REDASH_BASE_URL = "https://redash.zp-int.com"
REDASH_QUERY_ID = "133695"

print("📥 Fetching from Redash...")
headers = {"Authorization": f"Key {REDASH_API_KEY}"}
refresh_url = f"{REDASH_BASE_URL}/api/queries/{REDASH_QUERY_ID}/refresh"

try:
    refresh_response = requests.post(refresh_url, headers=headers, timeout=30)
    refresh_response.raise_for_status()
    job_id = refresh_response.json()['job']['id']
    
    # Poll for results
    job_url = f"{REDASH_BASE_URL}/api/jobs/{job_id}"
    for _ in range(60):
        time.sleep(2)
        job_response = requests.get(job_url, headers=headers, timeout=10)
        job_response.raise_for_status()
        status = job_response.json()['job']['status']
        if status == 3:  # SUCCESS
            break
        elif status == 4:  # FAILURE
            raise Exception("Query failed")
    
    # Get results
    results_url = f"{REDASH_BASE_URL}/api/queries/{REDASH_QUERY_ID}/results.json"
    results_response = requests.get(results_url, headers=headers, timeout=30)
    results_response.raise_for_status()
    rows = results_response.json()['query_result']['data']['rows']
    df = pd.DataFrame(rows)
    
    print(f"✅ Fetched {len(df):,} transactions")
    
    if len(df) == 0:
        print("⚠️  No transactions (probably weekend)")
        exit(0)
    
    # Save
    output_file = f"/Users/yarkin.akcil/Desktop/cursor_data/redash_raw_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv"
    df.to_csv(output_file, index=False)
    print(f"💾 Saved to: {output_file}")
    
except Exception as e:
    print(f"❌ Error: {e}")




