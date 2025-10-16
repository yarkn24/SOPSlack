#!/usr/bin/env python3
"""
Iterative Learning - Self-Improvement Loop
===========================================
Learn from errors, add rules, test, repeat!
"""

import pandas as pd
import numpy as np
import joblib
from scipy.sparse import hstack
from sklearn.preprocessing import LabelEncoder
from collections import Counter
import shutil
from datetime import datetime

def apply_rules_v1(row, icp_funding_amounts=None):
    """Baseline rules (current version)"""
    desc = str(row['description']).upper()
    acc = int(row['origination_account_id']) if pd.notna(row['origination_account_id']) else 0
    amt = float(row['amount'])
    pm = int(row['payment_method']) if pd.notna(row['payment_method']) else -1
    
    # PRIORITY ORDER
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
    elif 'ORIG CO NAME=STATE OF MONTANA' in desc or 'STATE OF MONTANA' in desc:
        return 'MT UI'
    elif '1HIOSDWH' in desc or 'OHSDWHTX' in desc:
        return 'OH SDWH'
    elif 'NYS DTF WT' in desc or 'NY DTF WT' in desc:
        return 'NY WH'
    elif 'NYS DOL UI' in desc:
        return 'NY UI'
    elif pm == 4 and ('ACH CREDIT SETTLEMENT' in desc or 'ACH DEBIT SETTLEMENT' in desc):
        if 'REVERSAL' in desc:
            return 'ACH Reversal'
        else:
            return 'ACH Transaction'
    elif 'WA' in desc and ('L&I' in desc or 'LNI' in desc or 'LABOR' in desc or 'INDUSTRIES' in desc):
        return 'WA LNI'
    elif 'ENTRY DESCR=ITL' in desc and 'GUSTO PAYROLL' in desc:
        return 'Company Balance Transfers'
    elif acc == 16 and 'CREDIT MEMO' in desc:
        return 'LOI'
    elif '100% US TREASURY CAPITAL 3163' in desc or 'MONEY MKT MUTUAL FUND' in desc:
        return 'Money Market Transfer'
    elif 'JPMORGAN ACCESS TRANSFER' in desc:
        return 'Treasury Transfer'
    elif 'INTEREST ADJUSTMENT' in desc:
        return 'Interest Adjustment'
    elif 'KEYSTONE' in desc:
        return 'PA UI'
    elif pm == 2:
        return 'Check'
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
    elif 'REMARK=WISE' in desc and amt < 50000:
        return 'ICP Refund'
    elif 'WISE' in desc and amt < 50000:
        return 'ICP Refund'
    elif 'YORK ADAMS' in desc:
        return 'York Adams'
    elif 'IRS' in desc:
        return 'IRS Wire'
    
    return None

def test_accuracy(apply_rules_func, df, icp_funding_amounts, model, tfidf, le_agent, le_account, le_payment):
    """Test accuracy with given rules function"""
    
    # Apply rules
    df_test = df.copy()
    df_test['rule_prediction'] = df_test.apply(lambda row: apply_rules_func(row, icp_funding_amounts), axis=1)
    rule_mask = df_test['rule_prediction'].notna()
    
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
        ml_df['ml_prediction'] = ml_predictions
    
    # Combine
    df_test.loc[rule_mask, 'predicted_agent'] = df_test.loc[rule_mask, 'rule_prediction']
    df_test.loc[~rule_mask, 'predicted_agent'] = ml_df['ml_prediction']
    
    # Calculate accuracy
    correct = (df_test['agent'] == df_test['predicted_agent']).sum()
    accuracy = correct / len(df_test) * 100
    
    return accuracy, df_test

def find_top_errors(df_test):
    """Find top error patterns"""
    errors = df_test[df_test['agent'] != df_test['predicted_agent']]
    error_by_agent = errors.groupby('agent').size().sort_values(ascending=False).head(5)
    return error_by_agent, errors

print("=" * 100)
print("🚀 ITERATIVE LEARNING - 5 ITERATIONS")
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
df = df[df['date'] >= '2024-10-01'].copy()
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

# Baseline accuracy
print("📊 ITERATION 0 (Baseline)")
baseline_acc, df_test = test_accuracy(apply_rules_v1, df, icp_funding_amounts, model, tfidf, le_agent, le_account, le_payment)
print(f"   Accuracy: {baseline_acc:.2f}%")

error_agents, errors = find_top_errors(df_test)
print(f"   Top errors: {error_agents.to_dict()}")
print()

# Store best version
best_accuracy = baseline_acc
best_rules_func = apply_rules_v1

print("🔄 Starting iterations...")
print()

# Simple iteration: just report what we found
for iteration in range(1, 6):
    print(f"📌 ITERATION {iteration}")
    print("   Analysis:")
    
    # Analyze top 3 error agents
    for agent in error_agents.head(3).index:
        agent_errors = errors[errors['agent'] == agent]
        
        # Find most common keywords
        descriptions = agent_errors['description'].str.upper().head(20)
        all_words = ' '.join(descriptions.values).split()
        word_counts = Counter([w for w in all_words if len(w) > 4 and not w.isdigit()])
        top_words = word_counts.most_common(3)
        
        # Check patterns
        pm_mode = agent_errors['payment_method'].mode()[0] if len(agent_errors) > 0 else None
        acc_mode = agent_errors['origination_account_id'].mode()[0] if len(agent_errors) > 0 else None
        
        print(f"   • {agent}: PM={pm_mode}, ACC={acc_mode}, Keywords={[w for w,c in top_words]}")
    
    print(f"   → Keeping baseline (manual improvement needed)")
    print(f"   → Accuracy: {baseline_acc:.2f}%")
    print()

print("=" * 100)
print(f"✅ BEST ACCURACY: {best_accuracy:.2f}%")
print("=" * 100)
print()

print("📝 MANUAL IMPROVEMENT SUGGESTIONS:")
print()
print("Based on error analysis, consider adding these rules:")
print()

# Suggest rules for top errors
for agent in error_agents.head(5).index:
    agent_errors = errors[errors['agent'] == agent]
    print(f"• {agent}:")
    
    # Sample description
    sample_desc = agent_errors.iloc[0]['description'][:100]
    print(f"  Sample: {sample_desc}...")
    
    # Patterns
    pm_dist = agent_errors['payment_method'].value_counts().head(1)
    acc_dist = agent_errors['origination_account_id'].value_counts().head(1)
    
    if len(pm_dist) > 0:
        print(f"  Common PM: {pm_dist.index[0]} ({pm_dist.values[0]} cases)")
    if len(acc_dist) > 0:
        print(f"  Common ACC: {acc_dist.index[0]} ({acc_dist.values[0]} cases)")
    
    print()

