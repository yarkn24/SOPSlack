#!/usr/bin/env python3
"""
Automatic 5-Iteration Improvement
==================================
Analyze errors, add rules, test, repeat!
"""

import pandas as pd
import numpy as np
import joblib
from scipy.sparse import hstack
from sklearn.preprocessing import LabelEncoder
from collections import Counter
import shutil
from datetime import datetime

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

# ICP Funding amounts
icp_funding_mask = (df['origination_account_id'] == 21) & (df['description'].str.contains('JPMORGAN ACCESS TRANSFER FROM', na=False))
icp_funding_amounts = set(df[icp_funding_mask]['amount'].values)

# Encoders
le_account = LabelEncoder()
le_payment = LabelEncoder()
le_account.fit(df['origination_account_id'].fillna(0).astype(int).astype(str))
le_payment.fit(df['payment_method'].fillna(-1).astype(int).astype(str))

def normalize_label(label):
    """Label unification"""
    label = str(label).strip()
    if 'YORK ADAMS' in label.upper():
        return 'York Adams'
    if label.startswith('Recovery Wire'):
        return 'Recovery Wire'
    if label == 'PNC LOI':
        return 'LOI'
    if label in ['MT WH', 'MT']:
        return 'MT UI'
    if label in ['ICP Refund ', ' ICP Refund']:
        return 'ICP Refund'
    if label in [' ICP Return']:
        return 'ICP Return'
    return label

# Normalize all labels
df['agent'] = df['agent'].apply(normalize_label)

def test_rules(rules_code):
    """Test rules and return accuracy"""
    exec(rules_code, globals())
    
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
    
    # Combine
    df_test.loc[rule_mask, 'predicted'] = df_test.loc[rule_mask, 'rule_pred']
    df_test.loc[~rule_mask, 'predicted'] = ml_df['ml_pred']
    
    # Calculate
    correct = (df_test['agent'] == df_test['predicted']).sum()
    accuracy = correct / len(df_test) * 100
    
    # Find errors
    errors = df_test[df_test['agent'] != df_test['predicted']]
    error_by_agent = errors.groupby('agent').size().sort_values(ascending=False).head(10)
    
    return accuracy, error_by_agent, errors

# BASELINE RULES
baseline_rules = '''
def apply_rules(row, icp_funding_amounts=None):
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
    elif acc == 21 and 'REFUND' in desc:
        return 'ICP Return'
    elif 'OHEMWHTX' in desc or 'OH WH TAX' in desc or '8011OHIO-TAXOEWH' in desc:
        return 'OH WH'
    elif 'CHECK' in desc and ('REFERENCE' in desc or 'ITEM' in desc or 'POSTED' in desc):
        return 'Check Adjustment'
    elif 'YORK ADAMS' in desc:
        return 'York Adams'
    elif 'IRS' in desc:
        return 'IRS Wire'
    
    return None
'''

print("=" * 100)
print("🚀 5-ITERATION AUTOMATIC IMPROVEMENT")
print("=" * 100)
print()

# Test baseline
print("📊 ITERATION 0 (Baseline)")
baseline_acc, baseline_errors, errors_df = test_rules(baseline_rules)
print(f"   Accuracy: {baseline_acc:.2f}%")
print(f"   Top 5 errors: {dict(list(baseline_errors.head(5).items()))}")
print()

best_acc = baseline_acc
best_rules = baseline_rules
history = [(0, baseline_acc, "Baseline")]

# ITERATIONS
for iteration in range(1, 6):
    print(f"🔄 ITERATION {iteration}")
    
    # Analyze top error
    top_error_agent = baseline_errors.index[0]
    agent_errors = errors_df[errors_df['agent'] == top_error_agent]
    
    print(f"   Target: {top_error_agent} ({baseline_errors.iloc[0]} errors)")
    
    # Find pattern
    descriptions = agent_errors['description'].str.upper().head(30)
    
    # Find common 3-word phrases
    phrases = []
    for desc in descriptions:
        words = desc.split()
        for i in range(len(words)-2):
            phrase = ' '.join(words[i:i+3])
            if len(phrase) > 10 and not phrase.replace(' ', '').isdigit():
                phrases.append(phrase)
    
    phrase_counts = Counter(phrases)
    
    if len(phrase_counts) > 0:
        top_phrase, count = phrase_counts.most_common(1)[0]
        coverage = count / len(agent_errors) * 100
        
        print(f"   Pattern found: '{top_phrase[:50]}' ({coverage:.1f}% coverage)")
        
        # Check PM/ACC patterns
        pm_mode = agent_errors['payment_method'].mode()[0] if len(agent_errors) > 0 else None
        acc_mode = agent_errors['origination_account_id'].mode()[0] if len(agent_errors) > 0 else None
        
        # Try adding rule
        new_rule_line = f"    elif '{top_phrase[:30]}' in desc:\n        return '{top_error_agent}'\n"
        
        # Insert before last return
        new_rules = best_rules.replace("    return None", new_rule_line + "    return None")
        
        # Test new rules
        try:
            new_acc, new_errors, new_errors_df = test_rules(new_rules)
            
            if new_acc > best_acc:
                print(f"   ✅ Improvement: {best_acc:.2f}% → {new_acc:.2f}% (+{new_acc-best_acc:.2f}%)")
                best_acc = new_acc
                best_rules = new_rules
                baseline_errors = new_errors
                errors_df = new_errors_df
                history.append((iteration, new_acc, f"Added rule for {top_error_agent}"))
            else:
                print(f"   ❌ No improvement: {new_acc:.2f}% (keeping {best_acc:.2f}%)")
                history.append((iteration, best_acc, f"Skipped (no improvement)"))
        except Exception as e:
            print(f"   ⚠️  Error testing rule: {e}")
            history.append((iteration, best_acc, "Error in rule"))
    else:
        print(f"   ⚠️  No clear pattern found")
        history.append((iteration, best_acc, "No pattern"))
    
    print()

print("=" * 100)
print("FINAL RESULTS")
print("=" * 100)
print()

print("📈 Improvement History:")
for it, acc, note in history:
    print(f"   Iteration {it}: {acc:.2f}% - {note}")

print()
print(f"🎯 BEST ACCURACY: {best_acc:.2f}%")
print(f"📈 IMPROVEMENT: +{best_acc - baseline_acc:.2f}%")
print()

# Save best rules
with open('best_rules_auto.py', 'w') as f:
    f.write(best_rules)

print("✅ Best rules saved to: best_rules_auto.py")

