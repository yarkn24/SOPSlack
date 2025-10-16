#!/usr/bin/env python3
"""
Show Worst Performing Agents
=============================
"""

import pandas as pd
import numpy as np
import joblib
from scipy.sparse import hstack
from sklearn.preprocessing import LabelEncoder
from datetime import datetime

def apply_rules(row, icp_funding_amounts=None):
    """Apply business rules. Returns agent name if rule matches, None otherwise. UPDATED WITH NEW RULES."""
    desc = str(row['description']).upper()
    acc = int(row['origination_account_id']) if pd.notna(row['origination_account_id']) else 0
    amt = float(row['amount'])
    pm = int(row['payment_method']) if pd.notna(row['payment_method']) else -1
    
    # PRIORITY ORDER (HIGHEST TO LOWEST)
    
    # 1. Payment Method 12 = ZBT
    if pm == 12:
        return 'ZBT'
    # 2. NIUM = Nium Payment
    elif 'NIUM' in desc:
        return 'Nium Payment'
    # 3. ICP Funding - Chase ICP + JPMORGAN ACCESS TRANSFER FROM
    elif acc == 21 and 'REMARK=JPMORGAN ACCESS TRANSFER FROM' in desc:
        return 'ICP Funding'
    # 4. ICP Funding - Paired transaction (same amount + JPMORGAN)
    elif icp_funding_amounts and amt in icp_funding_amounts and 'REMARK=JPMORGAN ACCESS TRANSFER' in desc:
        return 'ICP Funding'
    # 5. 1TRV = RISK (ANY ACCOUNT - HIGHEST PRIORITY)
    elif '1TRV' in desc:
        return 'Risk'
    # 6. STATE rules
    elif 'STATE OF MONTANA' in desc:
        return 'MT WH'
    elif 'NYS DTF WT' in desc or 'NY DTF WT' in desc:
        return 'NY WH'
    elif 'NYS DOL UI' in desc:
        return 'NY UI'
    # 7. Treasury/Money Market
    elif '100% US TREASURY CAPITAL 3163' in desc or 'MONEY MKT MUTUAL FUND' in desc:
        return 'Money Market Transfer'
    elif 'JPMORGAN ACCESS TRANSFER' in desc:
        return 'Treasury Transfer'
    # 8. Payment method based
    elif pm == 2:
        return 'Check'
    elif pm == 4:
        return 'ACH'
    # 9. Recovery accounts (WITHOUT 1TRV)
    elif acc in [7, 28]:
        if 'INTEREST' in desc:
            return 'Interest Payment'
        else:
            return 'Recovery Wire'
    # 10. Risk accounts
    elif acc in [6, 9, 18] and pm == 0:
        return 'Risk'
    # 11. Blueridge Operations
    elif acc == 26:
        if amt < 0.5:
            return 'Bad Debt'
        else:
            return 'BRB'
    elif amt < 0.5 and amt > 0:
        return 'Bad Debt'
    # 12. Other patterns
    elif 'LOCKBOX' in desc:
        return 'Lockbox'
    elif 'TS FX ACCOUNTS RECEIVABLE' in desc or 'JPV' in desc:
        return 'ICP Return'
    elif 'WISE' in desc and amt < 50000:
        return 'ICP Refund'
    elif 'YORK ADAMS' in desc:
        return 'York Adams Tax'
    return None

print("=" * 100)
print("WORST PERFORMING AGENTS ANALYSIS")
print("=" * 100)
print()

# Load model
model = joblib.load('ultra_fast_model.pkl')
tfidf = joblib.load('ultra_fast_tfidf.pkl')
le_agent = joblib.load('ultra_fast_agent_encoder.pkl')

# Load data
df = pd.read_csv('/Users/yarkin.akcil/Downloads/Unrecon_2025_10_05_updated.csv', low_memory=False)
df['amount'] = df['amount'] / 100
df['date'] = pd.to_datetime(df['date'], format='mixed')
df = df[df['date'] >= '2024-01-01'].copy()
df = df[df['agent'].notna()].copy()

svb_accounts = [1, 2, 5, 10, 24]
df = df[~df['origination_account_id'].isin(svb_accounts)].copy()
df['agent'] = df['agent'].str.strip()

# Find ICP Funding amounts
icp_funding_mask = (df['origination_account_id'] == 21) & (df['description'].str.contains('JPMORGAN ACCESS TRANSFER FROM', na=False))
icp_funding_amounts = set(df[icp_funding_mask]['amount'].values)

# Split validation set (Oct+)
val_df = df[df['date'] >= '2024-10-01'].copy()

print(f"📊 Validation set: {len(val_df):,} transactions")
print()

# Prepare encoders
le_account = LabelEncoder()
le_payment = LabelEncoder()
le_account.fit(df['origination_account_id'].fillna(0).astype(int).astype(str))
le_payment.fit(df['payment_method'].fillna(-1).astype(int).astype(str))

# Apply rules
val_df['rule_prediction'] = val_df.apply(lambda row: apply_rules(row, icp_funding_amounts), axis=1)
rule_mask = val_df['rule_prediction'].notna()

# ML for rest
ml_df = val_df[~rule_mask].copy()

if len(ml_df) > 0:
    # TF-IDF
    X_tfidf = tfidf.transform(ml_df['description'].fillna(''))
    
    # Encode features
    payment_encoded = le_payment.transform(ml_df['payment_method'].fillna(-1).astype(int).astype(str))
    account_encoded = le_account.transform(ml_df['origination_account_id'].fillna(0).astype(int).astype(str))
    
    # Create feature dataframe
    X_ex = pd.DataFrame({
        'payment': payment_encoded,
        'account': account_encoded,
        'amount': ml_df['amount'].values,
        'amount_log': np.log1p(ml_df['amount'].abs().values)
    })
    
    # Combine
    X_ml = hstack([X_tfidf, X_ex.values])
    
    ml_pred_encoded = model.predict(X_ml)
    ml_predictions = le_agent.inverse_transform(ml_pred_encoded)
    ml_df['ml_prediction'] = ml_predictions
else:
    ml_df['ml_prediction'] = None

# Combine
val_df.loc[rule_mask, 'predicted_agent'] = val_df.loc[rule_mask, 'rule_prediction']
val_df.loc[~rule_mask, 'predicted_agent'] = ml_df['ml_prediction']

# Calculate accuracy per agent
agent_stats = []

for agent in val_df['agent'].unique():
    agent_mask = val_df['agent'] == agent
    agent_data = val_df[agent_mask]
    
    total = len(agent_data)
    correct = (agent_data['agent'] == agent_data['predicted_agent']).sum()
    accuracy = correct / total * 100
    
    # Count rule vs ML
    rule_count = agent_data[agent_data['rule_prediction'].notna()].shape[0]
    ml_count = total - rule_count
    
    agent_stats.append({
        'agent': agent,
        'total': total,
        'correct': correct,
        'accuracy': accuracy,
        'rule_count': rule_count,
        'ml_count': ml_count
    })

stats_df = pd.DataFrame(agent_stats)
stats_df = stats_df.sort_values('accuracy')

# Show worst 20 (overall)
print("=" * 100)
print("WORST 20 AGENTS (by accuracy)")
print("=" * 100)
print(f"{'Agent':<40} {'Accuracy':>8} {'Total':>7} {'Correct':>7} {'Via Rules':>10} {'Via ML':>10}")
print("-" * 100)

for idx, row in stats_df.head(20).iterrows():
    print(f"{row['agent']:<40} {row['accuracy']:7.2f}% {row['total']:7d} {row['correct']:7d} {row['rule_count']:10d} {row['ml_count']:10d}")

# Show worst with significant volume (50+ transactions)
print()
print("=" * 100)
print("WORST AGENTS WITH SIGNIFICANT VOLUME (50+ transactions)")
print("=" * 100)
print(f"{'Agent':<40} {'Accuracy':>8} {'Total':>7} {'Correct':>7} {'Via Rules':>10} {'Via ML':>10}")
print("-" * 100)

significant_df = stats_df[stats_df['total'] >= 50].sort_values('accuracy')
for idx, row in significant_df.head(20).iterrows():
    print(f"{row['agent']:<40} {row['accuracy']:7.2f}% {row['total']:7d} {row['correct']:7d} {row['rule_count']:10d} {row['ml_count']:10d}")

print()
print("=" * 100)
print("SUMMARY")
print("=" * 100)
print(f"Total agents: {len(stats_df)}")
print(f"Agents < 90% accuracy: {len(stats_df[stats_df['accuracy'] < 90])}")
print(f"Agents < 80% accuracy: {len(stats_df[stats_df['accuracy'] < 80])}")
print(f"Agents < 50% accuracy: {len(stats_df[stats_df['accuracy'] < 50])}")

