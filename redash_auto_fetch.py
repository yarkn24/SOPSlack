"""
Redash Auto Fetch with Refresh
================================
Automatically refresh and fetch latest data from Redash.
No manual intervention needed!

Usage:
    python redash_auto_fetch.py
"""

import os
import time
import requests
import pandas as pd
from io import StringIO
from datetime import datetime


class RedashAutoFetcher:
    """Automatically refresh and fetch data from Redash."""
    
    def __init__(self):
        self.api_key = os.environ.get("REDASH_API_KEY", "wPoSJ9zxm7gAu5GYU44w3bY9hBmagjTMg7LfqDBH")
        self.base_url = os.environ.get("REDASH_BASE_URL", "https://redash.zp-int.com")
        self.query_id = os.environ.get("REDASH_QUERY_ID", "133695")
    
    def refresh_query(self, max_wait=900):  # 15 minutes
        """
        Refresh query and wait for completion.
        
        Args:
            max_wait: Maximum seconds to wait for query completion
        
        Returns:
            Query result ID
        """
        print(f"🔄 Refreshing query {self.query_id}...")
        
        # Start refresh
        refresh_url = f"{self.base_url}/api/queries/{self.query_id}/refresh"
        params = {"api_key": self.api_key, "max_age": 0}
        
        response = requests.post(refresh_url, params=params)
        response.raise_for_status()
        
        job_data = response.json()
        job_id = job_data['job']['id']
        
        print(f"⏳ Job started: {job_id}")
        print(f"   Waiting for completion (max {max_wait}s)...")
        
        # Poll job status
        start_time = time.time()
        job_url = f"{self.base_url}/api/jobs/{job_id}"
        
        while time.time() - start_time < max_wait:
            time.sleep(5)  # Check every 5 seconds
            
            response = requests.get(job_url, params={"api_key": self.api_key})
            response.raise_for_status()
            
            job_info = response.json()['job']
            status = job_info['status']
            
            # Status codes: 1=pending, 2=started, 3=success, 4=failure, 5=cancelled
            if status == 3:  # Success
                query_result_id = job_info['query_result_id']
                print(f"✅ Query completed! Result ID: {query_result_id}")
                return query_result_id
            
            elif status == 4:  # Failure
                error = job_info.get('error', 'Unknown error')
                raise Exception(f"Query failed: {error}")
            
            elif status == 5:  # Cancelled
                raise Exception("Query was cancelled")
            
            # Still running - show progress every 30 seconds
            elapsed = int(time.time() - start_time)
            if elapsed % 30 < 5:  # Show every 30 seconds
                minutes = elapsed // 60
                seconds = elapsed % 60
                print(f"   Still running... ({minutes}m {seconds}s elapsed)")
        
        raise TimeoutError(f"Query did not complete within {max_wait} seconds")
    
    def get_csv_data(self):
        """
        Get CSV data from Redash (uses cached or latest result).
        
        Returns:
            DataFrame with transaction data
        """
        print(f"📥 Fetching CSV data...")
        
        csv_url = f"{self.base_url}/api/queries/{self.query_id}/results.csv"
        params = {"api_key": self.api_key}
        
        response = requests.get(csv_url, params=params)
        response.raise_for_status()
        
        csv_data = StringIO(response.text)
        df = pd.read_csv(csv_data)
        
        print(f"✅ Loaded {len(df)} rows")
        return df
    
    def fetch_fresh_data(self):
        """
        Refresh query and fetch fresh data.
        
        Returns:
            DataFrame with fresh transaction data
        """
        print("=" * 80)
        print(f"REDASH AUTO FETCH - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
        print()
        
        # Refresh query
        try:
            self.refresh_query(max_wait=900)  # 15 minutes
        except Exception as e:
            print(f"⚠️  Refresh failed: {e}")
            print("   Falling back to cached results...")
        
        print()
        
        # Fetch data
        df = self.get_csv_data()
        
        print()
        print("📊 Data Summary:")
        print(f"   Total rows: {len(df)}")
        print(f"   Columns: {list(df.columns)}")
        
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
            print(f"   Date range: {df['date'].min()} to {df['date'].max()}")
        
        if 'payment_method' in df.columns:
            print(f"   Unique payment methods: {df['payment_method'].nunique()}")
            for pm, count in df['payment_method'].value_counts().head(10).items():
                print(f"      • {pm}: {count}")
        
        if 'account' in df.columns:
            print(f"   Unique accounts: {df['account'].nunique()}")
            for acc, count in df['account'].value_counts().head(10).items():
                print(f"      • {acc}: {count}")
        
        print()
        print("=" * 80)
        
        return df


def main():
    """Main function."""
    fetcher = RedashAutoFetcher()
    df = fetcher.fetch_fresh_data()
    
    print()
    print("🎉 Data ready for prediction!")
    print(f"   {len(df)} transactions loaded")


if __name__ == "__main__":
    main()

