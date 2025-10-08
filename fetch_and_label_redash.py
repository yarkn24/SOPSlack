#!/usr/bin/env python3
"""
Fetch data from Redash and predict agent labels
================================================
"""

import pandas as pd
import numpy as np
import joblib
import requests
import time
from scipy.sparse import hstack
from sklearn.preprocessing import LabelEncoder
from datetime import datetime

from predict_with_rules import apply_rules, normalize_label
from data_mapping import ACCOUNT_MAPPING, PAYMENT_METHOD_MAPPING

# Redash configuration
REDASH_API_KEY = "wPoSJ9zxm7gAu5GYU44w3bY9hBmagjTMg7LfqDBH"
REDASH_BASE_URL = "https://redash.zp-int.com"
REDASH_QUERY_ID = "133695"

print("=" * 100)
print("📊 FETCHING DATA FROM REDASH & PREDICTING LABELS")
print("=" * 100)
print()

# 1. Fetch data from Redash
print("🔄 Step 1: Fetching data from Redash...")
print(f"   Query ID: {REDASH_QUERY_ID}")

headers = {
    "Authorization": f"Key {REDASH_API_KEY}"
}

# Trigger query refresh
refresh_url = f"{REDASH_BASE_URL}/api/queries/{REDASH_QUERY_ID}/refresh"
print(f"   Triggering refresh...")

try:
    refresh_response = requests.post(refresh_url, headers=headers)
    refresh_response.raise_for_status()
    job = refresh_response.json()
    job_id = job['job']['id']
    
    print(f"   Job ID: {job_id}")
    print(f"   Waiting for results...")
    
    # Poll for results
    job_url = f"{REDASH_BASE_URL}/api/jobs/{job_id}"
    max_wait = 120  # 2 minutes
    start_time = time.time()
    
    while True:
        if time.time() - start_time > max_wait:
            print("   ❌ Timeout waiting for query results")
            exit(1)
        
        job_response = requests.get(job_url, headers=headers)
        job_response.raise_for_status()
        job_status = job_response.json()['job']['status']
        
        if job_status == 3:  # SUCCESS
            print(f"   ✅ Query completed!")
            break
        elif job_status == 4:  # FAILURE
            print(f"   ❌ Query failed")
            exit(1)
        
        time.sleep(2)
    
    # Get latest results
    results_url = f"{REDASH_BASE_URL}/api/queries/{REDASH_QUERY_ID}/results.json"
    results_response = requests.get(results_url, headers=headers)
    results_response.raise_for_status()
    results = results_response.json()
    
    # Convert to DataFrame
    rows = results['query_result']['data']['rows']
    df = pd.DataFrame(rows)
    
    print(f"   ✅ Fetched {len(df):,} transactions")
    print()
    
except Exception as e:
    print(f"   ❌ Error: {e}")
    exit(1)

# 2. Prepare data
print("🔧 Step 2: Preparing data...")

# Normalize column names
df.columns = df.columns.str.lower()

# Rename account column
if 'account' in df.columns:
    df['origination_account_id'] = df['account']

# Required columns
required_cols = ['description', 'payment_method', 'origination_account_id', 'amount']
missing = [col for col in required_cols if col not in df.columns]
if missing:
    print(f"   ❌ Missing columns: {missing}")
    print(f"   Available columns: {list(df.columns)}")
    exit(1)

# Convert amount (cents to dollars)
if df['amount'].dtype == 'object':
    df['amount'] = pd.to_numeric(df['amount'].str.replace(',', ''), errors='coerce')
df['amount'] = df['amount'] / 100

# Fill NaN
df['description'] = df['description'].fillna('')

# Map payment_method (might be string)
if df['payment_method'].dtype == 'object':
    # Create reverse mapping
    pm_name_to_id = {v: k for k, v in PAYMENT_METHOD_MAPPING.items()}
    df['payment_method'] = df['payment_method'].map(pm_name_to_id).fillna(-1).astype(int)
else:
    df['payment_method'] = df['payment_method'].fillna(-1).astype(int)

# Map origination_account_id (might be string)
if df['origination_account_id'].dtype == 'object':
    # Create reverse mapping
    acc_name_to_id = {v: k for k, v in ACCOUNT_MAPPING.items()}
    df['origination_account_id'] = df['origination_account_id'].map(acc_name_to_id).fillna(0).astype(int)
else:
    df['origination_account_id'] = df['origination_account_id'].fillna(0).astype(int)

print(f"   ✅ Data prepared")
print()

# 3. Load model
print("🤖 Step 3: Loading model...")

model = joblib.load('ultra_fast_model.pkl')
tfidf = joblib.load('ultra_fast_tfidf.pkl')
le_agent = joblib.load('ultra_fast_agent_encoder.pkl')

# Load training data to fit encoders
df_train = pd.read_csv('/Users/yarkin.akcil/Downloads/Unrecon_2025_10_05_updated.csv', low_memory=False)
df_train['amount'] = df_train['amount'] / 100

le_account = LabelEncoder()
le_payment = LabelEncoder()
le_account.fit(df_train['origination_account_id'].fillna(0).astype(int).astype(str))
le_payment.fit(df_train['payment_method'].fillna(-1).astype(int).astype(str))

# ICP Funding amounts
icp_funding_mask = (df_train['origination_account_id'] == 21) & (df_train['description'].str.contains('JPMORGAN ACCESS TRANSFER FROM', na=False))
icp_funding_amounts = set(df_train[icp_funding_mask]['amount'].values)

print(f"   ✅ Model loaded")
print()

# 4. Predict
print("🔮 Step 4: Predicting labels...")

start_time = time.time()

# Apply rules first
df['rule_pred'] = df.apply(lambda row: apply_rules(row, icp_funding_amounts), axis=1)
rule_mask = df['rule_pred'].notna()

print(f"   Rules matched: {rule_mask.sum():,}/{len(df):,} ({rule_mask.sum()/len(df)*100:.1f}%)")

# ML for rest
ml_df = df[~rule_mask].copy()

if len(ml_df) > 0:
    X_tfidf = tfidf.transform(ml_df['description'])
    
    # Handle unknown categories
    payment_str = ml_df['payment_method'].astype(str)
    account_str = ml_df['origination_account_id'].astype(str)
    
    payment_encoded = []
    for val in payment_str:
        if val in le_payment.classes_:
            payment_encoded.append(le_payment.transform([val])[0])
        else:
            payment_encoded.append(-1)  # Unknown
    
    account_encoded = []
    for val in account_str:
        if val in le_account.classes_:
            account_encoded.append(le_account.transform([val])[0])
        else:
            account_encoded.append(0)  # Unknown
    
    X_ex = pd.DataFrame({
        'payment': payment_encoded,
        'account': account_encoded,
        'amount': ml_df['amount'].values,
        'amount_log': np.log1p(ml_df['amount'].abs().values)
    })
    
    X_ml = hstack([X_tfidf, X_ex.values])
    ml_pred_encoded = model.predict(X_ml)
    ml_predictions = le_agent.inverse_transform(ml_pred_encoded)
    ml_df['ml_pred'] = [normalize_label(p) for p in ml_predictions]
    
    print(f"   ML predicted: {len(ml_df):,}/{len(df):,} ({len(ml_df)/len(df)*100:.1f}%)")

# Combine
df.loc[rule_mask, 'predicted_agent'] = df.loc[rule_mask, 'rule_pred']
df.loc[~rule_mask, 'predicted_agent'] = ml_df['ml_pred']

elapsed = time.time() - start_time
print(f"   ✅ Prediction completed in {elapsed:.2f}s ({elapsed/len(df)*1000:.2f}ms per txn)")
print()

# 5. Save results
print("💾 Step 5: Saving results...")

output_file = f"redash_labeled_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
df.to_csv(output_file, index=False)

print(f"   ✅ Saved to: {output_file}")
print()

# 6. Summary
print("=" * 100)
print("📊 PREDICTION SUMMARY")
print("=" * 100)
print()
print(f"Total transactions: {len(df):,}")
print(f"Rule-based: {rule_mask.sum():,} ({rule_mask.sum()/len(df)*100:.1f}%)")
print(f"ML-based: {(~rule_mask).sum():,} ({(~rule_mask).sum()/len(df)*100:.1f}%)")
print()

# Top agents
agent_counts = df['predicted_agent'].value_counts().head(10)
print("Top 10 predicted agents:")
for agent, count in agent_counts.items():
    print(f"   {agent}: {count:,}")
print()

print("=" * 100)
print(f"✅ RESULTS SAVED TO: {output_file}")
print("=" * 100)

