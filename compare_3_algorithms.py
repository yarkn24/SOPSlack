#!/usr/bin/env python3
"""
🎯 COMPARE 3 BEST ALGORITHMS (Kaggle Best Practices)
- LightGBM: Fast, great for text/sparse data
- XGBoost: High accuracy, industry standard
- CatBoost: Excellent for categorical features

With minute-by-minute status updates
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import classification_report, accuracy_score
from lightgbm import LGBMClassifier
from xgboost import XGBClassifier
from catboost import CatBoostClassifier
import joblib
from scipy.sparse import hstack
import warnings
import time
import threading
warnings.filterwarnings('ignore')

# Global for status monitoring
status = {"step": "Starting...", "progress": 0, "start_time": datetime.now()}

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)

def update_status(step, progress=None):
    status["step"] = step
    if progress is not None:
        status["progress"] = progress
    elapsed = (datetime.now() - status["start_time"]).total_seconds() / 60
    log(f"📊 {step} | Progress: {progress or 'N/A'} | Elapsed: {elapsed:.1f}m")

def status_monitor():
    """Monitor and report status every 60 seconds"""
    while True:
        time.sleep(60)
        if status["step"] != "Complete":
            elapsed = (datetime.now() - status["start_time"]).total_seconds() / 60
            log(f"⏱️  STATUS UPDATE: {status['step']} | Elapsed: {elapsed:.1f}m")

# Start background monitor
monitor_thread = threading.Thread(target=status_monitor, daemon=True)
monitor_thread.start()

log("=" * 80)
log("🎯 COMPARING 3 BEST ALGORITHMS")
log("=" * 80)
log("\n📋 Algorithms:")
log("   1. LightGBM - Fast, great for sparse/text data")
log("   2. XGBoost - High accuracy, industry standard")
log("   3. CatBoost - Excellent for categorical features")
log("\n⏱️  EST: 15-20 minutes")
log("=" * 80)

# ============================================================================
# LOAD DATA (same as fresh_training.py)
# ============================================================================
update_status("Loading 2024+ data", "0%")

df = pd.read_csv('/Users/yarkin.akcil/Downloads/Unrecon_2025_10_05.csv', low_memory=False)
df['amount'] = df['amount'] / 100
df['date'] = pd.to_datetime(df['date'])
df = df.sort_values('date').reset_index(drop=True)
df = df[df['date'] >= '2024-01-01'].copy()
df = df[df['agent'].notna()].copy()

log(f"✅ {len(df):,} transactions | {df['agent'].nunique()} agents")

# Remove SVB
svb_accounts = [1, 2, 5, 10, 24]
df = df[~df['origination_account_id'].isin(svb_accounts)].copy()

# Normalize agents
update_status("Normalizing agent names", "10%")
df['agent_normalized'] = df['agent'].str.strip().str.lower()
agent_mapping = {}
for norm_name in df['agent_normalized'].unique():
    variations = df[df['agent_normalized'] == norm_name]['agent'].value_counts()
    agent_mapping[norm_name] = variations.index[0]
df['agent'] = df['agent_normalized'].map(agent_mapping)
df = df.drop('agent_normalized', axis=1)

log(f"✅ {df['agent'].nunique()} unique agents")

# Smart deduplication
update_status("Smart deduplication", "20%")
sampled = []
for agent in df['agent'].unique():
    agent_data = df[df['agent'] == agent].copy()
    for desc in agent_data['description'].unique():
        desc_rows = agent_data[agent_data['description'] == desc].sort_values('date')
        if len(desc_rows) > 5:
            sampled.append(pd.concat([desc_rows.head(2), desc_rows.tail(3)]))
        else:
            sampled.append(desc_rows)

df_deduplicated = pd.concat(sampled).drop_duplicates().sort_values('date').reset_index(drop=True)
log(f"✅ Deduplicated: {len(df_deduplicated):,}")

# Split
update_status("Temporal split (70-15-15)", "30%")
train_list, test_list, val_list = [], [], []

for agent in df_deduplicated['agent'].unique():
    agent_data = df_deduplicated[df_deduplicated['agent'] == agent].sort_values('date').reset_index(drop=True)
    n = len(agent_data)
    
    if n >= 10:
        train_end = int(n * 0.70)
        test_end = int(n * 0.85)
        train_list.append(agent_data.iloc[:train_end])
        test_list.append(agent_data.iloc[train_end:test_end])
        val_list.append(agent_data.iloc[test_end:])
    elif n >= 3:
        train_end = int(n * 0.70)
        train_list.append(agent_data.iloc[:train_end])
        val_list.append(agent_data.iloc[train_end:])
    else:
        train_list.append(agent_data)

train_data = pd.concat(train_list).sort_values('date').reset_index(drop=True)
test_data = pd.concat(test_list).sort_values('date').reset_index(drop=True) if test_list else pd.DataFrame()
val_data = pd.concat(val_list).sort_values('date').reset_index(drop=True)

# Clean agents
train_agents = set(train_data['agent'].unique())
test_agents = set(test_data['agent'].unique()) if len(test_data) > 0 else set()
val_agents = set(val_data['agent'].unique())
missing = (test_agents | val_agents) - train_agents
if missing:
    test_data = test_data[~test_data['agent'].isin(missing)]
    val_data = val_data[~val_data['agent'].isin(missing)]

log(f"✅ Train: {len(train_data):,} | Test: {len(test_data):,} | Val: {len(val_data):,}")

# Feature engineering
update_status("Feature engineering", "40%")

tfidf = TfidfVectorizer(max_features=150, ngram_range=(1, 3), min_df=2)
X_train_tfidf = tfidf.fit_transform(train_data['description'].fillna(''))
X_test_tfidf = tfidf.transform(test_data['description'].fillna(''))
X_val_tfidf = tfidf.transform(val_data['description'].fillna(''))

le_account = LabelEncoder()
le_payment = LabelEncoder()
le_account.fit(df_deduplicated['origination_account_id'].fillna(0).astype(int).astype(str))
le_payment.fit(df_deduplicated['payment_method'].fillna('UNK').astype(str))

def extract_features(data):
    f = pd.DataFrame()
    f['payment'] = le_payment.transform(data['payment_method'].fillna('UNK').astype(str))
    f['account'] = le_account.transform(data['origination_account_id'].fillna(0).astype(int).astype(str))
    f['amount'] = data['amount'].values
    f['amount_log'] = np.log1p(data['amount'].abs().values)
    
    desc = data['description'].fillna('').astype(str).str.upper()
    account_id = data['origination_account_id'].fillna(0).astype(int)
    
    has_1trv = desc.str.contains('1TRV', regex=False, na=False)
    is_wire_account = (account_id == 6) | (account_id == 7) | (account_id == 9) | (account_id == 18)
    f['is_1trv_risk'] = (has_1trv & is_wire_account).astype(int).values
    
    f['is_risk_account'] = (((account_id == 6) | (account_id == 9) | (account_id == 18)) & ~has_1trv).astype(int).values
    
    has_interest = desc.str.contains('INTEREST', regex=False, na=False)
    f['is_recovery_account'] = (((account_id == 7) & ~has_1trv) | ((account_id == 28) & ~has_interest)).astype(int).values
    
    f['has_check'] = desc.str.contains('CHECK', regex=False).astype(int).values
    f['has_oh_wh'] = desc.str.contains('OH WH', regex=False).astype(int).values
    f['has_il_ui'] = desc.str.contains(' IL ', regex=False).astype(int).values
    
    return f

X_train_ex = extract_features(train_data)
X_test_ex = extract_features(test_data)
X_val_ex = extract_features(val_data)

X_train = hstack([X_train_tfidf, X_train_ex.values])
X_test = hstack([X_test_tfidf, X_test_ex.values])
X_val = hstack([X_val_tfidf, X_val_ex.values])

le_agent = LabelEncoder()
le_agent.fit(df_deduplicated['agent'])

y_train = le_agent.transform(train_data['agent'])
y_test = le_agent.transform(test_data['agent']) if len(test_data) > 0 else np.array([])
y_val = le_agent.transform(val_data['agent'])

log(f"✅ Features: {X_train.shape[1]} | Agents: {len(le_agent.classes_)}")

# ============================================================================
# TRAIN 3 ALGORITHMS
# ============================================================================
log("\n" + "=" * 80)
log("🏃 TRAINING 3 ALGORITHMS")
log("=" * 80)

results = []

# 1. LightGBM
update_status("Training LightGBM", "50%")
log("\n[1/3] LightGBM...")
start = datetime.now()

lgb = LGBMClassifier(
    n_estimators=200,
    max_depth=15,
    learning_rate=0.05,
    num_leaves=100,
    verbose=-1,
    random_state=42
)
lgb.fit(X_train, y_train)

y_pred_test_lgb = lgb.predict(X_test) if len(y_test) > 0 else []
y_pred_val_lgb = lgb.predict(X_val)

acc_test_lgb = accuracy_score(y_test, y_pred_test_lgb) * 100 if len(y_test) > 0 else 0
acc_val_lgb = accuracy_score(y_val, y_pred_val_lgb) * 100

elapsed = (datetime.now() - start).total_seconds() / 60
log(f"✅ LightGBM | Test: {acc_test_lgb:.2f}% | Val: {acc_val_lgb:.2f}% | Time: {elapsed:.1f}m")
results.append(('LightGBM', lgb, acc_test_lgb, acc_val_lgb, elapsed))

# 2. XGBoost
update_status("Training XGBoost", "70%")
log("\n[2/3] XGBoost...")
start = datetime.now()

xgb = XGBClassifier(
    n_estimators=200,
    max_depth=15,
    learning_rate=0.05,
    n_jobs=-1,
    random_state=42,
    eval_metric='mlogloss'
)
xgb.fit(X_train, y_train)

y_pred_test_xgb = xgb.predict(X_test) if len(y_test) > 0 else []
y_pred_val_xgb = xgb.predict(X_val)

acc_test_xgb = accuracy_score(y_test, y_pred_test_xgb) * 100 if len(y_test) > 0 else 0
acc_val_xgb = accuracy_score(y_val, y_pred_val_xgb) * 100

elapsed = (datetime.now() - start).total_seconds() / 60
log(f"✅ XGBoost | Test: {acc_test_xgb:.2f}% | Val: {acc_val_xgb:.2f}% | Time: {elapsed:.1f}m")
results.append(('XGBoost', xgb, acc_test_xgb, acc_val_xgb, elapsed))

# 3. CatBoost
update_status("Training CatBoost", "90%")
log("\n[3/3] CatBoost...")
start = datetime.now()

cat = CatBoostClassifier(
    iterations=200,
    depth=10,
    learning_rate=0.05,
    verbose=False,
    random_state=42
)
cat.fit(X_train, y_train)

y_pred_test_cat = cat.predict(X_test) if len(y_test) > 0 else []
y_pred_val_cat = cat.predict(X_val)

acc_test_cat = accuracy_score(y_test, y_pred_test_cat) * 100 if len(y_test) > 0 else 0
acc_val_cat = accuracy_score(y_val, y_pred_val_cat) * 100

elapsed = (datetime.now() - start).total_seconds() / 60
log(f"✅ CatBoost | Test: {acc_test_cat:.2f}% | Val: {acc_val_cat:.2f}% | Time: {elapsed:.1f}m")
results.append(('CatBoost', cat, acc_test_cat, acc_val_cat, elapsed))

# ============================================================================
# FINAL COMPARISON
# ============================================================================
update_status("Comparison complete", "100%")
status["step"] = "Complete"

log("\n" + "=" * 80)
log("🏆 FINAL COMPARISON")
log("=" * 80)

log("\n📊 Test Accuracy:")
for name, model, test_acc, val_acc, time_taken in results:
    log(f"   • {name:12s}: {test_acc:6.2f}%")

log("\n📊 Validation Accuracy:")
for name, model, test_acc, val_acc, time_taken in results:
    log(f"   • {name:12s}: {val_acc:6.2f}%")

log("\n⏱️  Training Time:")
for name, model, test_acc, val_acc, time_taken in results:
    log(f"   • {name:12s}: {time_taken:5.1f}m")

# Find best
best_by_val = max(results, key=lambda x: x[3])
log(f"\n🥇 BEST (by validation): {best_by_val[0]} - {best_by_val[3]:.2f}%")

# Save best
log("\n💾 Saving best model...")
joblib.dump(best_by_val[1], 'best_algorithm_model.pkl')
joblib.dump(tfidf, 'best_algorithm_tfidf.pkl')
joblib.dump(le_agent, 'best_algorithm_agent_encoder.pkl')
log("✅ Saved!")

log("\n" + "=" * 80)
log("✅ COMPARISON COMPLETE!")
log("=" * 80)
