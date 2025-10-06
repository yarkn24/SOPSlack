#!/usr/bin/env python3
"""
🎯 MEMORY-EFFICIENT TRAINING
- Sparse matrices (no toarray!)
- Reduced features (80 TF-IDF)
- Sampled training data
- Only 3 best algorithms
"""

import pandas as pd
import numpy as np
from datetime import datetime
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import classification_report, accuracy_score
from lightgbm import LGBMClassifier
from sklearn.ensemble import RandomForestClassifier, ExtraTreesClassifier
import joblib
from scipy.sparse import hstack
import warnings
warnings.filterwarnings('ignore')

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)

log("=" * 80)
log("🎯 MEMORY-EFFICIENT TRAINING TO 94%")
log("=" * 80)
log("\n📋 Strategy:")
log("   • TF-IDF: 80 features (not 500)")
log("   • Sparse matrices (no toarray)")
log("   • Sampled training (200/agent)")
log("   • 3 algorithms: LightGBM, RF, ExtraTrees")
log("\n⏱️  EST: 15-20 minutes")
log("=" * 80)

# ============================================================================
# LOAD DATA
# ============================================================================
log("\n📂 Loading 2024+ data...")
df = pd.read_csv('/Users/yarkin.akcil/Downloads/Unrecon_2025_10_05.csv')
df['amount'] = df['amount'] / 100
df['date'] = pd.to_datetime(df['date'])
df = df.sort_values('date').reset_index(drop=True)
df = df[df['date'] >= '2024-01-01'].copy()
df = df[df['agent'].notna()].copy()

log(f"✅ {len(df):,} transactions | {df['agent'].nunique()} unique agents")

# ============================================================================
# AGENT FILTERING: Remove agents with identical descriptions (max 200 agents)
# ============================================================================
log("\n🔍 Agent filtering (remove duplicate descriptions)...")

agent_stats = []
for agent in df['agent'].unique():
    agent_data = df[df['agent'] == agent]
    n_total = len(agent_data)
    n_unique_desc = agent_data['description'].nunique()
    diversity_ratio = n_unique_desc / n_total if n_total > 0 else 0
    
    agent_stats.append({
        'agent': agent,
        'total': n_total,
        'unique_desc': n_unique_desc,
        'diversity': diversity_ratio
    })

agent_stats_df = pd.DataFrame(agent_stats).sort_values(['diversity', 'total'], ascending=[True, True])

# Keep top 200 agents by diversity + total count
if len(agent_stats_df) > 200:
    agents_to_remove = agent_stats_df.head(len(agent_stats_df) - 200)['agent'].tolist()
    log(f"⚠️  Removing {len(agents_to_remove)} low-diversity agents:")
    
    for i, row in agent_stats_df.head(min(10, len(agents_to_remove))).iterrows():
        log(f"   • {row['agent']}: {row['total']} txns, {row['unique_desc']} unique desc ({row['diversity']*100:.1f}% diversity)")
    
    if len(agents_to_remove) > 10:
        log(f"   • ... and {len(agents_to_remove)-10} more")
    
    df = df[~df['agent'].isin(agents_to_remove)].copy()
    log(f"✅ Filtered: {len(df):,} transactions | {df['agent'].nunique()} agents")
else:
    log(f"✅ All {len(agent_stats_df)} agents have good diversity - keeping all")

# ============================================================================
# SMART SAMPLING: 200 per agent (temporal)
# ============================================================================
log("\n📊 Smart sampling (max 200/agent)...")
sampled = []
for agent in df['agent'].unique():
    agent_data = df[df['agent'] == agent].sort_values('date')
    if len(agent_data) > 200:
        # Take first 100 (old) + last 100 (recent)
        sampled.append(pd.concat([agent_data.head(100), agent_data.tail(100)]))
    else:
        sampled.append(agent_data)

df_sampled = pd.concat(sampled).sort_values('date').reset_index(drop=True)
log(f"✅ Sampled: {len(df_sampled):,} (from {len(df):,})")
log(f"   Memory saved: {100 - (len(df_sampled)/len(df)*100):.1f}%")

# ============================================================================
# SPLIT: 70-15-15
# ============================================================================
log("\n🔪 Splitting 70-15-15...")
train_list, test_list, val_list = [], [], []

for agent in df_sampled['agent'].unique():
    agent_data = df_sampled[df_sampled['agent'] == agent].sort_values('date').reset_index(drop=True)
    n = len(agent_data)
    
    if n >= 10:
        train_end = int(n * 0.70)
        test_end = int(n * 0.85)
        train_list.append(agent_data.iloc[:train_end])
        test_list.append(agent_data.iloc[train_end:test_end])
        val_list.append(agent_data.iloc[test_end:])
    elif n >= 3:
        train_list.append(agent_data.iloc[:n-1])
        val_list.append(agent_data.iloc[n-1:])
    else:
        train_list.append(agent_data)

train_data = pd.concat(train_list).sort_values('date').reset_index(drop=True)
test_data = pd.concat(test_list).sort_values('date').reset_index(drop=True) if test_list else pd.DataFrame()
val_data = pd.concat(val_list).sort_values('date').reset_index(drop=True)

log(f"✅ Train: {len(train_data):,} ({train_data['agent'].nunique()} agents)")
log(f"   Test:  {len(test_data):,} ({test_data['agent'].nunique()} agents)")
log(f"   Val:   {len(val_data):,} ({val_data['agent'].nunique()} agents)")

# Check for missing agents
train_agents = set(train_data['agent'].unique())
test_agents = set(test_data['agent'].unique()) if len(test_data) > 0 else set()
val_agents = set(val_data['agent'].unique())

missing = (test_agents | val_agents) - train_agents
if missing:
    log(f"\n⚠️  Removing {len(missing)} agents not in train:")
    for ag in sorted(missing)[:5]:
        log(f"   • {ag}")
    if len(missing) > 5:
        log(f"   • ... and {len(missing)-5} more")
    
    test_data = test_data[~test_data['agent'].isin(missing)]
    val_data = val_data[~val_data['agent'].isin(missing)]
    log(f"✅ Cleaned! Test: {len(test_data):,}, Val: {len(val_data):,}")

# ============================================================================
# FEATURE ENGINEERING (SPARSE!)
# ============================================================================
log("\n🔧 Feature engineering (sparse mode)...")

# TF-IDF: 80 features only
tfidf = TfidfVectorizer(max_features=80, ngram_range=(1, 2), min_df=2)
X_train_tfidf = tfidf.fit_transform(train_data['description'].fillna(''))
X_test_tfidf = tfidf.transform(test_data['description'].fillna(''))
X_val_tfidf = tfidf.transform(val_data['description'].fillna(''))

# Encoders
le_account = LabelEncoder()
le_payment = LabelEncoder()
le_account.fit(df_sampled['origination_account_id'].fillna('UNK').astype(str))
le_payment.fit(df_sampled['payment_method'].fillna('UNK').astype(str))

def extract_features(data):
    f = pd.DataFrame()
    f['payment'] = le_payment.transform(data['payment_method'].fillna('UNK').astype(str))
    f['account'] = le_account.transform(data['origination_account_id'].fillna('UNK').astype(str))
    f['amount'] = data['amount'].values
    f['amount_log'] = np.log1p(data['amount'].abs().values)
    f['amt_gt25k'] = (data['amount'] > 25000).astype(int).values
    f['amt_lt3500'] = (data['amount'] < 3500).astype(int).values
    
    desc = data['description'].fillna('').astype(str).str.upper()
    acc = data['origination_account_id'].fillna('').astype(str).str.lower()
    
    f['has_1trv'] = desc.str.contains('1TRV', regex=False).astype(int).values
    f['has_check'] = desc.str.contains('CHECK', regex=False).astype(int).values
    f['has_nys'] = desc.str.contains('NYS DTF', regex=False).astype(int).values
    f['has_oh'] = desc.str.contains('OH WH', regex=False).astype(int).values
    f['is_recovery'] = acc.str.contains('chase recovery', regex=False).astype(int).values
    f['is_wire'] = acc.str.contains('wire in', regex=False).astype(int).values
    
    return f

X_train_ex = extract_features(train_data)
X_test_ex = extract_features(test_data)
X_val_ex = extract_features(val_data)

# KEEP AS SPARSE!
X_train = hstack([X_train_tfidf, X_train_ex.values])
X_test = hstack([X_test_tfidf, X_test_ex.values])
X_val = hstack([X_val_tfidf, X_val_ex.values])

le_agent = LabelEncoder()
le_agent.fit(df_sampled['agent'])

y_train = le_agent.transform(train_data['agent'])
y_test = le_agent.transform(test_data['agent']) if len(test_data) > 0 else np.array([])
y_val = le_agent.transform(val_data['agent'])

log(f"✅ Features: {X_train.shape[1]} (sparse: {X_train.format})")
log(f"   Classes: {len(le_agent.classes_)}")
log(f"   Memory: ~{X_train.data.nbytes / 1024**2:.1f} MB (sparse)")

# ============================================================================
# TRAIN 3 ALGORITHMS
# ============================================================================
log("\n" + "=" * 80)
log("🏃 TRAINING 3 ALGORITHMS")
log("=" * 80)

results = []

# 1. LightGBM
log("\n[1/3] LightGBM (⏱️ ~3-4 min)...")
start = datetime.now()
lgb = LGBMClassifier(n_estimators=200, max_depth=15, learning_rate=0.05, 
                     num_leaves=100, verbose=-1, random_state=42)
lgb.fit(X_train, y_train)

y_pred_test = lgb.predict(X_test) if len(y_test) > 0 else []
y_pred_val = lgb.predict(X_val)

acc_test = accuracy_score(y_test, y_pred_test) * 100 if len(y_test) > 0 else 0
acc_val = accuracy_score(y_val, y_pred_val) * 100

elapsed = (datetime.now() - start).total_seconds() / 60
log(f"✅ LightGBM | Test: {acc_test:.2f}% | Val: {acc_val:.2f}% | Time: {elapsed:.1f}m")
results.append(('LightGBM', lgb, acc_val, elapsed))

# 2. Random Forest
log("\n[2/3] Random Forest (⏱️ ~4-5 min)...")
start = datetime.now()
rf = RandomForestClassifier(n_estimators=200, max_depth=20, min_samples_split=5,
                            n_jobs=-1, random_state=42, verbose=0)
rf.fit(X_train, y_train)

y_pred_test = rf.predict(X_test) if len(y_test) > 0 else []
y_pred_val = rf.predict(X_val)

acc_test = accuracy_score(y_test, y_pred_test) * 100 if len(y_test) > 0 else 0
acc_val = accuracy_score(y_val, y_pred_val) * 100

elapsed = (datetime.now() - start).total_seconds() / 60
log(f"✅ Random Forest | Test: {acc_test:.2f}% | Val: {acc_val:.2f}% | Time: {elapsed:.1f}m")
results.append(('Random Forest', rf, acc_val, elapsed))

# 3. Extra Trees
log("\n[3/3] Extra Trees (⏱️ ~3-4 min)...")
start = datetime.now()
et = ExtraTreesClassifier(n_estimators=200, max_depth=20, min_samples_split=5,
                          n_jobs=-1, random_state=42, verbose=0)
et.fit(X_train, y_train)

y_pred_test = et.predict(X_test) if len(y_test) > 0 else []
y_pred_val = et.predict(X_val)

acc_test = accuracy_score(y_test, y_pred_test) * 100 if len(y_test) > 0 else 0
acc_val = accuracy_score(y_val, y_pred_val) * 100

elapsed = (datetime.now() - start).total_seconds() / 60
log(f"✅ Extra Trees | Test: {acc_test:.2f}% | Val: {acc_val:.2f}% | Time: {elapsed:.1f}m")
results.append(('Extra Trees', et, acc_val, elapsed))

# ============================================================================
# RESULTS
# ============================================================================
log("\n" + "=" * 80)
log("🏆 FINAL RESULTS")
log("=" * 80)

results.sort(key=lambda x: x[2], reverse=True)
for i, (name, model, acc, time) in enumerate(results, 1):
    log(f"{i}. {name:15s} | Accuracy: {acc:.2f}% | Time: {time:.1f}m")

best_name, best_model, best_acc, _ = results[0]
log(f"\n🥇 BEST: {best_name} with {best_acc:.2f}% accuracy")

# Save best model
log("\n💾 Saving best model...")
joblib.dump(best_model, 'best_model.pkl')
joblib.dump(tfidf, 'tfidf_vectorizer.pkl')
joblib.dump(le_agent, 'label_encoder.pkl')
joblib.dump(le_account, 'account_encoder.pkl')
joblib.dump(le_payment, 'payment_encoder.pkl')

log("✅ Saved:")
log("   • best_model.pkl")
log("   • tfidf_vectorizer.pkl")
log("   • label_encoder.pkl")
log("   • account_encoder.pkl")
log("   • payment_encoder.pkl")

log("\n" + "=" * 80)
log("✅ TRAINING COMPLETE!")
log("=" * 80)
