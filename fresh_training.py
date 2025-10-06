#!/usr/bin/env python3
"""
🎯 FRESH TRAINING FROM SCRATCH
- 2024+ data only
- All data cleaning applied
- Proper train/test/validation split
- All business rules included
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import classification_report, accuracy_score
from sklearn.ensemble import RandomForestClassifier
import joblib
from scipy.sparse import hstack
import warnings
warnings.filterwarnings('ignore')

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)

log("=" * 80)
log("🎯 FRESH TRAINING FROM SCRATCH")
log("=" * 80)
log("\n📋 Strategy:")
log("   • 2024+ data only")
log("   • All cleaning: normalization, deduplication, rules")
log("   • Split: 70% train, 15% test, 15% validation")
log("   • Target: Maximum accuracy with clean data")
log("\n⏱️  EST: 10-15 minutes")
log("=" * 80)

# ============================================================================
# STEP 1: LOAD & CLEAN DATA
# ============================================================================
log("\n📂 STEP 1: Loading 2024+ data...")
df = pd.read_csv('/Users/yarkin.akcil/Downloads/Unrecon_2025_10_05.csv', low_memory=False)

# Fix amount (cents to dollars)
df['amount'] = df['amount'] / 100

# Parse dates
df['date'] = pd.to_datetime(df['date'])
df = df.sort_values('date').reset_index(drop=True)

# Filter: 2024+ only
df = df[df['date'] >= '2024-01-01'].copy()
df = df[df['agent'].notna()].copy()

log(f"✅ Loaded: {len(df):,} transactions | {df['agent'].nunique()} agents")
log(f"   Date range: {df['date'].min().date()} to {df['date'].max().date()}")

# ============================================================================
# STEP 2: REMOVE SVB ACCOUNTS (bank closed)
# ============================================================================
log("\n🗑️  STEP 2: Removing SVB accounts...")
svb_accounts = [1, 2, 5, 10, 24]
df_before = len(df)
df = df[~df['origination_account_id'].isin(svb_accounts)].copy()
log(f"✅ Removed {df_before - len(df):,} transactions")

# ============================================================================
# STEP 3: NORMALIZE AGENT NAMES
# ============================================================================
log("\n🔤 STEP 3: Normalizing agent names...")
log("   • Trim whitespace")
log("   • Case-insensitive merge")
log("   • Use most common variation")

# Normalize: trim + lowercase
df['agent_normalized'] = df['agent'].str.strip().str.lower()

# Find most common variation for each normalized name
agent_mapping = {}
for norm_name in df['agent_normalized'].unique():
    variations = df[df['agent_normalized'] == norm_name]['agent'].value_counts()
    most_common = variations.index[0]
    agent_mapping[norm_name] = most_common

# Apply mapping
df['agent'] = df['agent_normalized'].map(agent_mapping)
df = df.drop('agent_normalized', axis=1)

agents_before = df['agent'].nunique()
log(f"✅ Normalized to {agents_before} unique agents")

# ============================================================================
# STEP 4: SMART DEDUPLICATION (keep diversity)
# ============================================================================
log("\n🎨 STEP 4: Smart deduplication...")
log("   • Keep max 5 samples per unique description")
log("   • Preserve temporal diversity (first 2 + last 3)")

sampled = []
for agent in df['agent'].unique():
    agent_data = df[df['agent'] == agent].copy()
    
    for desc in agent_data['description'].unique():
        desc_rows = agent_data[agent_data['description'] == desc].sort_values('date')
        
        if len(desc_rows) > 5:
            # Keep first 2 + last 3
            sampled.append(pd.concat([desc_rows.head(2), desc_rows.tail(3)]))
        else:
            sampled.append(desc_rows)

df_deduplicated = pd.concat(sampled).drop_duplicates().sort_values('date').reset_index(drop=True)

log(f"✅ Deduplicated: {len(df_deduplicated):,} (from {len(df):,})")
log(f"   Saved: {100 - (len(df_deduplicated)/len(df)*100):.1f}% memory")
log(f"   Agents: {df_deduplicated['agent'].nunique()}")
log(f"   Unique descriptions: {df_deduplicated['description'].nunique():,}")

# ============================================================================
# STEP 5: TEMPORAL SPLIT (70-15-15)
# ============================================================================
log("\n🔪 STEP 5: Temporal split (70% train, 15% test, 15% val)...")

# For each agent: split temporally
train_list, test_list, val_list = [], [], []

for agent in df_deduplicated['agent'].unique():
    agent_data = df_deduplicated[df_deduplicated['agent'] == agent].sort_values('date').reset_index(drop=True)
    n = len(agent_data)
    
    if n >= 10:
        # Enough data: 70-15-15 split
        train_end = int(n * 0.70)
        test_end = int(n * 0.85)
        
        train_list.append(agent_data.iloc[:train_end])
        test_list.append(agent_data.iloc[train_end:test_end])
        val_list.append(agent_data.iloc[test_end:])
    
    elif n >= 3:
        # Medium data: 70% train, 30% val
        train_end = int(n * 0.70)
        train_list.append(agent_data.iloc[:train_end])
        val_list.append(agent_data.iloc[train_end:])
    
    else:
        # Small data: all to train
        train_list.append(agent_data)

train_data = pd.concat(train_list).sort_values('date').reset_index(drop=True)
test_data = pd.concat(test_list).sort_values('date').reset_index(drop=True) if test_list else pd.DataFrame()
val_data = pd.concat(val_list).sort_values('date').reset_index(drop=True)

log(f"✅ Train: {len(train_data):,} ({train_data['agent'].nunique()} agents)")
log(f"   Test:  {len(test_data):,} ({test_data['agent'].nunique()} agents)")
log(f"   Val:   {len(val_data):,} ({val_data['agent'].nunique()} agents)")

# Ensure all agents in test/val are in train
train_agents = set(train_data['agent'].unique())
test_agents = set(test_data['agent'].unique()) if len(test_data) > 0 else set()
val_agents = set(val_data['agent'].unique())

missing = (test_agents | val_agents) - train_agents
if missing:
    log(f"⚠️  Removing {len(missing)} agents not in train")
    test_data = test_data[~test_data['agent'].isin(missing)]
    val_data = val_data[~val_data['agent'].isin(missing)]

log(f"✅ All test/val agents present in training!")

# ============================================================================
# STEP 6: FEATURE ENGINEERING with BUSINESS RULES
# ============================================================================
log("\n🔧 STEP 6: Feature engineering...")

# TF-IDF on description
tfidf = TfidfVectorizer(max_features=150, ngram_range=(1, 3), min_df=2)
X_train_tfidf = tfidf.fit_transform(train_data['description'].fillna(''))
X_test_tfidf = tfidf.transform(test_data['description'].fillna(''))
X_val_tfidf = tfidf.transform(val_data['description'].fillna(''))

# Encoders
le_account = LabelEncoder()
le_payment = LabelEncoder()
le_account.fit(df_deduplicated['origination_account_id'].fillna(0).astype(int).astype(str))
le_payment.fit(df_deduplicated['payment_method'].fillna('UNK').astype(str))

def extract_features(data):
    f = pd.DataFrame()
    
    # Categorical
    f['payment'] = le_payment.transform(data['payment_method'].fillna('UNK').astype(str))
    f['account'] = le_account.transform(data['origination_account_id'].fillna(0).astype(int).astype(str))
    
    # Numerical
    f['amount'] = data['amount'].values
    f['amount_log'] = np.log1p(data['amount'].abs().values)
    
    # Description & Account
    desc = data['description'].fillna('').astype(str).str.upper()
    account_id = data['origination_account_id'].fillna(0).astype(int)
    
    # BUSINESS RULES:
    # Account IDs: 6=Chase Payroll Wire, 7=Chase Recovery, 9=Chase Wire In, 
    #              18=PNC Wire In, 28=Blueridge Recovery
    
    # Rule 1: "1TRV" in description + account 6/7/9/18 = RISK (definitive)
    has_1trv = desc.str.contains('1TRV', regex=False, na=False)
    is_wire_account = (account_id == 6) | (account_id == 7) | (account_id == 9) | (account_id == 18)
    f['is_1trv_risk'] = (has_1trv & is_wire_account).astype(int).values
    
    # Rule 2: Account 6/9/18 (no 1TRV) = Risk
    f['is_risk_account'] = (
        ((account_id == 6) | (account_id == 9) | (account_id == 18)) & ~has_1trv
    ).astype(int).values
    
    # Rule 3: Account 7 (no 1TRV) = Recovery Wire
    has_interest = desc.str.contains('INTEREST', regex=False, na=False)
    f['is_recovery_account'] = (
        ((account_id == 7) & ~has_1trv) |
        ((account_id == 28) & ~has_interest)
    ).astype(int).values
    
    # Combined flags
    f['is_definitive_risk'] = (f['is_1trv_risk'] | f['is_risk_account']).values
    f['is_definitive_recovery'] = f['is_recovery_account'].values
    
    # Other patterns
    f['has_check'] = desc.str.contains('CHECK', regex=False).astype(int).values
    f['has_nys_dtf'] = desc.str.contains('NYS DTF', regex=False).astype(int).values
    f['has_oh_wh'] = desc.str.contains('OH WH', regex=False).astype(int).values
    f['has_oh_sdwh'] = desc.str.contains('OH SDWH', regex=False).astype(int).values
    f['has_il_ui'] = desc.str.contains(' IL ', regex=False).astype(int).values
    f['has_ok_ui'] = desc.str.contains(' OK ', regex=False).astype(int).values
    
    # Account flags
    f['acc_chase_recovery'] = (account_id == 7).astype(int).values
    f['acc_chase_payroll'] = (account_id == 6).astype(int).values
    f['acc_chase_wire'] = (account_id == 9).astype(int).values
    f['acc_pnc_wire'] = (account_id == 18).astype(int).values
    
    return f

X_train_ex = extract_features(train_data)
X_test_ex = extract_features(test_data)
X_val_ex = extract_features(val_data)

# Combine (sparse)
X_train = hstack([X_train_tfidf, X_train_ex.values])
X_test = hstack([X_test_tfidf, X_test_ex.values])
X_val = hstack([X_val_tfidf, X_val_ex.values])

# Labels
le_agent = LabelEncoder()
le_agent.fit(df_deduplicated['agent'])

y_train = le_agent.transform(train_data['agent'])
y_test = le_agent.transform(test_data['agent']) if len(test_data) > 0 else np.array([])
y_val = le_agent.transform(val_data['agent'])

log(f"✅ Features: {X_train.shape[1]} (sparse matrix)")
log(f"   Agents: {len(le_agent.classes_)}")

# ============================================================================
# STEP 7: TRAIN MODEL
# ============================================================================
log("\n" + "=" * 80)
log("🏃 STEP 7: TRAINING MODEL")
log("=" * 80)

log("\n⚡ Random Forest...")
start = datetime.now()

model = RandomForestClassifier(
    n_estimators=200,
    max_depth=20,
    min_samples_split=3,
    n_jobs=-1,
    random_state=42,
    verbose=0
)

model.fit(X_train, y_train)
elapsed = (datetime.now() - start).total_seconds() / 60

log(f"✅ Training time: {elapsed:.1f}m")

# ============================================================================
# STEP 8: EVALUATE
# ============================================================================
log("\n" + "=" * 80)
log("📊 STEP 8: EVALUATION")
log("=" * 80)

# Test accuracy
if len(y_test) > 0:
    y_pred_test = model.predict(X_test)
    acc_test = accuracy_score(y_test, y_pred_test) * 100
    log(f"\n✅ Test Accuracy: {acc_test:.2f}%")

# Validation accuracy
y_pred_val = model.predict(X_val)
acc_val = accuracy_score(y_val, y_pred_val) * 100
log(f"✅ Validation Accuracy: {acc_val:.2f}%")

# ============================================================================
# FINAL RESULTS
# ============================================================================
log("\n" + "=" * 80)
log("🏆 FINAL RESULTS")
log("=" * 80)

if len(y_test) > 0:
    log(f"\n📊 Test: {acc_test:.2f}%")
log(f"📊 Validation: {acc_val:.2f}%")

if acc_val >= 95.0:
    log("\n✅✅✅ EXCELLENT! >= 95%")
elif acc_val >= 90.0:
    log(f"\n✅ VERY GOOD! Need {95-acc_val:.2f}% more for 95% target")
elif acc_val >= 80.0:
    log(f"\n✅ GOOD! Need {95-acc_val:.2f}% more for 95% target")
else:
    log(f"\n⚠️  Need improvement: {95-acc_val:.2f}% more for 95% target")

# Save models
log("\n💾 Saving models...")
joblib.dump(model, 'fresh_model.pkl')
joblib.dump(tfidf, 'fresh_tfidf.pkl')
joblib.dump(le_agent, 'fresh_agent_encoder.pkl')
joblib.dump(le_account, 'fresh_account_encoder.pkl')
joblib.dump(le_payment, 'fresh_payment_encoder.pkl')
log("✅ All models saved!")

# Detailed report
log("\n📋 Detailed Validation Report:")
val_agent_names = val_data['agent'].unique()
val_agent_indices = [list(le_agent.classes_).index(a) for a in val_agent_names if a in le_agent.classes_]

print("\n" + classification_report(
    y_val,
    y_pred_val,
    labels=val_agent_indices,
    target_names=val_agent_names,
    zero_division=0
))

log("\n" + "=" * 80)
log("✅ TRAINING COMPLETE!")
log("=" * 80)
