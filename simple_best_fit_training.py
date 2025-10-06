"""
Simple & Best-Fit Training for Bank Transaction Labeling
Based on Kaggle best practices for text + tabular classification
Focus: 2024+ data (most accurate)
"""

import pandas as pd
import numpy as np
from datetime import datetime
import time
import warnings
warnings.filterwarnings('ignore')

from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score, classification_report
import joblib

try:
    import lightgbm as lgb
    print("✅ LightGBM available")
except:
    lgb = None
    print("⚠️  LightGBM not available")

try:
    from catboost import CatBoostClassifier
    print("✅ CatBoost available")
except:
    CatBoostClassifier = None
    print("⚠️  CatBoost not available")

print("\n" + "=" * 80)
print("🎯 SIMPLE BEST-FIT TRAINING")
print("=" * 80)
print("\n📋 Strategy (based on Kaggle best practices):")
print("   • Use only 2024+ data (most accurate)")
print("   • Top 3 algorithms for text+tabular:")
print("     1. CatBoost (best for categorical features)")
print("     2. LightGBM (fast, powerful)")
print("     3. Random Forest (reliable baseline)")
print("\n⏱️  ESTIMATED TIME: 15-20 minutes")
print("🎯 TARGET: 94% accuracy")
print("=" * 80)

start_time = time.time()

# ============================================================================
# LOAD DATA - ONLY 2024+
# ============================================================================
print("\n📂 Loading data (2024+ only)...")
df = pd.read_csv('/Users/yarkin.akcil/Downloads/Unrecon_2025_10_05.csv')
df['amount'] = df['amount'] / 100
df['date'] = pd.to_datetime(df['date'])

# Filter: Only 2024+
df = df[df['date'] >= '2024-01-01'].copy()
df = df[df['agent'].notna()].copy()

print(f"✅ {len(df):,} transactions (2024+)")
print(f"   Date range: {df['date'].min().date()} to {df['date'].max().date()}")
print(f"   Unique agents: {df['agent'].nunique()}")

# Split: 60% train, 20% test, 20% validation (temporal)
df = df.sort_values('date').reset_index(drop=True)
n = len(df)
train_end = int(n * 0.6)
test_end = int(n * 0.8)

train_data = df.iloc[:train_end].copy()
test_data = df.iloc[train_end:test_end].copy()
validation_data = df.iloc[test_end:].copy()

print(f"\n📊 Split:")
print(f"   Train: {len(train_data):,} ({len(train_data)/n*100:.1f}%)")
print(f"   Test:  {len(test_data):,} ({len(test_data)/n*100:.1f}%)")
print(f"   Val:   {len(validation_data):,} ({len(validation_data)/n*100:.1f}%)")

# ============================================================================
# FEATURE ENGINEERING
# ============================================================================
print("\n🔧 Feature engineering...")

# TF-IDF on description
tfidf = TfidfVectorizer(max_features=500, ngram_range=(1, 3), min_df=2)
X_train_tfidf = tfidf.fit_transform(train_data['description'].fillna(''))
X_test_tfidf = tfidf.transform(test_data['description'].fillna(''))
X_val_tfidf = tfidf.transform(validation_data['description'].fillna(''))

# Categorical encoders
le_account = LabelEncoder()
le_payment = LabelEncoder()

le_account.fit(df['origination_account_id'].fillna('UNKNOWN').astype(str))
le_payment.fit(df['payment_method'].fillna('UNKNOWN').astype(str))

def extract_features(data):
    features = pd.DataFrame()
    features['payment_method'] = le_payment.transform(data['payment_method'].fillna('UNKNOWN').astype(str))
    features['account_id'] = le_account.transform(data['origination_account_id'].fillna('UNKNOWN').astype(str))
    features['amount'] = data['amount'].values
    features['amount_log'] = np.log1p(data['amount'].abs().values)
    features['amount_gt_25k'] = (data['amount'] > 25000).astype(int).values
    features['amount_lt_3500'] = (data['amount'] < 3500).astype(int).values
    features['amount_gt_1m'] = (data['amount'] > 1000000).astype(int).values
    
    desc = data['description'].fillna('').astype(str).str.upper()
    account = data['origination_account_id'].fillna('').astype(str).str.lower()
    
    features['has_1trv'] = desc.str.contains('1TRV', regex=False).astype(int).values
    features['has_check'] = desc.str.contains('CHECK', regex=False).astype(int).values
    features['has_nys_dtf'] = desc.str.contains('NYS DTF', regex=False).astype(int).values
    features['has_oh_wh'] = desc.str.contains('OH WH', regex=False).astype(int).values
    features['has_csc'] = desc.str.contains('CSC', regex=False).astype(int).values
    features['has_lockbox'] = desc.str.contains('LOCKBOX', regex=False).astype(int).values
    features['is_chase_recovery'] = account.str.contains('chase recovery', regex=False).astype(int).values
    features['is_wire_in'] = account.str.contains('wire in', regex=False).astype(int).values
    
    return features

X_train_extra = extract_features(train_data)
X_test_extra = extract_features(test_data)
X_val_extra = extract_features(validation_data)

# Combine
from scipy.sparse import hstack
X_train = hstack([X_train_tfidf, X_train_extra.values])
X_test = hstack([X_test_tfidf, X_test_extra.values])
X_val = hstack([X_val_tfidf, X_val_extra.values])

X_train_dense = X_train.toarray()
X_test_dense = X_test.toarray()
X_val_dense = X_val.toarray()

# Labels - simple, no fancy remapping
le_agent = LabelEncoder()
le_agent.fit(df['agent'])  # Fit on all 2024+ agents

y_train = le_agent.transform(train_data['agent'])
y_test = le_agent.transform(test_data['agent'])
y_val = le_agent.transform(validation_data['agent'])

print(f"✅ Features ready: {X_train.shape[1]}")
print(f"   Agents: {len(le_agent.classes_)}")

# ============================================================================
# ALGORITHM 1: CATBOOST (BEST FOR CATEGORICAL)
# ============================================================================
if CatBoostClassifier:
    print("\n" + "=" * 80)
    print("[1/3] CatBoost - Best for categorical features")
    print("=" * 80)
    print("⏱️  ETA: 5-7 minutes")
    
    start = time.time()
    catboost_model = CatBoostClassifier(
        iterations=1000,
        learning_rate=0.1,
        depth=10,
        l2_leaf_reg=3,
        random_state=42,
        verbose=100,
        thread_count=-1
    )
    catboost_model.fit(X_train_dense, y_train, eval_set=(X_val_dense, y_val), early_stopping_rounds=50, verbose=50)
    
    y_val_pred = catboost_model.predict(X_val_dense)
    catboost_acc = accuracy_score(y_val, y_val_pred)
    catboost_time = time.time() - start
    
    print(f"\n✅ CatBoost Validation Accuracy: {catboost_acc*100:.2f}%")
    print(f"⏱️  Training time: {catboost_time/60:.1f} minutes")
    
    # Save
    joblib.dump(catboost_model, 'catboost_model.pkl')
    
    # Show per-agent performance for key agents
    print("\n🎯 Key Agents Performance:")
    for agent in ['Risk', 'Recovery Wire', 'Check', 'NY WH', 'OH WH']:
        if agent in le_agent.classes_:
            agent_idx = list(le_agent.classes_).index(agent)
            mask = (y_val == agent_idx)
            if mask.sum() > 0:
                agent_acc = (y_val_pred[mask] == agent_idx).sum() / mask.sum()
                print(f"   {agent}: {agent_acc*100:.2f}% ({mask.sum()} samples)")

# ============================================================================
# ALGORITHM 2: LIGHTGBM (FAST & POWERFUL)
# ============================================================================
if lgb:
    print("\n" + "=" * 80)
    print("[2/3] LightGBM - Fast & Powerful")
    print("=" * 80)
    print("⏱️  ETA: 3-4 minutes")
    
    start = time.time()
    lgb_model = lgb.LGBMClassifier(
        n_estimators=1000,
        learning_rate=0.1,
        num_leaves=80,
        max_depth=15,
        min_child_samples=10,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
        n_jobs=-1,
        verbose=-1
    )
    lgb_model.fit(
        X_train_dense, y_train,
        eval_set=[(X_val_dense, y_val)],
        callbacks=[lgb.early_stopping(50), lgb.log_evaluation(100)]
    )
    
    y_val_pred = lgb_model.predict(X_val_dense)
    lgb_acc = accuracy_score(y_val, y_val_pred)
    lgb_time = time.time() - start
    
    print(f"\n✅ LightGBM Validation Accuracy: {lgb_acc*100:.2f}%")
    print(f"⏱️  Training time: {lgb_time/60:.1f} minutes")
    
    # Save
    joblib.dump(lgb_model, 'lightgbm_model.pkl')

# ============================================================================
# ALGORITHM 3: RANDOM FOREST (RELIABLE BASELINE)
# ============================================================================
print("\n" + "=" * 80)
print("[3/3] Random Forest - Reliable Baseline")
print("=" * 80)
print("⏱️  ETA: 5-6 minutes")

start = time.time()
rf_model = RandomForestClassifier(
    n_estimators=1000,
    max_depth=40,
    min_samples_split=2,
    min_samples_leaf=1,
    max_features='sqrt',
    random_state=42,
    n_jobs=-1,
    verbose=1
)
rf_model.fit(X_train, y_train)

y_val_pred = rf_model.predict(X_val)
rf_acc = accuracy_score(y_val, y_val_pred)
rf_time = time.time() - start

print(f"\n✅ Random Forest Validation Accuracy: {rf_acc*100:.2f}%")
print(f"⏱️  Training time: {rf_time/60:.1f} minutes")

# Save
joblib.dump(rf_model, 'random_forest_model.pkl')

# ============================================================================
# FINAL COMPARISON & ENSEMBLE
# ============================================================================
print("\n" + "=" * 80)
print("📊 FINAL RESULTS")
print("=" * 80)

results = []
if CatBoostClassifier:
    results.append(('CatBoost', catboost_acc, catboost_time))
if lgb:
    results.append(('LightGBM', lgb_acc, lgb_time))
results.append(('Random Forest', rf_acc, rf_time))

results.sort(key=lambda x: x[1], reverse=True)

print("\n🏆 Rankings:")
for rank, (name, acc, t) in enumerate(results, 1):
    print(f"   {rank}. {name}: {acc*100:.2f}% ({t/60:.1f} min)")

best_name, best_acc, _ = results[0]
print(f"\n🥇 WINNER: {best_name} with {best_acc*100:.2f}% accuracy")

# Ensemble voting
if len(results) >= 2:
    print("\n🤝 Testing ensemble voting...")
    predictions = []
    
    if CatBoostClassifier:
        predictions.append(catboost_model.predict(X_val_dense))
    if lgb:
        predictions.append(lgb_model.predict(X_val_dense))
    predictions.append(rf_model.predict(X_val))
    
    # Majority voting
    from scipy import stats
    ensemble_pred = stats.mode(np.array(predictions), axis=0, keepdims=False)[0]
    ensemble_acc = accuracy_score(y_val, ensemble_pred)
    
    print(f"   Ensemble: {ensemble_acc*100:.2f}%")
    
    if ensemble_acc > best_acc:
        print(f"   🎉 Ensemble is better! (+{(ensemble_acc-best_acc)*100:.2f}%)")
        best_acc = ensemble_acc

total_time = time.time() - start_time

print("\n" + "=" * 80)
if best_acc >= 0.94:
    print(f"✅ SUCCESS! {best_acc*100:.2f}% ≥ 94% TARGET")
else:
    print(f"📊 Result: {best_acc*100:.2f}% (Gap to 94%: {(0.94-best_acc)*100:.2f}%)")

print(f"⏱️  Total time: {total_time/60:.1f} minutes")
print("=" * 80)

# Save encoders
joblib.dump(tfidf, 'tfidf_vectorizer.pkl')
joblib.dump(le_agent, 'label_encoder_agent.pkl')
joblib.dump(le_account, 'label_encoder_account.pkl')
joblib.dump(le_payment, 'label_encoder_payment.pkl')

print("\n💾 All models and encoders saved!")
print("✅ TRAINING COMPLETE!")



