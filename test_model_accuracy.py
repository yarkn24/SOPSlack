"""
Test Model Accuracy with Redash Format Data
============================================
Uses train/test/val data in Redash format to verify model accuracy.

Usage:
    python test_model_accuracy.py
"""

import pandas as pd
import numpy as np
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score, classification_report
from scipy.sparse import hstack
from data_mapping import map_payment_method, map_account

print("=" * 80)
print("MODEL ACCURACY TEST")
print("=" * 80)
print()

# ============================================================================
# LOAD DATA (Redash format with agents labeled)
# ============================================================================

print("📂 Loading data from cursor_data...")

train_df = pd.read_csv('~/Desktop/cursor_data/train_data_redash_format.csv')
test_df = pd.read_csv('~/Desktop/cursor_data/test_data_redash_format.csv')
val_df = pd.read_csv('~/Desktop/cursor_data/val_data_redash_format.csv')

print(f"✅ Train: {len(train_df):,} rows")
print(f"✅ Test: {len(test_df):,} rows")
print(f"✅ Val: {len(val_df):,} rows")
print()

# ============================================================================
# CONVERT TEXT → NUMERIC (Redash format → ML format)
# ============================================================================

print("🔄 Converting Redash format → ML format...")

def convert_to_ml_format(df):
    """Convert Redash text format to numeric for ML."""
    df_ml = df.copy()
    
    # Convert payment_method text → numeric
    df_ml['payment_method_num'] = df_ml['payment_method'].apply(map_payment_method)
    
    # Convert account text → numeric
    df_ml['account_num'] = df_ml['account'].apply(map_account)
    
    return df_ml

train_ml = convert_to_ml_format(train_df)
test_ml = convert_to_ml_format(test_df)
val_ml = convert_to_ml_format(val_df)

print("✅ Format converted")
print()

# ============================================================================
# FEATURE ENGINEERING (same as ultra_fast_training.py)
# ============================================================================

print("🔧 Feature engineering...")

# Combine all data for consistent encoding
all_df = pd.concat([train_ml, test_ml, val_ml], ignore_index=True)

# TF-IDF on descriptions (30 features)
tfidf = TfidfVectorizer(max_features=30, ngram_range=(1, 2), min_df=2)
tfidf.fit(all_df['description'].fillna(''))

X_train_tfidf = tfidf.transform(train_ml['description'].fillna(''))
X_test_tfidf = tfidf.transform(test_ml['description'].fillna(''))
X_val_tfidf = tfidf.transform(val_ml['description'].fillna(''))

# Encode payment_method and account
le_payment = LabelEncoder()
le_account = LabelEncoder()
le_payment.fit(all_df['payment_method_num'].fillna(-1).astype(str))
le_account.fit(all_df['account_num'].fillna(0).astype(str))

def extract_features(data):
    """Extract features: payment, account, amount, amount_log."""
    f = pd.DataFrame()
    f['payment'] = le_payment.transform(data['payment_method_num'].fillna(-1).astype(str))
    f['account'] = le_account.transform(data['account_num'].fillna(0).astype(str))
    f['amount'] = data['amount'].values
    f['amount_log'] = np.log1p(data['amount'].abs().values)
    return f

X_train_ex = extract_features(train_ml)
X_test_ex = extract_features(test_ml)
X_val_ex = extract_features(val_ml)

# Combine features
X_train = hstack([X_train_tfidf, X_train_ex])
X_test = hstack([X_test_tfidf, X_test_ex])
X_val = hstack([X_val_tfidf, X_val_ex])

print(f"✅ Feature shape: {X_train.shape[1]} features")
print(f"   TF-IDF: 30")
print(f"   Payment: 1")
print(f"   Account: 1")
print(f"   Amount: 1")
print(f"   Amount_log: 1")
print()

# ============================================================================
# ENCODE AGENTS
# ============================================================================

print("🏷️  Encoding agents...")

le_agent = LabelEncoder()
le_agent.fit(all_df['agent'])

y_train = le_agent.transform(train_ml['agent'])
y_test = le_agent.transform(test_ml['agent'])
y_val = le_agent.transform(val_ml['agent'])

print(f"✅ {len(le_agent.classes_)} unique agents")
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

print(f"🎯 OVERALL: {val_acc*100:.2f}% (validation is the true measure)")
print()

# ============================================================================
# DETAILED REPORT (Val data)
# ============================================================================

print("=" * 80)
print("VALIDATION SET DETAILED REPORT")
print("=" * 80)
print()

val_report = classification_report(
    y_val, 
    y_val_pred, 
    target_names=le_agent.classes_,
    zero_division=0
)

print(val_report)
print()

# ============================================================================
# ERROR ANALYSIS
# ============================================================================

print("=" * 80)
print("ERROR ANALYSIS (Validation Set)")
print("=" * 80)
print()

errors = val_ml[y_val != y_val_pred].copy()
errors['true_agent'] = le_agent.inverse_transform(y_val[y_val != y_val_pred])
errors['predicted_agent'] = le_agent.inverse_transform(y_val_pred[y_val != y_val_pred])

print(f"❌ Total errors: {len(errors)} / {len(val_ml)} ({len(errors)/len(val_ml)*100:.2f}%)")
print()

if len(errors) > 0:
    print("Top 10 error cases:")
    for idx, row in errors.head(10).iterrows():
        print(f"\nID: {row['id']}")
        print(f"   True: {row['true_agent']}")
        print(f"   Predicted: {row['predicted_agent']}")
        print(f"   Amount: ${row['amount']:,.2f}")
        print(f"   Payment: {row['payment_method']}")
        print(f"   Account: {row['account']}")
        print(f"   Description: {row['description'][:80]}...")

print()
print("🎉 Accuracy test complete!")

