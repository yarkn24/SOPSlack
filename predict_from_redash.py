"""
Predict Agents from Redash Data (Production)
=============================================
Fetches unlabeled data from Redash and predicts agents.

Usage:
    python predict_from_redash.py
"""

import pandas as pd
from redash_auto_fetch import RedashAutoFetcher
from data_mapping import (
    map_payment_method, 
    map_account, 
    is_corporate_account,
    PAYMENT_METHOD_REVERSE,
    ACCOUNT_REVERSE
)
import joblib
import scipy.sparse as sp

print("=" * 80)
print("REDASH → ML PREDICTION PIPELINE")
print("=" * 80)
print()

# ============================================================================
# STEP 1: FETCH DATA FROM REDASH
# ============================================================================

print("📊 Step 1: Fetching data from Redash...")
fetcher = RedashAutoFetcher()
df = fetcher.fetch_fresh_data()

if len(df) == 0:
    print("⚠️  No transactions to predict!")
    exit(0)

print(f"✅ Loaded {len(df)} transactions")
print()

# ============================================================================
# STEP 2: FILTER OUT CORPORATE ACCOUNTS
# ============================================================================

print("🔍 Step 2: Filtering corporate accounts...")
df['is_corporate'] = df['account'].apply(is_corporate_account)
corporate_count = df['is_corporate'].sum()

if corporate_count > 0:
    print(f"   ⚠️  Skipping {corporate_count} corporate account transactions")
    df = df[~df['is_corporate']].copy()

print(f"✅ {len(df)} transactions to predict")
print()

# ============================================================================
# STEP 3: CONVERT TO ML FORMAT
# ============================================================================

print("🔄 Step 3: Converting to ML format...")

# Convert text → numeric
df['payment_method_numeric'] = df['payment_method'].apply(map_payment_method)
df['origination_account_numeric'] = df['account'].apply(map_account)

# Handle unknown mappings
unknown_pm = df[df['payment_method_numeric'] == 8]
unknown_acc = df[df['origination_account_numeric'] == 0]

if len(unknown_pm) > 0:
    print(f"   ⚠️  {len(unknown_pm)} transactions with unknown payment method")
    
if len(unknown_acc) > 0:
    print(f"   ⚠️  {len(unknown_acc)} transactions with unknown account")

print("✅ Format converted")
print()

# ============================================================================
# STEP 4: LOAD ML MODEL
# ============================================================================

print("🤖 Step 4: Loading ML model...")

try:
    model = joblib.load('ultra_fast_model.pkl')
    label_encoder = joblib.load('label_encoder.pkl')
    tfidf_vectorizer = joblib.load('tfidf_vectorizer.pkl')
    pm_encoder = joblib.load('pm_encoder.pkl')
    acc_encoder = joblib.load('acc_encoder.pkl')
    print("✅ Model loaded (98.64% accuracy)")
except FileNotFoundError as e:
    print(f"❌ Model files not found: {e}")
    print("   Run ultra_fast_training.py first!")
    exit(1)

print()

# ============================================================================
# STEP 5: APPLY BUSINESS RULES (Hybrid Approach)
# ============================================================================

print("🔧 Step 5: Applying business rules...")

def apply_rules(desc, amount, pm, acc, icp_funding_amounts):
    """Apply business rules before ML prediction."""
    desc = str(desc).upper()
    
    # Priority 1: 1TRV = Risk
    if '1TRV' in desc:
        return 'Risk'
    
    # Priority 2: PM = 12 = ZBT
    if pm == 12:
        return 'ZBT'
    
    # Priority 3: NIUM
    if 'NIUM' in desc:
        return 'Nium Payment'
    
    # Priority 4: ICP Funding
    if acc == 21 and 'REMARK=JPMORGAN ACCESS TRANSFER FROM' in desc:
        return 'ICP Funding'
    if amount in icp_funding_amounts and 'REMARK=JPMORGAN ACCESS TRANSFER' in desc:
        return 'ICP Funding'
    
    # Priority 5: Account-based
    if acc in [7, 28]:
        return 'Recovery Wire'
    
    if acc == 16 and 'CREDIT MEMO' in desc:
        return 'PNC LOI'
    
    # State taxes
    if 'NYS DTF WT' in desc or 'NY DTF WT' in desc:
        return 'NY WH'
    if 'NYS DOL UI' in desc:
        return 'NY UI'
    if 'STATE OF MONTANA' in desc:
        return 'MT WH'
    if 'KEYSTONE' in desc:
        return 'PA UI'
    
    # Treasury/Money Market
    if 'REMARK=JPMORGAN ACCESS TRANSFER' in desc and acc != 21:
        return 'Treasury Transfer'
    if 'MONEY MKT MUTUAL FUND' in desc or 'REMARK=100% US TREASURY CAPITAL' in desc:
        return 'Money Market Transfer'
    
    # Interest
    if 'INTEREST ADJUSTMENT' in desc:
        return 'Interest Adjustment'
    
    # ICP Returns
    if 'TS FX ACCOUNTS RECEIVABLE' in desc and 'JPV' in desc:
        return 'ICP Return'
    
    # Payment method based
    if pm == 4:
        return 'ACH'
    if pm == 2:
        return 'Check'
    
    return None  # No rule matched, use ML

# Calculate ICP funding amounts
icp_funding_amounts = set()
for _, row in df.iterrows():
    if (row['origination_account_numeric'] == 21 and 
        'REMARK=JPMORGAN ACCESS TRANSFER FROM' in str(row['description']).upper()):
        icp_funding_amounts.add(row['amount'])

# Apply rules
predictions = []
rule_based_count = 0

for _, row in df.iterrows():
    rule_agent = apply_rules(
        row['description'],
        row['amount'],
        row['payment_method_numeric'],
        row['origination_account_numeric'],
        icp_funding_amounts
    )
    
    if rule_agent:
        predictions.append(rule_agent)
        rule_based_count += 1
    else:
        predictions.append(None)  # ML will predict

print(f"✅ Rules matched: {rule_based_count}/{len(df)} transactions")
print()

# ============================================================================
# STEP 6: ML PREDICTION (for non-rule matches)
# ============================================================================

print("🤖 Step 6: ML prediction for remaining...")

ml_indices = [i for i, pred in enumerate(predictions) if pred is None]
print(f"   Predicting {len(ml_indices)} transactions with ML")

if len(ml_indices) > 0:
    # Prepare features for ML
    ml_df = df.iloc[ml_indices].copy()
    
    # TF-IDF on descriptions
    desc_features = tfidf_vectorizer.transform(ml_df['description'])
    
    # Encode payment methods
    pm_features = pm_encoder.transform(ml_df[['payment_method_numeric']])
    
    # Encode accounts
    acc_features = acc_encoder.transform(ml_df[['origination_account_numeric']])
    
    # Combine features
    X = sp.hstack([
        desc_features,
        sp.csr_matrix(ml_df[['amount']].values),
        sp.csr_matrix(pm_features),
        sp.csr_matrix(acc_features)
    ])
    
    # Predict
    ml_predictions = model.predict(X)
    ml_agents = label_encoder.inverse_transform(ml_predictions)
    
    # Fill in ML predictions
    for idx, agent in zip(ml_indices, ml_agents):
        predictions[idx] = agent

print(f"✅ ML prediction complete")
print()

# ============================================================================
# STEP 7: ADD PREDICTIONS TO DATAFRAME
# ============================================================================

df['predicted_agent'] = predictions

# ============================================================================
# STEP 8: SUMMARY
# ============================================================================

print("=" * 80)
print("PREDICTION SUMMARY")
print("=" * 80)
print()

agent_counts = df['predicted_agent'].value_counts()
print(f"📊 Predicted Agents ({len(agent_counts)} unique):")
for agent, count in agent_counts.head(10).items():
    print(f"   • {agent}: {count}")

print()
print(f"🎯 Breakdown:")
print(f"   Rule-based: {rule_based_count} ({rule_based_count/len(df)*100:.1f}%)")
print(f"   ML-based: {len(ml_indices)} ({len(ml_indices)/len(df)*100:.1f}%)")
print()

# Save results
output_file = f'predictions_{pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")}.csv'
df.to_csv(f'~/Desktop/cursor_data/{output_file}', index=False)
print(f"💾 Saved: ~/Desktop/cursor_data/{output_file}")
print()

print("🎉 Prediction complete!")

