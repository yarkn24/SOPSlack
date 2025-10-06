"""
Fast Iterative Agent Classification Training
5 fastest algorithms for this dataset/use-case
Each algorithm: max 10 minutes
Total: 35-50 minutes to 90%+ accuracy
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import warnings
import os
warnings.filterwarnings('ignore')

os.environ['DYLD_LIBRARY_PATH'] = '/opt/homebrew/opt/libomp/lib'

from sklearn.ensemble import RandomForestClassifier, ExtraTreesClassifier, HistGradientBoostingClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import classification_report, accuracy_score
import joblib

try:
    import xgboost as xgb
    print("✅ XGBoost loaded")
except:
    xgb = None
    print("⚠️  XGBoost not available")

try:
    import lightgbm as lgb
    print("✅ LightGBM loaded")
except:
    lgb = None
    print("⚠️  LightGBM not available")

print("\n" + "=" * 80)
print("🚀 FAST ITERATIVE TRAINING - 5 ALGORITHMS")
print("=" * 80)
print("\n🎯 Selected Algorithms (fastest for this use-case):")
print("   1. LightGBM          - 2-3 min (fastest)")
print("   2. XGBoost (hist)    - 3-4 min")
print("   3. Extra Trees       - 3-4 min (faster than RF)")
print("   4. Random Forest     - 4-5 min")
print("   5. HistGradientBoost - 3-4 min")
print("\n⏱️  TOTAL ESTIMATED: 35-50 minutes")
print("   Phase 1 (test all 5): 15-20 min")
print("   Phase 2 (tune top 3): 10-15 min")
print("   Phase 3 (improvement): 10-15 min")
print("\n🎯 TARGET: 94% accuracy (validation labels are 94% correct)")
print("=" * 80)

start_total = time.time()

# ============================================================================
# DATA LOADING
# ============================================================================
print("\n📂 Loading data...")
df = pd.read_csv('/Users/yarkin.akcil/Downloads/Unrecon_2025_10_05.csv')
df['amount'] = df['amount'] / 100
df['date'] = pd.to_datetime(df['date'])
df = df.sort_values('date').reset_index(drop=True)

latest_date = df['date'].max()
validation_cutoff = latest_date - timedelta(days=180)
test_cutoff = validation_cutoff - timedelta(days=365)

validation_data = df[df['date'] >= validation_cutoff].copy()
test_data = df[(df['date'] >= test_cutoff) & (df['date'] < validation_cutoff)].copy()
train_data = df[df['date'] < test_cutoff].copy()

train_data = train_data[train_data['agent'].notna()].copy()
test_data = test_data[test_data['agent'].notna()].copy()
validation_data = validation_data[validation_data['agent'].notna()].copy()

# Filter: only keep agents that exist in validation (last year = ground truth)
valid_agents = validation_data['agent'].unique()
print(f"\n🎯 Using {len(valid_agents)} agents from last year as reference")

train_data = train_data[train_data['agent'].isin(valid_agents)].copy()
test_data = test_data[test_data['agent'].isin(valid_agents)].copy()

print(f"✅ Train: {len(train_data):,} | Test: {len(test_data):,} | Val (2025): {len(validation_data):,}")
print(f"   All datasets now have same {len(valid_agents)} agents")

# ============================================================================
# FEATURE ENGINEERING
# ============================================================================
print("\n🔧 Feature engineering...")
print("   ⏱️  ETA: 2 minutes")

# TF-IDF
tfidf = TfidfVectorizer(max_features=500, ngram_range=(1, 3), min_df=2, stop_words='english')
X_train_tfidf = tfidf.fit_transform(train_data['description'].fillna(''))
X_test_tfidf = tfidf.transform(test_data['description'].fillna(''))
X_val_tfidf = tfidf.transform(validation_data['description'].fillna(''))

# Encoders
le_account = LabelEncoder()
le_payment = LabelEncoder()

all_accounts = pd.concat([train_data['origination_account_id'], test_data['origination_account_id'], validation_data['origination_account_id']]).fillna('UNKNOWN').astype(str)
le_account.fit(all_accounts)

all_payments = pd.concat([train_data['payment_method'], test_data['payment_method'], validation_data['payment_method']]).fillna('UNKNOWN').astype(str)
le_payment.fit(all_payments)

def extract_features(data):
    features = pd.DataFrame()
    features['payment_method'] = le_payment.transform(data['payment_method'].fillna('UNKNOWN').astype(str))
    features['account_id'] = le_account.transform(data['origination_account_id'].fillna('UNKNOWN').astype(str))
    features['amount'] = data['amount'].values
    features['amount_log'] = np.log1p(data['amount'].abs().values)
    features['amount_above_25k'] = (data['amount'] > 25000).astype(int).values
    features['amount_below_3500'] = (data['amount'] < 3500).astype(int).values
    features['amount_above_1m'] = (data['amount'] > 1000000).astype(int).values
    features['amount_tiny'] = (data['amount'] < 1.0).astype(int).values
    
    desc = data['description'].fillna('').astype(str).str.upper()
    account_lower = data['origination_account_id'].fillna('').astype(str).str.lower()
    
    features['has_1trv'] = desc.str.contains('1TRV', regex=False).astype(int).values
    features['has_check'] = desc.str.contains('CHECK', regex=False).astype(int).values
    features['has_nys_dtf'] = desc.str.contains('NYS DTF', regex=False).astype(int).values
    features['has_oh_wh'] = desc.str.contains('OH WH', regex=False).astype(int).values
    features['has_csc'] = desc.str.contains('CSC', regex=False).astype(int).values
    features['has_lockbox'] = desc.str.contains('LOCKBOX', regex=False).astype(int).values
    features['is_chase_recovery'] = account_lower.str.contains('chase recovery', regex=False).astype(int).values
    features['is_wire_in'] = (account_lower.str.contains('wire in', regex=False) | account_lower.str.contains('incoming wires', regex=False)).astype(int).values
    
    return features

X_train_extra = extract_features(train_data)
X_test_extra = extract_features(test_data)
X_val_extra = extract_features(validation_data)

from scipy.sparse import hstack
X_train = hstack([X_train_tfidf, X_train_extra.values])
X_test = hstack([X_test_tfidf, X_test_extra.values])
X_val = hstack([X_val_tfidf, X_val_extra.values])

X_train_dense = X_train.toarray()
X_test_dense = X_test.toarray()
X_val_dense = X_val.toarray()

# Use sorted unique agents from all data to ensure continuous labels
all_unique_agents = sorted(set(train_data['agent']) | set(test_data['agent']) | set(validation_data['agent']))
le_agent = LabelEncoder()
le_agent.fit(all_unique_agents)  # Fit on sorted list = continuous 0 to N-1

y_train = le_agent.transform(train_data['agent'])
y_test = le_agent.transform(test_data['agent'])
y_val = le_agent.transform(validation_data['agent'])

# Verify continuous
print(f"   Unique agents: {len(le_agent.classes_)}")
print(f"   Train labels: {np.unique(y_train).min()}-{np.unique(y_train).max()} (should be continuous)")
print(f"   Val labels: {np.unique(y_val).min()}-{np.unique(y_val).max()}")

print(f"✅ Features ready: {X_train.shape[1]}")

# ============================================================================
# PHASE 1: TEST ALL 5 ALGORITHMS
# ============================================================================
print("\n" + "=" * 80)
print("🏃 PHASE 1: TESTING 5 FAST ALGORITHMS")
print("=" * 80)
print("⏱️  ETA: 15-20 minutes")

results = {}
phase1_start = time.time()

# Algorithm 1: LightGBM (FASTEST)
if lgb:
    print(f"\n[1/5] LightGBM (ETA: 2-3 min)")
    start = time.time()
    model_lgb = lgb.LGBMClassifier(
        n_estimators=500,
        max_depth=12,
        learning_rate=0.1,
        subsample=0.8,
        colsample_bytree=0.8,
        num_leaves=50,
        random_state=42,
        n_jobs=-1,
        verbose=-1
    )
    model_lgb.fit(X_train_dense, y_train)
    y_val_pred = model_lgb.predict(X_val_dense)
    acc = accuracy_score(y_val, y_val_pred)
    elapsed = time.time() - start
    results['LightGBM'] = {'model': model_lgb, 'accuracy': acc, 'time': elapsed, 'sparse': False}
    print(f"   ✅ Accuracy: {acc*100:.2f}% | Time: {elapsed:.1f}s")

# Algorithm 2: XGBoost (remap labels to continuous for XGBoost)
if xgb:
    print(f"\n[2/5] XGBoost hist (ETA: 3-4 min)")
    start = time.time()
    
    # Remap sparse labels to continuous for XGBoost
    unique_train_labels = np.unique(y_train)
    train_label_map = {old: new for new, old in enumerate(unique_train_labels)}
    reverse_map = {new: old for old, new in train_label_map.items()}
    
    y_train_cont = np.array([train_label_map[y] for y in y_train])
    
    model_xgb = xgb.XGBClassifier(
        n_estimators=500,
        max_depth=12,
        learning_rate=0.1,
        subsample=0.8,
        colsample_bytree=0.8,
        tree_method='hist',
        random_state=42,
        n_jobs=-1
    )
    model_xgb.fit(X_train_dense, y_train_cont)
    y_val_pred_cont = model_xgb.predict(X_val_dense)
    # Map back to original labels
    y_val_pred = np.array([reverse_map.get(y, y) for y in y_val_pred_cont])
    acc = accuracy_score(y_val, y_val_pred)
    elapsed = time.time() - start
    results['XGBoost'] = {'model': model_xgb, 'accuracy': acc, 'time': elapsed, 'sparse': False, 'label_map': train_label_map, 'reverse_map': reverse_map}
    print(f"   ✅ Accuracy: {acc*100:.2f}% | Time: {elapsed:.1f}s")

# Algorithm 3: Extra Trees
print(f"\n[3/5] Extra Trees (ETA: 3-4 min)")
start = time.time()
model_et = ExtraTreesClassifier(
    n_estimators=500,
    max_depth=35,
    min_samples_split=2,
    random_state=42,
    n_jobs=-1
)
model_et.fit(X_train, y_train)
y_val_pred = model_et.predict(X_val)
acc = accuracy_score(y_val, y_val_pred)
elapsed = time.time() - start
results['Extra Trees'] = {'model': model_et, 'accuracy': acc, 'time': elapsed, 'sparse': True}
print(f"   ✅ Accuracy: {acc*100:.2f}% | Time: {elapsed:.1f}s")

# Algorithm 4: Random Forest
print(f"\n[4/5] Random Forest (ETA: 4-5 min)")
start = time.time()
model_rf = RandomForestClassifier(
    n_estimators=500,
    max_depth=35,
    min_samples_split=2,
    random_state=42,
    n_jobs=-1
)
model_rf.fit(X_train, y_train)
y_val_pred = model_rf.predict(X_val)
acc = accuracy_score(y_val, y_val_pred)
elapsed = time.time() - start
results['Random Forest'] = {'model': model_rf, 'accuracy': acc, 'time': elapsed, 'sparse': True}
print(f"   ✅ Accuracy: {acc*100:.2f}% | Time: {elapsed:.1f}s")

# Algorithm 5: HistGradientBoosting
print(f"\n[5/5] HistGradientBoosting (ETA: 3-4 min)")
start = time.time()
model_hgb = HistGradientBoostingClassifier(
    max_iter=500,
    max_depth=12,
    learning_rate=0.1,
    random_state=42
)
model_hgb.fit(X_train_dense, y_train)
y_val_pred = model_hgb.predict(X_val_dense)
acc = accuracy_score(y_val, y_val_pred)
elapsed = time.time() - start
results['HistGradientBoosting'] = {'model': model_hgb, 'accuracy': acc, 'time': elapsed, 'sparse': False}
print(f"   ✅ Accuracy: {acc*100:.2f}% | Time: {elapsed:.1f}s")

phase1_time = time.time() - phase1_start

# Results summary
print("\n" + "=" * 80)
print("📊 PHASE 1 RESULTS")
print("=" * 80)
sorted_results = sorted(results.items(), key=lambda x: x[1]['accuracy'], reverse=True)
for rank, (name, res) in enumerate(sorted_results, 1):
    print(f"   {rank}. {name}: {res['accuracy']*100:.2f}% ({res['time']:.1f}s)")
print(f"\n⏱️  Phase 1 Total: {phase1_time/60:.1f} minutes")

best_name = sorted_results[0][0]
best_acc = sorted_results[0][1]['accuracy']
print(f"\n🏆 Best: {best_name} ({best_acc*100:.2f}%)")

# ============================================================================
# PHASE 2: IMPROVE TOP 3
# ============================================================================
print("\n" + "=" * 80)
print("🔧 PHASE 2: IMPROVING TOP 3")
print("=" * 80)
print("⏱️  ETA: 10-15 minutes")

top_3 = sorted_results[:3]
improved_results = {}
phase2_start = time.time()

for rank, (name, res) in enumerate(top_3, 1):
    print(f"\n[{rank}/3] Improving {name}...")
    start = time.time()
    
    if name == 'LightGBM':
        improved_model = lgb.LGBMClassifier(
            n_estimators=1000,
            max_depth=15,
            learning_rate=0.08,
            subsample=0.85,
            colsample_bytree=0.85,
            num_leaves=80,
            min_child_samples=10,
            random_state=42,
            n_jobs=-1,
            verbose=-1
        )
        improved_model.fit(X_train_dense, y_train)
        y_val_pred = improved_model.predict(X_val_dense)
        
    elif name == 'XGBoost':
        improved_model = xgb.XGBClassifier(
            n_estimators=1000,
            max_depth=15,
            learning_rate=0.08,
            subsample=0.85,
            colsample_bytree=0.85,
            min_child_weight=3,
            tree_method='hist',
            random_state=42,
            n_jobs=-1
        )
        improved_model.fit(X_train_dense, y_train)
        y_val_pred = improved_model.predict(X_val_dense)
        
    elif name == 'Extra Trees':
        improved_model = ExtraTreesClassifier(
            n_estimators=1000,
            max_depth=40,
            min_samples_split=2,
            min_samples_leaf=1,
            random_state=42,
            n_jobs=-1
        )
        improved_model.fit(X_train, y_train)
        y_val_pred = improved_model.predict(X_val)
        
    elif name == 'Random Forest':
        improved_model = RandomForestClassifier(
            n_estimators=1000,
            max_depth=40,
            min_samples_split=2,
            min_samples_leaf=1,
            random_state=42,
            n_jobs=-1
        )
        improved_model.fit(X_train, y_train)
        y_val_pred = improved_model.predict(X_val)
        
    elif name == 'HistGradientBoosting':
        improved_model = HistGradientBoostingClassifier(
            max_iter=1000,
            max_depth=15,
            learning_rate=0.08,
            min_samples_leaf=10,
            random_state=42
        )
        improved_model.fit(X_train_dense, y_train)
        y_val_pred = improved_model.predict(X_val_dense)
    
    acc = accuracy_score(y_val, y_val_pred)
    elapsed = time.time() - start
    improvement = (acc - res['accuracy']) * 100
    
    improved_results[name] = {
        'model': improved_model,
        'accuracy': acc,
        'time': elapsed,
        'improvement': improvement
    }
    
    print(f"   ✅ New Accuracy: {acc*100:.2f}% (+{improvement:.2f}%)")
    print(f"   ⏱️  Time: {elapsed:.1f}s")

phase2_time = time.time() - phase2_start

# Find new best
best_improved = max(improved_results.items(), key=lambda x: x[1]['accuracy'])
best_name = best_improved[0]
best_acc = best_improved[1]['accuracy']

print(f"\n🏆 Best After Improvement: {best_name} ({best_acc*100:.2f}%)")
print(f"⏱️  Phase 2 Total: {phase2_time/60:.1f} minutes")

# ============================================================================
# PHASE 3: ENSEMBLE + FINAL PUSH
# ============================================================================
print("\n" + "=" * 80)
print("🎯 PHASE 3: ENSEMBLE & FINAL OPTIMIZATION")
print("=" * 80)
print("⏱️  ETA: 10-15 minutes")

phase3_start = time.time()

# Weighted ensemble voting
print("\nBuilding weighted ensemble...")
ensemble_predictions = []
weights = []

for name, res in improved_results.items():
    model = res['model']
    if name in ['LightGBM', 'XGBoost', 'HistGradientBoosting']:
        pred = model.predict(X_val_dense)
    else:
        pred = model.predict(X_val)
    
    ensemble_predictions.append(pred)
    weights.append(res['accuracy'])

# Weighted voting
ensemble_predictions = np.array(ensemble_predictions)
weights = np.array(weights) / np.sum(weights)

final_predictions = []
for i in range(len(y_val)):
    votes = ensemble_predictions[:, i]
    # Weighted vote
    vote_scores = {}
    for pred, weight in zip(votes, weights):
        vote_scores[pred] = vote_scores.get(pred, 0) + weight
    final_pred = max(vote_scores.items(), key=lambda x: x[1])[0]
    final_predictions.append(final_pred)

ensemble_acc = accuracy_score(y_val, final_predictions)
print(f"✅ Ensemble Accuracy: {ensemble_acc*100:.2f}%")

# Try ultra-boosted best model
print(f"\nFinal push: Ultra-boost {best_name}...")
start = time.time()

if best_name == 'LightGBM':
    final_model = lgb.LGBMClassifier(
        n_estimators=2000,
        max_depth=18,
        learning_rate=0.05,
        subsample=0.9,
        colsample_bytree=0.9,
        num_leaves=100,
        min_child_samples=5,
        random_state=42,
        n_jobs=-1,
        verbose=-1
    )
    final_model.fit(X_train_dense, y_train)
    y_val_final = final_model.predict(X_val_dense)
elif best_name == 'XGBoost':
    final_model = xgb.XGBClassifier(
        n_estimators=2000,
        max_depth=18,
        learning_rate=0.05,
        subsample=0.9,
        colsample_bytree=0.9,
        tree_method='hist',
        random_state=42,
        n_jobs=-1
    )
    final_model.fit(X_train_dense, y_train)
    y_val_final = final_model.predict(X_val_dense)
else:  # Tree-based
    if 'Extra' in best_name:
        final_model = ExtraTreesClassifier(
            n_estimators=2000,
            max_depth=45,
            min_samples_split=2,
            random_state=42,
            n_jobs=-1
        )
    else:
        final_model = RandomForestClassifier(
            n_estimators=2000,
            max_depth=45,
            min_samples_split=2,
            random_state=42,
            n_jobs=-1
        )
    final_model.fit(X_train, y_train)
    y_val_final = final_model.predict(X_val)

final_acc = accuracy_score(y_val, y_val_final)
elapsed = time.time() - start
print(f"✅ Final Model Accuracy: {final_acc*100:.2f}%")
print(f"⏱️  Time: {elapsed:.1f}s")

phase3_time = time.time() - phase3_start
total_time = time.time() - start_total

# ============================================================================
# FINAL REPORT
# ============================================================================
print("\n" + "=" * 80)
print("📊 FINAL REPORT")
print("=" * 80)

print(f"\n📈 Progression:")
print(f"   Phase 1 (baseline): {best_acc*100:.2f}%")
print(f"   Phase 2 (improved): {improved_results[best_name]['accuracy']*100:.2f}%")
print(f"   Phase 3 (ensemble): {ensemble_acc*100:.2f}%")
print(f"   Phase 3 (final):    {final_acc*100:.2f}%")

best_final_acc = max(ensemble_acc, final_acc)
print(f"\n🏆 BEST RESULT: {best_final_acc*100:.2f}%")

print(f"\n⏱️  Time Breakdown:")
print(f"   Phase 1: {phase1_time/60:.1f} min")
print(f"   Phase 2: {phase2_time/60:.1f} min")
print(f"   Phase 3: {phase3_time/60:.1f} min")
print(f"   TOTAL:   {total_time/60:.1f} min")

if best_final_acc >= 0.94:
    print(f"\n🎉 EXCELLENT! {best_final_acc*100:.2f}% ≥ 94%")
elif best_final_acc >= 0.90:
    print(f"\n✅ GOOD! {best_final_acc*100:.2f}% ≥ 90%")
    print(f"📊 Gap to 94%: {(0.94-best_final_acc)*100:.2f}%")
else:
    print(f"\n📊 Current: {best_final_acc*100:.2f}%")

# Key agents performance
print(f"\n🎯 Key Agents:")
key_agents = ['Risk', 'Recovery Wire', 'Check', 'NY WH']
for agent in key_agents:
    mask = validation_data['agent'] == agent
    if mask.sum() > 0:
        if ensemble_acc > final_acc:
            agent_preds = np.array(final_predictions)[mask]
        else:
            agent_preds = y_val_final[mask]
        agent_acc = (agent_preds == le_agent.transform([agent])[0]).sum() / mask.sum()
        print(f"   {agent}: {agent_acc*100:.2f}% ({mask.sum()} samples)")

# Save best model
print("\n💾 Saving models...")
if ensemble_acc > final_acc:
    joblib.dump(improved_results, 'ensemble_models.pkl')
    print("✅ Saved ensemble models")
else:
    joblib.dump(final_model, f'final_model_{best_name.replace(" ", "_").lower()}.pkl')
    print(f"✅ Saved {best_name}")

joblib.dump(tfidf, 'tfidf_vectorizer_fast.pkl')
joblib.dump(le_agent, 'label_encoder_agent_fast.pkl')

print("\n" + "=" * 80)
print("✅ TRAINING COMPLETE!")
print("=" * 80)
