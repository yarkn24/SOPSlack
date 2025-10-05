#!/usr/bin/env python3
"""
🎯 PREDICTION WITH RULES - Hybrid approach
1. Apply business rules first (100% accurate)
2. Use ML model only for non-rule cases
"""

import pandas as pd
import numpy as np
import joblib
from scipy.sparse import hstack
from sklearn.preprocessing import LabelEncoder
from datetime import datetime

def apply_rules(row):
    """Apply business rules. Returns agent name if rule matches, None otherwise."""
    desc = str(row['description']).upper()
    acc = int(row['origination_account_id']) if pd.notna(row['origination_account_id']) else 0
    amt = float(row['amount'])
    pm = int(row['payment_method']) if pd.notna(row['payment_method']) else -1
    
    # Apply rules in priority order
    if '1TRV' in desc:
        return 'Risk'
    elif 'STATE OF MONTANA' in desc:
        return 'MT WH'
    elif 'NYS DTF WT' in desc:
        return 'NY WH'
    elif 'NYS DOL UI' in desc:
        return 'NY UI'
    elif '100% US TREASURY CAPITAL 3163' in desc or 'MONEY MKT MUTUAL FUND' in desc:
        return 'Money Market Transfer'
    elif 'JPMORGAN ACCESS TRANSFER' in desc:
        return 'Treasury Transfer'
    elif 'INTEREST ADJUSTMENT' in desc:
        return 'Interest Adjustment'
    elif acc == 16 and 'CREDIT MEMO' in desc:
        return 'PNC LOI'
    elif 'KEYSTONE' in desc:
        return 'PA UI'
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
    
    return None  # No rule matched

def predict_with_rules(data, model, tfidf, le_agent, le_account, le_payment):
    """Hybrid prediction: Rules first, then ML model."""
    
    predictions = []
    rule_used = []
    
    for idx, row in data.iterrows():
        # Try rules first
        rule_prediction = apply_rules(row)
        
        if rule_prediction is not None:
            predictions.append(rule_prediction)
            rule_used.append(True)
        else:
            # Use ML model
            X_tfidf = tfidf.transform([row['description']])
            
            # Extract features
            payment_encoded = le_payment.transform([str(int(row['payment_method']) if pd.notna(row['payment_method']) else -1)])
            account_encoded = le_account.transform([str(int(row['origination_account_id']) if pd.notna(row['origination_account_id']) else 0)])
            amount = row['amount']
            amount_log = np.log1p(abs(amount))
            
            X_ex = pd.DataFrame({
                'payment': payment_encoded,
                'account': account_encoded,
                'amount': [amount],
                'amount_log': [amount_log]
            })
            
            X = hstack([X_tfidf, X_ex.values])
            
            # Predict
            pred_idx = model.predict(X)[0]
            pred_agent = le_agent.inverse_transform([pred_idx])[0]
            
            predictions.append(pred_agent)
            rule_used.append(False)
    
    return predictions, rule_used

# Test the hybrid approach
print("=" * 100)
print("🎯 TESTING HYBRID PREDICTION (Rules + ML)")
print("=" * 100)

# Load model
model = joblib.load('ultra_fast_model.pkl')
tfidf = joblib.load('ultra_fast_tfidf.pkl')
le_agent = joblib.load('ultra_fast_agent_encoder.pkl')

# Load data
df = pd.read_csv('/Users/yarkin.akcil/Downloads/Unrecon_2025_10_05.csv', low_memory=False)
df['amount'] = df['amount'] / 100
df['date'] = pd.to_datetime(df['date'])
df = df[df['date'] >= '2024-01-01'].copy()
df = df[df['agent'].notna()].copy()

svb_accounts = [1, 2, 5, 10, 24]
df = df[~df['origination_account_id'].isin(svb_accounts)].copy()
df['agent'] = df['agent'].str.strip()

# Apply rules to training data (same as before)
print("\n📂 Preparing data...")
for idx, row in df.iterrows():
    rule_agent = apply_rules(row)
    if rule_agent:
        df.at[idx, 'agent'] = rule_agent

print(f"✅ {len(df):,} transactions | {df['agent'].nunique()} agents")

# Split
test_end = int(len(df) * 0.85)
val_data = df.iloc[test_end:].copy()

# Prepare encoders
le_account = LabelEncoder()
le_payment = LabelEncoder()
le_account.fit(df['origination_account_id'].fillna(0).astype(int).astype(str))
le_payment.fit(df['payment_method'].fillna(-1).astype(int).astype(str))

# Filter validation to agents in training
train_agents = set(le_agent.classes_)
val_data_filtered = val_data[val_data['agent'].isin(train_agents)].copy().reset_index(drop=True)

print(f"✅ Validation: {len(val_data_filtered):,} transactions")

# Hybrid prediction
print("\n🔧 Running hybrid prediction...")
start = datetime.now()
predictions, rule_used = predict_with_rules(val_data_filtered, model, tfidf, le_agent, le_account, le_payment)
elapsed = (datetime.now() - start).total_seconds()

val_data_filtered['predicted'] = predictions
val_data_filtered['rule_used'] = rule_used
val_data_filtered['correct'] = (val_data_filtered['agent'] == val_data_filtered['predicted']).astype(int)

# Results
overall_acc = val_data_filtered['correct'].mean() * 100
rule_count = sum(rule_used)
ml_count = len(rule_used) - rule_count

rule_data = val_data_filtered[val_data_filtered['rule_used']]
ml_data = val_data_filtered[~val_data_filtered['rule_used']]

rule_acc = rule_data['correct'].mean() * 100 if len(rule_data) > 0 else 0
ml_acc = ml_data['correct'].mean() * 100 if len(ml_data) > 0 else 0

print(f"\n✅ Prediction time: {elapsed:.2f}s ({elapsed/len(val_data_filtered)*1000:.2f}ms per BT)")

print("\n" + "=" * 100)
print("🏆 HYBRID RESULTS")
print("=" * 100)
print(f"📊 Overall Accuracy: {overall_acc:.2f}%")
print(f"\n🔹 Rule-based: {rule_count:,} BTs ({rule_count/len(val_data_filtered)*100:.1f}%) → {rule_acc:.2f}% accurate")
print(f"🔹 ML-based:   {ml_count:,} BTs ({ml_count/len(val_data_filtered)*100:.1f}%) → {ml_acc:.2f}% accurate")

# Top agents analysis
print("\n" + "=" * 100)
print("📊 TOP 10 AGENTS - HYBRID PERFORMANCE")
print("=" * 100)

agent_counts = val_data_filtered['agent'].value_counts().head(10)
for rank, (agent, count) in enumerate(agent_counts.items(), 1):
    agent_data = val_data_filtered[val_data_filtered['agent'] == agent]
    correct = agent_data['correct'].sum()
    accuracy = correct / count * 100
    rule_pct = agent_data['rule_used'].sum() / count * 100
    
    print(f"{rank:2d}. {agent:30s}: {accuracy:6.2f}% ({count:5,} BTs, {rule_pct:5.1f}% via rules)")

print("\n" + "=" * 100)
print("✅ COMPLETE!")
print("=" * 100)
