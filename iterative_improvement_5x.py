#!/usr/bin/env python3
"""
5 Iterative Improvements
========================
"""

import pandas as pd
import numpy as np
import joblib
from scipy.sparse import hstack
from sklearn.preprocessing import LabelEncoder
from datetime import datetime
import sys

# Load everything
model = joblib.load('ultra_fast_model.pkl')
tfidf = joblib.load('ultra_fast_tfidf.pkl')
le_agent = joblib.load('ultra_fast_agent_encoder.pkl')

df = pd.read_csv('/Users/yarkin.akcil/Downloads/Unrecon_2025_10_05_updated.csv', low_memory=False)
df['amount'] = df['amount'] / 100
df['date'] = pd.to_datetime(df['date'], format='mixed')
df = df[df['date'] >= '2024-10-01'].copy()
df = df[df['agent'].notna()].copy()

svb_accounts = [1, 2, 5, 10, 24]
df = df[~df['origination_account_id'].isin(svb_accounts)].copy()

icp_funding_mask = (df['origination_account_id'] == 21) & (df['description'].str.contains('JPMORGAN ACCESS TRANSFER FROM', na=False))
icp_funding_amounts = set(df[icp_funding_mask]['amount'].values)

le_account = LabelEncoder()
le_payment = LabelEncoder()
le_account.fit(df['origination_account_id'].fillna(0).astype(int).astype(str))
le_payment.fit(df['payment_method'].fillna(-1).astype(int).astype(str))

def normalize_label(label):
    label = str(label).strip()
    if 'YORK ADAMS' in label.upper(): return 'York Adams'
    if label.startswith('Recovery Wire'): return 'Recovery Wire'
    if label == 'PNC LOI': return 'LOI'
    if label in ['MT WH', 'MT', 'MT ']: return 'MT UI'
    if label in ['NY WTH', 'NY WH ', 'NY WH']: return 'NY WH'
    if label in ['RIsk', 'RISK', 'Risk ', 'Risk  ']: return 'Risk'
    if label in ['Bad Dept', 'Bad Debt ', 'Bad Debt']: return 'Bad Debt'
    if label in ['ICP Refund ', ' ICP Refund', 'ICP Refund  ']: return 'ICP Refund'
    if label in [' ICP Return', 'ICP Return ', 'ICP Return  ']: return 'ICP Return'
    if label in ['IL UI ', 'IL UI  ', 'IL UI']: return 'IL UI'
    if label in ['Check ', 'Check  ', 'Check']: return 'Check'
    if label in ['OH SDWH ', 'OH SDWH  ', 'OH SDWH']: return 'OH SDWH'
    if label.upper() == 'GRASSHOPPER RETURN': return 'Grasshopper Return'
    if label in ['Company Balance Transfer', 'Company Balance Transfers']: return 'Company Balance Transfers'
    if label in ['Treasury Transsfer', 'Treasury Transfer']: return 'Treasury Transfer'
    if label in ['Canary Payment', 'Canary Payments']: return 'Canary Payments'
    if label in ['Debit Authorisation', 'Debit Authorization']: return 'Debit Authorization'
    if label in ['Berk Tax', 'Berks Tax']: return 'Berks Tax'
    return label

df['agent'] = df['agent'].apply(normalize_label)

print("=" * 100)
print("🎯 5-ITERATION IMPROVEMENT PROCESS")
print("=" * 100)
print()

# Import current rules
with open('predict_with_rules.py', 'r') as f:
    predict_rules_content = f.read()

# Extract just the apply_rules function
import re
match = re.search(r'def apply_rules\(.*?\):(.*?)(?=\ndef |$)', predict_rules_content, re.DOTALL)
if match:
    rules_func_body = match.group(0)
    print("✅ Loaded current rules")
else:
    print("❌ Could not load rules")
    sys.exit(1)

print()

for iteration in range(1, 6):
    print(f"{'='*100}")
    print(f"🔄 ITERATION {iteration}")
    print(f"{'='*100}")
    print()
    
    # Execute current rules
    exec(rules_func_body, globals())
    
    # Apply rules
    df_test = df.copy()
    df_test['rule_pred'] = df_test.apply(lambda row: apply_rules(row, icp_funding_amounts), axis=1)
    rule_mask = df_test['rule_pred'].notna()
    
    # ML for rest
    ml_df = df_test[~rule_mask].copy()
    
    if len(ml_df) > 0:
        X_tfidf = tfidf.transform(ml_df['description'].fillna(''))
        payment_encoded = le_payment.transform(ml_df['payment_method'].fillna(-1).astype(int).astype(str))
        account_encoded = le_account.transform(ml_df['origination_account_id'].fillna(0).astype(int).astype(str))
        
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
    
    df_test.loc[rule_mask, 'predicted'] = df_test.loc[rule_mask, 'rule_pred']
    df_test.loc[~rule_mask, 'predicted'] = ml_df['ml_pred']
    
    correct = (df_test['agent'] == df_test['predicted']).sum()
    accuracy = correct / len(df_test) * 100
    
    rule_count = rule_mask.sum()
    ml_count = (~rule_mask).sum()
    
    print(f"📊 Current Accuracy: {accuracy:.2f}%")
    print(f"   Rules: {rule_count} ({rule_count/len(df_test)*100:.1f}%)")
    print(f"   ML: {ml_count} ({ml_count/len(df_test)*100:.1f}%)")
    print()
    
    # Find errors
    errors = df_test[df_test['agent'] != df_test['predicted']]
    error_by_agent = errors.groupby('agent').size().sort_values(ascending=False).head(5)
    
    if len(errors) == 0:
        print("✅ Perfect accuracy! No errors to fix.")
        break
    
    print(f"❌ Total errors: {len(errors)}")
    print(f"   Top error agents: {dict(error_by_agent.head(3))}")
    print()
    
    # Analyze top error
    top_agent = error_by_agent.index[0]
    agent_errors = errors[errors['agent'] == top_agent]
    
    print(f"🔍 Analyzing: {top_agent} ({len(agent_errors)} errors)")
    print(f"   Predicted as: {agent_errors['predicted'].value_counts().head(3).to_dict()}")
    
    # Show 3 samples
    print(f"   Sample descriptions:")
    for idx, row in agent_errors.head(3).iterrows():
        print(f"   • PM={row['payment_method']}, ACC={row['origination_account_id']}")
        print(f"     {row['description'][:100]}...")
    
    print()
    print(f"💡 Iteration {iteration} complete. Review needed for next step.")
    print()

