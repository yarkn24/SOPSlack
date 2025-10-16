#!/usr/bin/env python3
"""
Show Error Examples - Transactions that model predicted wrong
==============================================================
"""

import pandas as pd
import numpy as np
import joblib
from scipy.sparse import hstack
from sklearn.preprocessing import LabelEncoder

def apply_rules(row, icp_funding_amounts=None):
    """Apply business rules."""
    desc = str(row['description']).upper()
    acc = int(row['origination_account_id']) if pd.notna(row['origination_account_id']) else 0
    amt = float(row['amount'])
    pm = int(row['payment_method']) if pd.notna(row['payment_method']) else -1
    
    if pm == 12:
        return 'ZBT'
    elif 'NIUM' in desc:
        return 'Nium Payment'
    elif acc == 21 and 'REMARK=JPMORGAN ACCESS TRANSFER FROM' in desc:
        return 'ICP Funding'
    elif icp_funding_amounts and amt in icp_funding_amounts and 'REMARK=JPMORGAN ACCESS TRANSFER' in desc:
        return 'ICP Funding'
    elif '1TRV' in desc:
        return 'Risk'
    elif 'STATE OF MONTANA' in desc:
        return 'MT WH'
    elif 'NYS DTF WT' in desc or 'NY DTF WT' in desc:
        return 'NY WH'
    elif 'NYS DOL UI' in desc:
        return 'NY UI'
    elif '100% US TREASURY CAPITAL 3163' in desc or 'MONEY MKT MUTUAL FUND' in desc:
        return 'Money Market Transfer'
    elif 'JPMORGAN ACCESS TRANSFER' in desc:
        return 'Treasury Transfer'
    elif pm == 2:
        return 'Check'
    elif pm == 4:
        return 'ACH'
    elif acc in [7, 28]:
        if 'INTEREST' in desc:
            return 'Interest Payment'
        else:
            return 'Recovery Wire'
    elif acc in [6, 9, 18] and pm == 0:
        return 'Risk'
    elif acc == 26:
        if amt < 0.5:
            return 'Bad Debt'
        else:
            return 'BRB'
    elif amt < 0.5 and amt > 0:
        return 'Bad Debt'
    elif 'LOCKBOX' in desc:
        return 'Lockbox'
    elif 'TS FX ACCOUNTS RECEIVABLE' in desc or 'JPV' in desc:
        return 'ICP Return'
    elif 'WISE' in desc and amt < 50000:
        return 'ICP Refund'
    elif 'YORK ADAMS' in desc:
        return 'York Adams Tax'
    
    return None

print("=" * 120)
print("ERROR EXAMPLES - Wrong Predictions")
print("=" * 120)
print()

# Load model
model = joblib.load('ultra_fast_model.pkl')
tfidf = joblib.load('ultra_fast_tfidf.pkl')
le_agent = joblib.load('ultra_fast_agent_encoder.pkl')

# Load data
df = pd.read_csv('/Users/yarkin.akcil/Downloads/Unrecon_2025_10_05_updated.csv', low_memory=False)
df['amount'] = df['amount'] / 100
df['date'] = pd.to_datetime(df['date'], format='mixed')
df = df[df['date'] >= '2024-10-01'].copy()  # Validation set
df = df[df['agent'].notna()].copy()

svb_accounts = [1, 2, 5, 10, 24]
df = df[~df['origination_account_id'].isin(svb_accounts)].copy()

# Find ICP Funding amounts
icp_funding_mask = (df['origination_account_id'] == 21) & (df['description'].str.contains('JPMORGAN ACCESS TRANSFER FROM', na=False))
icp_funding_amounts = set(df[icp_funding_mask]['amount'].values)

# Prepare encoders
le_account = LabelEncoder()
le_payment = LabelEncoder()
le_account.fit(df['origination_account_id'].fillna(0).astype(int).astype(str))
le_payment.fit(df['payment_method'].fillna(-1).astype(int).astype(str))

# Apply rules
df['rule_prediction'] = df.apply(lambda row: apply_rules(row, icp_funding_amounts), axis=1)
rule_mask = df['rule_prediction'].notna()

# ML for rest
ml_df = df[~rule_mask].copy()

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

# Combine
df.loc[rule_mask, 'predicted_agent'] = df.loc[rule_mask, 'rule_prediction']
df.loc[~rule_mask, 'predicted_agent'] = ml_df['ml_prediction']

# Find errors
df['is_error'] = df['agent'] != df['predicted_agent']

# Top problem agents
problem_agents = [
    'ACH Transaction',
    'Company Balance Transfers',
    'MT UI',
    'OH SDWH',
    'ICP Return',
    'Canary Payments',
    'York Adams',
    'LOI',
    'Treasury Transfer'
]

for agent in problem_agents:
    errors = df[(df['agent'] == agent) & (df['is_error'])].copy()
    
    if len(errors) == 0:
        continue
    
    print("=" * 120)
    print(f"AGENT: {agent} - {len(errors)} ERRORS")
    print("=" * 120)
    print()
    
    # Show first 5 errors
    for i, (idx, row) in enumerate(errors.head(5).iterrows(), 1):
        print(f"Error {i}:")
        print(f"  ID: {row['id']}")
        print(f"  TRUE AGENT: {row['agent']}")
        print(f"  PREDICTED: {row['predicted_agent']}")
        print(f"  Amount: ${row['amount']:,.2f}")
        print(f"  Payment Method: {row['payment_method']}")
        print(f"  Account: {row['origination_account_id']}")
        print(f"  Description: {row['description']}")
        print()
    
    print()

