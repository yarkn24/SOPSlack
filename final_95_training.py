#!/usr/bin/env python3
"""
🎯 FINAL TRAINING TO 95% CONFIDENCE
- 2024+ all data
- Last 1 year = 100% accurate
- All improvements applied
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import classification_report, accuracy_score
from sklearn.ensemble import RandomForestClassifier, ExtraTreesClassifier
from lightgbm import LGBMClassifier
import joblib
from scipy.sparse import hstack
import warnings
warnings.filterwarnings('ignore')

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)

log("=" * 80)
log("🎯 FINAL TRAINING TO 95% CONFIDENCE")
log("=" * 80)
log("\n📋 Strategy:")
log("   • 2024-today: ALL data")
log("   • Last 1 year = 100% accurate (ground truth)")
log("   • All rules applied: 1TRV, accounts, no duplicates")
log("   • Target: 95% confidence")
log("\n⏱️  EST: 15-20 minutes")
log("=" * 80)

# ============================================================================
# LOAD & FILTER LAST 1.5 YEARS DATA
# ============================================================================
log("\n📂 Loading data...")
df = pd.read_csv('/Users/yarkin.akcil/Downloads/Unrecon_2025_10_05.csv', low_memory=False)

# Fix amount (cents to dollars)
df['amount'] = df['amount'] / 100

# Parse dates
df['date'] = pd.to_datetime(df['date'])
df = df.sort_values('date').reset_index(drop=True)

# Filter: 2024+ data
df = df[df['date'] >= '2024-01-01'].copy()
df = df[df['agent'].notna()].copy()

log(f"✅ {len(df):,} transactions | {df['agent'].nunique()} agents")
log(f"   Date range: {df['date'].min().date()} to {df['date'].max().date()}")

# Remove SVB accounts (bank closed)
svb_accounts = [1, 2, 5, 10, 24]
df_before = len(df)
df = df[~df['origination_account_id'].isin(svb_accounts)].copy()
log(f"✅ Removed {df_before - len(df):,} SVB transactions")

# ============================================================================
# AGENT NORMALIZATION: Merge variations
# ============================================================================
log("\n🔤 Normalizing agent names...")

# Step 1: Trim whitespace and normalize case
df['agent_normalized'] = df['agent'].str.strip().str.lower()

# Step 2: Find most common variation for each normalized name
agent_mapping = {}
for norm_name in df['agent_normalized'].unique():
    # Get all original variations
    variations = df[df['agent_normalized'] == norm_name]['agent'].value_counts()
    # Use the most common variation
    most_common = variations.index[0]
    agent_mapping[norm_name] = most_common

# Step 3: Apply mapping
df['agent'] = df['agent_normalized'].map(agent_mapping)
df = df.drop('agent_normalized', axis=1)

before_norm = len(df['agent'].unique())
log(f"✅ Normalized: {before_norm} unique agents")

# Show some examples of normalization
log("\n📋 Normalization examples:")
agent_counts = df['agent'].value_counts().head(10)
for agent, count in agent_counts.items():
    log(f"   • {agent}: {count:,} transactions")

# ============================================================================
# UNIQUE DESCRIPTIONS ONLY (NO DUPLICATES)
# ============================================================================
log("\n🎨 Removing duplicate descriptions...")

sampled = []
for agent in df['agent'].unique():
    agent_data = df[df['agent'] == agent].copy()
    
    # For each unique description, take ONLY the most recent one
    for desc in agent_data['description'].unique():
        desc_rows = agent_data[agent_data['description'] == desc].sort_values('date')
        sampled.append(desc_rows.tail(1))

df_sampled = pd.concat(sampled).drop_duplicates().sort_values('date').reset_index(drop=True)

log(f"✅ Unique: {len(df_sampled):,} (from {len(df):,})")
log(f"   Agents: {df_sampled['agent'].nunique()}")
log(f"   Descriptions: {df_sampled['description'].nunique():,}")

# ============================================================================
# SPLIT: Each agent → train + val (from last 1 year)
# ============================================================================
log("\n🔪 Smart split (all agents in both train & val)...")

cutoff_date = df_sampled['date'].max() - timedelta(days=365)
log(f"   Last 1 year cutoff: {cutoff_date.date()}")

# For each agent: split descriptions temporally
train_list, val_list = [], []

for agent in df_sampled['agent'].unique():
    agent_data = df_sampled[df_sampled['agent'] == agent].sort_values('date').reset_index(drop=True)
    
    # Get last 1 year data for this agent
    last_year = agent_data[agent_data['date'] > cutoff_date]
    older = agent_data[agent_data['date'] <= cutoff_date]
    
    # Strategy: Use older data for training, last year for validation
    # BUT ensure agent is in both sets
    
    if len(last_year) > 0 and len(older) > 0:
        # Perfect: agent has data in both periods
        train_list.append(older)
        val_list.append(last_year)
    
    elif len(last_year) > 0:
        # Agent only in last year: split 70/30
        n = len(last_year)
        if n >= 3:
            n_train = int(n * 0.70)
            train_list.append(last_year.iloc[:n_train])
            val_list.append(last_year.iloc[n_train:])
        else:
            # Very few: put 1 in train, rest in val
            train_list.append(last_year.head(1))
            if n > 1:
                val_list.append(last_year.tail(n-1))
    
    else:
        # Agent only in older data: all to train
        train_list.append(older)

train_data = pd.concat(train_list).sort_values('date').reset_index(drop=True) if train_list else pd.DataFrame()
validation_data = pd.concat(val_list).sort_values('date').reset_index(drop=True) if val_list else pd.DataFrame()

log(f"✅ Train: {len(train_data):,} ({train_data['agent'].nunique()} agents)")
log(f"   Val (last 1yr): {len(validation_data):,} ({validation_data['agent'].nunique()} agents)")

# Verify all val agents are in train
train_agents = set(train_data['agent'].unique())
val_agents = set(validation_data['agent'].unique())

missing = val_agents - train_agents
if missing:
    log(f"⚠️  ERROR: {len(missing)} agents in val but not in train!")
else:
    log(f"✅ Perfect! All {len(val_agents)} val agents are in training")

test_data = pd.DataFrame()  # No separate test set

# ============================================================================
# FEATURE ENGINEERING with ALL RULES
# ============================================================================
log("\n🔧 Feature engineering with definitive rules...")

# TF-IDF: 150 features
tfidf = TfidfVectorizer(max_features=150, ngram_range=(1, 3), min_df=2)
X_train_tfidf = tfidf.fit_transform(train_data['description'].fillna(''))
X_val_tfidf = tfidf.transform(validation_data['description'].fillna(''))

# Encoders
le_account = LabelEncoder()
le_payment = LabelEncoder()
le_account.fit(df_sampled['origination_account_id'].fillna(0).astype(int).astype(str))
le_payment.fit(df_sampled['payment_method'].fillna('UNK').astype(str))

def extract_features(data):
    f = pd.DataFrame()
    
    # Categorical
    f['payment'] = le_payment.transform(data['payment_method'].fillna('UNK').astype(str))
    f['account'] = le_account.transform(data['origination_account_id'].fillna(0).astype(int).astype(str))
    
    # Numerical
    f['amount'] = data['amount'].values
    f['amount_log'] = np.log1p(data['amount'].abs().values)
    f['amount_sqrt'] = np.sqrt(data['amount'].abs().values)
    
    # Description
    desc = data['description'].fillna('').astype(str).str.upper()
    account_id = data['origination_account_id'].fillna(0).astype(int)
    
    # CRITICAL DEFINITIVE RULES:
    # Account IDs from mapping:
    # ID 6: Chase Payroll Incoming Wires → Risk
    # ID 7: Chase Recovery → Recovery Wire (unless 1TRV)
    # ID 9: Chase Wire In → Risk
    # ID 18: PNC Wire In → Risk
    # ID 28: Blueridge Recovery → Recovery Wire (unless INTEREST)
    
    # Step 1: Identify special accounts
    is_wire_or_recovery_account = (
        (account_id == 6) | (account_id == 7) | (account_id == 9) | (account_id == 18)
    )
    
    # Step 2: Check for "1TRV" code (DEFINITIVE RISK)
    has_1trv = desc.str.contains('1TRV', regex=False, na=False)
    
    # Step 3: Risk/Recovery classification
    # Rule 1: Account 6/7/9/18 + "1TRV" → DEFINITIVE RISK
    f['is_1trv_risk'] = (is_wire_or_recovery_account & has_1trv).astype(int).values
    
    # Rule 2: Account 6/9/18 (no 1TRV) → Risk
    f['is_risk_account'] = (
        ((account_id == 6) | (account_id == 9) | (account_id == 18)) & ~has_1trv
    ).astype(int).values
    
    # Rule 3: Account 7 (no 1TRV) → Recovery Wire
    has_interest = desc.str.contains('INTEREST', regex=False, na=False)
    f['is_recovery_account'] = (
        ((account_id == 7) & ~has_1trv) |
        ((account_id == 28) & ~has_interest)
    ).astype(int).values
    
    # Combined definitive features
    f['is_definitive_risk'] = (f['is_1trv_risk'] | f['is_risk_account']).values
    f['is_definitive_recovery'] = f['is_recovery_account'].values
    
    # Other patterns
    f['has_check'] = desc.str.contains('CHECK', regex=False).astype(int).values
    f['has_nys_dtf'] = desc.str.contains('NYS DTF', regex=False).astype(int).values
    f['has_oh_wh'] = desc.str.contains('OH WH', regex=False).astype(int).values
    f['has_il'] = desc.str.contains(' IL ', regex=False).astype(int).values
    f['has_ok'] = desc.str.contains(' OK ', regex=False).astype(int).values
    
    # Account flags
    f['is_chase_recovery'] = (account_id == 7).astype(int).values
    f['is_chase_payroll_wire'] = (account_id == 6).astype(int).values
    f['is_chase_wire_in'] = (account_id == 9).astype(int).values
    f['is_pnc_wire_in'] = (account_id == 18).astype(int).values
    
    # Description stats
    f['desc_len'] = data['description'].fillna('').astype(str).apply(len).values
    f['desc_words'] = data['description'].fillna('').astype(str).str.split().apply(len).values
    
    return f

X_train_ex = extract_features(train_data)
X_val_ex = extract_features(validation_data)

# SPARSE matrices
X_train = hstack([X_train_tfidf, X_train_ex.values])
X_val = hstack([X_val_tfidf, X_val_ex.values])

le_agent = LabelEncoder()
le_agent.fit(df_sampled['agent'])

y_train = le_agent.transform(train_data['agent'])
y_val = le_agent.transform(validation_data['agent'])

log(f"✅ Features: {X_train.shape[1]} (sparse)")
log(f"   Classes: {len(le_agent.classes_)}")

# ============================================================================
# TRAIN BEST MODEL: RandomForest (won in previous run)
# ============================================================================
log("\n" + "=" * 80)
log("🏃 TRAINING BEST MODEL")
log("=" * 80)

log("\n⚡ Random Forest (optimized)...")
start = datetime.now()

model = RandomForestClassifier(
    n_estimators=100, 
    max_depth=15, 
    min_samples_split=5,
    n_jobs=-1, 
    random_state=42, 
    verbose=0
)

model.fit(X_train, y_train)
elapsed = (datetime.now() - start).total_seconds() / 60

# Evaluate on validation (last 1 year)
y_pred_val = model.predict(X_val)
acc_val = accuracy_score(y_val, y_pred_val) * 100

log(f"\n✅ Training time: {elapsed:.1f}m")
log(f"✅ Validation Accuracy (last 1yr): {acc_val:.2f}%")

# ============================================================================
# FINAL RESULTS
# ============================================================================
log("\n" + "=" * 80)
log("🏆 FINAL RESULTS")
log("=" * 80)
log(f"\n📊 Validation (Last 1 Year): {acc_val:.2f}%")

if acc_val >= 95.0:
    log("✅✅✅ TARGET REACHED! (>= 95%)")
elif acc_val >= 92.0:
    log(f"✅ EXCELLENT! Need {95-acc_val:.2f}% more for 95% target")
elif acc_val >= 90.0:
    log(f"✅ VERY GOOD! Need {95-acc_val:.2f}% more for 95% target")

# Save
log("\n💾 Saving final model...")
joblib.dump(model, 'final_model_95.pkl')
joblib.dump(tfidf, 'final_tfidf.pkl')
joblib.dump(le_agent, 'final_label_encoder.pkl')
joblib.dump(le_account, 'final_account_encoder.pkl')
joblib.dump(le_payment, 'final_payment_encoder.pkl')

log("✅ All models saved!")

# Detailed report on validation (last 1 year)
log("\n📋 Detailed Report (Last 1 Year - Ground Truth):")

# Get unique agents in validation set
val_agent_names = validation_data['agent'].unique()
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
