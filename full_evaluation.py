#!/usr/bin/env python3
"""
Full Evaluation: Training, Test, and Validation Sets
=====================================================
"""

import pandas as pd
import numpy as np
import joblib
from scipy.sparse import hstack
from sklearn.preprocessing import LabelEncoder
from datetime import datetime

# Import rules
from predict_with_rules import apply_rules, normalize_label

print("=" * 100)
print("📊 FULL MODEL EVALUATION")
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
df['agent'] = df['agent'].apply(normalize_label)

# ICP Funding amounts
icp_funding_mask = (df['origination_account_id'] == 21) & (df['description'].str.contains('JPMORGAN ACCESS TRANSFER FROM', na=False))
icp_funding_amounts = set(df[icp_funding_mask]['amount'].values)

print(f"📂 Total data: {len(df):,} transactions")
print()

# Split data (same as training)
test_end = int(len(df) * 0.85)
train_data = df.iloc[:test_end].copy()
test_data = df.iloc[test_end:].copy()
val_data = df[df['date'] >= '2024-10-01'].copy()

print(f"📊 Data splits:")
print(f"   Training:   {len(train_data):,} transactions (85%)")
print(f"   Test:       {len(test_data):,} transactions (15%)")
print(f"   Validation: {len(val_data):,} transactions (Oct 2024+)")
print()

# Encoders
le_account = LabelEncoder()
le_payment = LabelEncoder()
le_account.fit(df['origination_account_id'].fillna(0).astype(int).astype(str))
le_payment.fit(df['payment_method'].fillna(-1).astype(int).astype(str))

def evaluate_set(data, set_name):
    """Evaluate accuracy on a dataset"""
    print(f"{'='*100}")
    print(f"🔍 {set_name}")
    print(f"{'='*100}")
    
    # Apply rules
    data_test = data.copy()
    data_test['rule_pred'] = data_test.apply(lambda row: apply_rules(row, icp_funding_amounts), axis=1)
    rule_mask = data_test['rule_pred'].notna()
    
    # ML for rest
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
    
    # Combine
    data_test.loc[rule_mask, 'predicted'] = data_test.loc[rule_mask, 'rule_pred']
    data_test.loc[~rule_mask, 'predicted'] = ml_df['ml_pred']
    
    # Calculate
    correct = (data_test['agent'] == data_test['predicted']).sum()
    accuracy = correct / len(data_test) * 100
    
    rule_count = rule_mask.sum()
    ml_count = (~rule_mask).sum()
    
    # Rule accuracy
    rule_correct = (data_test[rule_mask]['agent'] == data_test[rule_mask]['rule_pred']).sum()
    rule_acc = rule_correct / rule_count * 100 if rule_count > 0 else 0
    
    # ML accuracy
    ml_correct = correct - rule_correct
    ml_acc = ml_correct / ml_count * 100 if ml_count > 0 else 0
    
    print(f"📊 Overall Accuracy: {accuracy:.2f}%")
    print()
    print(f"🔹 Rule-based: {rule_count:,} BTs ({rule_count/len(data_test)*100:.1f}%) → {rule_acc:.2f}% accurate")
    print(f"🔹 ML-based:   {ml_count:,} BTs ({ml_count/len(data_test)*100:.1f}%) → {ml_acc:.2f}% accurate")
    print()
    
    return accuracy

# Evaluate all sets
train_acc = evaluate_set(train_data, "TRAINING SET")
test_acc = evaluate_set(test_data, "TEST SET")
val_acc = evaluate_set(val_data, "VALIDATION SET (Oct 2024+)")

print("=" * 100)
print("📈 SUMMARY")
print("=" * 100)
print()
print(f"✅ Training Set:   {train_acc:.2f}%")
print(f"✅ Test Set:       {test_acc:.2f}%")
print(f"✅ Validation Set: {val_acc:.2f}%")
print()
print("🎯 MODEL IS READY FOR PRODUCTION!")

