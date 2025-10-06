#!/usr/bin/env python3
"""
🎯 XGBoost DETAILED ANALYSIS
- Train XGBoost with same settings
- Show detailed classification report
- Analyze wrong predictions with descriptions
"""

import pandas as pd
import numpy as np
from datetime import datetime
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import classification_report, accuracy_score, confusion_matrix
from xgboost import XGBClassifier
from scipy.sparse import hstack
import warnings
warnings.filterwarnings('ignore')

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)

log("=" * 80)
log("🎯 XGBoost DETAILED ANALYSIS")
log("=" * 80)

# ============================================================================
# LOAD & PREPARE DATA (same as before)
# ============================================================================
log("\n📂 Loading data...")
df = pd.read_csv('/Users/yarkin.akcil/Downloads/Unrecon_2025_10_05.csv', low_memory=False)
df['amount'] = df['amount'] / 100
df['date'] = pd.to_datetime(df['date'])
df = df.sort_values('date').reset_index(drop=True)
df = df[df['date'] >= '2024-01-01'].copy()
df = df[df['agent'].notna()].copy()

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

# Smart deduplication
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

# Split
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

log(f"✅ Train: {len(train_data):,} | Val: {len(val_data):,}")

# Feature engineering
log("🔧 Feature engineering...")

tfidf = TfidfVectorizer(max_features=150, ngram_range=(1, 3), min_df=2)
X_train_tfidf = tfidf.fit_transform(train_data['description'].fillna(''))
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
    
    has_1trv = desc.str.contains('1TRV', regex=False, na=False)
    is_wire_account = (account_id == 6) | (account_id == 7) | (account_id == 9) | (account_id == 18)
    f['is_1trv_risk'] = (has_1trv & is_wire_account).astype(int).values
    f['is_risk_account'] = (((account_id == 6) | (account_id == 9) | (account_id == 18)) & ~has_1trv).astype(int).values
    
    has_interest = desc.str.contains('INTEREST', regex=False, na=False)
    f['is_recovery_account'] = (((account_id == 7) & ~has_1trv) | ((account_id == 28) & ~has_interest)).astype(int).values
    
    f['has_check'] = desc.str.contains('CHECK', regex=False).astype(int).values
    f['has_oh_wh'] = desc.str.contains('OH WH', regex=False).astype(int).values
    f['has_il_ui'] = desc.str.contains(' IL ', regex=False).astype(int).values
    
    return f

X_train_ex = extract_features(train_data)
X_val_ex = extract_features(val_data)

X_train = hstack([X_train_tfidf, X_train_ex.values])
X_val = hstack([X_val_tfidf, X_val_ex.values])

le_agent = LabelEncoder()
le_agent.fit(df_deduplicated['agent'])

y_train = le_agent.transform(train_data['agent'])
y_val = le_agent.transform(val_data['agent'])

# ============================================================================
# TRAIN XGBoost
# ============================================================================
log("\n🏃 Training XGBoost...")

model = XGBClassifier(
    n_estimators=200,
    max_depth=15,
    learning_rate=0.05,
    n_jobs=-1,
    random_state=42,
    eval_metric='mlogloss'
)
model.fit(X_train, y_train)

# Predict
y_pred_val = model.predict(X_val)
acc_val = accuracy_score(y_val, y_pred_val) * 100

log(f"✅ Validation Accuracy: {acc_val:.2f}%")

# ============================================================================
# DETAILED CLASSIFICATION REPORT
# ============================================================================
log("\n" + "=" * 80)
log("📊 DETAILED CLASSIFICATION REPORT")
log("=" * 80)

val_agent_names = val_data['agent'].unique()
val_agent_indices = [list(le_agent.classes_).index(a) for a in val_agent_names if a in le_agent.classes_]

report = classification_report(
    y_val,
    y_pred_val,
    labels=val_agent_indices,
    target_names=val_agent_names,
    zero_division=0,
    output_dict=True
)

# Sort by F1-score
agent_scores = []
for agent in val_agent_names:
    if agent in report:
        agent_scores.append((
            agent,
            report[agent]['precision'],
            report[agent]['recall'],
            report[agent]['f1-score'],
            report[agent]['support']
        ))

agent_scores.sort(key=lambda x: x[3], reverse=True)

print("\n" + "=" * 100)
print(f"{'Agent':<40} {'Precision':>10} {'Recall':>10} {'F1-Score':>10} {'Support':>10}")
print("=" * 100)

for agent, prec, rec, f1, supp in agent_scores:
    print(f"{agent:<40} {prec:>10.2%} {rec:>10.2%} {f1:>10.2%} {int(supp):>10,}")

# ============================================================================
# ANALYZE WRONG PREDICTIONS
# ============================================================================
log("\n" + "=" * 80)
log("❌ WRONG PREDICTIONS ANALYSIS")
log("=" * 80)

# Get wrong predictions
wrong_mask = y_val != y_pred_val
wrong_indices = val_data.index[wrong_mask].tolist()

log(f"\n📊 Total wrong predictions: {len(wrong_indices):,} / {len(val_data):,} ({len(wrong_indices)/len(val_data)*100:.1f}%)")

# Analyze by agent
wrong_df = val_data.loc[wrong_indices].copy()
wrong_df['predicted_agent'] = le_agent.inverse_transform(y_pred_val[wrong_mask])

log("\n🔍 Top 10 agents with most wrong predictions:")
wrong_by_agent = wrong_df['agent'].value_counts().head(10)

for i, (agent, count) in enumerate(wrong_by_agent.items(), 1):
    total_agent = len(val_data[val_data['agent'] == agent])
    error_rate = count / total_agent * 100 if total_agent > 0 else 0
    log(f"{i:2d}. {agent:35s}: {count:4,} wrong / {total_agent:4,} total ({error_rate:5.1f}% error)")

# Show sample wrong predictions with descriptions
log("\n📋 Sample wrong predictions (first 20):")
print("\n" + "=" * 120)
print(f"{'ID':<12} {'Actual':<25} {'Predicted':<25} {'Amount':>12} {'Description':<50}")
print("=" * 120)

for idx in wrong_indices[:20]:
    row = val_data.loc[idx]
    pred_idx = list(val_data.index).index(idx)
    predicted = le_agent.inverse_transform([y_pred_val[pred_idx]])[0]
    
    desc = str(row['description'])[:50] + "..." if len(str(row['description'])) > 50 else str(row['description'])
    
    print(f"{row['id']:<12} {row['agent']:<25} {predicted:<25} ${row['amount']:>10,.2f} {desc}")

print("=" * 120)

# Group wrong predictions by true agent
log("\n📊 Wrong predictions grouped by TRUE agent (showing first 3 for top 5 agents):")

for agent in wrong_by_agent.head(5).index:
    agent_wrong = wrong_df[wrong_df['agent'] == agent].head(3)
    
    log(f"\n🔴 TRUE AGENT: {agent}")
    for idx, row in agent_wrong.iterrows():
        predicted = row['predicted_agent']
        desc_short = str(row['description'])[:80] + "..." if len(str(row['description'])) > 80 else str(row['description'])
        log(f"   → Predicted as: {predicted}")
        log(f"      ID: {row['id']} | Amount: ${row['amount']:.2f}")
        log(f"      Description: {desc_short}")

log("\n" + "=" * 80)
log("✅ ANALYSIS COMPLETE!")
log("=" * 80)
