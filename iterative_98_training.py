"""
Iterative Agent Classification Training to 98% Accuracy
Strategy:
1. Test 5 algorithms (baseline)
2. Eliminate low performers
3. Improve top 3 with hyperparameter tuning
4. Focus on best until reaching 98% accuracy
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import warnings
import os
warnings.filterwarnings('ignore')

# Set environment for XGBoost
os.environ['DYLD_LIBRARY_PATH'] = '/opt/homebrew/opt/libomp/lib'

# ML Libraries
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import classification_report, accuracy_score, confusion_matrix
from sklearn.model_selection import GridSearchCV
import joblib

try:
    import xgboost as xgb
    print("✅ XGBoost loaded")
except Exception as e:
    print(f"❌ XGBoost error: {e}")
    xgb = None

try:
    import lightgbm as lgb
    print("✅ LightGBM loaded")
except Exception as e:
    print(f"❌ LightGBM error: {e}")
    lgb = None

try:
    from catboost import CatBoostClassifier
    print("✅ CatBoost loaded")
except Exception as e:
    print(f"❌ CatBoost error: {e}")
    CatBoostClassifier = None

print("\n" + "=" * 80)
print("🎯 ITERATIVE TRAINING TO 98% ACCURACY")
print("=" * 80)
print("\n📋 Strategy:")
print("   1️⃣  Test 5 algorithms (baseline)")
print("   2️⃣  Eliminate low performers") 
print("   3️⃣  Improve top 3 with hyperparameter tuning")
print("   4️⃣  Focus on best until 98% accuracy")
print("\n⏱️  TOTAL ESTIMATED TIME: 40-60 minutes (optimized, no Gradient Boosting)")
print("=" * 80)

# ============================================================================
# STEP 1: LOAD AND PREPARE DATA
# ============================================================================
print("\n📂 [1/4] Loading data...")
start_total = time.time()

df = pd.read_csv('/Users/yarkin.akcil/Downloads/Unrecon_2025_10_05.csv')
df['amount'] = df['amount'] / 100
df['date'] = pd.to_datetime(df['date'])
df = df.sort_values('date').reset_index(drop=True)

print(f"✅ Loaded {len(df):,} transactions")
print(f"   Date range: {df['date'].min().date()} to {df['date'].max().date()}")

# ============================================================================
# STEP 2: TEMPORAL SPLIT (FOCUS ON 2025 FOR VALIDATION)
# ============================================================================
print("\n📊 Creating temporal split (2025 data for validation)...")
latest_date = df['date'].max()
validation_cutoff = latest_date - timedelta(days=180)  # Last 6 months (most of 2025)
test_cutoff = validation_cutoff - timedelta(days=365)

validation_data = df[df['date'] >= validation_cutoff].copy()
test_data = df[(df['date'] >= test_cutoff) & (df['date'] < validation_cutoff)].copy()
train_data = df[df['date'] < test_cutoff].copy()

# Remove missing agents
train_data = train_data[train_data['agent'].notna()].copy()
test_data = test_data[test_data['agent'].notna()].copy()
validation_data = validation_data[validation_data['agent'].notna()].copy()

print(f"✅ Training: {len(train_data):,} | Test: {len(test_data):,} | Validation (2025): {len(validation_data):,}")
print(f"   Validation date range: {validation_data['date'].min().date()} to {validation_data['date'].max().date()}")

# ============================================================================
# STEP 3: ENHANCED FEATURE ENGINEERING WITH SOP RULES
# ============================================================================
print("\n🔧 Enhanced feature engineering with SOP rules...")
print("   ⏱️  Estimated: 2-3 minutes")

# TF-IDF on description (most important feature per SOP)
tfidf = TfidfVectorizer(
    max_features=500,
    ngram_range=(1, 3),
    min_df=2,
    stop_words='english'
)

X_train_tfidf = tfidf.fit_transform(train_data['description'].fillna(''))
X_test_tfidf = tfidf.transform(test_data['description'].fillna(''))
X_val_tfidf = tfidf.transform(validation_data['description'].fillna(''))

# Global label encoders
le_account = LabelEncoder()
le_payment = LabelEncoder()

all_accounts = pd.concat([
    train_data['origination_account_id'], 
    test_data['origination_account_id'],
    validation_data['origination_account_id']
]).fillna('UNKNOWN')
le_account.fit(all_accounts)

all_payments = pd.concat([
    train_data['payment_method'], 
    test_data['payment_method'],
    validation_data['payment_method']
]).fillna('UNKNOWN')
le_payment.fit(all_payments)

def extract_sop_features(data):
    """
    SOP-based feature extraction:
    Priority: description > payment_method > account > amount
    """
    features = pd.DataFrame()
    
    # 1. Payment method (2nd most important)
    features['payment_method'] = le_payment.transform(data['payment_method'].fillna('UNKNOWN'))
    
    # 2. Account ID (3rd - critical for Risk/Recovery)
    features['account_id'] = le_account.transform(data['origination_account_id'].fillna('UNKNOWN'))
    
    # 3. Amount features (4th - critical for Risk vs Recovery)
    features['amount'] = data['amount'].values
    features['amount_log'] = np.log1p(data['amount'].abs().values)
    features['amount_above_25k'] = (data['amount'] > 25000).astype(int).values
    features['amount_below_3500'] = (data['amount'] < 3500).astype(int).values
    features['amount_above_1m'] = (data['amount'] > 1000000).astype(int).values
    features['amount_tiny'] = (data['amount'] < 1.0).astype(int).values  # Bad Debt
    
    # SOP Rule patterns
    desc = data['description'].fillna('').astype(str).str.upper()
    account_lower = data['origination_account_id'].fillna('').astype(str).str.lower()
    
    # DEFINITIVE patterns (from SOP)
    features['has_1trv'] = desc.str.contains('1TRV', regex=False).astype(int).values  # DEFINITIVE Risk
    features['has_check'] = desc.str.contains('CHECK', regex=False).astype(int).values
    features['has_nys_dtf'] = desc.str.contains('NYS DTF', regex=False).astype(int).values  # NY WH
    features['has_oh_wh'] = desc.str.contains('OH WH', regex=False).astype(int).values  # OH WH
    features['has_oh_sdwh'] = desc.str.contains('OH SDWH', regex=False).astype(int).values
    features['has_csc'] = desc.str.contains('CSC', regex=False).astype(int).values
    features['has_lockbox'] = desc.str.contains('LOCKBOX', regex=False).astype(int).values
    
    # Account patterns
    features['is_chase_recovery'] = account_lower.str.contains('chase recovery', regex=False).astype(int).values
    features['is_wire_in'] = (
        account_lower.str.contains('wire in', regex=False) | 
        account_lower.str.contains('incoming wires', regex=False)
    ).astype(int).values
    features['is_intl_contractor'] = account_lower.str.contains('international contractor', regex=False).astype(int).values
    features['is_ops_account'] = (
        account_lower.str.contains('chase ops', regex=False) | 
        account_lower.str.contains('pnc ops', regex=False)
    ).astype(int).values
    
    # Combination rules (from SOP feedback)
    # Risk = wire account + high amount + 1TRV
    features['risk_definitive'] = features['has_1trv'].values  # DEFINITIVE
    features['risk_probable'] = (
        features['is_wire_in'] & 
        features['amount_above_25k']
    ).astype(int).values
    
    # Recovery = chase recovery + normal amount
    features['recovery_probable'] = (
        features['is_chase_recovery'] & 
        ~features['amount_above_25k']
    ).astype(int).values
    
    # Wrong account detection (from user feedback)
    features['recovery_in_risk_account'] = (
        features['is_wire_in'] & 
        features['amount_below_3500']
    ).astype(int).values
    
    features['risk_in_recovery_account'] = (
        features['is_chase_recovery'] & 
        features['amount_above_25k']
    ).astype(int).values
    
    return features

print("   Extracting SOP-based features...")
X_train_extra = extract_sop_features(train_data)
X_test_extra = extract_sop_features(test_data)
X_val_extra = extract_sop_features(validation_data)

# Combine features
from scipy.sparse import hstack
X_train = hstack([X_train_tfidf, X_train_extra.values])
X_test = hstack([X_test_tfidf, X_test_extra.values])
X_val = hstack([X_val_tfidf, X_val_extra.values])

# Dense versions
X_train_dense = X_train.toarray()
X_test_dense = X_test.toarray()
X_val_dense = X_val.toarray()

# Encode targets
le_agent = LabelEncoder()
all_agents = pd.concat([train_data['agent'], test_data['agent'], validation_data['agent']])
le_agent.fit(all_agents)

y_train = le_agent.transform(train_data['agent'])
y_test = le_agent.transform(test_data['agent'])
y_val = le_agent.transform(validation_data['agent'])

print(f"✅ Features ready: {X_train.shape[1]} total (500 TF-IDF + {X_train_extra.shape[1]} SOP features)")
print(f"   Unique agents: {len(le_agent.classes_)}")

# ============================================================================
# PHASE 1: TEST 5 ALGORITHMS (BASELINE)
# ============================================================================
print("\n" + "=" * 80)
print("🏃 PHASE 1: BASELINE TEST (5 ALGORITHMS)")
print("=" * 80)
print("⏱️  Estimated: 10-12 minutes")
print("=" * 80)

algorithms = [
    {
        'name': 'Random Forest',
        'model': RandomForestClassifier(n_estimators=300, random_state=42, n_jobs=-1, max_depth=30),
        'sparse': True
    }
]

if xgb:
    algorithms.append({
        'name': 'XGBoost',
        'model': xgb.XGBClassifier(
            n_estimators=500,
            random_state=42,
            n_jobs=-1,
            max_depth=10,
            learning_rate=0.1,
            tree_method='hist',
            subsample=0.8,
            colsample_bytree=0.8
        ),
        'sparse': False
    })

if lgb:
    algorithms.append({
        'name': 'LightGBM',
        'model': lgb.LGBMClassifier(
            n_estimators=500,
            random_state=42,
            n_jobs=-1,
            max_depth=10,
            learning_rate=0.1,
            subsample=0.8,
            colsample_bytree=0.8
        ),
        'sparse': False
    })

if CatBoostClassifier:
    algorithms.append({
        'name': 'CatBoost',
        'model': CatBoostClassifier(
            iterations=500,
            random_state=42,
            thread_count=-1,
            max_depth=10,
            learning_rate=0.1,
            verbose=0
        ),
        'sparse': False
    })

print(f"Testing {len(algorithms)} algorithms...\n")

results = {}
for i, algo in enumerate(algorithms, 1):
    print(f"[{i}/{len(algorithms)}] {algo['name']}...")
    start = time.time()
    
    try:
        if algo['sparse']:
            algo['model'].fit(X_train, y_train)
            y_val_pred = algo['model'].predict(X_val)
        else:
            algo['model'].fit(X_train_dense, y_train)
            y_val_pred = algo['model'].predict(X_val_dense)
        
        val_acc = accuracy_score(y_val, y_val_pred)
        elapsed = time.time() - start
        
        results[algo['name']] = {
            'model': algo['model'],
            'accuracy': val_acc,
            'time': elapsed,
            'sparse': algo['sparse']
        }
        
        print(f"   ✅ Val Accuracy: {val_acc*100:.2f}% ({elapsed:.1f}s)")
        
    except Exception as e:
        print(f"   ❌ Failed: {e}")

# Sort by accuracy
sorted_results = sorted(results.items(), key=lambda x: x[1]['accuracy'], reverse=True)

print("\n📊 BASELINE RESULTS:")
print("=" * 80)
for rank, (name, res) in enumerate(sorted_results, 1):
    print(f"   {rank}. {name}: {res['accuracy']*100:.2f}%")

# Eliminate bottom performers
top_3 = sorted_results[:3]
print(f"\n✅ Top 3 selected for improvement:")
for rank, (name, _) in enumerate(top_3, 1):
    print(f"   {rank}. {name}")

# ============================================================================
# PHASE 2: IMPROVE TOP 3 WITH HYPERPARAMETER TUNING
# ============================================================================
print("\n" + "=" * 80)
print("🔧 PHASE 2: HYPERPARAMETER TUNING (TOP 3)")
print("=" * 80)
print("⏱️  Estimated: 20-25 minutes")
print("=" * 80)

tuned_results = {}

for rank, (name, res) in enumerate(top_3, 1):
    print(f"\n[{rank}/3] Tuning {name}...")
    start = time.time()
    
    try:
        if name == 'Random Forest':
            param_grid = {
                'n_estimators': [500, 800],
                'max_depth': [30, 35, 40],
                'min_samples_split': [2, 3],
                'min_samples_leaf': [1, 2]
            }
            base_model = RandomForestClassifier(random_state=42, n_jobs=-1)
            
        elif name == 'XGBoost':
            param_grid = {
                'n_estimators': [300, 500],
                'max_depth': [6, 8, 10],
                'learning_rate': [0.05, 0.1, 0.15],
                'subsample': [0.8, 1.0],
                'colsample_bytree': [0.8, 1.0]
            }
            base_model = xgb.XGBClassifier(random_state=42, n_jobs=-1, tree_method='hist')
            
        elif name == 'LightGBM':
            param_grid = {
                'n_estimators': [300, 500],
                'max_depth': [6, 8, 10],
                'learning_rate': [0.05, 0.1, 0.15],
                'subsample': [0.8, 1.0],
                'colsample_bytree': [0.8, 1.0]
            }
            base_model = lgb.LGBMClassifier(random_state=42, n_jobs=-1)
            
        elif name == 'CatBoost':
            param_grid = {
                'iterations': [300, 500],
                'max_depth': [6, 8, 10],
                'learning_rate': [0.05, 0.1, 0.15]
            }
            base_model = CatBoostClassifier(random_state=42, thread_count=-1, verbose=0)
        
        # GridSearch with 3-fold CV
        grid = GridSearchCV(
            base_model,
            param_grid,
            cv=3,
            scoring='accuracy',
            n_jobs=-1,
            verbose=1
        )
        
        if res['sparse']:
            grid.fit(X_train, y_train)
            y_val_pred = grid.predict(X_val)
        else:
            grid.fit(X_train_dense, y_train)
            y_val_pred = grid.predict(X_val_dense)
        
        val_acc = accuracy_score(y_val, y_val_pred)
        elapsed = time.time() - start
        
        tuned_results[name] = {
            'model': grid.best_estimator_,
            'accuracy': val_acc,
            'params': grid.best_params_,
            'time': elapsed,
            'sparse': res['sparse']
        }
        
        print(f"   ✅ Tuned Accuracy: {val_acc*100:.2f}% (+{(val_acc-res['accuracy'])*100:.2f}%)")
        print(f"   ⏱️  Time: {elapsed/60:.1f} min")
        print(f"   🎛️  Best params: {grid.best_params_}")
        
    except Exception as e:
        print(f"   ❌ Tuning failed: {e}")
        tuned_results[name] = res

# Find best tuned model
best_name = max(tuned_results.items(), key=lambda x: x[1]['accuracy'])[0]
best_acc = tuned_results[best_name]['accuracy']

print(f"\n🏆 BEST MODEL: {best_name} ({best_acc*100:.2f}%)")

# ============================================================================
# PHASE 3: FOCUS ON BEST - ITERATIVE IMPROVEMENT TO 98%
# ============================================================================
print("\n" + "=" * 80)
print(f"🎯 PHASE 3: ITERATIVE IMPROVEMENT TO 98%")
print("=" * 80)
print(f"Current: {best_acc*100:.2f}% | Target: 98.00%")
print("⏱️  Estimated: 30-40 minutes")
print("=" * 80)

best_model = tuned_results[best_name]['model']
best_sparse = tuned_results[best_name]['sparse']

# Detailed evaluation
if best_sparse:
    y_val_pred = best_model.predict(X_val)
else:
    y_val_pred = best_model.predict(X_val_dense)

print("\n📊 Current Performance Analysis:")
print("=" * 80)

# Overall metrics
print(f"\nOverall Validation Accuracy: {best_acc*100:.2f}%")

# Per-agent analysis
agent_accuracies = {}
for agent_name in le_agent.classes_:
    agent_idx = list(le_agent.classes_).index(agent_name)
    mask = (y_val == agent_idx)
    if mask.sum() > 0:
        agent_acc = (y_val_pred[mask] == agent_idx).sum() / mask.sum()
        agent_accuracies[agent_name] = {
            'accuracy': agent_acc,
            'count': mask.sum()
        }

# Show worst performing agents
print("\n🔴 Worst Performing Agents:")
worst_agents = sorted(agent_accuracies.items(), key=lambda x: x[1]['accuracy'])[:10]
for agent, metrics in worst_agents:
    print(f"   {agent}: {metrics['accuracy']*100:.1f}% ({metrics['count']} samples)")

# Show best performing agents
print("\n🟢 Best Performing Agents:")
best_agents = sorted(agent_accuracies.items(), key=lambda x: x[1]['accuracy'], reverse=True)[:10]
for agent, metrics in best_agents:
    print(f"   {agent}: {metrics['accuracy']*100:.1f}% ({metrics['count']} samples)")

# Key agents (Risk vs Recovery)
print("\n🎯 Key Agents (Risk vs Recovery Wire):")
for key_agent in ['Risk', 'Recovery Wire', 'Check', 'NY WH', 'OH WH', 'CSC', 'Lockbox']:
    if key_agent in agent_accuracies:
        acc = agent_accuracies[key_agent]['accuracy']
        count = agent_accuracies[key_agent]['count']
        print(f"   {key_agent}: {acc*100:.2f}% ({count} samples)")

# ============================================================================
# PHASE 4: FINAL OPTIMIZATION
# ============================================================================
print("\n" + "=" * 80)
print("🚀 PHASE 4: FINAL OPTIMIZATION")
print("=" * 80)

if best_acc >= 0.98:
    print(f"✅ GOAL ACHIEVED: {best_acc*100:.2f}% ≥ 98%")
else:
    gap = 0.98 - best_acc
    print(f"📊 Gap to 98%: {gap*100:.2f}%")
    print("\n💡 Strategies for improvement:")
    print("   1. Increase ensemble size (more trees)")
    print("   2. Add more TF-IDF features (currently 500)")
    print("   3. Feature engineering for worst-performing agents")
    print("   4. Class-weighted training")
    print("   5. Ensemble of top models")
    
    # Try increasing ensemble size
    print("\n🔄 Trying larger ensemble...")
    start = time.time()
    
    if best_name == 'Random Forest':
        final_model = RandomForestClassifier(
            n_estimators=1500,
            **{k: v for k, v in tuned_results[best_name]['params'].items() if k != 'n_estimators'},
            random_state=42,
            n_jobs=-1
        )
    elif best_name == 'XGBoost':
        final_model = xgb.XGBClassifier(
            n_estimators=1500,
            **{k: v for k, v in tuned_results[best_name]['params'].items() if k != 'n_estimators'},
            random_state=42,
            n_jobs=-1,
            tree_method='hist'
        )
    elif best_name == 'LightGBM':
        final_model = lgb.LGBMClassifier(
            n_estimators=1500,
            **{k: v for k, v in tuned_results[best_name]['params'].items() if k != 'n_estimators'},
            random_state=42,
            n_jobs=-1
        )
    elif best_name == 'CatBoost':
        final_model = CatBoostClassifier(
            iterations=1500,
            **{k: v for k, v in tuned_results[best_name]['params'].items() if k != 'iterations'},
            random_state=42,
            thread_count=-1,
            verbose=0
        )
    
    if best_sparse:
        final_model.fit(X_train, y_train)
        y_val_final = final_model.predict(X_val)
    else:
        final_model.fit(X_train_dense, y_train)
        y_val_final = final_model.predict(X_val_dense)
    
    final_acc = accuracy_score(y_val, y_val_final)
    elapsed = time.time() - start
    
    print(f"   Final Accuracy: {final_acc*100:.2f}% (+{(final_acc-best_acc)*100:.2f}%)")
    print(f"   Training time: {elapsed/60:.1f} min")
    
    if final_acc >= 0.98:
        print(f"\n🎉 GOAL ACHIEVED: {final_acc*100:.2f}% ≥ 98%!")
        best_model = final_model
        best_acc = final_acc
    else:
        print(f"\n📊 Final: {final_acc*100:.2f}% (Gap: {(0.98-final_acc)*100:.2f}%)")
        if final_acc > best_acc:
            best_model = final_model
            best_acc = final_acc

# ============================================================================
# SAVE FINAL MODEL
# ============================================================================
print("\n💾 Saving final model...")
joblib.dump(best_model, f'final_model_{best_name.replace(" ", "_").lower()}_98.pkl')
joblib.dump(tfidf, 'tfidf_vectorizer_98.pkl')
joblib.dump(le_agent, 'label_encoder_agent_98.pkl')
joblib.dump(le_account, 'label_encoder_account_98.pkl')
joblib.dump(le_payment, 'label_encoder_payment_98.pkl')

print(f"✅ Saved: final_model_{best_name.replace(' ', '_').lower()}_98.pkl")

# ============================================================================
# FINAL REPORT
# ============================================================================
total_time = time.time() - start_total

print("\n" + "=" * 80)
print("📊 FINAL REPORT")
print("=" * 80)
print(f"\n🏆 Best Algorithm: {best_name}")
print(f"🎯 Final Validation Accuracy: {best_acc*100:.2f}%")
print(f"⏱️  Total Time: {total_time/60:.1f} minutes")
print(f"📅 Validation Period: {validation_data['date'].min().date()} to {validation_data['date'].max().date()}")
print(f"📊 Validation Samples: {len(validation_data):,}")

if best_acc >= 0.98:
    print(f"\n✅ SUCCESS: Target of 98% achieved!")
else:
    print(f"\n📊 Gap to target: {(0.98-best_acc)*100:.2f}%")
    print("💡 Recommendations:")
    print("   - Review worst-performing agent patterns")
    print("   - Add more domain-specific rules")
    print("   - Consider ensemble voting of top 3 models")

print("\n" + "=" * 80)
print("✅ TRAINING COMPLETE!")
print("=" * 80)
