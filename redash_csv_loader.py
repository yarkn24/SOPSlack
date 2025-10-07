"""
Redash CSV Data Loader
======================
Load transaction data from Redash CSV API endpoint.

Usage:
    python redash_csv_loader.py

Environment Variables:
    REDASH_API_KEY - Your Redash API key
    REDASH_BASE_URL - Redash instance URL
    REDASH_QUERY_ID - Query ID to fetch
"""

import os
import requests
import pandas as pd
from datetime import datetime
from typing import Optional
from io import StringIO


class RedashCSVLoader:
    """Load transaction data from Redash CSV endpoint."""
    
    def __init__(self, api_key: str = None, base_url: str = None, query_id: str = None):
        """
        Initialize Redash CSV loader.
        
        Args:
            api_key: Redash API key
            base_url: Redash instance URL
            query_id: Query ID to fetch
        """
        self.api_key = api_key or os.environ.get("REDASH_API_KEY")
        self.base_url = (base_url or os.environ.get("REDASH_BASE_URL", "")).rstrip("/")
        self.query_id = query_id or os.environ.get("REDASH_QUERY_ID")
        
        if not self.api_key:
            raise ValueError("REDASH_API_KEY not found")
        if not self.base_url:
            raise ValueError("REDASH_BASE_URL not found")
        if not self.query_id:
            raise ValueError("REDASH_QUERY_ID not found")
    
    def load_transactions(self, date: Optional[str] = None) -> pd.DataFrame:
        """
        Load transactions from Redash CSV endpoint.
        
        Args:
            date: Date filter (YYYY-MM-DD, default: today)
        
        Returns:
            DataFrame with transactions
        """
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        
        print(f"📊 Loading transactions for {date}...")
        
        # Build CSV API URL
        csv_url = f"{self.base_url}/api/queries/{self.query_id}/results.csv"
        params = {"api_key": self.api_key}
        
        print(f"🔗 Fetching: {csv_url}")
        
        # Fetch CSV data
        response = requests.get(csv_url, params=params)
        response.raise_for_status()
        
        # Parse CSV
        csv_data = StringIO(response.text)
        df = pd.read_csv(csv_data)
        
        print(f"✅ Loaded {len(df)} total rows")
        
        # Filter for today's date if date column exists
        if "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"])
            df = df[df["date"].dt.strftime("%Y-%m-%d") == date]
            print(f"📅 Filtered to {len(df)} transactions for {date}")
        
        # Show columns
        print(f"📋 Columns: {list(df.columns)}")
        
        # Check required columns
        required = ["description", "amount"]
        missing = [col for col in required if col not in df.columns]
        
        if missing:
            print(f"⚠️  Warning: Missing columns: {missing}")
        
        return df
    
    def test_connection(self) -> bool:
        """
        Test Redash connection.
        
        Returns:
            True if successful
        """
        try:
            csv_url = f"{self.base_url}/api/queries/{self.query_id}/results.csv"
            params = {"api_key": self.api_key}
            
            print("🔌 Testing Redash connection...")
            response = requests.get(csv_url, params=params)
            response.raise_for_status()
            
            print("✅ Redash connection successful!")
            print(f"   Query ID: {self.query_id}")
            print(f"   Data size: {len(response.text)} bytes")
            
            # Preview first few lines
            lines = response.text.split('\n')[:3]
            print(f"   Preview:")
            for line in lines:
                print(f"      {line[:80]}...")
            
            return True
            
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            return False


def main():
    """Test the Redash CSV loader."""
    print("=" * 80)
    print("REDASH CSV LOADER TEST")
    print("=" * 80)
    print()
    
    # Check environment variables
    api_key = os.environ.get("REDASH_API_KEY")
    base_url = os.environ.get("REDASH_BASE_URL")
    query_id = os.environ.get("REDASH_QUERY_ID")
    
    if not api_key:
        print("❌ REDASH_API_KEY not found")
        print()
        print("Set environment variables:")
        print('  export REDASH_API_KEY="jcocIPKxWDQ6ko43UIroBFHCspisGPsWbOmWB1He"')
        print('  export REDASH_BASE_URL="https://redash.zp-int.com"')
        print('  export REDASH_QUERY_ID="133695"')
        return
    
    print(f"🔑 API Key: {api_key[:20]}...")
    print(f"🌐 Base URL: {base_url}")
    print(f"🔢 Query ID: {query_id}")
    print()
    
    # Initialize loader
    try:
        loader = RedashCSVLoader()
    except ValueError as e:
        print(f"❌ Error: {e}")
        return
    
    # Test connection
    if not loader.test_connection():
        return
    
    print()
    
    # Load today's transactions
    try:
        df = loader.load_transactions()
        
        if len(df) > 0:
            print()
            print("=" * 80)
            print("SAMPLE DATA")
            print("=" * 80)
            print(df.head())
            print()
            print(f"✅ Total transactions: {len(df)}")
            print(f"📊 Columns: {list(df.columns)}")
            
            # Show value ranges
            if 'amount' in df.columns:
                print(f"💰 Amount range: ${df['amount'].min():,.2f} - ${df['amount'].max():,.2f}")
            
        else:
            print("⚠️  No transactions found for today")
        
    except Exception as e:
        print(f"❌ Error loading transactions: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

