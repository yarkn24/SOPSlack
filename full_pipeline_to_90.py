"""
Full Training Pipeline to 90%+ Accuracy
5 Algorithms → Top 3 → Best → 90%
With minute-by-minute progress tracking
"""

import pandas as pd
import numpy as np
from datetime import datetime
import time
import warnings
import sys
warnings.filterwarnings('ignore')

from sklearn.ensemble import RandomForestClassifier, ExtraTreesClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score
import joblib

try:
    import lightgbm as lgb
    LGB_OK = True
except:
    LGB_OK = False

try:
    from catboost import CatBoostClassifier
    CAT_OK = True
except:
    CAT_OK = False

try:
    import xgboost as xgb
    XGB_OK = True
except:
    XGB_OK = False

def log(msg):
    """Print with timestamp and flush immediately"""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)

log("=" * 80)
log("🎯 FULL PIPELINE TO 90%+ ACCURACY")
log("=" * 80)
log("\n📋 Strategy:")
log("   Phase 1: Test 5 algorithms (15-20 min)")
log("   Phase 2: Improve top 3 (10-15 min)")  
log("   Phase 3: Best to 90%+ (10-20 min)")
log("\n⏱️  TOTAL EST: 35-55 minutes")
log("🎯 TARGET: 90%+ accuracy")
log("=" * 80)

start_global = time.time()

# ============================================================================
# LOAD DATA (2024+ only)
# ============================================================================
log("\n📂 Loading 2024+ data...")
df = pd.read_csv('/Users/yarkin.akcil/Downloads/Unrecon_2025_10_05.csv')
df['amount'] = df['amount'] / 100
df['date'] = pd.to_datetime(df['date'])
df = df[df['date'] >= '2024-01-01'].copy()
df = df[df['agent'].notna()].copy()

log(f"✅ {len(df):,} transactions | {df['agent'].nunique()} unique agents")

# Smart split: 70% train, 15% test, 15% val (per agent, temporal order)
log("   Creating 70-15-15 split (all agents in train)...")

train_list, test_list, val_list = [], [], []

for agent in df['agent'].unique():
    agent_data = df[df['agent'] == agent].sort_values('date').reset_index(drop=True)
    n_agent = len(agent_data)
    
    if n_agent >= 10:  # Need at least 10 samples
        train_end = int(n_agent * 0.70)
        test_end = int(n_agent * 0.85)
        
        train_list.append(agent_data.iloc[:train_end])
        test_list.append(agent_data.iloc[train_end:test_end])
        val_list.append(agent_data.iloc[test_end:])
    elif n_agent >= 3:  # Smaller agents: most in train, rest in val
        train_list.append(agent_data.iloc[:n_agent-1])
        val_list.append(agent_data.iloc[n_agent-1:])
    else:  # Very rare: all in train only
        train_list.append(agent_data)

train_data = pd.concat(train_list).sort_values('date').reset_index(drop=True)
test_data = pd.concat(test_list).sort_values('date').reset_index(drop=True) if test_list else pd.DataFrame()
validation_data = pd.concat(val_list).sort_values('date').reset_index(drop=True)

# Check for agents in test/val that are NOT in train
train_agents = set(train_data['agent'].unique())
test_agents = set(test_data['agent'].unique()) if len(test_data) > 0 else set()
val_agents = set(validation_data['agent'].unique())

missing_in_train_test = test_agents - train_agents
missing_in_train_val = val_agents - train_agents
all_missing = missing_in_train_test | missing_in_train_val

log(f"\n📊 Split summary:")
log(f"   Train: {len(train_data):,} ({len(train_agents)} agents)")
log(f"   Test:  {len(test_data):,} ({len(test_agents)} agents)")
log(f"   Val:   {len(validation_data):,} ({len(val_agents)} agents)")

if all_missing:
    # Count samples per missing agent to sort by least used
    missing_counts = []
    for ag in all_missing:
        count = 0
        if ag in missing_in_train_test:
            count += len(test_data[test_data['agent'] == ag])
        if ag in missing_in_train_val:
            count += len(validation_data[validation_data['agent'] == ag])
        missing_counts.append((ag, count))
    
    # Sort by count (ascending - least used first)
    missing_counts.sort(key=lambda x: x[1])
    
    log(f"\n⚠️  Found {len(all_missing)} agents in test/val but NOT in train:")
    log(f"   (Sorted by usage, least used first)")
    for ag, count in missing_counts:
        in_test = ag in missing_in_train_test
        in_val = ag in missing_in_train_val
        location = []
        if in_test:
            location.append("test")
        if in_val:
            location.append("val")
        log(f"      • {ag}: {count} samples ({', '.join(location)})")
    
    if len(all_missing) <= 5:
        log(f"\n🗑️  Auto-removing {len(all_missing)} least-used agents from test/val:")
        log(f"   (They cannot be predicted since they're not in training)")
        
        for ag, count in missing_counts:
            log(f"      ❌ Removing: {ag} ({count} samples)")
        
        test_data = test_data[~test_data['agent'].isin(all_missing)].copy()
        validation_data = validation_data[~validation_data['agent'].isin(all_missing)].copy()
        
        log(f"\n   ✅ Removed! New sizes:")
        log(f"      Test: {len(test_data):,}")
        log(f"      Val:  {len(validation_data):,}")
    else:
        log(f"\n❌ Too many missing agents ({len(all_missing)} > 5)")
        log(f"   Strategy: Moving least-used to train, removing rest...")
        
        # Move first 5 least-used to train
        to_move = [ag for ag, _ in missing_counts[:5]]
        to_remove = [ag for ag, _ in missing_counts[5:]]
        
        if to_move:
            log(f"\n   📦 Moving {len(to_move)} least-used to train:")
            for ag in to_move:
                count = next(c for a, c in missing_counts if a == ag)
                log(f"      ↪️  {ag} ({count} samples)")
                
                if ag in missing_in_train_test:
                    agent_data = test_data[test_data['agent'] == ag]
                    train_data = pd.concat([train_data, agent_data])
                    test_data = test_data[test_data['agent'] != ag]
                if ag in missing_in_train_val:
                    agent_data = validation_data[validation_data['agent'] == ag]
                    train_data = pd.concat([train_data, agent_data])
                    validation_data = validation_data[validation_data['agent'] != ag]
        
        if to_remove:
            log(f"\n   🗑️  Removing {len(to_remove)} remaining agents:")
            for ag in to_remove:
                count = next(c for a, c in missing_counts if a == ag)
                log(f"      ❌ {ag} ({count} samples)")
            
            test_data = test_data[~test_data['agent'].isin(to_remove)].copy()
            validation_data = validation_data[~validation_data['agent'].isin(to_remove)].copy()
        
        train_data = train_data.sort_values('date').reset_index(drop=True)
        test_data = test_data.sort_values('date').reset_index(drop=True)
        validation_data = validation_data.sort_values('date').reset_index(drop=True)
        
        log(f"\n   ✅ Final sizes:")
        log(f"      Train: {len(train_data):,} ({train_data['agent'].nunique()} agents)")
        log(f"      Test:  {len(test_data):,} ({test_data['agent'].nunique()} agents)")
        log(f"      Val:   {len(validation_data):,} ({validation_data['agent'].nunique()} agents)")
else:
    log(f"   ✅ Perfect! All test/val agents are in training!")

# ============================================================================
# FEATURE ENGINEERING
# ============================================================================
log("\n🔧 Feature engineering...")

tfidf = TfidfVectorizer(max_features=500, ngram_range=(1, 3), min_df=2)
X_train_tfidf = tfidf.fit_transform(train_data['description'].fillna(''))
X_test_tfidf = tfidf.transform(test_data['description'].fillna(''))
X_val_tfidf = tfidf.transform(validation_data['description'].fillna(''))

le_account = LabelEncoder()
le_payment = LabelEncoder()
le_account.fit(df['origination_account_id'].fillna('UNK').astype(str))
le_payment.fit(df['payment_method'].fillna('UNK').astype(str))

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
X_val_ex = extract_features(validation_data)

from scipy.sparse import hstack
X_train = hstack([X_train_tfidf, X_train_ex.values])
X_test = hstack([X_test_tfidf, X_test_ex.values])
X_val = hstack([X_val_tfidf, X_val_ex.values])

X_train_dense = X_train.toarray()
X_test_dense = X_test.toarray()
X_val_dense = X_val.toarray()

le_agent = LabelEncoder()
le_agent.fit(df['agent'])
y_train = le_agent.transform(train_data['agent'])
y_test = le_agent.transform(test_data['agent'])
y_val = le_agent.transform(validation_data['agent'])

log(f"✅ {X_train.shape[1]} features | {len(le_agent.classes_)} agents")

# ============================================================================
# PHASE 1: TEST 5 ALGORITHMS
# ============================================================================
log("\n" + "=" * 80)
log("🏃 PHASE 1: TESTING 5 ALGORITHMS")
log("=" * 80)

results = {}
phase1_start = time.time()

# 1. CatBoost
if CAT_OK:
    log("\n[1/5] CatBoost...")
    s = time.time()
    m = CatBoostClassifier(iterations=500, depth=10, learning_rate=0.1, random_state=42, verbose=0, thread_count=-1)
    m.fit(X_train_dense, y_train)
    pred = m.predict(X_val_dense)
    acc = accuracy_score(y_val, pred)
    results['CatBoost'] = {'model': m, 'acc': acc, 'time': time.time()-s, 'dense': True}
    log(f"   ✅ {acc*100:.2f}% ({time.time()-s:.0f}s)")

# 2. LightGBM  
if LGB_OK:
    log("\n[2/5] LightGBM...")
    s = time.time()
    m = lgb.LGBMClassifier(n_estimators=500, max_depth=12, learning_rate=0.1, random_state=42, n_jobs=-1, verbose=-1)
    m.fit(X_train_dense, y_train)
    pred = m.predict(X_val_dense)
    acc = accuracy_score(y_val, pred)
    results['LightGBM'] = {'model': m, 'acc': acc, 'time': time.time()-s, 'dense': True}
    log(f"   ✅ {acc*100:.2f}% ({time.time()-s:.0f}s)")

# 3. XGBoost
if XGB_OK:
    log("\n[3/5] XGBoost...")
    s = time.time()
    m = xgb.XGBClassifier(n_estimators=500, max_depth=12, learning_rate=0.1, tree_method='hist', random_state=42, n_jobs=-1)
    m.fit(X_train_dense, y_train)
    pred = m.predict(X_val_dense)
    acc = accuracy_score(y_val, pred)
    results['XGBoost'] = {'model': m, 'acc': acc, 'time': time.time()-s, 'dense': True}
    log(f"   ✅ {acc*100:.2f}% ({time.time()-s:.0f}s)")

# 4. Random Forest
log("\n[4/5] Random Forest...")
s = time.time()
m = RandomForestClassifier(n_estimators=500, max_depth=35, min_samples_split=2, random_state=42, n_jobs=-1, verbose=0)
m.fit(X_train, y_train)
pred = m.predict(X_val)
acc = accuracy_score(y_val, pred)
results['Random Forest'] = {'model': m, 'acc': acc, 'time': time.time()-s, 'dense': False}
log(f"   ✅ {acc*100:.2f}% ({time.time()-s:.0f}s)")

# 5. Extra Trees
log("\n[5/5] Extra Trees...")
s = time.time()
m = ExtraTreesClassifier(n_estimators=500, max_depth=35, min_samples_split=2, random_state=42, n_jobs=-1, verbose=0)
m.fit(X_train, y_train)
pred = m.predict(X_val)
acc = accuracy_score(y_val, pred)
results['Extra Trees'] = {'model': m, 'acc': acc, 'time': time.time()-s, 'dense': False}
log(f"   ✅ {acc*100:.2f}% ({time.time()-s:.0f}s)")

phase1_time = time.time() - phase1_start

log("\n📊 Phase 1 Results:")
sorted_res = sorted(results.items(), key=lambda x: x[1]['acc'], reverse=True)
for i, (name, r) in enumerate(sorted_res, 1):
    log(f"   {i}. {name}: {r['acc']*100:.2f}%")
log(f"⏱️  Phase 1: {phase1_time/60:.1f} min")

top3 = sorted_res[:3]
log(f"\n✅ Top 3: {', '.join([n for n, _ in top3])}")

# ============================================================================
# PHASE 2: IMPROVE TOP 3
# ============================================================================
log("\n" + "=" * 80)
log("🔧 PHASE 2: IMPROVING TOP 3")
log("=" * 80)

phase2_start = time.time()
improved = {}

for i, (name, r) in enumerate(top3, 1):
    log(f"\n[{i}/3] Improving {name}...")
    s = time.time()
    
    if name == 'CatBoost':
        m = CatBoostClassifier(iterations=1500, depth=12, learning_rate=0.08, l2_leaf_reg=5, random_state=42, verbose=0, thread_count=-1)
        m.fit(X_train_dense, y_train)
        pred = m.predict(X_val_dense)
    elif name == 'LightGBM':
        m = lgb.LGBMClassifier(n_estimators=1500, max_depth=15, num_leaves=100, learning_rate=0.08, random_state=42, n_jobs=-1, verbose=-1)
        m.fit(X_train_dense, y_train)
        pred = m.predict(X_val_dense)
    elif name == 'XGBoost':
        m = xgb.XGBClassifier(n_estimators=1500, max_depth=15, learning_rate=0.08, tree_method='hist', random_state=42, n_jobs=-1)
        m.fit(X_train_dense, y_train)
        pred = m.predict(X_val_dense)
    elif name == 'Random Forest':
        m = RandomForestClassifier(n_estimators=1500, max_depth=40, min_samples_split=2, random_state=42, n_jobs=-1, verbose=0)
        m.fit(X_train, y_train)
        pred = m.predict(X_val)
    elif name == 'Extra Trees':
        m = ExtraTreesClassifier(n_estimators=1500, max_depth=40, min_samples_split=2, random_state=42, n_jobs=-1, verbose=0)
        m.fit(X_train, y_train)
        pred = m.predict(X_val)
    
    acc = accuracy_score(y_val, pred)
    improved[name] = {'model': m, 'acc': acc, 'time': time.time()-s, 'dense': r['dense']}
    improvement = (acc - r['acc']) * 100
    log(f"   ✅ {acc*100:.2f}% (+{improvement:.2f}%) ({time.time()-s:.0f}s)")

phase2_time = time.time() - phase2_start
log(f"\n⏱️  Phase 2: {phase2_time/60:.1f} min")

best_name = max(improved.items(), key=lambda x: x[1]['acc'])[0]
best_acc = improved[best_name]['acc']
log(f"\n🏆 Best: {best_name} ({best_acc*100:.2f}%)")

# ============================================================================
# PHASE 3: PUSH BEST TO 90%+
# ============================================================================
log("\n" + "=" * 80)
log("🚀 PHASE 3: PUSHING TO 90%+")
log("=" * 80)

phase3_start = time.time()

if best_acc >= 0.90:
    log(f"✅ Already at {best_acc*100:.2f}% ≥ 90%!")
else:
    gap = (0.90 - best_acc) * 100
    log(f"📊 Current: {best_acc*100:.2f}% | Gap: {gap:.2f}%")
    log("\n🔄 Ultra-boosting best model...")
    
    s = time.time()
    if best_name == 'CatBoost':
        final_model = CatBoostClassifier(iterations=3000, depth=15, learning_rate=0.05, l2_leaf_reg=3, random_state=42, verbose=0, thread_count=-1)
        final_model.fit(X_train_dense, y_train)
        pred = final_model.predict(X_val_dense)
    elif best_name == 'LightGBM':
        final_model = lgb.LGBMClassifier(n_estimators=3000, max_depth=18, num_leaves=150, learning_rate=0.05, random_state=42, n_jobs=-1, verbose=-1)
        final_model.fit(X_train_dense, y_train)
        pred = final_model.predict(X_val_dense)
    elif best_name == 'XGBoost':
        final_model = xgb.XGBClassifier(n_estimators=3000, max_depth=18, learning_rate=0.05, tree_method='hist', random_state=42, n_jobs=-1)
        final_model.fit(X_train_dense, y_train)
        pred = final_model.predict(X_val_dense)
    else:  # RF or ET
        cls = RandomForestClassifier if 'Random' in best_name else ExtraTreesClassifier
        final_model = cls(n_estimators=3000, max_depth=45, min_samples_split=2, random_state=42, n_jobs=-1, verbose=0)
        final_model.fit(X_train, y_train)
        pred = final_model.predict(X_val)
    
    final_acc = accuracy_score(y_val, pred)
    final_time = time.time() - s
    
    log(f"   ✅ Final: {final_acc*100:.2f}% (+{(final_acc-best_acc)*100:.2f}%) ({final_time:.0f}s)")
    
    if final_acc > best_acc:
        best_acc = final_acc
        improved[best_name]['model'] = final_model
        improved[best_name]['acc'] = final_acc

phase3_time = time.time() - phase3_start
log(f"\n⏱️  Phase 3: {phase3_time/60:.1f} min")

# ============================================================================
# FINAL REPORT
# ============================================================================
total_time = time.time() - start_global

log("\n" + "=" * 80)
log("📊 FINAL REPORT")
log("=" * 80)
log(f"\n🏆 Best Model: {best_name}")
log(f"🎯 Final Accuracy: {best_acc*100:.2f}%")
log(f"\n⏱️  Time Breakdown:")
log(f"   Phase 1: {phase1_time/60:.1f} min")
log(f"   Phase 2: {phase2_time/60:.1f} min")
log(f"   Phase 3: {phase3_time/60:.1f} min")
log(f"   TOTAL: {total_time/60:.1f} min")

if best_acc >= 0.90:
    log(f"\n🎉 SUCCESS! {best_acc*100:.2f}% ≥ 90%")
else:
    log(f"\n📊 Gap to 90%: {(0.90-best_acc)*100:.2f}%")

# Save best model
joblib.dump(improved[best_name]['model'], f'best_model_{best_name.replace(" ", "_").lower()}.pkl')
joblib.dump(tfidf, 'tfidf.pkl')
joblib.dump(le_agent, 'le_agent.pkl')

log("\n💾 Models saved!")
log("=" * 80)
log("✅ TRAINING COMPLETE!")
