#!/usr/bin/env python3
"""
⚡ ULTRA FAST TRAINING - No deduplication, optimized for speed
Target: <40s prediction per BT, 95%+ accuracy
"""

import pandas as pd
import numpy as np
from datetime import datetime
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score
from xgboost import XGBClassifier
import joblib
from scipy.sparse import hstack
import warnings
warnings.filterwarnings('ignore')

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)

log("=" * 80)
log("⚡ ULTRA FAST TRAINING")
log("=" * 80)

# Load
log("\n📂 Loading...")
df = pd.read_csv('/Users/yarkin.akcil/Downloads/Unrecon_2025_10_05.csv', low_memory=False)
df['amount'] = df['amount'] / 100
df['date'] = pd.to_datetime(df['date'])
df = df[df['date'] >= '2024-01-01'].copy()
df = df[df['agent'].notna()].copy()

# Remove SVB
svb_accounts = [1, 2, 5, 10, 24]
df = df[~df['origination_account_id'].isin(svb_accounts)].copy()

# Normalize (only trim whitespace, keep original case)
df['agent'] = df['agent'].str.strip()

log(f"✅ {len(df):,} transactions | {df['agent'].nunique()} agents")

# Apply rules - UPDATED WITH NEW RULES
log("\n🔧 Rules...")

# First pass: Find ICP Funding amounts (Chase ICP + JPMORGAN ACCESS TRANSFER FROM)
icp_funding_amounts = set()
for idx, row in df.iterrows():
    if pd.notna(row['origination_account_id']) and int(row['origination_account_id']) == 21:
        desc = str(row['description']).upper()
        if 'REMARK=JPMORGAN ACCESS TRANSFER FROM' in desc:
            icp_funding_amounts.add(float(row['amount']))

log(f"   📌 ICP Funding amounts: {len(icp_funding_amounts)}")

# Second pass: Apply all rules
for idx, row in df.iterrows():
    desc = str(row['description']).upper()
    acc = int(row['origination_account_id']) if pd.notna(row['origination_account_id']) else 0
    amt = float(row['amount'])
    pm = int(row['payment_method']) if pd.notna(row['payment_method']) else -1
    
    # PRIORITY ORDER (HIGHEST TO LOWEST)
    
    # 1. Payment Method 12 = ZBT
    if pm == 12:
        df.at[idx, 'agent'] = 'ZBT'
    # 2. NIUM = Nium Payment
    elif 'NIUM' in desc:
        df.at[idx, 'agent'] = 'Nium Payment'
    # 3. ICP Funding - Chase ICP + JPMORGAN ACCESS TRANSFER FROM
    elif acc == 21 and 'REMARK=JPMORGAN ACCESS TRANSFER FROM' in desc:
        df.at[idx, 'agent'] = 'ICP Funding'
    # 4. ICP Funding - Paired transaction (same amount + JPMORGAN)
    elif amt in icp_funding_amounts and 'REMARK=JPMORGAN ACCESS TRANSFER' in desc:
        df.at[idx, 'agent'] = 'ICP Funding'
    # 5. 1TRV = RISK (ANY ACCOUNT - HIGHEST PRIORITY)
    elif '1TRV' in desc:
        df.at[idx, 'agent'] = 'Risk'
    # 6. STATE rules
    elif 'STATE OF MONTANA' in desc:
        df.at[idx, 'agent'] = 'MT WH'
    elif 'NYS DTF WT' in desc:
        df.at[idx, 'agent'] = 'NY WH'
    elif 'NYS DOL UI' in desc:
        df.at[idx, 'agent'] = 'NY UI'
    # 7. Treasury/Money Market
    elif '100% US TREASURY CAPITAL 3163' in desc or 'MONEY MKT MUTUAL FUND' in desc:
        df.at[idx, 'agent'] = 'Money Market Transfer'
    elif 'JPMORGAN ACCESS TRANSFER' in desc:
        df.at[idx, 'agent'] = 'Treasury Transfer'
    elif 'INTEREST ADJUSTMENT' in desc:
        df.at[idx, 'agent'] = 'Interest Adjustment'
    # 8. Account-specific rules
    elif acc == 16 and 'CREDIT MEMO' in desc:
        df.at[idx, 'agent'] = 'PNC LOI'
    elif 'KEYSTONE' in desc:
        df.at[idx, 'agent'] = 'PA UI'
    elif pm == 2:
        df.at[idx, 'agent'] = 'Check'
    elif pm == 4:
        df.at[idx, 'agent'] = 'ACH'
    # 9. Recovery accounts (WITHOUT 1TRV)
    elif acc in [7, 28]:
        if 'INTEREST' in desc:
            df.at[idx, 'agent'] = 'Interest Payment'
        else:
            df.at[idx, 'agent'] = 'Recovery Wire'
    # 10. Risk accounts
    elif acc in [6, 9, 18] and pm == 0:
        df.at[idx, 'agent'] = 'Risk'
    # 11. Blueridge Operations
    elif acc == 26:
        if amt < 0.5:
            df.at[idx, 'agent'] = 'Bad Debt'
        else:
            df.at[idx, 'agent'] = 'BRB'
    elif amt < 0.5 and amt > 0:
        df.at[idx, 'agent'] = 'Bad Debt'
    # 12. Other patterns
    elif 'LOCKBOX' in desc:
        df.at[idx, 'agent'] = 'Lockbox'
    elif 'TS FX ACCOUNTS RECEIVABLE' in desc or 'JPV' in desc:
        df.at[idx, 'agent'] = 'ICP Return'
    elif 'WISE' in desc and amt < 50000:
        df.at[idx, 'agent'] = 'ICP Refund'
    elif 'YORK ADAMS' in desc:
        df.at[idx, 'agent'] = 'York Adams Tax'

log(f"✅ {df['agent'].nunique()} agents | {len(df):,} transactions after rules")

# Split
log("\n🔪 Split...")
train_end = int(len(df) * 0.70)
test_end = int(len(df) * 0.85)

train_data = df.iloc[:train_end]
test_data = df.iloc[train_end:test_end]
val_data = df.iloc[test_end:]

log(f"✅ Train: {len(train_data):,} | Test: {len(test_data):,} | Val: {len(val_data):,}")

# Fast features (minimal)
log("\n🔧 Features...")

tfidf = TfidfVectorizer(max_features=30, ngram_range=(1, 2), min_df=2)
X_train_tfidf = tfidf.fit_transform(train_data['description'].fillna(''))
X_test_tfidf = tfidf.transform(test_data['description'].fillna(''))
X_val_tfidf = tfidf.transform(val_data['description'].fillna(''))

le_account = LabelEncoder()
le_payment = LabelEncoder()
le_account.fit(df['origination_account_id'].fillna(0).astype(int).astype(str))
le_payment.fit(df['payment_method'].fillna(-1).astype(int).astype(str))

def extract_features(data):
    f = pd.DataFrame()
    f['payment'] = le_payment.transform(data['payment_method'].fillna(-1).astype(int).astype(str))
    f['account'] = le_account.transform(data['origination_account_id'].fillna(0).astype(int).astype(str))
    f['amount'] = data['amount'].values
    f['amount_log'] = np.log1p(data['amount'].abs().values)
    return f

X_train_ex = extract_features(train_data)
X_test_ex = extract_features(test_data)
X_val_ex = extract_features(val_data)

X_train = hstack([X_train_tfidf, X_train_ex.values])
X_test = hstack([X_test_tfidf, X_test_ex.values])
X_val = hstack([X_val_tfidf, X_val_ex.values])

# Filter test/val to only have agents in train
train_agents = set(train_data['agent'].unique())
test_data = test_data[test_data['agent'].isin(train_agents)]
val_data = val_data[val_data['agent'].isin(train_agents)]

# Recompute test/val features after filtering
X_test_tfidf = tfidf.transform(test_data['description'].fillna(''))
X_test_ex = extract_features(test_data)
X_test = hstack([X_test_tfidf, X_test_ex.values])

X_val_tfidf = tfidf.transform(val_data['description'].fillna(''))
X_val_ex = extract_features(val_data)
X_val = hstack([X_val_tfidf, X_val_ex.values])

le_agent = LabelEncoder()
le_agent.fit(train_data['agent'])

y_train = le_agent.transform(train_data['agent'])
y_test = le_agent.transform(test_data['agent'])
y_val = le_agent.transform(val_data['agent'])

log(f"✅ Features: {X_train.shape[1]} | Agents: {len(le_agent.classes_)}")

# Ultra fast XGBoost
log("\n🏃 Training...")
start = datetime.now()

model = XGBClassifier(
    n_estimators=100,  # Increased for better accuracy
    max_depth=12,      # Deeper trees
    learning_rate=0.1,
    n_jobs=-1,
    random_state=42
)

model.fit(X_train, y_train)
elapsed = (datetime.now() - start).total_seconds()

log(f"✅ Training: {elapsed:.0f}s")

# Evaluate with HYBRID approach (rules + ML)
def apply_rules_single(row, icp_funding_amounts=None):
    """Apply business rules to a single row. UPDATED WITH NEW RULES."""
    desc = str(row['description']).upper()
    acc = int(row['origination_account_id']) if pd.notna(row['origination_account_id']) else 0
    amt = float(row['amount'])
    pm = int(row['payment_method']) if pd.notna(row['payment_method']) else -1
    
    # PRIORITY ORDER (HIGHEST TO LOWEST)
    
    # 1. Payment Method 12 = ZBT
    if pm == 12:
        return 'ZBT'
    # 2. NIUM = Nium Payment
    elif 'NIUM' in desc:
        return 'Nium Payment'
    # 3. ICP Funding - Chase ICP + JPMORGAN ACCESS TRANSFER FROM
    elif acc == 21 and 'REMARK=JPMORGAN ACCESS TRANSFER FROM' in desc:
        return 'ICP Funding'
    # 4. ICP Funding - Paired transaction (same amount + JPMORGAN)
    elif icp_funding_amounts and amt in icp_funding_amounts and 'REMARK=JPMORGAN ACCESS TRANSFER' in desc:
        return 'ICP Funding'
    # 5. 1TRV = RISK (ANY ACCOUNT - HIGHEST PRIORITY)
    elif '1TRV' in desc:
        return 'Risk'
    # 6. STATE rules
    elif 'STATE OF MONTANA' in desc:
        return 'MT WH'
    elif 'NYS DTF WT' in desc:
        return 'NY WH'
    elif 'NYS DOL UI' in desc:
        return 'NY UI'
    # 7. Treasury/Money Market
    elif '100% US TREASURY CAPITAL 3163' in desc or 'MONEY MKT MUTUAL FUND' in desc:
        return 'Money Market Transfer'
    elif 'JPMORGAN ACCESS TRANSFER' in desc:
        return 'Treasury Transfer'
    elif 'INTEREST ADJUSTMENT' in desc:
        return 'Interest Adjustment'
    # 8. Account-specific rules
    elif acc == 16 and 'CREDIT MEMO' in desc:
        return 'PNC LOI'
    elif 'KEYSTONE' in desc:
        return 'PA UI'
    elif pm == 2:
        return 'Check'
    elif pm == 4:
        return 'ACH'
    # 9. Recovery accounts (WITHOUT 1TRV)
    elif acc in [7, 28]:
        if 'INTEREST' in desc:
            return 'Interest Payment'
        else:
            return 'Recovery Wire'
    # 10. Risk accounts
    elif acc in [6, 9, 18] and pm == 0:
        return 'Risk'
    # 11. Blueridge Operations
    elif acc == 26:
        if amt < 0.5:
            return 'Bad Debt'
        else:
            return 'BRB'
    elif amt < 0.5 and amt > 0:
        return 'Bad Debt'
    # 12. Other patterns
    elif 'LOCKBOX' in desc:
        return 'Lockbox'
    elif 'TS FX ACCOUNTS RECEIVABLE' in desc or 'JPV' in desc:
        return 'ICP Return'
    elif 'WISE' in desc and amt < 50000:
        return 'ICP Refund'
    elif 'YORK ADAMS' in desc:
        return 'York Adams Tax'
    return None

# Hybrid prediction for test
y_pred_test_ml = model.predict(X_test)
y_pred_test_hybrid = []
for i, idx in enumerate(test_data.index):
    rule_pred = apply_rules_single(test_data.loc[idx], icp_funding_amounts)
    if rule_pred and rule_pred in le_agent.classes_:
        y_pred_test_hybrid.append(le_agent.transform([rule_pred])[0])
    else:
        y_pred_test_hybrid.append(y_pred_test_ml[i])

# Hybrid prediction for validation
y_pred_val_ml = model.predict(X_val)
y_pred_val_hybrid = []
for i, idx in enumerate(val_data.index):
    rule_pred = apply_rules_single(val_data.loc[idx], icp_funding_amounts)
    if rule_pred and rule_pred in le_agent.classes_:
        y_pred_val_hybrid.append(le_agent.transform([rule_pred])[0])
    else:
        y_pred_val_hybrid.append(y_pred_val_ml[i])

acc_test = accuracy_score(y_test, y_pred_test_hybrid) * 100
acc_val = accuracy_score(y_val, y_pred_val_hybrid) * 100

log(f"✅ Test (Hybrid): {acc_test:.2f}%")
log(f"✅ Validation (Hybrid): {acc_val:.2f}%")

# Test prediction time for 1 BT
log("\n⚡ Testing prediction time (1 BT)...")
test_sample = val_data.head(1)
X_sample_tfidf = tfidf.transform(test_sample['description'].fillna(''))
X_sample_ex = extract_features(test_sample)
X_sample = hstack([X_sample_tfidf, X_sample_ex.values])

# Test 10 times and average
times = []
for i in range(10):
    start = datetime.now()
    pred = model.predict(X_sample)
    elapsed_ms = (datetime.now() - start).total_seconds() * 1000
    times.append(elapsed_ms)

avg_time = np.mean(times)
max_time = np.max(times)

log(f"✅ Avg prediction: {avg_time:.2f}ms")
log(f"✅ Max prediction: {max_time:.2f}ms")

# Result
log("\n" + "=" * 80)
log("🏆 RESULTS")
log("=" * 80)
log(f"📊 Test: {acc_test:.2f}%")
log(f"📊 Validation: {acc_val:.2f}%")
log(f"⚡ Prediction: {avg_time:.2f}ms avg, {max_time:.2f}ms max")

if max_time < 40000:  # 40 seconds = 40000 ms
    log(f"✅ SPEED OK! {max_time:.2f}ms < 40000ms")
else:
    log(f"❌ TOO SLOW! {max_time:.2f}ms > 40000ms")

if acc_val >= 95.0:
    log("✅ ACCURACY OK! >= 95%")
else:
    log(f"⚠️  Accuracy: {acc_val:.2f}% (target: 95%)")

# Save
log("\n💾 Saving...")
joblib.dump(model, 'ultra_fast_model.pkl')
joblib.dump(tfidf, 'ultra_fast_tfidf.pkl')
joblib.dump(le_agent, 'ultra_fast_agent_encoder.pkl')
log("✅ Done!")

log("\n" + "=" * 80)
log("✅ COMPLETE!")
log("=" * 80)
