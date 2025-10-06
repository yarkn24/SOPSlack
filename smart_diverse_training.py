#!/usr/bin/env python3
"""
🎯 SMART DIVERSE TRAINING
- Max 10 samples per unique description
- High diversity, low memory
- Fast iterations with improvements
"""

import pandas as pd
import numpy as np
from datetime import datetime
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import classification_report, accuracy_score
from lightgbm import LGBMClassifier
from sklearn.ensemble import RandomForestClassifier
import joblib
from scipy.sparse import hstack
import warnings
warnings.filterwarnings('ignore')

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)

log("=" * 80)
log("🎯 SMART DIVERSE TRAINING")
log("=" * 80)
log("\n📋 Strategy:")
log("   • Max 10 samples per unique description (no thousands of ACH!)")
log("   • Keep diversity high, memory low")
log("   • Iterative improvement")
log("\n⏱️  EST: 10-15 minutes per iteration")
log("=" * 80)

# ============================================================================
# LOAD & SMART SAMPLE
# ============================================================================
log("\n📂 Loading 2024+ data...")
df = pd.read_csv('/Users/yarkin.akcil/Downloads/Unrecon_2025_10_05.csv')
df['amount'] = df['amount'] / 100
df['date'] = pd.to_datetime(df['date'])
df = df.sort_values('date').reset_index(drop=True)
df = df[df['date'] >= '2024-01-01'].copy()
df = df[df['agent'].notna()].copy()

log(f"✅ {len(df):,} transactions | {df['agent'].nunique()} agents")

# ============================================================================
# SMART DIVERSE SAMPLING: Max 10 per unique description
# ============================================================================
log("\n🎨 Diverse sampling (max 10 per unique description)...")

sampled = []
desc_stats = {}

for agent in df['agent'].unique():
    agent_data = df[df['agent'] == agent].copy()
    agent_sampled = []
    
    # For each unique description, take max 10 samples (first 5 + last 5)
    for desc in agent_data['description'].unique():
        desc_rows = agent_data[agent_data['description'] == desc].sort_values('date')
        
        if len(desc_rows) > 10:
            # Take first 5 (old) + last 5 (recent)
            agent_sampled.append(pd.concat([desc_rows.head(5), desc_rows.tail(5)]))
            desc_stats[desc] = desc_stats.get(desc, 0) + 10
        else:
            agent_sampled.append(desc_rows)
            desc_stats[desc] = desc_stats.get(desc, 0) + len(desc_rows)
    
    if agent_sampled:
        sampled.append(pd.concat(agent_sampled))

df_sampled = pd.concat(sampled).drop_duplicates().sort_values('date').reset_index(drop=True)

log(f"✅ Sampled: {len(df_sampled):,} (from {len(df):,})")
log(f"   Memory saved: {100 - (len(df_sampled)/len(df)*100):.1f}%")
log(f"   Unique descriptions: {df_sampled['description'].nunique():,}")

# Show top repeated descriptions
top_desc = pd.Series(desc_stats).sort_values(ascending=False).head(5)
log("\n📊 Top descriptions in sample:")
for desc, count in top_desc.items():
    short_desc = desc[:50] + "..." if len(str(desc)) > 50 else desc
    log(f"   • {count:3d}x: {short_desc}")

# ============================================================================
# FILTER TO TOP 150 AGENTS (by transaction count)
# ============================================================================
log("\n🔍 Filtering to top 150 agents...")
agent_counts = df_sampled['agent'].value_counts()

if len(agent_counts) > 150:
    top_agents = agent_counts.head(150).index.tolist()
    df_sampled = df_sampled[df_sampled['agent'].isin(top_agents)].copy()
    log(f"✅ Kept top 150 agents: {len(df_sampled):,} transactions")
else:
    log(f"✅ All {len(agent_counts)} agents kept")

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

# Clean missing agents
train_agents = set(train_data['agent'].unique())
test_agents = set(test_data['agent'].unique()) if len(test_data) > 0 else set()
val_agents = set(val_data['agent'].unique())
missing = (test_agents | val_agents) - train_agents

if missing:
    log(f"⚠️  Removing {len(missing)} agents not in train")
    test_data = test_data[~test_data['agent'].isin(missing)]
    val_data = val_data[~val_data['agent'].isin(missing)]

# ============================================================================
# FEATURE ENGINEERING (SPARSE!)
# ============================================================================
log("\n🔧 Feature engineering...")

# TF-IDF: 100 features
tfidf = TfidfVectorizer(max_features=100, ngram_range=(1, 2), min_df=2)
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

# SPARSE!
X_train = hstack([X_train_tfidf, X_train_ex.values])
X_test = hstack([X_test_tfidf, X_test_ex.values])
X_val = hstack([X_val_tfidf, X_val_ex.values])

le_agent = LabelEncoder()
le_agent.fit(df_sampled['agent'])

y_train = le_agent.transform(train_data['agent'])
y_test = le_agent.transform(test_data['agent']) if len(test_data) > 0 else np.array([])
y_val = le_agent.transform(val_data['agent'])

log(f"✅ Features: {X_train.shape[1]} (sparse)")
log(f"   Classes: {len(le_agent.classes_)}")
log(f"   Sparsity: {100 - (X_train.nnz / (X_train.shape[0] * X_train.shape[1]) * 100):.1f}%")

# ============================================================================
# ITERATIVE TRAINING: 3 rounds of improvement
# ============================================================================
log("\n" + "=" * 80)
log("🏃 ITERATIVE TRAINING (3 ROUNDS)")
log("=" * 80)

best_acc = 0
best_model = None
best_name = ""

for round_num in range(1, 4):
    log(f"\n{'='*80}")
    log(f"🔄 ROUND {round_num}/3")
    log(f"{'='*80}")
    
    # Round 1: Quick test
    if round_num == 1:
        log("\n[1/2] LightGBM (quick) ⏱️ ~2 min...")
        start = datetime.now()
        model = LGBMClassifier(n_estimators=100, max_depth=10, learning_rate=0.05, 
                              num_leaves=50, verbose=-1, random_state=42)
        model.fit(X_train, y_train)
        elapsed = (datetime.now() - start).total_seconds() / 60
        
        y_pred_val = model.predict(X_val)
        acc_val = accuracy_score(y_val, y_pred_val) * 100
        
        log(f"✅ LightGBM | Val: {acc_val:.2f}% | Time: {elapsed:.1f}m")
        
        if acc_val > best_acc:
            best_acc, best_model, best_name = acc_val, model, "LightGBM-R1"
        
        log("\n[2/2] Random Forest (quick) ⏱️ ~3 min...")
        start = datetime.now()
        model = RandomForestClassifier(n_estimators=100, max_depth=15, min_samples_split=5,
                                      n_jobs=-1, random_state=42, verbose=0)
        model.fit(X_train, y_train)
        elapsed = (datetime.now() - start).total_seconds() / 60
        
        y_pred_val = model.predict(X_val)
        acc_val = accuracy_score(y_val, y_pred_val) * 100
        
        log(f"✅ Random Forest | Val: {acc_val:.2f}% | Time: {elapsed:.1f}m")
        
        if acc_val > best_acc:
            best_acc, best_model, best_name = acc_val, model, "RF-R1"
    
    # Round 2: Improve best
    elif round_num == 2:
        if "LightGBM" in best_name:
            log("\n[Improving] LightGBM (deeper) ⏱️ ~3 min...")
            start = datetime.now()
            model = LGBMClassifier(n_estimators=200, max_depth=15, learning_rate=0.05, 
                                  num_leaves=100, verbose=-1, random_state=42)
        else:
            log("\n[Improving] Random Forest (deeper) ⏱️ ~4 min...")
            start = datetime.now()
            model = RandomForestClassifier(n_estimators=200, max_depth=20, min_samples_split=3,
                                          n_jobs=-1, random_state=42, verbose=0)
        
        model.fit(X_train, y_train)
        elapsed = (datetime.now() - start).total_seconds() / 60
        
        y_pred_val = model.predict(X_val)
        acc_val = accuracy_score(y_val, y_pred_val) * 100
        
        log(f"✅ Improved | Val: {acc_val:.2f}% (was {best_acc:.2f}%) | Time: {elapsed:.1f}m")
        
        if acc_val > best_acc:
            best_acc, best_model, best_name = acc_val, model, best_name.replace("R1", "R2")
    
    # Round 3: Final push
    else:
        if "LightGBM" in best_name:
            log("\n[Final] LightGBM (optimized) ⏱️ ~4 min...")
            start = datetime.now()
            model = LGBMClassifier(n_estimators=300, max_depth=20, learning_rate=0.03, 
                                  num_leaves=150, min_child_samples=10, verbose=-1, random_state=42)
        else:
            log("\n[Final] Random Forest (optimized) ⏱️ ~5 min...")
            start = datetime.now()
            model = RandomForestClassifier(n_estimators=300, max_depth=25, min_samples_split=2,
                                          min_samples_leaf=1, n_jobs=-1, random_state=42, verbose=0)
        
        model.fit(X_train, y_train)
        elapsed = (datetime.now() - start).total_seconds() / 60
        
        y_pred_val = model.predict(X_val)
        acc_val = accuracy_score(y_val, y_pred_val) * 100
        
        log(f"✅ Final | Val: {acc_val:.2f}% (was {best_acc:.2f}%) | Time: {elapsed:.1f}m")
        
        if acc_val > best_acc:
            best_acc, best_model, best_name = acc_val, model, best_name.replace("R2", "R3-FINAL")

# ============================================================================
# RESULTS
# ============================================================================
log("\n" + "=" * 80)
log("🏆 FINAL RESULTS")
log("=" * 80)
log(f"\n🥇 BEST: {best_name}")
log(f"📊 Validation Accuracy: {best_acc:.2f}%")

if best_acc >= 94.0:
    log("✅ TARGET REACHED! (>= 94%)")
elif best_acc >= 90.0:
    log("✅ EXCELLENT! (>= 90%)")
elif best_acc >= 85.0:
    log("✅ GOOD! (>= 85%)")
else:
    log("⚠️  Need more improvement")

# Detailed report
log("\n📋 Detailed Classification Report:")
y_pred_val = best_model.predict(X_val)
report = classification_report(y_val, y_pred_val, target_names=le_agent.classes_, zero_division=0)
print(report)

# Save
log("\n💾 Saving best model...")
joblib.dump(best_model, 'best_model.pkl')
joblib.dump(tfidf, 'tfidf_vectorizer.pkl')
joblib.dump(le_agent, 'label_encoder.pkl')
joblib.dump(le_account, 'account_encoder.pkl')
joblib.dump(le_payment, 'payment_encoder.pkl')

log("✅ Saved all models!")
log("\n" + "=" * 80)
log("✅ TRAINING COMPLETE!")
log("=" * 80)
