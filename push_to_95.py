#!/usr/bin/env python3
"""
🎯 PUSH TO 95% ACCURACY
- 2023+ data (300 agents!)
- True test set: descriptions NOT in training
- 5 iterative improvement rounds
- Advanced feature engineering
"""

import pandas as pd
import numpy as np
from datetime import datetime
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import classification_report, accuracy_score, confusion_matrix
from lightgbm import LGBMClassifier
from sklearn.ensemble import RandomForestClassifier, ExtraTreesClassifier
import joblib
from scipy.sparse import hstack
import warnings
warnings.filterwarnings('ignore')

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)

log("=" * 80)
log("🎯 PUSH TO 95% ACCURACY")
log("=" * 80)
log("\n📋 Strategy:")
log("   • 2023+ data (300 agents, 173K transactions)")
log("   • Smart sampling: diverse unique descriptions")
log("   • TRUE test set: unseen descriptions")
log("   • 5 iterative improvement rounds")
log("   • Advanced features")
log("\n⏱️  EST: 25-30 minutes")
log("=" * 80)

# ============================================================================
# LOAD 2023+ DATA
# ============================================================================
log("\n📂 Loading 2023+ data...")
df = pd.read_csv('/Users/yarkin.akcil/Downloads/Unrecon_2025_10_05.csv', low_memory=False)
df['amount'] = df['amount'] / 100
df['date'] = pd.to_datetime(df['date'])
df = df.sort_values('date').reset_index(drop=True)
df = df[df['date'] >= '2023-01-01'].copy()
df = df[df['agent'].notna()].copy()

log(f"✅ {len(df):,} transactions | {df['agent'].nunique()} agents")
log(f"   Unique descriptions: {df['description'].nunique():,}")

# ============================================================================
# REMOVE SVB ACCOUNTS (bank no longer in use)
# ============================================================================
log("\n🗑️  Removing SVB accounts (bank closed)...")

# SVB account IDs from mapping:
# ID 1: SVB Operations
# ID 2: SVB Corporate
# ID 5: SVB Health Insurance
# ID 10: SVB Wire In
# ID 24: SVB Everyday Pay Repayment
svb_accounts = [1, 2, 5, 10, 24]

df_before = len(df)
df = df[~df['origination_account_id'].isin(svb_accounts)].copy()
df_after = len(df)

log(f"✅ Removed {df_before - df_after:,} SVB transactions")
log(f"   Remaining: {df_after:,} transactions | {df['agent'].nunique()} agents")

# ============================================================================
# UNIQUE DESCRIPTIONS ONLY: 1 sample per unique description
# ============================================================================
log("\n🎨 Unique descriptions (NO duplicates)...")

sampled = []

for agent in df['agent'].unique():
    agent_data = df[df['agent'] == agent].copy()
    
    # For each unique description, take ONLY the most recent one
    for desc in agent_data['description'].unique():
        desc_rows = agent_data[agent_data['description'] == desc].sort_values('date')
        # Take the LAST (most recent) transaction
        sampled.append(desc_rows.tail(1))

df_sampled = pd.concat(sampled).drop_duplicates().sort_values('date').reset_index(drop=True)

log(f"✅ Sampled: {len(df_sampled):,} (from {len(df):,})")
log(f"   Agents: {df_sampled['agent'].nunique()}")
log(f"   Memory saved: {100 - (len(df_sampled)/len(df)*100):.1f}%")

# ============================================================================
# SPLIT STRATEGY: Training uses diverse descriptions, Test uses UNSEEN ones
# ============================================================================
log("\n🔪 Strategic split (train vs unseen test)...")

# For each agent, separate descriptions into train vs test
train_list, test_list, val_list = [], [], []

for agent in df_sampled['agent'].unique():
    agent_data = df_sampled[df_sampled['agent'] == agent].sort_values('date').reset_index(drop=True)
    
    # Get unique descriptions for this agent
    unique_descs = agent_data['description'].unique()
    n_descs = len(unique_descs)
    
    if n_descs >= 10:
        # 70% descriptions → train, 15% → test (unseen), 15% → val (unseen)
        n_train = int(n_descs * 0.70)
        n_test = int(n_descs * 0.85)
        
        train_descs = unique_descs[:n_train]
        test_descs = unique_descs[n_train:n_test]
        val_descs = unique_descs[n_test:]
        
        train_list.append(agent_data[agent_data['description'].isin(train_descs)])
        test_list.append(agent_data[agent_data['description'].isin(test_descs)])
        val_list.append(agent_data[agent_data['description'].isin(val_descs)])
    
    elif n_descs >= 3:
        # Most to train, few to val
        n_train = n_descs - 1
        train_descs = unique_descs[:n_train]
        val_descs = unique_descs[n_train:]
        
        train_list.append(agent_data[agent_data['description'].isin(train_descs)])
        val_list.append(agent_data[agent_data['description'].isin(val_descs)])
    
    else:
        # All to train
        train_list.append(agent_data)

train_data = pd.concat(train_list).sort_values('date').reset_index(drop=True) if train_list else pd.DataFrame()
test_data = pd.concat(test_list).sort_values('date').reset_index(drop=True) if test_list else pd.DataFrame()
val_data = pd.concat(val_list).sort_values('date').reset_index(drop=True) if val_list else pd.DataFrame()

log(f"✅ Train: {len(train_data):,} ({train_data['agent'].nunique()} agents)")
log(f"   Test:  {len(test_data):,} ({test_data['agent'].nunique()} agents)")
log(f"   Val:   {len(val_data):,} ({val_data['agent'].nunique()} agents)")

# Verify test descriptions are NOT in training
train_descs = set(train_data['description'].unique())
test_descs = set(test_data['description'].unique())
val_descs = set(val_data['description'].unique())

overlap_test = len(test_descs & train_descs)
overlap_val = len(val_descs & train_descs)

log(f"\n🔍 Description overlap check:")
log(f"   Test descriptions in train: {overlap_test} ({overlap_test/len(test_descs)*100 if len(test_descs) > 0 else 0:.1f}%)")
log(f"   Val descriptions in train: {overlap_val} ({overlap_val/len(val_descs)*100 if len(val_descs) > 0 else 0:.1f}%)")

# Clean agents not in training
train_agents = set(train_data['agent'].unique())
test_agents = set(test_data['agent'].unique()) if len(test_data) > 0 else set()
val_agents = set(val_data['agent'].unique())

missing = (test_agents | val_agents) - train_agents
if missing:
    log(f"⚠️  Removing {len(missing)} agents not in train")
    test_data = test_data[~test_data['agent'].isin(missing)]
    val_data = val_data[~val_data['agent'].isin(missing)]

# ============================================================================
# ADVANCED FEATURE ENGINEERING
# ============================================================================
log("\n🔧 Advanced feature engineering...")

# TF-IDF: 150 features
tfidf = TfidfVectorizer(max_features=150, ngram_range=(1, 3), min_df=2)
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
    
    # Categorical
    f['payment'] = le_payment.transform(data['payment_method'].fillna('UNK').astype(str))
    f['account'] = le_account.transform(data['origination_account_id'].fillna('UNK').astype(str))
    
    # Numerical
    f['amount'] = data['amount'].values
    f['amount_log'] = np.log1p(data['amount'].abs().values)
    f['amount_sqrt'] = np.sqrt(data['amount'].abs().values)
    f['amt_gt25k'] = (data['amount'] > 25000).astype(int).values
    f['amt_gt100k'] = (data['amount'] > 100000).astype(int).values
    f['amt_gt1m'] = (data['amount'] > 1000000).astype(int).values
    f['amt_lt3500'] = (data['amount'] < 3500).astype(int).values
    f['amt_lt1'] = (data['amount'] < 1.0).astype(int).values
    
    # Description patterns
    desc = data['description'].fillna('').astype(str).str.upper()
    acc = data['origination_account_id'].fillna('').astype(str).str.lower()
    
    # Definitive patterns
    f['has_1trv'] = desc.str.contains('1TRV', regex=False).astype(int).values
    f['has_check'] = desc.str.contains('CHECK', regex=False).astype(int).values
    f['has_nys_dtf'] = desc.str.contains('NYS DTF', regex=False).astype(int).values
    f['has_oh_wh'] = desc.str.contains('OH WH', regex=False).astype(int).values
    f['has_csc'] = desc.str.contains('CSC', regex=False).astype(int).values
    f['has_lockbox'] = desc.str.contains('LOCKBOX', regex=False).astype(int).values
    f['has_oh_sdwh'] = desc.str.contains('OH SDWH', regex=False).astype(int).values
    
    # State patterns
    f['has_il'] = desc.str.contains(' IL ', regex=False).astype(int).values
    f['has_ok'] = desc.str.contains(' OK ', regex=False).astype(int).values
    f['has_wa'] = desc.str.contains(' WA ', regex=False).astype(int).values
    
    # Account patterns using REAL IDs from mapping
    # ID 6: Chase Payroll Incoming Wires
    # ID 7: Chase Recovery
    # ID 9: Chase Wire In
    # ID 18: PNC Wire In
    # ID 28: Blueridge Recovery
    
    account_id = data['origination_account_id'].fillna(0).astype(int)
    
    f['is_chase_recovery'] = (account_id == 7).astype(int).values
    f['is_chase_payroll_wire'] = (account_id == 6).astype(int).values
    f['is_chase_wire_in'] = (account_id == 9).astype(int).values
    f['is_pnc_wire_in'] = (account_id == 18).astype(int).values
    f['is_blueridge_recovery'] = (account_id == 28).astype(int).values
    
    # CRITICAL DEFINITIVE RULES - USER'S LOGIC:
    # Step 1: Filter by account (6/7/9/18)
    # Step 2: Check description for "1TRV"
    # Step 3: Classify
    
    # Step 1: Identify special accounts
    is_wire_or_recovery_account = (
        (account_id == 6) |  # Chase Payroll Incoming Wires
        (account_id == 7) |  # Chase Recovery
        (account_id == 9) |  # Chase Wire In
        (account_id == 18)   # PNC Wire In
    )
    
    # Step 2: Check for "1TRV" code in description
    has_1trv_code = desc.str.contains('1TRV', regex=False, na=False)
    
    # Step 3: Classification logic
    # Rule 1: Account 6/7/9/18 + "1TRV" → KESINLIKLE RISK
    f['is_1trv_risk'] = (is_wire_or_recovery_account & has_1trv_code).astype(int).values
    
    # Rule 2: Account 6/9/18 (NO 1TRV) → Risk (normal)
    is_risk_account_no_1trv = (
        ((account_id == 6) | (account_id == 9) | (account_id == 18)) & 
        ~has_1trv_code
    )
    f['is_risk_account'] = is_risk_account_no_1trv.astype(int).values
    
    # Rule 3: Account 7 (NO 1TRV) → Recovery Wire (~90%)
    # Rule 3b: Account 28 (Blueridge Recovery) → Check description
    #          - If "interest" → Interest Payment (not recovery)
    #          - Otherwise → Recovery Wire (mostly)
    
    has_interest = desc.str.contains('INTEREST', regex=False, na=False)
    
    is_blueridge_recovery = (account_id == 28) & ~has_interest
    
    is_recovery_no_1trv = (
        ((account_id == 7) & ~has_1trv_code) |
        is_blueridge_recovery
    )
    f['is_recovery_account'] = is_recovery_no_1trv.astype(int).values
    
    # Blueridge Interest (not recovery)
    f['is_blueridge_interest'] = ((account_id == 28) & has_interest).astype(int).values
    
    # Combined: DEFINITIVE Risk (1TRV or risk account)
    f['is_definitive_risk'] = (f['is_1trv_risk'] | f['is_risk_account']).values
    
    # Combined: DEFINITIVE Recovery (recovery account, no 1TRV)
    f['is_definitive_recovery'] = f['is_recovery_account'].values
    
    # Description length
    f['desc_len'] = data['description'].fillna('').astype(str).apply(len).values
    f['desc_words'] = data['description'].fillna('').astype(str).str.split().apply(len).values
    
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

# ============================================================================
# ITERATIVE TRAINING: 5 ROUNDS
# ============================================================================
log("\n" + "=" * 80)
log("🏃 ITERATIVE TRAINING (5 ROUNDS TO 95%)")
log("=" * 80)

best_acc = 0
best_model = None
best_name = ""

algorithms = [
    ('LightGBM', lambda: LGBMClassifier(n_estimators=100, max_depth=10, learning_rate=0.05, num_leaves=50, verbose=-1, random_state=42)),
    ('RandomForest', lambda: RandomForestClassifier(n_estimators=100, max_depth=15, min_samples_split=5, n_jobs=-1, random_state=42, verbose=0)),
    ('ExtraTrees', lambda: ExtraTreesClassifier(n_estimators=100, max_depth=15, min_samples_split=5, n_jobs=-1, random_state=42, verbose=0)),
]

for round_num in range(1, 6):
    log(f"\n{'='*80}")
    log(f"🔄 ROUND {round_num}/5")
    log(f"{'='*80}")
    
    if round_num == 1:
        # Test all 3 algorithms
        log("\n⚡ Testing 3 algorithms...")
        
        for i, (name, model_fn) in enumerate(algorithms, 1):
            log(f"\n[{i}/3] {name}...")
            start = datetime.now()
            model = model_fn()
            model.fit(X_train, y_train)
            
            y_pred_val = model.predict(X_val)
            acc_val = accuracy_score(y_val, y_pred_val) * 100
            
            elapsed = (datetime.now() - start).total_seconds() / 60
            log(f"✅ {name:15s} | Val: {acc_val:.2f}% | Time: {elapsed:.1f}m")
            
            if acc_val > best_acc:
                best_acc, best_model, best_name = acc_val, model, f"{name}-R1"
    
    elif round_num == 2:
        # Improve best with more estimators
        log(f"\n💪 Improving {best_name} (more estimators)...")
        start = datetime.now()
        
        if "LightGBM" in best_name:
            model = LGBMClassifier(n_estimators=200, max_depth=15, learning_rate=0.05, num_leaves=100, verbose=-1, random_state=42)
        elif "RandomForest" in best_name:
            model = RandomForestClassifier(n_estimators=200, max_depth=20, min_samples_split=3, n_jobs=-1, random_state=42, verbose=0)
        else:
            model = ExtraTreesClassifier(n_estimators=200, max_depth=20, min_samples_split=3, n_jobs=-1, random_state=42, verbose=0)
        
        model.fit(X_train, y_train)
        y_pred_val = model.predict(X_val)
        acc_val = accuracy_score(y_val, y_pred_val) * 100
        
        elapsed = (datetime.now() - start).total_seconds() / 60
        log(f"✅ Val: {acc_val:.2f}% (was {best_acc:.2f}%) | Δ: {acc_val-best_acc:+.2f}% | Time: {elapsed:.1f}m")
        
        if acc_val > best_acc:
            best_acc, best_model, best_name = acc_val, model, best_name.replace("R1", "R2")
    
    elif round_num == 3:
        # Deeper trees
        log(f"\n🌳 Deepening {best_name}...")
        start = datetime.now()
        
        if "LightGBM" in best_name:
            model = LGBMClassifier(n_estimators=300, max_depth=20, learning_rate=0.03, num_leaves=150, min_child_samples=5, verbose=-1, random_state=42)
        elif "RandomForest" in best_name:
            model = RandomForestClassifier(n_estimators=300, max_depth=25, min_samples_split=2, min_samples_leaf=1, n_jobs=-1, random_state=42, verbose=0)
        else:
            model = ExtraTreesClassifier(n_estimators=300, max_depth=25, min_samples_split=2, min_samples_leaf=1, n_jobs=-1, random_state=42, verbose=0)
        
        model.fit(X_train, y_train)
        y_pred_val = model.predict(X_val)
        acc_val = accuracy_score(y_val, y_pred_val) * 100
        
        elapsed = (datetime.now() - start).total_seconds() / 60
        log(f"✅ Val: {acc_val:.2f}% (was {best_acc:.2f}%) | Δ: {acc_val-best_acc:+.2f}% | Time: {elapsed:.1f}m")
        
        if acc_val > best_acc:
            best_acc, best_model, best_name = acc_val, model, best_name.replace("R2", "R3")
    
    elif round_num == 4:
        # Ensemble of top 2
        log(f"\n🎭 Testing ensemble...")
        start = datetime.now()
        
        # Train top 2 models
        model1 = RandomForestClassifier(n_estimators=300, max_depth=25, n_jobs=-1, random_state=42, verbose=0)
        model2 = ExtraTreesClassifier(n_estimators=300, max_depth=25, n_jobs=-1, random_state=43, verbose=0)
        
        model1.fit(X_train, y_train)
        model2.fit(X_train, y_train)
        
        # Voting
        pred1 = model1.predict(X_val)
        pred2 = model2.predict(X_val)
        
        # Majority vote
        from scipy.stats import mode
        y_pred_val = mode([pred1, pred2], axis=0, keepdims=False)[0]
        acc_val = accuracy_score(y_val, y_pred_val) * 100
        
        elapsed = (datetime.now() - start).total_seconds() / 60
        log(f"✅ Ensemble Val: {acc_val:.2f}% (was {best_acc:.2f}%) | Δ: {acc_val-best_acc:+.2f}% | Time: {elapsed:.1f}m")
        
        if acc_val > best_acc:
            best_acc = acc_val
            best_model = (model1, model2)
            best_name = "Ensemble-R4"
    
    else:
        # Final optimization
        log(f"\n🚀 Final optimization...")
        start = datetime.now()
        
        if "Ensemble" in best_name:
            # Improve ensemble
            model1 = RandomForestClassifier(n_estimators=400, max_depth=30, n_jobs=-1, random_state=42, verbose=0)
            model2 = ExtraTreesClassifier(n_estimators=400, max_depth=30, n_jobs=-1, random_state=43, verbose=0)
            
            model1.fit(X_train, y_train)
            model2.fit(X_train, y_train)
            
            pred1 = model1.predict(X_val)
            pred2 = model2.predict(X_val)
            
            from scipy.stats import mode
            y_pred_val = mode([pred1, pred2], axis=0, keepdims=False)[0]
            acc_val = accuracy_score(y_val, y_pred_val) * 100
        else:
            # Single model optimization
            if "LightGBM" in best_name:
                model = LGBMClassifier(n_estimators=400, max_depth=25, learning_rate=0.02, num_leaves=200, min_child_samples=3, verbose=-1, random_state=42)
            elif "RandomForest" in best_name:
                model = RandomForestClassifier(n_estimators=400, max_depth=30, min_samples_split=2, min_samples_leaf=1, n_jobs=-1, random_state=42, verbose=0)
            else:
                model = ExtraTreesClassifier(n_estimators=400, max_depth=30, min_samples_split=2, min_samples_leaf=1, n_jobs=-1, random_state=42, verbose=0)
            
            model.fit(X_train, y_train)
            y_pred_val = model.predict(X_val)
            acc_val = accuracy_score(y_val, y_pred_val) * 100
        
        elapsed = (datetime.now() - start).total_seconds() / 60
        log(f"✅ Final: {acc_val:.2f}% (was {best_acc:.2f}%) | Δ: {acc_val-best_acc:+.2f}% | Time: {elapsed:.1f}m")
        
        if acc_val > best_acc:
            if "Ensemble" in best_name:
                best_acc, best_model, best_name = acc_val, (model1, model2), "Ensemble-FINAL"
            else:
                best_acc, best_model, best_name = acc_val, model, best_name.replace("R3", "FINAL")
    
    # Check if target reached
    if best_acc >= 95.0:
        log(f"\n🎉 TARGET REACHED! {best_acc:.2f}% >= 95%")
        break

# ============================================================================
# FINAL RESULTS
# ============================================================================
log("\n" + "=" * 80)
log("🏆 FINAL RESULTS")
log("=" * 80)
log(f"\n🥇 BEST: {best_name}")
log(f"📊 Validation Accuracy: {best_acc:.2f}%")

if best_acc >= 95.0:
    log("✅✅✅ TARGET REACHED! (>= 95%)")
elif best_acc >= 90.0:
    log(f"✅ EXCELLENT! Need {95-best_acc:.2f}% more for target")
elif best_acc >= 85.0:
    log(f"✅ GOOD! Need {95-best_acc:.2f}% more for target")

# Test on unseen descriptions
if len(y_test) > 0:
    log("\n🔬 Testing on UNSEEN descriptions...")
    if "Ensemble" in best_name:
        model1, model2 = best_model
        pred1 = model1.predict(X_test)
        pred2 = model2.predict(X_test)
        from scipy.stats import mode
        y_pred_test = mode([pred1, pred2], axis=0, keepdims=False)[0]
    else:
        y_pred_test = best_model.predict(X_test)
    
    acc_test = accuracy_score(y_test, y_pred_test) * 100
    log(f"   Test Accuracy (unseen): {acc_test:.2f}%")

# Save
log("\n💾 Saving models...")
if "Ensemble" not in best_name:
    joblib.dump(best_model, 'best_model_95.pkl')
else:
    joblib.dump(best_model[0], 'ensemble_model1_95.pkl')
    joblib.dump(best_model[1], 'ensemble_model2_95.pkl')

joblib.dump(tfidf, 'tfidf_vectorizer_95.pkl')
joblib.dump(le_agent, 'label_encoder_95.pkl')
joblib.dump(le_account, 'account_encoder_95.pkl')
joblib.dump(le_payment, 'payment_encoder_95.pkl')

log("✅ All models saved!")
log("\n" + "=" * 80)
log("✅ TRAINING COMPLETE!")
log("=" * 80)
