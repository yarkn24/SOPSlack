#!/usr/bin/env python3
"""
Test Vercel API performance with 20 sample transactions
Simulates production environment
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

# Import Vercel API logic
from api.predict import predict_transaction

# Sample 20 transactions (same as top_20_labels.py)
test_transactions = [
    {
        "transaction_id": "59315257",
        "amount": "$5,100.00",
        "date": "10/14/2025",
        "payment_method": "wire in",
        "origination_account_id": "Chase Wire In",
        "description": "YOUR REF=POH OF 25/10/14,REC FROM=00000000730103207 CHELSEA N SARVER 5605 SCURTICE ST UNIT A LITTLETON CO 80120-1188 US,REMARK=1TRVXX9QP28C DEBIT REF POH OF"
    },
    {
        "transaction_id": "59318456",
        "amount": "$1,250.00",
        "date": "10/14/2025",
        "payment_method": "Check",
        "origination_account_id": "Chase Operations",
        "description": "CHECK PAID 00123456789 PAYEE: ABC COMPANY"
    },
    {
        "transaction_id": "59319234",
        "amount": "$850.00",
        "date": "10/14/2025",
        "payment_method": "wire in",
        "origination_account_id": "Chase Operations",
        "description": "NYS DTF WT WITHHOLDING TAX PAYMENT"
    },
    {
        "transaction_id": "59319567",
        "amount": "$620.00",
        "date": "10/14/2025",
        "payment_method": "wire in",
        "origination_account_id": "Chase Operations",
        "description": "OH WH TAX WITHHOLDING PAYMENT STATE OF OHIO"
    },
    {
        "transaction_id": "59321123",
        "amount": "$1,200.00",
        "date": "10/14/2025",
        "payment_method": "wire in",
        "origination_account_id": "Chase Operations",
        "description": "NYS DOL UI UNEMPLOYMENT INSURANCE PAYMENT"
    },
    {
        "transaction_id": "59318890",
        "amount": "$345.00",
        "date": "10/14/2025",
        "payment_method": "wire in",
        "origination_account_id": "Chase Operations",
        "description": "DESC=CSC123456 CHILD SUPPORT PAYMENT"
    },
    {
        "transaction_id": "59319890",
        "amount": "$25,000.00",
        "date": "10/14/2025",
        "payment_method": "wire in",
        "origination_account_id": "Chase International Contractor Payment",
        "description": "TRANSFER FROM ACCOUNT000000807737908 REMARK=JPMORGAN ACCESS TRANSFER"
    },
    {
        "transaction_id": "59321789",
        "amount": "$100.00",
        "date": "10/14/2025",
        "payment_method": "wire in",
        "origination_account_id": "Chase Operations",
        "description": "REMARK=ACH RETURN SETTLEMENT"
    },
    {
        "transaction_id": "59320456",
        "amount": "$15.00",
        "date": "10/14/2025",
        "payment_method": "wire in",
        "origination_account_id": "Chase Operations",
        "description": "LOCKBOX PAYMENT PROCESSING FEE"
    },
    {
        "transaction_id": "59320789",
        "amount": "$430.00",
        "date": "10/14/2025",
        "payment_method": "wire in",
        "origination_account_id": "Chase Operations",
        "description": "OH SDWH STATE TAX PAYMENT OHIO"
    },
    {
        "transaction_id": "59321456",
        "amount": "$550.00",
        "date": "10/14/2025",
        "payment_method": "wire in",
        "origination_account_id": "Chase Operations",
        "description": "STATE OF MONTANA UNEMPLOYMENT TAX"
    },
    {
        "transaction_id": "59322100",
        "amount": "$780.00",
        "date": "10/14/2025",
        "payment_method": "wire in",
        "origination_account_id": "Chase Operations",
        "description": "IL DEPT EMPL SEC UNEMPLOYMENT INSURANCE"
    },
    {
        "transaction_id": "59322200",
        "amount": "$920.00",
        "date": "10/14/2025",
        "payment_method": "wire in",
        "origination_account_id": "Chase Operations",
        "description": "STATE OF WA ESD UNEMPLOYMENT TAX"
    },
    {
        "transaction_id": "59322300",
        "amount": "$250.00",
        "date": "10/14/2025",
        "payment_method": "wire in",
        "origination_account_id": "Chase Operations",
        "description": "REMARK=EFT REVERSAL PAYMENT RETURN"
    },
    {
        "transaction_id": "59322400",
        "amount": "$180.00",
        "date": "10/14/2025",
        "payment_method": "wire in",
        "origination_account_id": "Chase Operations",
        "description": "RTN OFFSET RETURN PAYMENT"
    },
    {
        "transaction_id": "59322123",
        "amount": "$50,000.00",
        "date": "10/14/2025",
        "payment_method": "wire in",
        "origination_account_id": "Chase Operations",
        "description": "MONEY MKT MUTUAL FUND TRANSFER"
    },
    {
        "transaction_id": "59322456",
        "amount": "$100,000.00",
        "date": "10/14/2025",
        "payment_method": "wire in",
        "origination_account_id": "Chase Operations",
        "description": "US TREASURY CAPITAL TRANSFER"
    },
    {
        "transaction_id": "59322500",
        "amount": "$340.00",
        "date": "10/14/2025",
        "payment_method": "wire in",
        "origination_account_id": "Chase Operations",
        "description": "L&I LABOR&INDUSTRIES TAX PAYMENT"
    },
    {
        "transaction_id": "59322600",
        "amount": "$0.03",
        "date": "10/14/2025",
        "payment_method": "wire in",
        "origination_account_id": "Chase Operations",
        "description": "MICROVARIANCE ADJUSTMENT"
    },
    {
        "transaction_id": "59322700",
        "amount": "$690.00",
        "date": "10/14/2025",
        "payment_method": "wire in",
        "origination_account_id": "Chase Operations",
        "description": "VA. EMPLOY COMM UNEMPLOYMENT INSURANCE"
    }
]

def main():
    print("\n" + "="*80)
    print("🧪 VERCEL PERFORMANCE TEST - 20 Transactions")
    print("="*80)
    print(f"\nTesting {len(test_transactions)} transactions...\n")
    
    results = {
        'tier_1_rule_based': 0,
        'tier_2_ml_model': 0,
        'tier_3_gemini': 0,
        'correct_predictions': 0,
        'total': len(test_transactions)
    }
    
    expected_labels = {
        "59315257": "Risk",
        "59318456": "Check",
        "59319234": "NY WH",
        "59319567": "OH WH",
        "59321123": "NY UI",
        "59318890": "CSC",
        "59319890": "ICP Funding",
        "59321789": "LOI",
        "59320456": "Lockbox",
        "59320789": "OH SDWH",
        "59321456": "MT UI",
        "59322100": "IL UI",
        "59322200": "WA ESD",
        "59322300": "ACH",
        "59322400": "ACH Return",
        "59322123": "Money Market Fund",
        "59322456": "Treasury Transfer",
        "59322500": "WA LNI",
        "59322600": "Bad Debt",
        "59322700": "VA UI"
    }
    
    for i, txn in enumerate(test_transactions, 1):
        txn_id = txn['transaction_id']
        expected = expected_labels.get(txn_id, "Unknown")
        
        # Predict using Vercel API logic
        label, method, reason, confidence = predict_transaction(txn)
        
        # Track tier used
        if 'rule-based' in method:
            results['tier_1_rule_based'] += 1
            tier = "Tier 1"
        elif 'Trained Model' in method:
            results['tier_2_ml_model'] += 1
            tier = "Tier 2"
        else:
            results['tier_3_gemini'] += 1
            tier = "Tier 3"
        
        # Check if correct
        is_correct = label == expected
        if is_correct:
            results['correct_predictions'] += 1
            status = "✅"
        else:
            status = "❌"
        
        print(f"{status} {i:2d}. ID:{txn_id} | Expected:{expected:20s} | Got:{label:20s} | {tier} | {confidence:.0%}")
    
    # Calculate accuracy
    accuracy = (results['correct_predictions'] / results['total']) * 100
    
    print("\n" + "="*80)
    print("📊 PERFORMANCE RESULTS")
    print("="*80)
    print(f"\n✅ Correct Predictions: {results['correct_predictions']}/{results['total']}")
    print(f"🎯 Accuracy: {accuracy:.1f}%")
    print(f"\n📈 Tier Usage:")
    print(f"   Tier 1 (Rule-Based):   {results['tier_1_rule_based']:2d} ({results['tier_1_rule_based']/results['total']*100:.0f}%)")
    print(f"   Tier 2 (ML Model):     {results['tier_2_ml_model']:2d} ({results['tier_2_ml_model']/results['total']*100:.0f}%)")
    print(f"   Tier 3 (Gemini AI):    {results['tier_3_gemini']:2d} ({results['tier_3_gemini']/results['total']*100:.0f}%)")
    
    print("\n" + "="*80)
    if accuracy >= 98:
        print("🎉 PERFORMANCE TEST PASSED! (%98+ accuracy achieved)")
    elif accuracy >= 95:
        print("✅ GOOD PERFORMANCE! (95%+ accuracy)")
    elif accuracy >= 90:
        print("⚠️  ACCEPTABLE PERFORMANCE (90%+)")
    else:
        print("❌ PERFORMANCE BELOW TARGET (<90%)")
    print("="*80 + "\n")
    
    return accuracy >= 98

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

