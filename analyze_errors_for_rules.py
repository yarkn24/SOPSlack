#!/usr/bin/env python3
"""
Analyze Errors and Extract Patterns for New Rules
==================================================
"""

import pandas as pd
import numpy as np
import joblib
from scipy.sparse import hstack
from sklearn.preprocessing import LabelEncoder
from predict_with_rules import apply_rules

print("=" * 100)
print("ERROR ANALYSIS FOR RULE EXTRACTION")
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

print("📊 Applying rules and ML...")

# Apply rules
df['rule_prediction'] = df.apply(lambda row: apply_rules(row, icp_funding_amounts), axis=1)
rule_mask = df['rule_prediction'].notna()

# ML for rest
ml_df = df[~rule_mask].copy()

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
df.loc[rule_mask, 'predicted_agent'] = df.loc[rule_mask, 'rule_prediction']
df.loc[~rule_mask, 'predicted_agent'] = ml_df['ml_prediction']

# Find errors
df['is_error'] = df['agent'] != df['predicted_agent']
errors = df[df['is_error']].copy()

print(f"✅ Total errors: {len(errors)} / {len(df)} ({len(errors)/len(df)*100:.2f}%)")
print()

# Analyze top error patterns
print("=" * 100)
print("TOP ERROR PATTERNS (by agent)")
print("=" * 100)
print()

error_by_agent = errors.groupby('agent').size().sort_values(ascending=False).head(15)

for agent, count in error_by_agent.items():
    agent_errors = errors[errors['agent'] == agent]
    
    print(f"\n📌 {agent}: {count} errors")
    print(f"   Predicted as: {agent_errors['predicted_agent'].value_counts().head(3).to_dict()}")
    
    # Analyze patterns
    descriptions = agent_errors['description'].str.upper()
    
    # Find common keywords
    all_desc = ' '.join(descriptions.values)
    words = all_desc.split()
    
    # Filter meaningful words (longer than 3 chars)
    meaningful_words = [w for w in words if len(w) > 3 and not w.isdigit()]
    
    from collections import Counter
    word_counts = Counter(meaningful_words)
    top_words = word_counts.most_common(5)
    
    print(f"   Common keywords: {[w for w, c in top_words]}")
    
    # Check payment method
    pm_dist = agent_errors['payment_method'].value_counts().head(2)
    print(f"   Payment methods: {pm_dist.to_dict()}")
    
    # Check accounts
    acc_dist = agent_errors['origination_account_id'].value_counts().head(2)
    print(f"   Accounts: {acc_dist.to_dict()}")

print()
print("=" * 100)
print("SUGGESTED RULE PATTERNS")
print("=" * 100)
print()

# Generate rule suggestions
for agent, count in error_by_agent.head(10).items():
    agent_errors = errors[errors['agent'] == agent]
    
    # Check if there's a strong keyword pattern
    descriptions = agent_errors['description'].str.upper()
    
    # Look for common 2-3 word phrases
    common_phrases = []
    for desc in descriptions.head(10):
        words = desc.split()
        # Check 2-word phrases
        for i in range(len(words)-1):
            phrase = ' '.join(words[i:i+2])
            if len(phrase) > 8 and not phrase.replace(' ', '').isdigit():
                common_phrases.append(phrase)
    
    from collections import Counter
    phrase_counts = Counter(common_phrases)
    top_phrases = phrase_counts.most_common(3)
    
    if len(top_phrases) > 0 and top_phrases[0][1] >= count * 0.3:  # At least 30% coverage
        phrase, phrase_count = top_phrases[0]
        coverage = phrase_count / count * 100
        
        print(f"✨ {agent}:")
        print(f"   Pattern: '{phrase}' appears in {phrase_count}/{count} errors ({coverage:.1f}%)")
        print(f"   Suggested rule: elif '{phrase}' in desc: return '{agent}'")
        print()

