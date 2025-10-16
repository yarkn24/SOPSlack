"""
Quick Prediction from Redash (Simple Version)
==============================================
Uses only the 3 model files we have + data_mapping.

Usage:
    python quick_predict_redash.py
"""

import pandas as pd
from redash_auto_fetch import RedashAutoFetcher
from data_mapping import map_payment_method, map_account, is_corporate_account
import joblib
import scipy.sparse as sp

print("=" * 80)
print("QUICK REDASH → PREDICTION")
print("=" * 80)
print()

# Load model files
print("🤖 Loading model...")
model = joblib.load('ultra_fast_model.pkl')
agent_encoder = joblib.load('ultra_fast_agent_encoder.pkl')
tfidf = joblib.load('ultra_fast_tfidf.pkl')
print("✅ Model loaded")
print()

# Fetch data
print("📊 Fetching Redash data...")
fetcher = RedashAutoFetcher()
df = fetcher.fetch_fresh_data()
print(f"✅ {len(df)} transactions")
print()

# Filter corporate
print("🔍 Filtering corporate accounts...")
df = df[~df['account'].apply(is_corporate_account)].copy()
print(f"✅ {len(df)} after filter")
print()

# Convert to numeric
print("🔄 Converting format...")
df['pm_num'] = df['payment_method'].apply(map_payment_method)
df['acc_num'] = df['account'].apply(map_account)
print("✅ Converted")
print()

# Simple prediction (rules first, then ML)
print("🎯 Predicting...")

def apply_simple_rules(row):
    """Quick rules check."""
    desc = str(row['description']).upper()
    pm = row['pm_num']
    acc = row['acc_num']
    
    if '1TRV' in desc:
        return 'Risk'
    if pm == 12:
        return 'ZBT'
    if 'NIUM' in desc:
        return 'Nium Payment'
    if pm == 2:
        return 'Check'
    if pm == 4:
        return 'ACH'
    if acc in [7, 28]:
        return 'Recovery Wire'
    if 'NYS DTF WT' in desc:
        return 'NY WH'
    if 'NYS DOL UI' in desc:
        return 'NY UI'
    
    return None

# Apply rules
df['predicted_agent'] = df.apply(apply_simple_rules, axis=1)
rule_count = df['predicted_agent'].notna().sum()
print(f"   Rules: {rule_count} matched")

# ML for rest
ml_mask = df['predicted_agent'].isna()
ml_count = ml_mask.sum()

if ml_count > 0:
    print(f"   ML: {ml_count} remaining...")
    
    ml_df = df[ml_mask].copy()
    
    # TF-IDF
    X = tfidf.transform(ml_df['description'])
    
    # Predict
    ml_pred = model.predict(X)
    ml_agents = agent_encoder.inverse_transform(ml_pred)
    
    df.loc[ml_mask, 'predicted_agent'] = ml_agents

print("✅ Prediction complete!")
print()

# Summary
print("=" * 80)
print("RESULTS")
print("=" * 80)
print()

agent_counts = df['predicted_agent'].value_counts()
print(f"📊 Top agents:")
for agent, count in agent_counts.head(10).items():
    print(f"   • {agent}: {count}")

print()
print(f"🎯 Total: {len(df)} transactions")
print(f"   Rules: {rule_count} ({rule_count/len(df)*100:.1f}%)")
print(f"   ML: {ml_count} ({ml_count/len(df)*100:.1f}%)")

