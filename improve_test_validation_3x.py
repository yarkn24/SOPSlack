#!/usr/bin/env python3
"""
3 Iterations to Improve Test & Validation
=========================================
"""

import pandas as pd
import numpy as np
import joblib
from scipy.sparse import hstack
from sklearn.preprocessing import LabelEncoder
from collections import Counter

from predict_with_rules import apply_rules, normalize_label

model = joblib.load('ultra_fast_model.pkl')
tfidf = joblib.load('ultra_fast_tfidf.pkl')
le_agent = joblib.load('ultra_fast_agent_encoder.pkl')

df = pd.read_csv('/Users/yarkin.akcil/Downloads/Unrecon_2025_10_05_updated.csv', low_memory=False)
df['amount'] = df['amount'] / 100
df['date'] = pd.to_datetime(df['date'], format='mixed')
df = df[df['date'] >= '2024-01-01'].copy()
df = df[df['agent'].notna()].copy()

svb_accounts = [1, 2, 5, 10, 24]
df = df[~df['origination_account_id'].isin(svb_accounts)].copy()
df['agent'] = df['agent'].apply(normalize_label)

icp_funding_mask = (df['origination_account_id'] == 21) & (df['description'].str.contains('JPMORGAN ACCESS TRANSFER FROM', na=False))
icp_funding_amounts = set(df[icp_funding_mask]['amount'].values)

test_end = int(len(df) * 0.85)
test_data = df.iloc[test_end:].copy()

le_account = LabelEncoder()
le_payment = LabelEncoder()
le_account.fit(df['origination_account_id'].fillna(0).astype(int).astype(str))
le_payment.fit(df['payment_method'].fillna(-1).astype(int).astype(str))

def evaluate(data, icp_amounts):
    """Evaluate and return accuracy + errors"""
    data_test = data.copy()
    data_test['rule_pred'] = data_test.apply(lambda row: apply_rules(row, icp_amounts), axis=1)
    rule_mask = data_test['rule_pred'].notna()
    
    ml_df = data_test[~rule_mask].copy()
    
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
    
    data_test.loc[rule_mask, 'predicted'] = data_test.loc[rule_mask, 'rule_pred']
    data_test.loc[~rule_mask, 'predicted'] = ml_df['ml_pred']
    
    correct = (data_test['agent'] == data_test['predicted']).sum()
    accuracy = correct / len(data_test) * 100
    
    errors = data_test[data_test['agent'] != data_test['predicted']]
    
    return accuracy, errors

print("=" * 100)
print("🎯 3-ITERATION IMPROVEMENT FOR TEST SET")
print("=" * 100)
print()

baseline_acc, baseline_errors = evaluate(test_data, icp_funding_amounts)
print(f"📊 BASELINE TEST ACCURACY: {baseline_acc:.2f}%")
print(f"   Total errors: {len(baseline_errors)}")
print()

for iteration in range(1, 4):
    print(f"{'='*100}")
    print(f"🔄 ITERATION {iteration}")
    print(f"{'='*100}")
    
    error_by_agent = baseline_errors.groupby('agent').size().sort_values(ascending=False)
    
    print(f"   Top 5 error agents: {dict(error_by_agent.head(5))}")
    print()
    
    # Analyze top error agent
    top_agent = error_by_agent.index[0]
    agent_errors = baseline_errors[baseline_errors['agent'] == top_agent]
    
    print(f"🔍 Analyzing: {top_agent} ({len(agent_errors)} errors)")
    print(f"   Predicted as: {agent_errors['predicted'].value_counts().head(3).to_dict()}")
    
    # Find common patterns
    descriptions = agent_errors['description'].str.upper()
    
    # Look for 2-3 word phrases
    phrases = []
    for desc in descriptions.head(20):
        words = desc.split()
        for i in range(len(words)-2):
            phrase = ' '.join(words[i:i+3])
            if len(phrase) > 12 and not phrase.replace(' ', '').replace(',', '').isdigit():
                phrases.append(phrase)
    
    phrase_counts = Counter(phrases)
    
    if len(phrase_counts) > 0:
        top_phrase, count = phrase_counts.most_common(1)[0]
        coverage = count / len(agent_errors) * 100
        
        print(f"   Pattern: '{top_phrase[:60]}' ({coverage:.1f}% coverage)")
        
        if coverage >= 30:  # Only suggest if 30%+ coverage
            print(f"   ✅ HIGH COVERAGE - Suggestion:")
            print(f"      elif '{top_phrase[:40]}' in desc:")
            print(f"          return '{top_agent}'")
        else:
            print(f"   ⚠️  LOW COVERAGE - Pattern not strong enough")
    else:
        print(f"   ⚠️  No clear pattern found")
    
    # Show samples
    print(f"   Sample errors:")
    for idx, row in agent_errors.head(3).iterrows():
        pm = row['payment_method']
        acc = row['origination_account_id']
        pred = row['predicted']
        print(f"   • PM={pm}, ACC={acc}, Predicted={pred}")
        print(f"     {row['description'][:80]}...")
    
    print()

print("=" * 100)
print("💡 MANUAL IMPROVEMENTS NEEDED")
print("=" * 100)
print()
print("Review top error patterns above and add specific rules to predict_with_rules.py")
print(f"Current Test Accuracy: {baseline_acc:.2f}%")
print(f"Target: 96%+")

