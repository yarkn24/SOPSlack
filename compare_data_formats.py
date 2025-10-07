"""
Compare Redash Data vs Training Data
=====================================
Identify all unique payment methods and accounts.
Verify mapping is correct.
"""

import pandas as pd
import os
import requests
from io import StringIO

# Redash config
REDASH_API_KEY = "wPoSJ9zxm7gAu5GYU44w3bY9hBmagjTMg7LfqDBH"
REDASH_BASE_URL = "https://redash.zp-int.com"
REDASH_QUERY_ID = "133695"

print("=" * 80)
print("REDASH DATA ANALYSIS (2024+)")
print("=" * 80)
print()

# Fetch Redash data
print("📊 Fetching Redash data...")
csv_url = f"{REDASH_BASE_URL}/api/queries/{REDASH_QUERY_ID}/results.csv"
params = {"api_key": REDASH_API_KEY}
response = requests.get(csv_url, params=params)
response.raise_for_status()

# Parse CSV
csv_data = StringIO(response.text)
redash_df = pd.read_csv(csv_data)
print(f"✅ Loaded {len(redash_df)} transactions from Redash")
print()

# Show columns
print("📋 Redash Columns:")
for col in redash_df.columns:
    print(f"   - {col}")
print()

# Unique Payment Methods
print("💳 UNIQUE PAYMENT METHODS in Redash:")
payment_methods = redash_df['payment_method'].value_counts()
for pm, count in payment_methods.items():
    print(f"   '{pm}': {count} transactions")
print()

# Unique Accounts
print("🏦 UNIQUE ACCOUNTS in Redash:")
accounts = redash_df['account'].value_counts()
for acc, count in accounts.items():
    print(f"   '{acc}': {count} transactions")
print()

# Check if training data exists
print("=" * 80)
print("TRAINING DATA ANALYSIS")
print("=" * 80)
print()

train_file = "2024_labeled_transactions.csv"
if os.path.exists(train_file):
    print(f"📊 Loading training data from {train_file}...")
    train_df = pd.read_csv(train_file)
    print(f"✅ Loaded {len(train_df)} transactions from training data")
    print()
    
    print("📋 Training Data Columns:")
    for col in train_df.columns:
        print(f"   - {col}")
    print()
    
    # Check payment_method column
    if 'payment_method' in train_df.columns:
        print("💳 PAYMENT METHOD VALUES in Training Data:")
        pm_values = train_df['payment_method'].value_counts()
        for pm, count in pm_values.head(20).items():
            print(f"   {pm}: {count} transactions")
        print()
    
    # Check origination_account column
    if 'origination_account' in train_df.columns:
        print("🏦 ORIGINATION ACCOUNT VALUES in Training Data:")
        acc_values = train_df['origination_account'].value_counts()
        for acc, count in acc_values.head(20).items():
            print(f"   {acc}: {count} transactions")
        print()
    
    # Sample comparison
    print("=" * 80)
    print("SAMPLE COMPARISON")
    print("=" * 80)
    print()
    
    print("🔍 Redash Sample (first row):")
    redash_sample = redash_df.iloc[0]
    print(f"   id: {redash_sample['id']}")
    print(f"   amount: ${redash_sample['amount']:,.2f}")
    print(f"   payment_method: '{redash_sample['payment_method']}'")
    print(f"   account: '{redash_sample['account']}'")
    print(f"   description: {redash_sample['description'][:60]}...")
    print()
    
    print("🔍 Training Sample (first row):")
    train_sample = train_df.iloc[0]
    for col in ['id', 'amount', 'payment_method', 'origination_account', 'description']:
        if col in train_sample.index:
            val = train_sample[col]
            if col == 'description':
                print(f"   {col}: {str(val)[:60]}...")
            elif col == 'amount':
                print(f"   {col}: ${val:,.2f}")
            else:
                print(f"   {col}: {val}")
    
else:
    print(f"⚠️  Training data file not found: {train_file}")
    print()
    print("Please ensure training data is in the current directory.")
    print("Expected columns: id, amount, payment_method, origination_account, description, agent")

print()
print("=" * 80)
print("MAPPING REQUIREMENTS")
print("=" * 80)
print()

print("📝 Based on Redash data, we need mappings for:")
print()
print("Payment Methods:")
for pm in redash_df['payment_method'].unique():
    print(f"   '{pm}' → ?")
print()
print("Accounts:")
for acc in redash_df['account'].unique():
    print(f"   '{acc}' → ?")

