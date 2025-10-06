#!/usr/bin/env python3
"""
🎯 FINAL TRAINING WITH ALL USER RULES
- All previous cleaning
- New business rules from analysis
- XGBoost model
"""

import pandas as pd
import numpy as np
from datetime import datetime
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import classification_report, accuracy_score
from xgboost import XGBClassifier
import joblib
from scipy.sparse import hstack
import warnings
warnings.filterwarnings('ignore')

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)

log("=" * 80)
log("🎯 FINAL TRAINING WITH ALL USER RULES")
log("=" * 80)

# ============================================================================
# LOAD & CLEAN DATA
# ============================================================================
log("\n📂 Loading 2024+ data...")
df = pd.read_csv('/Users/yarkin.akcil/Downloads/Unrecon_2025_10_05.csv', low_memory=False)
df['amount'] = df['amount'] / 100
df['date'] = pd.to_datetime(df['date'])
df = df.sort_values('date').reset_index(drop=True)
df = df[df['date'] >= '2024-01-01'].copy()
df = df[df['agent'].notna()].copy()

log(f"✅ {len(df):,} transactions | {df['agent'].nunique()} agents")

# Remove SVB
svb_accounts = [1, 2, 5, 10, 24]
df = df[~df['origination_account_id'].isin(svb_accounts)].copy()

# Normalize agents
df['agent_normalized'] = df['agent'].str.strip().str.lower()
agent_mapping = {}
for norm_name in df['agent_normalized'].unique():
    variations = df[df['agent_normalized'] == norm_name]['agent'].value_counts()
    agent_mapping[norm_name] = variations.index[0]
df['agent'] = df['agent_normalized'].map(agent_mapping)
df = df.drop('agent_normalized', axis=1)

log(f"✅ Normalized to {df['agent'].nunique()} agents")

# ============================================================================
# APPLY USER RULES (BEFORE DEDUPLICATION)
# ============================================================================
log("\n🔧 Applying user business rules...")

# Get Blueridge account ID (ID 28)
blueridge_account = 28

rule_changes = 0

for idx, row in df.iterrows():
    desc = str(row['description']).upper()
    acc_id = int(row['origination_account_id']) if pd.notna(row['origination_account_id']) else 0
    amount = float(row['amount'])
    payment_method = str(row['payment_method']).strip()
    
    # RULE 1 (HIGHEST PRIORITY): 1TRV → Risk
    if '1TRV' in desc and acc_id in [6, 7, 9, 18]:
        if df.at[idx, 'agent'] != 'Risk':
            df.at[idx, 'agent'] = 'Risk'
            rule_changes += 1
    
    # RULE 2: Bad Debt (Blueridge + amount < $0.5 OR "ITT GUSTO CORPORATE CCD")
    elif acc_id == blueridge_account and (amount < 0.5 or 'ITT GUSTO CORPORATE CCD' in desc):
        if df.at[idx, 'agent'] != 'Bad Debt':
            df.at[idx, 'agent'] = 'Bad Debt'
            rule_changes += 1
    
    # RULE 3: BRB (Blueridge + amount >= $0.5, no check/interest)
    elif acc_id == blueridge_account and amount >= 0.5:
        if 'CHECK' not in desc and 'INTEREST' not in desc:
            if df.at[idx, 'agent'] != 'BRB':
                df.at[idx, 'agent'] = 'BRB'
                rule_changes += 1
    
    # RULE 4: York Adams Tax (merge EIT, LST, etc)
    elif 'York Adams' in df.at[idx, 'agent']:
        if df.at[idx, 'agent'] != 'York Adams Tax':
            df.at[idx, 'agent'] = 'York Adams Tax'
            rule_changes += 1
    
    # RULE 5: ICP Return (TS FX ACCOUNTS RECEIVABLE or JPV pattern)
    elif 'TS FX ACCOUNTS RECEIVABLE' in desc or 'JPV' in desc:
        if df.at[idx, 'agent'] != 'ICP Return':
            df.at[idx, 'agent'] = 'ICP Return'
            rule_changes += 1
    
    # RULE 6: ICP Refund (wise + amount < $50k)
    elif 'WISE' in desc and amount < 50000:
        if df.at[idx, 'agent'] != 'ICP Refund':
            df.at[idx, 'agent'] = 'ICP Refund'
            rule_changes += 1
    
    # RULE 7: Risk (Wire accounts: 6, 9, 18)
    elif acc_id in [6, 9, 18]:
        if df.at[idx, 'agent'] != 'Risk':
            df.at[idx, 'agent'] = 'Risk'
            rule_changes += 1
    
    # RULE 8: Recovery Wire (Chase Recovery: 7)
    elif acc_id == 7:
        if df.at[idx, 'agent'] != 'Recovery Wire':
            df.at[idx, 'agent'] = 'Recovery Wire'
            rule_changes += 1
    
    # RULE 9: ACH (payment method = "ACH External")
    elif 'ACH EXTERNAL' in payment_method.upper():
        if df.at[idx, 'agent'] != 'ACH':
            df.at[idx, 'agent'] = 'ACH'
            rule_changes += 1

log(f"✅ Applied rules: {rule_changes:,} changes made")
log(f"   Final agents: {df['agent'].nunique()}")

# Smart deduplication
log("\n🎨 Smart deduplication...")
sampled = []
for agent in df['agent'].unique():
    agent_data = df[df['agent'] == agent].copy()
    for desc in agent_data['description'].unique():
        desc_rows = agent_data[agent_data['description'] == desc].sort_values('date')
        if len(desc_rows) > 5:
            sampled.append(pd.concat([desc_rows.head(2), desc_rows.tail(3)]))
        else:
            sampled.append(desc_rows)

df_deduplicated = pd.concat(sampled).drop_duplicates().sort_values('date').reset_index(drop=True)
log(f"✅ Deduplicated: {len(df_deduplicated):,}")

# Split
log("\n🔪 Temporal split (70-15-15)...")
train_list, test_list, val_list = [], [], []

for agent in df_deduplicated['agent'].unique():
    agent_data = df_deduplicated[df_deduplicated['agent'] == agent].sort_values('date').reset_index(drop=True)
    n = len(agent_data)
    
    if n >= 10:
        train_end = int(n * 0.70)
        test_end = int(n * 0.85)
        train_list.append(agent_data.iloc[:train_end])
        test_list.append(agent_data.iloc[train_end:test_end])
        val_list.append(agent_data.iloc[test_end:])
    elif n >= 3:
        train_end = int(n * 0.70)
        train_list.append(agent_data.iloc[:train_end])
        val_list.append(agent_data.iloc[train_end:])
    else:
        train_list.append(agent_data)

train_data = pd.concat(train_list).sort_values('date').reset_index(drop=True)
test_data = pd.concat(test_list).sort_values('date').reset_index(drop=True) if test_list else pd.DataFrame()
val_data = pd.concat(val_list).sort_values('date').reset_index(drop=True)

# Clean agents
train_agents = set(train_data['agent'].unique())
test_agents = set(test_data['agent'].unique()) if len(test_data) > 0 else set()
val_agents = set(val_data['agent'].unique())
missing = (test_agents | val_agents) - train_agents
if missing:
    test_data = test_data[~test_data['agent'].isin(missing)]
    val_data = val_data[~val_data['agent'].isin(missing)]

log(f"✅ Train: {len(train_data):,} | Test: {len(test_data):,} | Val: {len(val_data):,}")

# Feature engineering
log("\n🔧 Feature engineering...")

tfidf = TfidfVectorizer(max_features=150, ngram_range=(1, 3), min_df=2)
X_train_tfidf = tfidf.fit_transform(train_data['description'].fillna(''))
X_test_tfidf = tfidf.transform(test_data['description'].fillna(''))
X_val_tfidf = tfidf.transform(val_data['description'].fillna(''))

le_account = LabelEncoder()
le_payment = LabelEncoder()
le_account.fit(df_deduplicated['origination_account_id'].fillna(0).astype(int).astype(str))
le_payment.fit(df_deduplicated['payment_method'].fillna('UNK').astype(str))

def extract_features(data):
    f = pd.DataFrame()
    f['payment'] = le_payment.transform(data['payment_method'].fillna('UNK').astype(str))
    f['account'] = le_account.transform(data['origination_account_id'].fillna(0).astype(int).astype(str))
    f['amount'] = data['amount'].values
    f['amount_log'] = np.log1p(data['amount'].abs().values)
    
    desc = data['description'].fillna('').astype(str).str.upper()
    account_id = data['origination_account_id'].fillna(0).astype(int)
    
    # Rule-based features
    f['has_1trv'] = desc.str.contains('1TRV', regex=False).astype(int).values
    f['has_itt_gusto'] = desc.str.contains('ITT GUSTO CORPORATE', regex=False).astype(int).values
    f['has_ts_fx'] = desc.str.contains('TS FX ACCOUNTS', regex=False).astype(int).values
    f['has_jpv'] = desc.str.contains('JPV', regex=False).astype(int).values
    f['has_wise'] = desc.str.contains('WISE', regex=False).astype(int).values
    f['has_check'] = desc.str.contains('CHECK', regex=False).astype(int).values
    f['has_interest'] = desc.str.contains('INTEREST', regex=False).astype(int).values
    
    # Account flags
    f['is_blueridge'] = (account_id == 28).astype(int).values
    f['is_wire_risk'] = ((account_id == 6) | (account_id == 9) | (account_id == 18)).astype(int).values
    f['is_recovery'] = (account_id == 7).astype(int).values
    
    # Amount thresholds
    f['amt_tiny'] = (data['amount'] < 0.5).astype(int).values
    f['amt_large'] = (data['amount'] > 50000).astype(int).values
    
    return f

X_train_ex = extract_features(train_data)
X_test_ex = extract_features(test_data)
X_val_ex = extract_features(val_data)

X_train = hstack([X_train_tfidf, X_train_ex.values])
X_test = hstack([X_test_tfidf, X_test_ex.values])
X_val = hstack([X_val_tfidf, X_val_ex.values])

le_agent = LabelEncoder()
le_agent.fit(df_deduplicated['agent'])

y_train = le_agent.transform(train_data['agent'])
y_test = le_agent.transform(test_data['agent']) if len(test_data) > 0 else np.array([])
y_val = le_agent.transform(val_data['agent'])

log(f"✅ Features: {X_train.shape[1]} | Agents: {len(le_agent.classes_)}")

# ============================================================================
# TRAIN XGBoost
# ============================================================================
log("\n" + "=" * 80)
log("🏃 TRAINING XGBoost")
log("=" * 80)

model = XGBClassifier(
    n_estimators=200,
    max_depth=15,
    learning_rate=0.05,
    n_jobs=-1,
    random_state=42,
    eval_metric='mlogloss'
)

model.fit(X_train, y_train)

# Evaluate
if len(y_test) > 0:
    y_pred_test = model.predict(X_test)
    acc_test = accuracy_score(y_test, y_pred_test) * 100
    log(f"\n✅ Test Accuracy: {acc_test:.2f}%")

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
    log("\n✅✅✅ TARGET REACHED! >= 95%")
elif acc_val >= 90.0:
    log(f"\n✅ EXCELLENT! Need {95-acc_val:.2f}% more for 95% target")

# Save
log("\n💾 Saving models...")
joblib.dump(model, 'final_model_with_rules.pkl')
joblib.dump(tfidf, 'final_tfidf_with_rules.pkl')
joblib.dump(le_agent, 'final_agent_encoder_with_rules.pkl')
log("✅ Saved!")

# Show top errors
log("\n📊 Checking remaining errors...")
wrong_mask = y_val != y_pred_val
if np.sum(wrong_mask) > 0:
    wrong_df = val_data.loc[val_data.index[wrong_mask]].copy()
    wrong_by_agent = wrong_df['agent'].value_counts().head(5)
    
    log("\n🔍 Top 5 agents with errors:")
    for i, (agent, count) in enumerate(wrong_by_agent.items(), 1):
        total = len(val_data[val_data['agent'] == agent])
        log(f"   {i}. {agent:30s}: {count:4,} / {total:4,} ({count/total*100:.1f}% error)")

log("\n" + "=" * 80)
log("✅ TRAINING COMPLETE!")
log("=" * 80)
