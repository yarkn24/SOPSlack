"""
Test Original 98.64% Model
===========================
Uses the EXACT same data and split as ultra_fast_training.py

Usage:
    python test_original_model.py
"""

import pandas as pd
import numpy as np
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score
from scipy.sparse import hstack
from datetime import datetime

print("=" * 80)
print("TESTING ORIGINAL 98.64% MODEL")
print("=" * 80)
print()

# ============================================================================
# LOAD EXACT SAME DATA (as ultra_fast_training.py)
# ============================================================================

print("📂 Loading data...")
df = pd.read_csv('/Users/yarkin.akcil/Desktop/cursor_data/Unrecon_2025_10_05_updated.csv', low_memory=False)
print(f"   Loaded: {len(df):,} rows")

# EXACT same processing as ultra_fast_training.py
df['amount'] = df['amount'] / 100
df['date'] = pd.to_datetime(df['date'], format='mixed')
df = df[df['date'] >= '2024-01-01'].copy()
df = df[df['agent'].notna()].copy()

# Remove SVB
svb_accounts = [1, 2, 5, 10, 24]
df = df[~df['origination_account_id'].isin(svb_accounts)].copy()

# Normalize agent
df['agent'] = df['agent'].str.strip()

print(f"✅ Processed: {len(df):,} transactions | {df['agent'].nunique()} agents")
print()

# ============================================================================
# EXACT SAME SPLIT (temporal)
# ============================================================================

print("🔪 Splitting...")

# Sort by date
df = df.sort_values('date').reset_index(drop=True)

# Split dates
split_date_1 = '2024-09-01'
split_date_2 = '2024-10-01'

train_data = df[df['date'] < split_date_1].copy()
test_data = df[(df['date'] >= split_date_1) & (df['date'] < split_date_2)].copy()
val_data = df[df['date'] >= split_date_2].copy()

print(f"✅ Train: {len(train_data):,} (before {split_date_1})")
print(f"✅ Test: {len(test_data):,} ({split_date_1} to {split_date_2})")
print(f"✅ Val: {len(val_data):,} (after {split_date_2})")
print()

# ============================================================================
# EXACT SAME FEATURES (as ultra_fast_training.py)
# ============================================================================

print("🔧 Feature engineering...")

# TF-IDF (30 features)
tfidf = TfidfVectorizer(max_features=30, ngram_range=(1, 2), min_df=2)
X_train_tfidf = tfidf.fit_transform(train_data['description'].fillna(''))
X_test_tfidf = tfidf.transform(test_data['description'].fillna(''))
X_val_tfidf = tfidf.transform(val_data['description'].fillna(''))

# Encoders
le_account = LabelEncoder()
le_payment = LabelEncoder()
le_account.fit(df['origination_account_id'].fillna(0).astype(int).astype(str))
le_payment.fit(df['payment_method'].fillna(-1).astype(int).astype(str))

def extract_features(data):
    f = pd.DataFrame()
    f['payment'] = le_payment.transform(data['payment_method'].fillna(-1).astype(int).astype(str))
    f['account'] = le_account.transform(data['origination_account_id'].fillna(0).astype(int).astype(str))
    f['amount'] = data['amount'].values
    f['amount_log'] = np.log1p(data['amount'].abs().values)
    return f

X_train_ex = extract_features(train_data)
X_test_ex = extract_features(test_data)
X_val_ex = extract_features(val_data)

# Combine
X_train = hstack([X_train_tfidf, X_train_ex])
X_test = hstack([X_test_tfidf, X_test_ex])
X_val = hstack([X_val_tfidf, X_val_ex])

print(f"✅ Features: {X_train.shape[1]} (30 TF-IDF + 4 others)")
print()

# ============================================================================
# ENCODE AGENTS
# ============================================================================

print("🏷️  Encoding agents...")

le_agent = LabelEncoder()
le_agent.fit(train_data['agent'])

# Filter test/val to only include agents seen in training
train_agents = set(train_data['agent'])
test_data_filtered = test_data[test_data['agent'].isin(train_agents)].copy()
val_data_filtered = val_data[val_data['agent'].isin(train_agents)].copy()

print(f"   Filtered test: {len(test_data)} → {len(test_data_filtered)}")
print(f"   Filtered val: {len(val_data)} → {len(val_data_filtered)}")

y_train = le_agent.transform(train_data['agent'])
y_test = le_agent.transform(test_data_filtered['agent'])
y_val = le_agent.transform(val_data_filtered['agent'])

# Update X matrices
X_test_tfidf = tfidf.transform(test_data_filtered['description'].fillna(''))
X_val_tfidf = tfidf.transform(val_data_filtered['description'].fillna(''))
X_test_ex = extract_features(test_data_filtered)
X_val_ex = extract_features(val_data_filtered)
X_test = hstack([X_test_tfidf, X_test_ex])
X_val = hstack([X_val_tfidf, X_val_ex])

print(f"✅ {len(le_agent.classes_)} unique agents (training)")
print()

# ============================================================================
# LOAD MODEL & PREDICT
# ============================================================================

print("🤖 Loading model...")
model = joblib.load('ultra_fast_model.pkl')
print("✅ Model loaded")
print()

print("🎯 Predicting...")
y_train_pred = model.predict(X_train)
y_test_pred = model.predict(X_test)
y_val_pred = model.predict(X_val)
print("✅ Predictions complete")
print()

# ============================================================================
# CALCULATE ACCURACY
# ============================================================================

print("=" * 80)
print("ACCURACY RESULTS")
print("=" * 80)
print()

train_acc = accuracy_score(y_train, y_train_pred)
test_acc = accuracy_score(y_test, y_test_pred)
val_acc = accuracy_score(y_val, y_val_pred)

print(f"📊 ACCURACY:")
print(f"   Training:   {train_acc*100:.2f}%")
print(f"   Test:       {test_acc*100:.2f}%")
print(f"   Validation: {val_acc*100:.2f}%")
print()

print(f"🎯 OVERALL: {val_acc*100:.2f}%")
print()

# ============================================================================
# TOP AGENTS BREAKDOWN
# ============================================================================

print("=" * 80)
print("TOP 10 AGENTS (Validation Set)")
print("=" * 80)
print()

top_agents = val_data_filtered['agent'].value_counts().head(10)
for agent in top_agents.index:
    agent_mask = val_data_filtered['agent'] == agent
    agent_true = y_val[agent_mask]
    agent_pred = y_val_pred[agent_mask]
    agent_acc = accuracy_score(agent_true, agent_pred)
    
    print(f"{agent:30s} | {top_agents[agent]:5d} txns | {agent_acc*100:5.1f}% accuracy")

print()
print("🎉 Test complete!")

