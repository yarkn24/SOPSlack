#!/usr/bin/env python3
"""
CODE7 DEMO - Quick Redash Data Labeling (Sample Data Version)
==============================================================
Demonstrates the code7 workflow with sample transaction data
"""

import pandas as pd
import numpy as np
import os
from datetime import datetime

from data_mapping import ACCOUNT_MAPPING, PAYMENT_METHOD_MAPPING
from agent_sop_mapping import get_confluence_links_for_agent
from slack_message_generator import save_slack_message
from labeling_rules import should_skip_labeling, get_unlabeled_summary
from predict_with_rules import apply_rules, normalize_label

print("\n" + "="*80)
print("🚀 CODE7 DEMO - TRANSACTION LABELING (SAMPLE DATA)")
print("="*80 + "\n")

# 1. Create sample data (simulating Redash fetch)
print("📥 Step 1/5: Creating sample data (Redash simulation)...")

sample_data = [
    # ZBT transaction (should be skipped)
    {'id': 1001, 'date': '2025-10-11', 'amount': 250000, 'payment_method': 12, 
     'account': 'Chase Payroll', 'description': 'ZERO BALANCE TRANSFER'},
    
    # ACH transactions
    {'id': 1002, 'date': '2025-10-11', 'amount': 150000, 'payment_method': 4,
     'account': 'Chase Operating', 'description': 'ACH PAYMENT PROCESSING'},
    {'id': 1003, 'date': '2025-10-11', 'amount': 75000, 'payment_method': 4,
     'account': 'Chase Operating', 'description': 'ACH DEBIT TRANSACTION'},
    
    # Check transactions
    {'id': 1004, 'date': '2025-10-11', 'amount': 45000, 'payment_method': 2,
     'account': 'Chase Operating', 'description': 'CHECK PAYMENT 1234'},
    
    # Nium Payment
    {'id': 1005, 'date': '2025-10-11', 'amount': 487500, 'payment_method': 0,
     'account': 'Chase Operating', 'description': 'ORIG CO NAME=NIUM INC,ORIG ID=0514672353'},
    
    # Risk transaction
    {'id': 1006, 'date': '2025-10-11', 'amount': 125000, 'payment_method': 0,
     'account': 'Chase Wire In', 'description': '1TRV RISK TRANSACTION'},
    
    # ICP Funding
    {'id': 1007, 'date': '2025-10-11', 'amount': 500000, 'payment_method': 0,
     'account': 'Chase ICP', 'description': 'REMARK=JPMORGAN ACCESS TRANSFER FROM ACCOUNT'},
    
    # NY WH (New York Withholding)
    {'id': 1008, 'date': '2025-10-11', 'amount': 12500, 'payment_method': 0,
     'account': 'Chase Operating', 'description': 'NYS DTF WT TAX PAYMENT'},
    
    # MT UI (Montana Unemployment)
    {'id': 1009, 'date': '2025-10-11', 'amount': 8900, 'payment_method': 0,
     'account': 'Chase Operating', 'description': 'STATE OF MONTANA UI PAYMENT'},
    
    # Treasury Transfer
    {'id': 1010, 'date': '2025-10-11', 'amount': 1000000, 'payment_method': 0,
     'account': 'Chase Operating', 'description': 'JPMORGAN ACCESS TRANSFER TO TREASURY'},
]

df = pd.DataFrame(sample_data)
print(f"   ✅ Created {len(df):,} sample transactions\n")

# 2. Prepare data
print("🔧 Step 2/5: Preparing data...")

# Map account names to IDs
account_reverse = {v: k for k, v in ACCOUNT_MAPPING.items()}
df['origination_account_id_num'] = df['account'].map(account_reverse).fillna(0).astype(int)

# Convert amounts (from cents to dollars)
df['amount'] = df['amount'] / 100

# Payment methods already as IDs
df['payment_method_id'] = df['payment_method']

print(f"   ✅ Data prepared\n")

# 3. Apply Rules (No ML model needed for demo)
print("🔮 Step 3/5: Applying business rules...")

# For ICP Funding amounts
icp_funding_amounts = set()
for idx, row in df.iterrows():
    if row['origination_account_id_num'] == 21:
        desc = str(row['description']).upper()
        if 'JPMORGAN ACCESS TRANSFER FROM' in desc:
            icp_funding_amounts.add(float(row['amount']))

# Apply rules
predictions = []
for idx, row in df.iterrows():
    pred_row = pd.Series({
        'description': row['description'],
        'origination_account_id': row['origination_account_id_num'],
        'payment_method': row['payment_method_id'],
        'amount': row['amount']
    })
    pred = apply_rules(pred_row, icp_funding_amounts)
    predictions.append(normalize_label(pred) if pred else 'Unknown')

df['predicted_agent'] = predictions

print(f"   ✅ Rules applied to all transactions\n")

# 4. Apply labeling rules
print("🔍 Step 4/5: Applying labeling rules...")

skip_results = df.apply(lambda row: should_skip_labeling(pd.Series({
    'description': row['description'],
    'origination_account_id': row['origination_account_id_num'],
    'payment_method': row['payment_method_id'],
    'amount': row['amount'],
    'date': row['date']
})), axis=1)

df['skip_labeling'] = skip_results.apply(lambda x: x[0])
df['skip_reason'] = skip_results.apply(lambda x: x[1])

# Clear predicted_agent for skipped transactions
skipped_count = df['skip_labeling'].sum()
if skipped_count > 0:
    df.loc[df['skip_labeling'], 'predicted_agent'] = ''
    print(f"   ⚠️  {skipped_count} transaction(s) not labeled (business rules)")

print(f"   ✅ Labeling rules applied\n")

# 5. Prepare output with SOP links
print("💾 Step 5/5: Preparing output with SOP links...")

# Get SOP links for each predicted agent
sop_links = []
comments = []
for idx, row in df.iterrows():
    agent = row['predicted_agent']
    skip = row['skip_labeling']
    skip_reason = row['skip_reason']
    
    if skip or agent == '':
        sop_links.append('')
        comments.append(skip_reason if skip_reason else '')
    else:
        links = get_confluence_links_for_agent(agent)
        if links:
            sop_links.append(' | '.join(links))
        else:
            sop_links.append('No SOP available')
        comments.append('')

# Create output dataframe
output_df = pd.DataFrame({
    'id': df['id'],
    'date': df['date'],
    'amount': df['amount'],
    'payment_method': df['payment_method'],
    'account': df['account'],
    'description': df['description'],
    'predicted_agent': df['predicted_agent'],
    'sop_links': sop_links,
    'prediction_method': 'Rule-based',
    'labeling_comment': comments,
})

# Save CSV to Desktop/cursor_data
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
output_dir = f"{os.path.expanduser('~')}/Desktop/cursor_data"
os.makedirs(output_dir, exist_ok=True)

csv_file = f"{output_dir}/redash_agents_demo_{timestamp}.csv"
output_df.to_csv(csv_file, index=False)

print(f"   ✅ CSV saved: {csv_file}")

# Generate Slack message
print("   📝 Generating Slack message...")
slack_file = f"{output_dir}/slack_message_demo_{timestamp}.txt"
slack_file = save_slack_message(output_df, slack_file)

print(f"   ✅ Slack message saved: {slack_file}\n")

# 6. Summary
print("="*80)
print("📊 SUMMARY")
print("="*80)
print(f"\n✅ Total: {len(df):,} transactions")
print(f"✅ Rule-based: {len(df):,} (100%)")
print(f"⚠️  Unlabeled: {skipped_count}")

print("\n📊 Agents Predicted:")
agent_counts = output_df[output_df['predicted_agent'] != '']['predicted_agent'].value_counts()
for agent, count in agent_counts.items():
    sop = get_confluence_links_for_agent(agent)
    sop_status = f"✅ {len(sop)} SOPs" if sop else "⚠️  No SOP"
    print(f"   • {agent}: {count} transactions - {sop_status}")

print(f"\n✅ CSV OUTPUT: {csv_file}")
print(f"✅ SLACK MESSAGE: {slack_file}")
print("="*80 + "\n")

print("📋 DEMO COMPLETE!")
print("   This demo shows code7 functionality with sample data.")
print("   For production: python3 code7.py (requires Redash access + trained models)")
print("="*80 + "\n")
