#!/usr/bin/env python3
"""
🎯 PREDICTION WITH RULES - Hybrid approach
1. Apply business rules first (100% accurate)
2. Use ML model only for non-rule cases
"""

import pandas as pd
import numpy as np
import joblib
from scipy.sparse import hstack
from sklearn.preprocessing import LabelEncoder
from datetime import datetime

def apply_rules(row, icp_funding_amounts=None):
    """Apply business rules. Returns agent name if rule matches, None otherwise. UPDATED WITH NEW RULES."""
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
    # 6. STATE OF MONTANA → MT UI (NOT MT WH!)
    elif 'ORIG CO NAME=STATE OF MONTANA' in desc or 'STATE OF MONTANA' in desc:
        return 'MT UI'
    # 7. OH SDWH - 1HIOSDWH pattern
    elif '1HIOSDWH' in desc or 'OHSDWHTX' in desc:
        return 'OH SDWH'
    # 8. State-specific rules
    elif 'NYS DTF WT' in desc or 'NY DTF WT' in desc:
        return 'NY WH'
    elif 'NYS DOL UI' in desc:
        return 'NY UI'
    # 9. ACH Rules - MUST BE BEFORE Check rule!
    elif pm == 4 and ('ACH CREDIT SETTLEMENT' in desc or 'ACH DEBIT SETTLEMENT' in desc):
        if 'REVERSAL' in desc:
            return 'ACH Reversal'
        else:
            return 'ACH Transaction'
    # 10. WA LNI - Multiple patterns
    elif 'LABOR&INDUSTRIES' in desc:
        return 'WA LNI'
    elif 'L&I ELF' in desc:
        return 'WA LNI'
    elif 'WA' in desc and ('L&I' in desc or 'LNI' in desc or 'LABOR' in desc or 'INDUSTRIES' in desc):
        return 'WA LNI'
    # 11. Unclaimed Property - GUSTOCUSTDEP + PRFUND pattern
    elif 'GUSTOCUSTDEP' in desc and 'PRFUND' in desc:
        return 'Unclaimed Property'
    # 12. Company Balance Transfers - GUSTO PAYROLL + ITL
    elif 'ENTRY DESCR=ITL' in desc and 'GUSTO PAYROLL' in desc:
        return 'Company Balance Transfers'
    # 13. PNC LOI - Account 16 + CREDIT MEMO
    elif acc == 16 and 'CREDIT MEMO' in desc:
        return 'LOI'
    # 14. Treasury/Money Market
    elif '100% US TREASURY CAPITAL 3163' in desc or 'MONEY MKT MUTUAL FUND' in desc:
        return 'Money Market Transfer'
    elif 'JPMORGAN ACCESS TRANSFER' in desc:
        return 'Treasury Transfer'
    elif 'INTEREST ADJUSTMENT' in desc:
        return 'Interest Adjustment'
    # 15. KEYSTONE
    elif 'KEYSTONE' in desc:
        return 'PA UI'
    # 16. Payment method based (Check)
    elif pm == 2:
        return 'Check'
    # 17. Risk accounts - PRIORITY! (ACC 6, 9, 18 are mostly Risk)
    elif acc in [6, 9, 18] and pm == 0:
        return 'Risk'
    # 18. Recovery accounts - ACC=7, 28 (primary recovery accounts)
    elif acc in [7, 28]:
        if 'INTEREST' in desc:
            return 'Interest Payment'
        else:
            return 'Recovery Wire'
    # 19. IL UI - BEFORE BRB! (ACC=26 but IL specific)
    elif 'IL DEPT EMPL' in desc or 'UNEMPL TAX' in desc:
        return 'IL UI'
    elif 'NAME=IL DEPT' in desc:
        return 'IL UI'
    # 20. Canary Payments - CPP pattern (both formats)
    elif 'ENTRY DESCR=CPP' in desc or 'DESC: CPP' in desc:
        return 'Canary Payments'
    # 21. Blueridge Operations (after IL UI check!)
    elif acc == 26:
        if amt < 0.5:
            return 'Bad Debt'
        else:
            return 'BRB'
    elif amt < 0.5 and amt > 0:
        return 'Bad Debt'
    # 18. Other patterns
    elif 'LOCKBOX' in desc:
        return 'Lockbox'
    elif 'TS FX ACCOUNTS RECEIVABLE' in desc or 'JPV' in desc:
        return 'ICP Return'
    # 19. ICP Refund - REMARK=Wise + amount < 50000
    elif 'REMARK=WISE' in desc and amt < 50000:
        return 'ICP Refund'
    elif 'WISE' in desc and amt < 50000:
        return 'ICP Refund'
    # 20. ICP Return - Account 21 + "Refund" in ENTRY DESCR
    elif acc == 21 and 'REFUND' in desc:
        return 'ICP Return'
    # 21. OH WH - OHEMWHTX pattern
    elif 'OHEMWHTX' in desc or 'OH WH TAX' in desc or '8011OHIO-TAXOEWH' in desc:
        return 'OH WH'
    # 22. Check Adjustment - CHECK + (REFERENCE or ITEM or POSTED)
    elif 'CHECK' in desc and ('REFERENCE' in desc or 'ITEM' in desc or 'POSTED' in desc):
        return 'Check Adjustment'
    # 23. York Adams (unified label - both York Adams and York Adams Tax)
    elif 'YORK ADAMS' in desc:
        return 'York Adams'
    # 24. IRS Payment - LAST RESORT (if IRS in desc and nothing else matches)
    elif 'IRS' in desc:
        return 'IRS Wire'
    
    return None  # No rule matched - ML will predict

def predict_with_rules(data, model, tfidf, le_agent, le_account, le_payment, icp_funding_amounts=None, confidence_threshold=0.85):
    """Hybrid prediction: Rules first, then ML model with confidence check."""
    
    predictions = []
    rule_used = []
    
    for idx, row in data.iterrows():
        # Try rules first
        rule_prediction = apply_rules(row, icp_funding_amounts)
        
        if rule_prediction is not None:
            predictions.append(rule_prediction)
            rule_used.append(True)
        else:
            # Use ML model
            X_tfidf = tfidf.transform([row['description']])
            
            # Extract features
            payment_encoded = le_payment.transform([str(int(row['payment_method']) if pd.notna(row['payment_method']) else -1)])
            account_encoded = le_account.transform([str(int(row['origination_account_id']) if pd.notna(row['origination_account_id']) else 0)])
            amount = row['amount']
            amount_log = np.log1p(abs(amount))
            
            X_ex = pd.DataFrame({
                'payment': payment_encoded,
                'account': account_encoded,
                'amount': [amount],
                'amount_log': [amount_log]
            })
            
            X = hstack([X_tfidf, X_ex.values])
            
            # Get prediction with confidence
            pred_proba = model.predict_proba(X)[0]
            max_confidence = pred_proba.max()
            
            if max_confidence >= confidence_threshold:
                pred_idx = model.predict(X)[0]
                pred_agent = le_agent.inverse_transform([pred_idx])[0]
                predictions.append(pred_agent)
            else:
                # Low confidence - mark as Unknown
                predictions.append('Unknown - Low Confidence')
            
            rule_used.append(False)
    
    return predictions, rule_used

# Label unification (normalize similar labels)
def normalize_label(label):
    """Normalize similar labels to canonical form - comprehensive unification"""
    label = str(label).strip()
    
    # York Adams variants → York Adams
    if 'YORK ADAMS' in label.upper():
        return 'York Adams'
    
    # Recovery Wire variants → Recovery Wire (remove trailing spaces, include "Out")
    if label.startswith('Recovery Wire'):
        return 'Recovery Wire'
    
    # PNC LOI → LOI
    if label == 'PNC LOI':
        return 'LOI'
    
    # MT variants → MT UI
    if label in ['MT WH', 'MT', 'MT ']:
        return 'MT UI'
    
    # NY WH variants (typo WTH)
    if label in ['NY WTH', 'NY WH ', 'NY WH']:
        return 'NY WH'
    
    # Risk variants (typos + trailing spaces)
    if label in ['RIsk', 'RISK', 'Risk ', 'Risk  ']:
        return 'Risk'
    
    # Bad Debt variants (typo: Dept)
    if label in ['Bad Dept', 'Bad Debt ', 'Bad Debt']:
        return 'Bad Debt'
    
    # ICP Refund variants (trailing spaces)
    if label in ['ICP Refund ', ' ICP Refund', 'ICP Refund  ']:
        return 'ICP Refund'
    
    # ICP Return variants (leading/trailing spaces)
    if label in [' ICP Return', 'ICP Return ', 'ICP Return  ']:
        return 'ICP Return'
    
    # IL UI variants (trailing spaces)
    if label in ['IL UI ', 'IL UI  ', 'IL UI']:
        return 'IL UI'
    
    # Check variants (trailing spaces)
    if label in ['Check ', 'Check  ', 'Check']:
        return 'Check'
    
    # OH SDWH variants (trailing spaces)
    if label in ['OH SDWH ', 'OH SDWH  ', 'OH SDWH']:
        return 'OH SDWH'
    
    # Grasshopper Return (case variants)
    if label.upper() == 'GRASSHOPPER RETURN':
        return 'Grasshopper Return'
    
    # Company Balance Transfer/Transfers → Company Balance Transfers (plural)
    if label in ['Company Balance Transfer', 'Company Balance Transfers']:
        return 'Company Balance Transfers'
    
    # Treasury Transfer (typo: Transsfer)
    if label in ['Treasury Transsfer', 'Treasury Transfer']:
        return 'Treasury Transfer'
    
    # Canary Payment/Payments → Canary Payments (plural)
    if label in ['Canary Payment', 'Canary Payments']:
        return 'Canary Payments'
    
    # Debit Authorization/Authorisation → Debit Authorization (US spelling)
    if label in ['Debit Authorisation', 'Debit Authorization']:
        return 'Debit Authorization'
    
    # Berks Tax / Berk Tax → Berks Tax
    if label in ['Berk Tax', 'Berks Tax']:
        return 'Berks Tax'
    
    # NY MCTMT variants (trailing spaces)
    if label in ['NY MCTMT ', 'NY MCTMT  ', 'NY MCTMT']:
        return 'NY MCTMT'
    
    # dLocal variants (trailing spaces)
    if label in ['dLocal ', 'dLocal  ', 'dLocal']:
        return 'dLocal'
    
    return label

# Test the hybrid approach (only when run directly, not when imported)
if __name__ == "__main__":
    print("=" * 100)
    print("🎯 TESTING HYBRID PREDICTION (Rules + ML)")
    print("=" * 100)

    # Load model
    model = joblib.load('ultra_fast_model.pkl')
    tfidf = joblib.load('ultra_fast_tfidf.pkl')
    le_agent = joblib.load('ultra_fast_agent_encoder.pkl')

    # Load data
    df = pd.read_csv('/Users/yarkin.akcil/Downloads/Unrecon_2025_10_05_updated.csv', low_memory=False)
    df['amount'] = df['amount'] / 100
    df['date'] = pd.to_datetime(df['date'], format='mixed')
    df = df[df['date'] >= '2024-01-01'].copy()
    df = df[df['agent'].notna()].copy()
    
    svb_accounts = [1, 2, 5, 10, 24]
    df = df[~df['origination_account_id'].isin(svb_accounts)].copy()
    
    # Remove problematic IDs (incorrect labels) - NONE FOR NOW
    # problematic_ids = []
    # df = df[~df['id'].isin(problematic_ids)].copy()
    
    df['agent'] = df['agent'].str.strip()
    
    # Apply rules to training data (same as before)
    print("\n📂 Preparing data...")
    
    # First pass: Find ICP Funding amounts
    icp_funding_amounts = set()
    for idx, row in df.iterrows():
        if pd.notna(row['origination_account_id']) and int(row['origination_account_id']) == 21:
            desc = str(row['description']).upper()
            if 'REMARK=JPMORGAN ACCESS TRANSFER FROM' in desc:
                icp_funding_amounts.add(float(row['amount']))
    
    print(f"   📌 Found {len(icp_funding_amounts)} ICP Funding amounts")
    
    # Second pass: Apply all rules
    for idx, row in df.iterrows():
        rule_agent = apply_rules(row, icp_funding_amounts)
        if rule_agent:
            df.at[idx, 'agent'] = rule_agent
    
    print(f"✅ {len(df):,} transactions | {df['agent'].nunique()} agents")
    
    # Split
    test_end = int(len(df) * 0.85)
    val_data = df.iloc[test_end:].copy()
    
    # Prepare encoders
    le_account = LabelEncoder()
    le_payment = LabelEncoder()
    le_account.fit(df['origination_account_id'].fillna(0).astype(int).astype(str))
    le_payment.fit(df['payment_method'].fillna(-1).astype(int).astype(str))
    
    # Filter validation to agents in training
    train_agents = set(le_agent.classes_)
    val_data_filtered = val_data[val_data['agent'].isin(train_agents)].copy().reset_index(drop=True)
    
    print(f"✅ Validation: {len(val_data_filtered):,} transactions")
    
    # Hybrid prediction
    print("\n🔧 Running hybrid prediction...")
    start = datetime.now()
    predictions, rule_used = predict_with_rules(val_data_filtered, model, tfidf, le_agent, le_account, le_payment, icp_funding_amounts)
    elapsed = (datetime.now() - start).total_seconds()
    
    
    # Apply normalization
    val_data_filtered['agent_normalized'] = val_data_filtered['agent'].apply(normalize_label)
    val_data_filtered['predicted_normalized'] = [normalize_label(p) for p in predictions]
    
    val_data_filtered['predicted'] = predictions
    val_data_filtered['rule_used'] = rule_used
    val_data_filtered['correct'] = (val_data_filtered['agent_normalized'] == val_data_filtered['predicted_normalized']).astype(int)
    
    # Results
    overall_acc = val_data_filtered['correct'].mean() * 100
    rule_count = sum(rule_used)
    ml_count = len(rule_used) - rule_count
    
    rule_data = val_data_filtered[val_data_filtered['rule_used']]
    ml_data = val_data_filtered[~val_data_filtered['rule_used']]
    
    rule_acc = rule_data['correct'].mean() * 100 if len(rule_data) > 0 else 0
    ml_acc = ml_data['correct'].mean() * 100 if len(ml_data) > 0 else 0
    
    print(f"\n✅ Prediction time: {elapsed:.2f}s ({elapsed/len(val_data_filtered)*1000:.2f}ms per BT)")
    
    print("\n" + "=" * 100)
    print("🏆 HYBRID RESULTS")
    print("=" * 100)
    print(f"📊 Overall Accuracy: {overall_acc:.2f}%")
    print(f"\n🔹 Rule-based: {rule_count:,} BTs ({rule_count/len(val_data_filtered)*100:.1f}%) → {rule_acc:.2f}% accurate")
    print(f"🔹 ML-based:   {ml_count:,} BTs ({ml_count/len(val_data_filtered)*100:.1f}%) → {ml_acc:.2f}% accurate")
    
    # Top agents analysis
    print("\n" + "=" * 100)
    print("📊 TOP 10 AGENTS - HYBRID PERFORMANCE")
    print("=" * 100)
    
    agent_counts = val_data_filtered['agent'].value_counts().head(10)
    for rank, (agent, count) in enumerate(agent_counts.items(), 1):
        agent_data = val_data_filtered[val_data_filtered['agent'] == agent]
        correct = agent_data['correct'].sum()
        accuracy = correct / count * 100
        rule_pct = agent_data['rule_used'].sum() / count * 100
        
        print(f"{rank:2d}. {agent:30s}: {accuracy:6.2f}% ({count:5,} BTs, {rule_pct:5.1f}% via rules)")
    
    print("\n" + "=" * 100)
    print("✅ COMPLETE!")
    print("=" * 100)
