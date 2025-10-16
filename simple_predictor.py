#!/usr/bin/env python3
"""
Simple Transaction Predictor
Clean input/output for manager demo
"""

import sys
from agent_sop_mapping import AGENT_SOP_MAPPING

def predict_label(narrative, amount, payment_method, account, date):
    """Simple rule-based prediction."""
    desc = str(narrative).upper()
    amt = float(str(amount).replace('$', '').replace(',', '')) if amount else 0
    pm = str(payment_method).upper()
    acc = str(account).upper()
    
    # Track which rule matched
    matched_rule = None
    prediction_type = None
    
    # Rule 1: Risk (1TRV pattern)
    if '1TRV' in desc:
        label = 'Risk'
        matched_rule = "Description contains '1TRV' code"
        prediction_type = "RULE-BASED"
    
    # Rule 2: NIUM
    elif 'NIUM' in desc:
        label = 'Nium Payment'
        matched_rule = "Description contains 'NIUM'"
        prediction_type = "RULE-BASED"
    
    # Rule 3: ICP Funding
    elif 'JPMORGAN ACCESS TRANSFER' in desc:
        label = 'ICP Funding'
        matched_rule = "Description contains 'JPMORGAN ACCESS TRANSFER'"
        prediction_type = "RULE-BASED"
    
    # Rule 4: State withholding
    elif 'NYS DTF WT' in desc or 'NY DTF WT' in desc:
        label = 'NY WH'
        matched_rule = "Description contains 'NYS DTF WT' or 'NY DTF WT'"
        prediction_type = "RULE-BASED"
    elif 'NYS DOL UI' in desc:
        label = 'NY UI'
        matched_rule = "Description contains 'NYS DOL UI'"
        prediction_type = "RULE-BASED"
    elif '1HIOSDWH' in desc or 'OHSDWHTX' in desc:
        label = 'OH SDWH'
        matched_rule = "Description contains '1HIOSDWH' or 'OHSDWHTX'"
        prediction_type = "RULE-BASED"
    elif 'STATE OF MONTANA' in desc:
        label = 'MT UI'
        matched_rule = "Description contains 'STATE OF MONTANA'"
        prediction_type = "RULE-BASED"
    elif 'CA EMPLOYMENT' in desc or 'CA EDD' in desc:
        label = 'CA WH'
        matched_rule = "Description contains 'CA EMPLOYMENT' or 'CA EDD'"
        prediction_type = "RULE-BASED"
    
    # Rule 5: Payroll
    elif 'PAYROLL' in desc or 'GUSTO' in desc:
        if 'WIRE' in pm or 'WIRE' in acc:
            label = 'Chase Payroll Incoming Wires'
            matched_rule = "Description contains 'PAYROLL'/'GUSTO' + Wire transfer"
        else:
            label = 'Payroll'
            matched_rule = "Description contains 'PAYROLL' or 'GUSTO'"
        prediction_type = "RULE-BASED"
    
    # Rule 6: Treasury/Money Market
    elif 'MONEY MARKET' in desc or 'MM SWEEP' in desc:
        label = 'Money Market Transfer'
        matched_rule = "Description contains 'MONEY MARKET' or 'MM SWEEP'"
        prediction_type = "RULE-BASED"
    elif 'TREASURY' in desc or 'SWEEP' in desc:
        label = 'Treasury Transfer'
        matched_rule = "Description contains 'TREASURY' or 'SWEEP'"
        prediction_type = "RULE-BASED"
    
    # Rule 7: Check
    elif 'CHECK' in pm or 'CHECK' in desc:
        label = 'Check'
        matched_rule = "Payment method or description contains 'CHECK'"
        prediction_type = "RULE-BASED"
    
    # Rule 8: ACH
    elif 'ACH' in pm or 'ACH' in desc:
        label = 'ACH'
        matched_rule = "Payment method or description contains 'ACH'"
        prediction_type = "RULE-BASED"
    
    # Rule 9: Returns
    elif 'RETURN' in desc or 'REVERSAL' in desc or 'REJECT' in desc:
        label = 'ICP Return'
        matched_rule = "Description contains 'RETURN', 'REVERSAL', or 'REJECT'"
        prediction_type = "RULE-BASED"
    
    # Rule 10: Wire (generic)
    elif 'WIRE' in pm or 'WIRE IN' in acc:
        if amt > 100000:
            label = 'ICP'
            matched_rule = "Wire transfer with amount > $100,000"
        else:
            label = 'Wire Transfer'
            matched_rule = "Wire transfer detected"
        prediction_type = "RULE-BASED"
    
    # No rule matched - would use ML
    else:
        label = 'Unknown - Would use ML'
        matched_rule = "No clear pattern match"
        prediction_type = "ML NEEDED"
    
    return label, matched_rule, prediction_type

def format_output(narrative, amount, payment_method, account, date):
    """Format clean output."""
    
    label, rule, pred_type = predict_label(narrative, amount, payment_method, account, date)
    
    output = []
    output.append("\n" + "="*80)
    output.append("TRANSACTION PREDICTION")
    output.append("="*80)
    
    # Input summary (compact)
    output.append(f"\nInput: ${amount} | {date} | {payment_method} | {account}")
    output.append(f"Narrative: {narrative[:100]}...")
    
    # Prediction
    output.append(f"\n{'─'*80}")
    output.append(f"\n✅ LABEL: {label}")
    output.append(f"\n📌 Why: {rule}")
    output.append(f"   Method: {pred_type}")
    
    # SOP Information (only if we have it)
    sop_info = AGENT_SOP_MAPPING.get(label)
    
    if sop_info and label != 'Unknown - Would use ML':
        output.append(f"\n{'─'*80}")
        output.append("\n📚 RELEVANT SOP SECTIONS:")
        
        # Note: These are CODE7's internal rules, not actual Confluence excerpts
        output.append("\n⚠️  Note: The following reconciliation steps are CODE7's internal logic.")
        output.append("   For official SOP documentation, refer to Confluence links below.")
        
        if sop_info.get('reconciliation_steps'):
            output.append("\n🔹 Reconciliation Steps (from CODE7 internal rules):")
            for i, step in enumerate(sop_info['reconciliation_steps'][:3], 1):  # Show first 3
                output.append(f"   {i}. {step}")
            if len(sop_info['reconciliation_steps']) > 3:
                output.append(f"   ... and {len(sop_info['reconciliation_steps']) - 3} more steps")
        
        if sop_info.get('confluence_links'):
            output.append("\n🔗 Official SOP Documentation:")
            for link in sop_info['confluence_links']:
                if 'Daily+Bank' in link:
                    output.append(f"   • Daily Bank Transaction Reconciliation")
                elif 'Escalating' in link:
                    output.append(f"   • Escalating Reconciliation Issues")
                elif 'Letter' in link:
                    output.append(f"   • Letter of Indemnity Process")
                output.append(f"     {link}")
    
    output.append("\n" + "="*80 + "\n")
    
    return "\n".join(output)

def interactive_mode():
    """Interactive input mode."""
    print("\n" + "="*80)
    print("SIMPLE TRANSACTION PREDICTOR")
    print("="*80)
    print("\nEnter transaction details:\n")
    
    amount = input("Amount (e.g., $5,100.00): ").strip()
    date = input("Date (e.g., 10/14/2025): ").strip()
    payment_method = input("Payment Method (e.g., wire in): ").strip()
    account = input("Account (e.g., Chase Wire In): ").strip()
    print("Narrative (paste and press Enter):")
    narrative = input().strip()
    
    print(format_output(narrative, amount, payment_method, account, date))

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == '--interactive':
        interactive_mode()
    else:
        # Demo with example
        print("\n🎯 DEMO MODE (use --interactive for custom input)\n")
        
        narrative = "YOUR REF=POH OF 25/10/14,REC FROM=00000000730103207 CHELSEA N SARVER 5605 SCURTICE ST UNIT A LITTLETON CO 80120-1188 US,REMARK=1TRVXX9QP28C DEBIT REF POH OF"
        amount = "$5,100.00"
        date = "10/14/2025"
        payment_method = "wire in"
        account = "Chase Wire In"
        
        print(format_output(narrative, amount, payment_method, account, date))

