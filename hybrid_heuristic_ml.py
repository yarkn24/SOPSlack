"""
Hybrid Heuristic + ML Agent Classification
Strategy:
1. Rule-based heuristics (SOP rules) - high confidence cases
2. ML models (XGBoost, Random Forest, LightGBM) - uncertain cases
3. Ensemble voting - final decision
Target: 90%+ accuracy, then iteratively to 94%
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import warnings
import os
import joblib
warnings.filterwarnings('ignore')

os.environ['DYLD_LIBRARY_PATH'] = '/opt/homebrew/opt/libomp/lib'

from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import classification_report, accuracy_score, confusion_matrix

try:
    import xgboost as xgb
    xgb_available = True
except:
    xgb_available = False

try:
    import lightgbm as lgb
    lgb_available = True
except:
    lgb_available = False

print("=" * 80)
print("🎯 HYBRID HEURISTIC + ML TRAINING")
print("=" * 80)
print("\n📋 Strategy:")
print("   1️⃣  Rule-based heuristics (SOP) - definitive cases")
print("   2️⃣  Train 3 fast ML models (RF, XGBoost, LightGBM)")
print("   3️⃣  Hybrid ensemble - rules + ML voting")
print("   4️⃣  Target: 90%+ → 94%+ accuracy")
print("\n⏱️  ESTIMATED TIME: 30-40 minutes")
print("=" * 80)

start_total = time.time()

# ============================================================================
# STEP 1: LOAD DATA
# ============================================================================
print("\n📂 [Step 1/6] Loading data...")
df = pd.read_csv('/Users/yarkin.akcil/Downloads/Unrecon_2025_10_05.csv')
df['amount'] = df['amount'] / 100
df['date'] = pd.to_datetime(df['date'])
df = df.sort_values('date').reset_index(drop=True)

print(f"✅ Loaded {len(df):,} transactions")

# Temporal split - 2025 for validation
latest_date = df['date'].max()
validation_cutoff = latest_date - timedelta(days=180)
test_cutoff = validation_cutoff - timedelta(days=365)

validation_data = df[df['date'] >= validation_cutoff].copy()
test_data = df[(df['date'] >= test_cutoff) & (df['date'] < validation_cutoff)].copy()
train_data = df[df['date'] < test_cutoff].copy()

train_data = train_data[train_data['agent'].notna()].copy()
test_data = test_data[test_data['agent'].notna()].copy()
validation_data = validation_data[validation_data['agent'].notna()].copy()

print(f"✅ Train: {len(train_data):,} | Test: {len(test_data):,} | Val: {len(validation_data):,}")

# ============================================================================
# STEP 2: RULE-BASED HEURISTIC (SOP RULES)
# ============================================================================
print("\n🔧 [Step 2/6] Building rule-based heuristic system...")
print("   ⏱️  Estimated: 1 minute")

class HeuristicLabeler:
    """Rule-based labeling from SOP documentation"""
    
    def predict(self, row):
        """Return (label, confidence) tuple"""
        desc = str(row.get('description', '')).upper()
        payment = str(row.get('payment_method', '')).lower()
        account = str(row.get('origination_account_id', '')).lower()
        amount = float(row.get('amount', 0))
        
        # DEFINITIVE RULES (100% confidence)
        
        # Rule 1: 1TRV pattern = RISK (100% confidence)
        if '1TRV' in desc:
            return ('Risk', 1.0)
        
        # Rule 2: Check payment method
        if 'check paid' in payment:
            return ('Check', 0.95)
        
        # Rule 3: NY Withholding
        if 'NYS DTF' in desc:
            return ('NY WH', 0.95)
        
        # Rule 4: OH Withholding
        if 'OH WH TAX' in desc:
            return ('OH WH', 0.95)
        
        # Rule 5: OH SDWH
        if 'OH SDWH' in desc:
            return ('OH SDWH', 0.95)
        
        # Rule 6: CSC pattern
        if 'CSC' in desc and len(desc) > 10:
            return ('CSC', 0.90)
        
        # Rule 7: Lockbox
        if 'LOCKBOX' in desc:
            return ('Lockbox', 0.90)
        
        # Rule 8: Bad Debt (tiny amounts)
        if 0 < amount < 1.0:
            return ('Bad Debt', 0.85)
        
        # Rule 9: ICP/Treasury (very large amounts)
        if amount > 1000000:
            if 'ICP' in desc or 'INTERNATIONAL' in desc:
                return ('ICP Funding', 0.80)
            else:
                return ('Treasury Transfer', 0.75)
        
        # Rule 10: Risk vs Recovery Wire (account + amount based)
        if 'chase recovery' in account:
            if amount > 25000:
                return ('Risk', 0.85)  # Probably wrong account
            else:
                return ('Recovery Wire', 0.85)
        
        if any(x in account for x in ['wire in', 'incoming wires', 'payroll incoming']):
            if amount < 3500 and amount > 0:
                return ('Recovery Wire', 0.80)  # Probably wrong account
            elif amount >= 3500:
                return ('Risk', 0.85)
        
        # Rule 11: International Contractor
        if 'international contractor' in account:
            return ('International Contractor Payment', 0.80)
        
        # No confident rule match
        return (None, 0.0)
    
    def predict_batch(self, data):
        """Predict for entire dataframe"""
        results = []
        for _, row in data.iterrows():
            results.append(self.predict(row))
        return results

heuristic = HeuristicLabeler()

# Test heuristic on validation set
print("   Testing heuristic on validation set...")
val_heuristic = heuristic.predict_batch(validation_data)
val_heuristic_labels = [label for label, conf in val_heuristic]
val_heuristic_confs = [conf for label, conf in val_heuristic]

# Count how many cases heuristic can handle with high confidence
high_conf_mask = np.array(val_heuristic_confs) >= 0.80
n_high_conf = high_conf_mask.sum()
pct_high_conf = n_high_conf / len(validation_data) * 100

print(f"   ✅ Heuristic handles {n_high_conf:,}/{len(validation_data):,} cases ({pct_high_conf:.1f}%) with ≥80% confidence")

# Calculate accuracy on high-confidence cases
high_conf_indices = np.where(high_conf_mask)[0]
if len(high_conf_indices) > 0:
    correct = sum(
        1 for i in high_conf_indices 
        if val_heuristic_labels[i] == validation_data.iloc[i]['agent']
    )
    heuristic_acc = correct / len(high_conf_indices)
    print(f"   📊 Heuristic accuracy on high-confidence cases: {heuristic_acc*100:.2f}%")

# ============================================================================
# STEP 3: FEATURE ENGINEERING FOR ML
# ============================================================================
print("\n🔧 [Step 3/6] Feature engineering for ML models...")
print("   ⏱️  Estimated: 2-3 minutes")

# TF-IDF
tfidf = TfidfVectorizer(max_features=500, ngram_range=(1, 3), min_df=2, stop_words='english')
X_train_tfidf = tfidf.fit_transform(train_data['description'].fillna(''))
X_test_tfidf = tfidf.transform(test_data['description'].fillna(''))
X_val_tfidf = tfidf.transform(validation_data['description'].fillna(''))

# Label encoders
le_account = LabelEncoder()
le_payment = LabelEncoder()

all_accounts = pd.concat([
    train_data['origination_account_id'],
    test_data['origination_account_id'],
    validation_data['origination_account_id']
]).fillna('UNKNOWN').astype(str)
le_account.fit(all_accounts)

all_payments = pd.concat([
    train_data['payment_method'],
    test_data['payment_method'],
    validation_data['payment_method']
]).fillna('UNKNOWN').astype(str)
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
    features['has_oh_sdwh'] = desc.str.contains('OH SDWH', regex=False).astype(int).values
    features['has_csc'] = desc.str.contains('CSC', regex=False).astype(int).values
    features['has_lockbox'] = desc.str.contains('LOCKBOX', regex=False).astype(int).values
    features['is_chase_recovery'] = account_lower.str.contains('chase recovery', regex=False).astype(int).values
    features['is_wire_in'] = (account_lower.str.contains('wire in', regex=False) | account_lower.str.contains('incoming wires', regex=False)).astype(int).values
    features['is_intl_contractor'] = account_lower.str.contains('international contractor', regex=False).astype(int).values
    
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

le_agent = LabelEncoder()
all_agents = pd.concat([train_data['agent'], test_data['agent'], validation_data['agent']])
le_agent.fit(all_agents)

y_train = le_agent.transform(train_data['agent'])
y_test = le_agent.transform(test_data['agent'])
y_val = le_agent.transform(validation_data['agent'])

print(f"✅ Features: {X_train.shape[1]} (500 TF-IDF + {X_train_extra.shape[1]} engineered)")

# ============================================================================
# STEP 4: TRAIN FAST ML MODELS
# ============================================================================
print("\n🤖 [Step 4/6] Training ML models...")
print("   ⏱️  Estimated: 8-10 minutes")

ml_models = {}

# Random Forest
print("\n[1/3] Random Forest...")
start = time.time()
rf_model = RandomForestClassifier(
    n_estimators=500,
    max_depth=35,
    min_samples_split=2,
    random_state=42,
    n_jobs=-1
)
rf_model.fit(X_train, y_train)
y_val_rf = rf_model.predict(X_val)
rf_acc = accuracy_score(y_val, y_val_rf)
ml_models['Random Forest'] = {'model': rf_model, 'accuracy': rf_acc, 'sparse': True}
print(f"   ✅ Accuracy: {rf_acc*100:.2f}% ({time.time()-start:.1f}s)")

# XGBoost
if xgb_available:
    print("\n[2/3] XGBoost...")
    start = time.time()
    xgb_model = xgb.XGBClassifier(
        n_estimators=500,
        max_depth=10,
        learning_rate=0.1,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
        n_jobs=-1,
        tree_method='hist'
    )
    xgb_model.fit(X_train_dense, y_train)
    y_val_xgb = xgb_model.predict(X_val_dense)
    xgb_acc = accuracy_score(y_val, y_val_xgb)
    ml_models['XGBoost'] = {'model': xgb_model, 'accuracy': xgb_acc, 'sparse': False}
    print(f"   ✅ Accuracy: {xgb_acc*100:.2f}% ({time.time()-start:.1f}s)")

# LightGBM
if lgb_available:
    print("\n[3/3] LightGBM...")
    start = time.time()
    lgb_model = lgb.LGBMClassifier(
        n_estimators=500,
        max_depth=10,
        learning_rate=0.1,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
        n_jobs=-1,
        verbose=-1
    )
    lgb_model.fit(X_train_dense, y_train)
    y_val_lgb = lgb_model.predict(X_val_dense)
    lgb_acc = accuracy_score(y_val, y_val_lgb)
    ml_models['LightGBM'] = {'model': lgb_model, 'accuracy': lgb_acc, 'sparse': False}
    print(f"   ✅ Accuracy: {lgb_acc*100:.2f}% ({time.time()-start:.1f}s)")

print("\n📊 ML Models Summary:")
for name, info in ml_models.items():
    print(f"   {name}: {info['accuracy']*100:.2f}%")

best_ml_name = max(ml_models.items(), key=lambda x: x[1]['accuracy'])[0]
best_ml_acc = ml_models[best_ml_name]['accuracy']
print(f"\n🏆 Best ML Model: {best_ml_name} ({best_ml_acc*100:.2f}%)")

# ============================================================================
# STEP 5: HYBRID ENSEMBLE (HEURISTIC + ML)
# ============================================================================
print("\n🎯 [Step 5/6] Building hybrid ensemble...")
print("   ⏱️  Estimated: 2 minutes")

def hybrid_predict(row_idx, data):
    """
    Hybrid prediction strategy:
    1. If heuristic has high confidence (≥85%), use it
    2. Otherwise, use ML ensemble voting
    """
    row = data.iloc[row_idx]
    
    # Get heuristic prediction
    heur_label, heur_conf = heuristic.predict(row)
    
    # If heuristic is confident, use it
    if heur_conf >= 0.85:
        return heur_label, heur_conf, 'heuristic'
    
    # Otherwise, use ML ensemble voting
    ml_votes = []
    
    if ml_models['Random Forest']['sparse']:
        rf_pred = ml_models['Random Forest']['model'].predict(X_val[row_idx:row_idx+1])[0]
        ml_votes.append(le_agent.classes_[rf_pred])
    
    if 'XGBoost' in ml_models:
        xgb_pred = ml_models['XGBoost']['model'].predict(X_val_dense[row_idx:row_idx+1])[0]
        ml_votes.append(le_agent.classes_[xgb_pred])
    
    if 'LightGBM' in ml_models:
        lgb_pred = ml_models['LightGBM']['model'].predict(X_val_dense[row_idx:row_idx+1])[0]
        ml_votes.append(le_agent.classes_[lgb_pred])
    
    # If heuristic has medium confidence, add it as a vote
    if heur_conf >= 0.70 and heur_label is not None:
        ml_votes.append(heur_label)
    
    # Majority voting
    from collections import Counter
    vote_counts = Counter(ml_votes)
    final_label = vote_counts.most_common(1)[0][0]
    vote_ratio = vote_counts[final_label] / len(ml_votes)
    
    return final_label, vote_ratio, 'ml_ensemble'

print("   Making predictions...")
start = time.time()
hybrid_predictions = []
hybrid_confidences = []
hybrid_sources = []

for i in range(len(validation_data)):
    pred, conf, source = hybrid_predict(i, validation_data)
    hybrid_predictions.append(pred)
    hybrid_confidences.append(conf)
    hybrid_sources.append(source)

hybrid_acc = accuracy_score(validation_data['agent'].values, hybrid_predictions)
print(f"   ✅ Hybrid prediction complete ({time.time()-start:.1f}s)")

# ============================================================================
# STEP 6: EVALUATE AND REPORT
# ============================================================================
print("\n📊 [Step 6/6] Evaluation and Results")
print("=" * 80)

print(f"\n🎯 VALIDATION RESULTS (2025 data):")
print(f"   Heuristic only (high conf): {heuristic_acc*100:.2f}%")
print(f"   Best ML model ({best_ml_name}): {best_ml_acc*100:.2f}%")
print(f"   🏆 HYBRID ENSEMBLE: {hybrid_acc*100:.2f}%")

# Source breakdown
source_counts = pd.Series(hybrid_sources).value_counts()
print(f"\n📈 Decision Sources:")
print(f"   Heuristic: {source_counts.get('heuristic', 0):,} ({source_counts.get('heuristic', 0)/len(validation_data)*100:.1f}%)")
print(f"   ML Ensemble: {source_counts.get('ml_ensemble', 0):,} ({source_counts.get('ml_ensemble', 0)/len(validation_data)*100:.1f}%)")

# Confidence distribution
avg_conf = np.mean(hybrid_confidences)
high_conf_pct = (np.array(hybrid_confidences) >= 0.90).sum() / len(hybrid_confidences) * 100
print(f"\n💪 Confidence:")
print(f"   Average: {avg_conf*100:.1f}%")
print(f"   High confidence (≥90%): {high_conf_pct:.1f}%")

# Key agents performance
print(f"\n🎯 Key Agents Performance:")
key_agents = ['Risk', 'Recovery Wire', 'Check', 'NY WH', 'OH WH', 'CSC']
for agent in key_agents:
    mask = validation_data['agent'] == agent
    if mask.sum() > 0:
        agent_preds = np.array(hybrid_predictions)[mask]
        agent_acc = (agent_preds == agent).sum() / mask.sum()
        print(f"   {agent}: {agent_acc*100:.2f}% ({mask.sum()} samples)")

total_time = time.time() - start_total

# ============================================================================
# CHECK IF TARGET REACHED
# ============================================================================
print("\n" + "=" * 80)
if hybrid_acc >= 0.94:
    print(f"🎉 EXCELLENT! TARGET EXCEEDED: {hybrid_acc*100:.2f}% ≥ 94%")
elif hybrid_acc >= 0.90:
    print(f"✅ PHASE 1 COMPLETE: {hybrid_acc*100:.2f}% ≥ 90%")
    gap = 0.94 - hybrid_acc
    print(f"📊 Gap to 94%: {gap*100:.2f}%")
    print("\n💡 Next steps to reach 94%:")
    print("   1. Increase ML model complexity (more trees)")
    print("   2. Add more heuristic rules for edge cases")
    print("   3. Fine-tune confidence thresholds")
    print("   4. Weighted voting based on model performance")
else:
    print(f"📊 Current: {hybrid_acc*100:.2f}%")
    print(f"   Gap to 90%: {(0.90-hybrid_acc)*100:.2f}%")

print(f"\n⏱️  Total Time: {total_time/60:.1f} minutes")
print("=" * 80)

# ============================================================================
# SAVE MODELS
# ============================================================================
print("\n💾 Saving models...")
joblib.dump(heuristic, 'heuristic_labeler.pkl')
joblib.dump(ml_models, 'ml_models_ensemble.pkl')
joblib.dump(tfidf, 'tfidf_vectorizer_hybrid.pkl')
joblib.dump(le_agent, 'label_encoder_agent_hybrid.pkl')
joblib.dump(le_account, 'label_encoder_account_hybrid.pkl')
joblib.dump(le_payment, 'label_encoder_payment_hybrid.pkl')

print("✅ All models saved!")
print("\n" + "=" * 80)
print("✅ TRAINING COMPLETE!")
print("=" * 80)



