"""
Multi-Algorithm Bank Transaction Agent Classification
Tests 5 different algorithms with time estimates
Incorporates all SOP rules and Confluence knowledge
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import warnings
warnings.filterwarnings('ignore')

# ML Libraries
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import classification_report, accuracy_score, confusion_matrix
import joblib

print("=" * 80)
print("🎯 MULTI-ALGORITHM AGENT CLASSIFICATION")
print("=" * 80)
print("\n📋 Testing 5 algorithms:")
print("   1. Random Forest")
print("   2. XGBoost")
print("   3. LightGBM")
print("   4. CatBoost")
print("   5. Gradient Boosting")

# Check for required packages
xgb_available = False
try:
    import xgboost as xgb
    xgb_available = True
    print("✅ XGBoost available")
except Exception as e:
    print(f"⚠️  XGBoost not available (skipping): {str(e)[:50]}...")

lgb_available = False
try:
    import lightgbm as lgb
    lgb_available = True
    print("✅ LightGBM available")
except Exception as e:
    print(f"⚠️  LightGBM not available (skipping): {str(e)[:50]}...")

catboost_available = False
try:
    from catboost import CatBoostClassifier
    catboost_available = True
    print("✅ CatBoost available")
except Exception as e:
    print(f"⚠️  CatBoost not available (skipping): {str(e)[:50]}...")

# ============================================================================
# STEP 1: LOAD AND PREPARE DATA (Same as before)
# ============================================================================
print("\n📂 Loading data...")
df = pd.read_csv('/Users/yarkin.akcil/Downloads/Unrecon_2025_10_05.csv')
df['amount'] = df['amount'] / 100
df['date'] = pd.to_datetime(df['date'])
df = df.sort_values('date').reset_index(drop=True)

print(f"✅ Loaded {len(df):,} transactions")
print(f"   Date range: {df['date'].min()} to {df['date'].max()}")

# ============================================================================
# STEP 2: TEMPORAL SPLIT
# ============================================================================
print("\n📊 Creating temporal split...")
latest_date = df['date'].max()
validation_cutoff = latest_date - timedelta(days=180)  # Last 6 months
test_cutoff = validation_cutoff - timedelta(days=365)  # 6-18 months back

validation_data = df[df['date'] >= validation_cutoff].copy()
test_data = df[(df['date'] >= test_cutoff) & (df['date'] < validation_cutoff)].copy()
train_data = df[df['date'] < test_cutoff].copy()

# Remove missing agents
train_data = train_data[train_data['agent'].notna()].copy()
test_data = test_data[test_data['agent'].notna()].copy()
validation_data = validation_data[validation_data['agent'].notna()].copy()

print(f"✅ Training: {len(train_data):,} | Test: {len(test_data):,} | Validation: {len(validation_data):,}")

# ============================================================================
# STEP 3: ENHANCED FEATURE ENGINEERING (with SOP rules)
# ============================================================================
print("\n🔧 Enhanced feature engineering with SOP rules...")

# TF-IDF on description
print("   Creating TF-IDF features...")
tfidf = TfidfVectorizer(
    max_features=500,
    ngram_range=(1, 3),
    min_df=2,
    stop_words='english'
)

X_train_tfidf = tfidf.fit_transform(train_data['description'].fillna(''))
X_test_tfidf = tfidf.transform(test_data['description'].fillna(''))
X_val_tfidf = tfidf.transform(validation_data['description'].fillna(''))

# Label Encoders (fit on ALL data to avoid unseen categories)
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

def extract_enhanced_features(data):
    """
    Enhanced feature extraction incorporating SOP rules:
    1. Description patterns (TF-IDF already covers this)
    2. Payment method (critical for Check)
    3. Origination account (critical for Risk/Recovery Wire)
    4. Amount patterns (critical for Risk vs Recovery Wire)
    5. SOP-specific patterns (1TRV, CSC, etc.)
    """
    features = pd.DataFrame()
    
    # Core features (in order of importance per SOP)
    features['payment_method'] = le_payment.transform(data['payment_method'].fillna('UNKNOWN'))
    features['account_id'] = le_account.transform(data['origination_account_id'].fillna('UNKNOWN'))
    
    # Amount features (critical for Risk/Recovery Wire distinction)
    features['amount'] = data['amount'].values
    features['amount_log'] = np.log1p(data['amount'].abs().values)
    features['amount_above_25k'] = (data['amount'] > 25000).astype(int).values
    features['amount_below_3500'] = (data['amount'] < 3500).astype(int).values
    features['amount_above_1m'] = (data['amount'] > 1000000).astype(int).values  # ICP/Treasury
    
    # SOP Rule-based features (from documentation)
    desc = data['description'].fillna('').str.upper()
    
    # Rule 1: 1TRV pattern (DEFINITIVE Risk indicator)
    features['has_1trv'] = desc.str.contains('1TRV').astype(int).values
    
    # Rule 2: Check-related
    features['has_check'] = desc.str.contains('CHECK').astype(int).values
    
    # Rule 3: Withholding taxes
    features['has_nys_dtf'] = desc.str.contains('NYS DTF').astype(int).values
    features['has_oh_wh'] = desc.str.contains('OH WH').astype(int).values
    features['has_oh_sdwh'] = desc.str.contains('OH SDWH').astype(int).values
    
    # Rule 4: CSC pattern
    features['has_csc'] = desc.str.contains('CSC').astype(int).values
    
    # Rule 5: Lockbox
    features['has_lockbox'] = desc.str.contains('LOCKBOX').astype(int).values
    
    # Rule 6: Recovery account patterns
    account_lower = data['origination_account_id'].fillna('').str.lower()
    features['is_chase_recovery'] = account_lower.str.contains('chase recovery').astype(int).values
    features['is_wire_in'] = (
        account_lower.str.contains('wire in') | 
        account_lower.str.contains('incoming wires')
    ).astype(int).values
    
    # Rule 7: International Contractor
    features['is_intl_contractor'] = account_lower.str.contains('international contractor').astype(int).values
    
    # Rule 8: Operations accounts (Chase Ops, PNC Ops)
    features['is_ops_account'] = (
        account_lower.str.contains('chase ops') | 
        account_lower.str.contains('pnc ops')
    ).astype(int).values
    
    # Combined rule-based features
    # Risk indicator: wire account + high amount + has 1TRV
    features['risk_combo'] = (
        features['is_wire_in'] & 
        features['amount_above_25k']
    ).astype(int).values
    
    # Recovery indicator: recovery account + low amount
    features['recovery_combo'] = (
        features['is_chase_recovery'] & 
        ~features['amount_above_25k']
    ).astype(int).values
    
    return features

print("   Extracting enhanced features...")
X_train_extra = extract_enhanced_features(train_data)
X_test_extra = extract_enhanced_features(test_data)
X_val_extra = extract_enhanced_features(validation_data)

# Combine TF-IDF + Enhanced features
from scipy.sparse import hstack
X_train = hstack([X_train_tfidf, X_train_extra.values])
X_test = hstack([X_test_tfidf, X_test_extra.values])
X_val = hstack([X_val_tfidf, X_val_extra.values])

# Encode target
le_agent = LabelEncoder()
all_agents = pd.concat([train_data['agent'], test_data['agent'], validation_data['agent']])
le_agent.fit(all_agents)

y_train = le_agent.transform(train_data['agent'])
y_test = le_agent.transform(test_data['agent'])
y_val = le_agent.transform(validation_data['agent'])

print(f"✅ Feature engineering complete")
print(f"   Total features: {X_train.shape[1]} (500 TF-IDF + {X_train_extra.shape[1]} enhanced)")
print(f"   Unique agents: {len(le_agent.classes_)}")

# ============================================================================
# STEP 4: QUICK BASELINE TEST (5-10 min estimate)
# ============================================================================
print("\n" + "=" * 80)
print("🏃 PHASE 1: QUICK BASELINE TEST")
print("=" * 80)
print("\n⏱️  Estimated time: 8-12 minutes")
print("   Testing all available algorithms with default parameters")
print("   This will help us identify the best performer")
print("\n🚀 Starting automatically...")

results = {}
start_time = time.time()

# Convert sparse matrix to dense for some algorithms
X_train_dense = X_train.toarray()
X_test_dense = X_test.toarray()
X_val_dense = X_val.toarray()

algorithms = [
    {
        'name': 'Random Forest',
        'model': RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1, verbose=1),
        'estimated_time': '2-3 min',
        'works_with_sparse': True
    },
    {
        'name': 'Gradient Boosting',
        'model': GradientBoostingClassifier(
            n_estimators=100,
            random_state=42,
            verbose=1
        ),
        'estimated_time': '4-5 min',
        'works_with_sparse': True
    }
]

# Add optional algorithms if available
if xgb_available:
    algorithms.append({
        'name': 'XGBoost',
        'model': xgb.XGBClassifier(
            n_estimators=100,
            random_state=42,
            n_jobs=-1,
            verbosity=1,
            tree_method='hist'
        ),
        'estimated_time': '3-4 min',
        'works_with_sparse': False,
        'notes': 'Good with categorical + numerical features'
    })

if lgb_available:
    algorithms.append({
        'name': 'LightGBM',
        'model': lgb.LGBMClassifier(
            n_estimators=100,
            random_state=42,
            n_jobs=-1,
            verbose=1
        ),
        'estimated_time': '1-2 min',
        'works_with_sparse': False,
        'notes': 'Fastest training, good with large datasets'
    })

if catboost_available:
    algorithms.append({
        'name': 'CatBoost',
        'model': CatBoostClassifier(
            iterations=100,
            random_state=42,
            thread_count=-1,
            verbose=50
        ),
        'estimated_time': '2-3 min',
        'works_with_sparse': False,
        'notes': 'Best with categorical features, no encoding needed'
    })

print(f"\n📊 Will test {len(algorithms)} available algorithms")

for i, algo in enumerate(algorithms, 1):
    print(f"\n{'=' * 80}")
    print(f"[{i}/{len(algorithms)}] Testing {algo['name']}")
    print(f"⏱️  Estimated time: {algo['estimated_time']}")
    if 'notes' in algo:
        print(f"📝 {algo['notes']}")
    print("=" * 80)
    
    algo_start = time.time()
    
    try:
        # Train
        if algo['works_with_sparse']:
            algo['model'].fit(X_train, y_train)
            y_pred_test = algo['model'].predict(X_test)
            y_pred_val = algo['model'].predict(X_val)
        else:
            algo['model'].fit(X_train_dense, y_train)
            y_pred_test = algo['model'].predict(X_test_dense)
            y_pred_val = algo['model'].predict(X_val_dense)
        
        # Evaluate
        test_acc = accuracy_score(y_test, y_pred_test)
        val_acc = accuracy_score(y_val, y_pred_val)
        
        algo_time = time.time() - algo_start
        
        results[algo['name']] = {
            'test_accuracy': test_acc,
            'validation_accuracy': val_acc,
            'training_time': algo_time,
            'model': algo['model']
        }
        
        print(f"\n✅ {algo['name']} completed in {algo_time:.1f}s")
        print(f"   Test Accuracy: {test_acc*100:.2f}%")
        print(f"   Validation Accuracy: {val_acc*100:.2f}% (98% accurate data!)")
        
    except Exception as e:
        print(f"\n❌ {algo['name']} failed: {str(e)}")
        results[algo['name']] = {
            'test_accuracy': 0,
            'validation_accuracy': 0,
            'training_time': 0,
            'error': str(e)
        }

total_time = time.time() - start_time

# ============================================================================
# STEP 5: COMPARE RESULTS
# ============================================================================
print("\n" + "=" * 80)
print("📊 BASELINE RESULTS COMPARISON")
print("=" * 80)
print(f"\nTotal time: {total_time/60:.1f} minutes\n")

results_df = pd.DataFrame([
    {
        'Algorithm': name,
        'Test Acc (%)': res['test_accuracy'] * 100,
        'Val Acc (%)': res['validation_accuracy'] * 100,
        'Time (s)': res['training_time']
    }
    for name, res in results.items()
    if 'error' not in res
]).sort_values('Val Acc (%)', ascending=False)

print(results_df.to_string(index=False))

# Find best model
best_name = results_df.iloc[0]['Algorithm']
best_val_acc = results_df.iloc[0]['Val Acc (%)']

print(f"\n🏆 WINNER: {best_name}")
print(f"   Validation Accuracy: {best_val_acc:.2f}%")
print(f"   (Remember: validation data is 98% accurate!)")

# ============================================================================
# STEP 6: DETAILED EVALUATION OF BEST MODEL
# ============================================================================
print("\n" + "=" * 80)
print(f"🔍 DETAILED EVALUATION: {best_name}")
print("=" * 80)

best_model = results[best_name]['model']

# Get predictions
if algorithms[[a['name'] for a in algorithms].index(best_name)]['works_with_sparse']:
    y_val_pred = best_model.predict(X_val)
else:
    y_val_pred = best_model.predict(X_val_dense)

# Classification report
print("\n📊 Validation Set Performance (Last 6 months - 98% accurate):")
print("=" * 80)
print(classification_report(
    y_val, 
    y_val_pred, 
    target_names=le_agent.classes_,
    zero_division=0
))

# Confusion matrix for key agents (Risk vs Recovery Wire)
print("\n🎯 Focus on Critical Agents (Risk vs Recovery Wire):")
print("=" * 80)

key_agents = ['Risk', 'Recovery Wire']
for agent in key_agents:
    if agent in le_agent.classes_:
        agent_idx = list(le_agent.classes_).index(agent)
        mask = (y_val == agent_idx)
        if mask.sum() > 0:
            agent_acc = (y_val_pred[mask] == agent_idx).sum() / mask.sum()
            print(f"   {agent}: {agent_acc*100:.2f}% accuracy ({mask.sum()} samples)")

# ============================================================================
# STEP 7: SAVE BEST MODEL
# ============================================================================
print("\n💾 Saving best model...")
joblib.dump(best_model, f'best_model_{best_name.replace(" ", "_").lower()}.pkl')
joblib.dump(tfidf, 'tfidf_vectorizer.pkl')
joblib.dump(le_agent, 'label_encoder_agent.pkl')
joblib.dump(le_account, 'label_encoder_account.pkl')
joblib.dump(le_payment, 'label_encoder_payment.pkl')

print(f"✅ Saved: best_model_{best_name.replace(' ', '_').lower()}.pkl")

# ============================================================================
# STEP 8: HYPERPARAMETER TUNING OPTION
# ============================================================================
print("\n" + "=" * 80)
print("🎛️  HYPERPARAMETER TUNING (OPTIONAL)")
print("=" * 80)
print(f"\nCurrent best: {best_name} with {best_val_acc:.2f}% validation accuracy")
print("\nWould you like to perform detailed hyperparameter tuning?")
print("⚠️  This will take 20-40 minutes but could improve accuracy by 1-3%")
print("\nTo run tuning later:")
print(f"   python detailed_tuning_{best_name.replace(' ', '_').lower()}.py")

print("\n" + "=" * 80)
print("✅ TRAINING COMPLETE!")
print("=" * 80)
print(f"\n📈 Summary:")
print(f"   Best Algorithm: {best_name}")
print(f"   Validation Accuracy: {best_val_acc:.2f}%")
print(f"   Total Time: {total_time/60:.1f} minutes")
print(f"\n🎯 Next steps:")
print(f"   1. Review detailed classification report above")
print(f"   2. Analyze confusion for Risk vs Recovery Wire")
print(f"   3. Consider hyperparameter tuning if needed")
print(f"   4. Deploy model: joblib.load('best_model_{best_name.replace(' ', '_').lower()}.pkl')")
