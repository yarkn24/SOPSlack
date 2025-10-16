#!/usr/bin/env python3
"""
CODE7 - Quick Redash Data Labeling
===================================
Fetches data from Redash, predicts agents, saves to Downloads
"""

import pandas as pd
import numpy as np
import joblib
import requests
import time
import os
import argparse
from scipy.sparse import hstack
from sklearn.preprocessing import LabelEncoder
from datetime import datetime

from predict_with_rules import apply_rules, normalize_label
from data_mapping import ACCOUNT_MAPPING, PAYMENT_METHOD_MAPPING
from agent_sop_mapping import get_confluence_links_for_agent
from slack_message_generator import save_slack_message
from labeling_rules import should_skip_labeling, get_unlabeled_summary

# Redash configuration
REDASH_API_KEY = "wPoSJ9zxm7gAu5GYU44w3bY9hBmagjTMg7LfqDBH"
REDASH_BASE_URL = "https://redash.zp-int.com"
REDASH_QUERY_ID = "133695"

# Parse arguments
parser = argparse.ArgumentParser(description='CODE7 - Redash Data Labeling')
parser.add_argument('--file', type=str, help='Use static CSV file instead of Redash')
parser.add_argument('--quick', action='store_true', help='Quick check only (Slack-friendly)')
args = parser.parse_args()

# Quick mode: Just check transaction count (2 seconds)
if args.quick:
    print("🚀 CODE7 Quick Check...")
    try:
        headers = {"Authorization": f"Key {REDASH_API_KEY}"}
        results_url = f"{REDASH_BASE_URL}/api/queries/{REDASH_QUERY_ID}/results.json"
        response = requests.get(results_url, headers=headers, timeout=5)
        response.raise_for_status()
        rows = response.json()['query_result']['data']['rows']
        count = len(rows)
        today = datetime.now().strftime('%A, %B %d, %Y')
        
        if count == 0:
            print(f"⚠️ No data - {today}")
        else:
            print(f"✅ {count} transactions - {today}")
            print(f"Run: python3 code7.py")
        exit(0)
    except Exception as e:
        print(f"❌ Error: {e}")
        exit(1)

print("\n" + "="*80)
print("🚀 CODE7 - REDASH DATA LABELING")
print("="*80 + "\n")

# 1. Fetch data (either from Redash or static file)
if args.file:
    print(f"📂 Step 1/5: Loading from file: {args.file}...")
    try:
        df = pd.read_csv(args.file)
        print(f"   ✅ Loaded {len(df):,} transactions\n")
        
        if len(df) == 0:
            print("\n" + "="*80)
            print("⚠️  NO TRANSACTIONS IN FILE")
            print("="*80)
            print(f"\nThe file {args.file} contains 0 transactions.")
            print("\n✅ CODE7 COMPLETED - No transactions to process.")
            print("="*80 + "\n")
            exit(0)
    except Exception as e:
        print(f"   ❌ Error loading file: {e}")
        exit(1)
else:
    print("📥 Step 1/5: Fetching from Redash...")
    headers = {"Authorization": f"Key {REDASH_API_KEY}"}
    refresh_url = f"{REDASH_BASE_URL}/api/queries/{REDASH_QUERY_ID}/refresh"

    try:
        refresh_response = requests.post(refresh_url, headers=headers, timeout=30)
        refresh_response.raise_for_status()
        job_id = refresh_response.json()['job']['id']
        
        # Poll for results
        job_url = f"{REDASH_BASE_URL}/api/jobs/{job_id}"
        for _ in range(60):  # Max 2 min
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
        
        print(f"   ✅ Fetched {len(df):,} transactions\n")
        
        if len(df) == 0:
            print("\n" + "="*80)
            print("⚠️  NO TRANSACTIONS FOUND")
            print("="*80)
            print("\n🔍 The Redash query returned 0 transactions.")
            print("\n📅 Likely reasons:")
            print("   • Weekend or banking holiday (banks closed)")
            print("   • No new transactions posted yet")
            print("   • Query date filter excludes today's data")
            print("\n💡 Next steps:")
            print("   • Try again during business hours (Mon-Fri 9am-5pm)")
            print("   • Check Redash: https://redash.zp-int.com/queries/133695")
            print("   • Test with file: python3 code7.py --file <csv_file>")
            print("\n" + "="*80)
            print("\n✅ CODE7 COMPLETED - No transactions to process today.")
            print("="*80 + "\n")
            
            # Return a simple message for Slack
            print("🤖 **Slack Summary:**")
            print("```")
            print("⚠️  Daily Reconciliation Report - No Data Available")
            print("")
            print("The Redash query returned 0 transactions.")
            print("")
            print("📅 Today: Saturday, Oct 11, 2025")
            print("🏦 Status: Weekend - Banks are closed")
            print("")
            print("💡 The bot will automatically run again on the next business day.")
            print("```")
            exit(0)
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        exit(1)

# 2. Prepare data
print("🔧 Step 2/5: Preparing data...")
df.columns = df.columns.str.lower()

if 'account' in df.columns:
    df['origination_account_id'] = df['account']

# Convert amounts
if df['amount'].dtype == 'object':
    df['amount'] = pd.to_numeric(df['amount'].str.replace(',', ''), errors='coerce')
df['amount'] = df['amount'] / 100

# Map payment methods and accounts
if df['payment_method'].dtype == 'object':
    pm_reverse = {v: k for k, v in PAYMENT_METHOD_MAPPING.items()}
    df['payment_method_id'] = df['payment_method'].map(pm_reverse).fillna(-1).astype(int)
else:
    df['payment_method_id'] = df['payment_method'].fillna(-1).astype(int)

if df['origination_account_id'].dtype == 'object':
    acc_reverse = {v: k for k, v in ACCOUNT_MAPPING.items()}
    df['origination_account_id_num'] = df['origination_account_id'].map(acc_reverse).fillna(0).astype(int)
else:
    df['origination_account_id_num'] = df['origination_account_id'].fillna(0).astype(int)

df['description'] = df['description'].fillna('')

print(f"   ✅ Data prepared\n")

# 3. Load model
print("🤖 Step 3/5: Loading model...")
model = joblib.load('ultra_fast_model.pkl')
tfidf = joblib.load('ultra_fast_tfidf.pkl')
le_agent = joblib.load('ultra_fast_agent_encoder.pkl')

# Load training data for encoders
df_train = pd.read_csv('/Users/yarkin.akcil/Downloads/Unrecon_2025_10_05_updated.csv', low_memory=False)
df_train['amount'] = df_train['amount'] / 100

le_account = LabelEncoder()
le_payment = LabelEncoder()
le_account.fit(df_train['origination_account_id'].fillna(0).astype(int).astype(str))
le_payment.fit(df_train['payment_method'].fillna(-1).astype(int).astype(str))

# ICP Funding amounts
icp_funding_mask = (df_train['origination_account_id'] == 21) & (df_train['description'].str.contains('JPMORGAN ACCESS TRANSFER FROM', na=False))
icp_funding_amounts = set(df_train[icp_funding_mask]['amount'].values)

print(f"   ✅ Model loaded\n")

# 4. Predict
print("🔮 Step 4/5: Predicting agents...")
start_time = time.time()

# Create temp dataframe with numeric IDs for prediction
df_pred = df.copy()
df_pred['payment_method'] = df['payment_method_id']
df_pred['origination_account_id'] = df['origination_account_id_num']

# Apply rules
df_pred['rule_pred'] = df_pred.apply(lambda row: apply_rules(row, icp_funding_amounts), axis=1)
rule_mask = df_pred['rule_pred'].notna()

# ML for rest
ml_df = df_pred[~rule_mask].copy()

if len(ml_df) > 0:
    X_tfidf = tfidf.transform(ml_df['description'])
    
    payment_str = ml_df['payment_method'].astype(str)
    account_str = ml_df['origination_account_id'].astype(str)
    
    payment_encoded = [le_payment.transform([v])[0] if v in le_payment.classes_ else -1 for v in payment_str]
    account_encoded = [le_account.transform([v])[0] if v in le_account.classes_ else 0 for v in account_str]
    
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

# Combine predictions
df_pred.loc[rule_mask, 'predicted_agent'] = df_pred.loc[rule_mask, 'rule_pred']
df_pred.loc[~rule_mask, 'predicted_agent'] = ml_df['ml_pred']

# Apply labeling rules (ZBT, Chase Payroll Account 6 TODAY, etc.)
print("   🔍 Applying labeling rules...")
skip_results = df_pred.apply(lambda row: should_skip_labeling(row), axis=1)
df_pred['skip_labeling'] = skip_results.apply(lambda x: x[0])
df_pred['skip_reason'] = skip_results.apply(lambda x: x[1])

# Clear predicted_agent for skipped transactions
skipped_count = df_pred['skip_labeling'].sum()
if skipped_count > 0:
    df_pred.loc[df_pred['skip_labeling'], 'predicted_agent'] = ''
    print(f"   ⚠️  {skipped_count} transaction(s) not labeled (business rules)")

elapsed = time.time() - start_time
print(f"   ✅ {rule_mask.sum()}/{len(df)} rule-based, {(~rule_mask).sum()}/{len(df)} ML-based")
print(f"   ✅ Completed in {elapsed:.2f}s\n")

# 5. Prepare output with text values and SOP links
print("💾 Step 5/5: Preparing output with SOP links...")

# Get SOP links for each predicted agent (only for labeled ones)
sop_links = []
comments = []
for idx, row in df_pred.iterrows():
    agent = row['predicted_agent']
    skip = row['skip_labeling']
    skip_reason = row['skip_reason']
    
    if skip or agent == '':
        sop_links.append('')  # No SOP for unlabeled
        comments.append(skip_reason if skip_reason else '')
    else:
        links = get_confluence_links_for_agent(agent)
        if links:
            sop_links.append(' | '.join(links))
        else:
            sop_links.append('No SOP available')
        comments.append('')

# Create output dataframe with text values
output_df = pd.DataFrame({
    'id': df['id'],
    'date': df['date'],
    'amount': df['amount'],
    'payment_method': df['payment_method'],  # Already text from Redash
    'account': df['account'],  # Already text from Redash
    'description': df['description'],
    'predicted_agent': df_pred['predicted_agent'],
    'sop_links': sop_links,
    'prediction_method': ['Rule-based' if r else 'ML-based' for r in rule_mask],
    'labeling_comment': comments,
})

# Save CSV to Desktop/cursor_data
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
output_dir = f"{os.path.expanduser('~')}/Desktop/cursor_data"
os.makedirs(output_dir, exist_ok=True)  # Create if doesn't exist

csv_file = f"{output_dir}/redash_agents_{timestamp}.csv"
output_df.to_csv(csv_file, index=False)

print(f"   ✅ CSV saved: {csv_file}")

# Generate Slack message
print("   📝 Generating Slack message...")
slack_file = f"{output_dir}/slack_message_{timestamp}.txt"
slack_file = save_slack_message(output_df, slack_file)

print(f"   ✅ Slack message saved: {slack_file}\n")

# 6. Summary
print("="*80)
print("📊 SUMMARY")
print("="*80)
print(f"\n✅ Total: {len(df):,} transactions")
print(f"✅ Rule-based: {rule_mask.sum():,} ({rule_mask.sum()/len(df)*100:.1f}%)")
print(f"✅ ML-based: {(~rule_mask).sum():,} ({(~rule_mask).sum()/len(df)*100:.1f}%)")

print("\n📊 Top Agents (with SOP availability):")
agent_counts = output_df['predicted_agent'].value_counts().head(10)
for agent, count in agent_counts.items():
    sop = get_confluence_links_for_agent(agent)
    sop_status = f"✅ {len(sop)} SOPs" if sop else "⚠️  No SOP"
    print(f"   • {agent}: {count} transactions - {sop_status}")

print(f"\n✅ CSV OUTPUT: {csv_file}")
print(f"✅ SLACK MESSAGE: {slack_file}")
print("="*80 + "\n")

# Slack-friendly summary
print("🤖 **Slack Summary:**")
print("```")
print(f"✅ Daily Reconciliation Report - {len(df):,} Transactions")
print("")
print(f"📊 Predictions:")
print(f"   • Rule-based: {rule_mask.sum():,} ({rule_mask.sum()/len(df)*100:.1f}%)")
print(f"   • ML-based: {(~rule_mask).sum():,} ({(~rule_mask).sum()/len(df)*100:.1f}%)")
print("")
print(f"🔝 Top 3 Agents:")
top_3 = output_df['predicted_agent'].value_counts().head(3)
for i, (agent, count) in enumerate(top_3.items(), 1):
    print(f"   {i}. {agent}: {count} transactions")
print("")
print(f"📄 Files saved to ~/Desktop/cursor_data/")
print(f"💬 Slack message ready to send!")
print("```")
print("="*80 + "\n")

