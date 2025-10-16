#!/usr/bin/env python3
"""
Transaction Predictor with Real SOP Content
ONLY shows what's actually in the SOP - nothing else!
"""

from complete_sop_mapping import COMPLETE_SOP_MAPPING

def predict_label(narrative, amount, payment_method, account, date):
    """Rule-based prediction."""
    desc = str(narrative).upper()
    acc = str(account).upper()
    
    # Account-based rules
    if 'CHASE RECOVERY' in acc:
        return 'Recovery Wire', 'rule-based', "Account is Chase Recovery"
    elif 'CHASE PAYROLL INCOMING WIRES' in acc:
        return 'Risk', 'rule-based', "Account is Chase Payroll Incoming Wires (leave UNLABELED if TODAY, label as Risk if 1+ days old)"
    elif 'PNC WIRE IN' in acc or 'CHASE WIRE IN' in acc:
        return 'Risk', 'rule-based', "Account is PNC Wire In or Chase Wire In"
    
    # Description-based patterns
    if '1TRV' in desc:
        return 'Risk', 'rule-based', "Description contains '1TRV' code"
    elif 'NIUM' in desc:
        return 'Nium Payment', 'rule-based', "Description contains 'NIUM'"
    elif 'JPMORGAN ACCESS TRANSFER' in desc:
        return 'ICP Funding', 'rule-based', "Description contains 'JPMORGAN ACCESS TRANSFER'"
    elif 'NYS DTF WT' in desc or 'NY DTF WT' in desc:
        return 'NY WH', 'rule-based', "Description contains 'NYS DTF WT'"
    elif 'NYS DOL UI' in desc:
        return 'NY UI', 'rule-based', "Description contains 'NYS DOL UI'"
    elif '1HIOSDWH' in desc or 'OHSDWHTX' in desc or 'OH SDWH' in desc:
        return 'OH SDWH', 'rule-based', "Description contains 'OH SDWH'"
    elif 'OH WH TAX' in desc:
        return 'OH WH', 'rule-based', "Description contains 'OH WH TAX'"
    elif 'STATE OF MONTANA' in desc or 'MT TAX' in desc:
        return 'MT UI', 'rule-based', "Description contains 'STATE OF MONTANA'"
    elif 'IL DEPT EMPL SEC' in desc:
        return 'IL UI', 'rule-based', "Description contains 'IL DEPT EMPL SEC'"
    elif 'STATE OF WA ESD' in desc or 'ESD WA UI-TAX' in desc:
        return 'WA ESD', 'rule-based', "Description contains 'STATE OF WA ESD'"
    elif 'STATE OF NM DWS' in desc:
        return 'NM UI', 'rule-based', "Description contains 'STATE OF NM DWS'"
    elif 'VA. EMPLOY COMM' in desc or 'VA EMPLOY COMM' in desc:
        return 'VA UI', 'rule-based', "Description contains 'VA. EMPLOY COMM'"
    elif 'L&I' in desc or 'LABOR&INDUSTRIES' in desc or 'LABOR & INDUSTRIES' in desc:
        return 'WA LNI', 'rule-based', "Description contains 'L&I' or 'Labor&Industries'"
    elif 'YORK ADAMS TAX' in desc:
        return 'York Adams Tax', 'rule-based', "Description contains 'YORK ADAMS TAX'"
    elif 'BERKS EIT' in desc:
        return 'Berks Tax', 'rule-based', "Description contains 'BERKS EIT'"
    elif 'ACCRUED INT' in desc:
        return 'Blueridge Interest', 'rule-based', "Description contains 'ACCRUED INT'"
    elif 'ACH CREDIT SETTLEMENT' in desc:
        return 'ACH Reversal', 'rule-based', "Description contains 'ACH CREDIT SETTLEMENT'"
    elif 'EFT REVERSAL' in desc:
        return 'ACH', 'rule-based', "Description contains 'EFT REVERSAL'"
    elif 'INTEREST ADJUSTMENT' in desc:
        return 'Interest Adjustment', 'rule-based', "Description contains 'INTEREST ADJUSTMENT'"
    elif 'RTN OFFSET' in desc:
        return 'ACH Return', 'rule-based', "Description contains 'RTN OFFSET'"
    elif float(amount.replace('$', '').replace(',', '')) < 1.0:
        return 'Bad Debt', 'rule-based', "Amount less than $1.00"
    elif 'DLOCAL' in desc or 'DLOCL' in desc:
        return 'ICP', 'rule-based', "Description contains 'DLOCAL'"
    elif 'CHECK' in payment_method.upper():
        return 'Check', 'rule-based', "Payment method is 'Check'"
    elif 'MONEY MARKET' in desc or 'MONEY MKT' in desc:
        return 'Money Market Fund', 'rule-based', "Description contains 'MONEY MARKET'"
    elif 'TREASURY' in desc or 'US TREASURY' in desc:
        return 'Treasury Transfer', 'rule-based', "Description contains 'TREASURY'"
    elif 'CSC' in desc:
        return 'CSC', 'rule-based', "Description contains 'CSC'"
    elif 'LOCKBOX' in desc:
        return 'Lockbox', 'rule-based', "Description contains 'LOCKBOX'"
    elif 'ACH RETURN SETTLEMENT' in desc or 'CREDIT MEMO' in desc:
        return 'LOI', 'rule-based', "Description indicates LOI"
    elif 'BREX' in desc:
        return 'Brex', 'rule-based', "Description contains 'BREX'"
    else:
        return 'Unknown (ML needed)', 'ml-based', "No pattern match"

def get_real_sop_content(label):
    """
    ONLY real SOP content - exactly as written in SOP
    Source: sop_daily_operations__how_to_label__reconcile_535003232.txt
    Uses COMPLETE_SOP_MAPPING which contains all 30 labels from SOP
    """
    
    return COMPLETE_SOP_MAPPING.get(label, {})
    
    # OLD MAPPING (replaced by complete mapping from complete_sop_mapping.py)
    old_real_sop = {
        "Risk": {
            "labeling": "If the account is 'PNC Wire In, or Chase Wire In' you should label that BT as Risk",
            "reconciliation": """Wait until 12 PM PST → #risk-payments

You should link BT, company, and payroll to your message.""",
            "sop_page": "Daily Operations : How to Label & Reconcile",
            "sop_link": "https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/535003232"
        },
        
        "Risk (Chase Payroll)": {
            "labeling": None,  # SOP has outdated info - see business rules instead
            "reconciliation": """Wait until 12 PM PST → #risk-payments → @credit-ops

You should link BT, company, and payroll to your message.""",
            "sop_page": "Daily Operations : How to Label & Reconcile",
            "sop_link": "https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/535003232"
        },
        
        "Recovery Wire": {
            "labeling": "If the account is 'Chase Recovery' you should label that BT as Recovery Wire",
            "reconciliation": """Wait until 12 PM PST → #risk-payments → @collections

You should link BT, company, and payroll to your message.""",
            "sop_page": "Daily Operations : How to Label & Reconcile",
            "sop_link": "https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/535003232"
        },
        
        "NY WH": {
            "labeling": "When you see NYS DTF WT on BT's description you should label that BT as NY WH",
            "reconciliation": "If there is a BT that the agent is NY WTH, you will see some suggested transmissions. You should reconcile it with the oldest transmission since NY WTH BTs don't give us any identifying information",
            "sop_page": "Daily Operations : How to Label & Reconcile",
            "sop_link": "https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/535003232"
        },
        
        "Check": {
            "labeling": "When you see check paid as the BT's payment method, you should label that BT as Check",
            "reconciliation": "If there is a BT that the agent is Check, you will see a customer reference number. This number contains zeros at the beginning. You should copy this number without the zeros and paste that number to the 'Mastertax Check Numbers' at the Mastertax Check Tracker and also select the relevant bank account.",
            "sop_page": "Daily Operations : How to Label & Reconcile",
            "sop_link": "https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/535003232"
        },
        
        "OH SDWH": {
            "labeling": "When you see OH SDWH on BT's description you should label that BT as OH SDWH",
            "reconciliation": None,
            "sop_page": "Daily Operations : How to Label & Reconcile",
            "sop_link": "https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/535003232"
        },
        
        "ICP Funding": {
            "labeling": """When you see Chase International Contractor Payment as the account and "TRANSFER FROM ACCOUNT000000807737908" in the description, you should label that BT as ICP Funding. 

In total, there will be 2 BTs to be labeled as ICP Funding and both of them will have "REMARK=JPMORGAN ACCESS TRANSFER" on their description. 

When you see "REMARK=JPMORGAN ACCESS TRANSFER" on BT's description label that BT as ICP Funding. There will be two ICP funding BTs, one from Chase ICP account and one from Chase Ops.""",
            "reconciliation": """First, you should search the amount in your mail. If no relative email exists you should search for electronic payment. You start to reconcile with wire out. If the electronic payment with the same amount does not exist, you should use the Electronic Payment Creator Tool.

For the payment account information section, after completing payment account type section and memo section in order to your unreconciled ICP BT, you should complete grouping attribute key value pairs. Click Payment Account Types and find the 12th item. This item shows Company ID and Payroll ID. Copy them to the grouping attribute key value pairs section.

With the created EP you can now reconcile the wire out. After that, you should reconcile wire in. For the wire in, you should use the payment reporter tool and reconcile it.""",
            "sop_page": "Daily Operations : How to Label & Reconcile",
            "sop_link": "https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/535003232"
        },
        
        "OH WH": {
            "labeling": "When you see OH WH TAX on BT's description you should label that BT as OH WH",
            "reconciliation": "If there is a BT that the agent is OH WH, you will see an IN ID NO in the description. This description contains zeros at the beginning. You should copy the ID number without the zeros and paste that number to the OH WTH section in the reconciliation cleanup dashboard (redash). Then, you will have the electronic payment ID. You should enter this ID as the transmission ID and select the electronic payment as the transmission type.",
            "sop_page": "Daily Operations : How to Label & Reconcile",
            "sop_link": "https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/535003232"
        },
        
        "NY UI": {
            "labeling": "When you see NYS DOL UI on BT's description you should label that BT as NY UI",
            "reconciliation": None,
            "sop_page": "Daily Operations : How to Label & Reconcile",
            "sop_link": "https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/535003232"
        },
        
        "CSC": {
            "labeling": "When you see CSCXXXXXX on BT's description you should label that BT as CSC",
            "reconciliation": "If there is a BT that the agent is CSC, you will see some suggested transmissions. The description of the transmission (CSC 123456) should match with the description in the transaction (DESC=CSC123456). If they match, you should also check the origination account and the amount.",
            "sop_page": "Daily Operations : How to Label & Reconcile",
            "sop_link": "https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/535003232"
        },
        
        "LOI": {
            "labeling": "When you see Remark: ACH RETURN SETTLEMENT on BT's description you should label that BT as LOI. If the description includes 'CREDIT MEMO', the BT should be labeled as 'LOI'.",
            "reconciliation": None,
            "sop_page": "Daily Operations : How to Label & Reconcile",
            "sop_link": "https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/535003232"
        },
        
        "Lockbox": {
            "labeling": "When you see Lockbox on the BT's description you should label that BT as Lockbox",
            "reconciliation": None,
            "sop_page": "Daily Operations : How to Label & Reconcile",
            "sop_link": "https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/535003232"
        },
    }
    
    return real_sop.get(label, {})

def get_business_rules(label):
    """
    Business rules that override or supplement SOP
    """
    
    business_rules = {
        "Risk (Chase Payroll)": [
            {
                "rule": "Chase Payroll Incoming Wires: Leave UNLABELED if transaction date is TODAY. Label as Risk if 1+ days old.",
                "reason": "Current labeling rule (SOP has outdated information)"
            }
        ]
    }
    
    return business_rules.get(label, [])

def format_output(narrative, amount, payment_method, account, date):
    """Format output with clear separation: SOP vs Business Rules."""
    
    label, method, reason = predict_label(narrative, amount, payment_method, account, date)
    sop_content = get_real_sop_content(label)
    business_rules = get_business_rules(label)
    
    output = []
    output.append("\n" + "="*80)
    output.append("TRANSACTION ANALYSIS")
    output.append("="*80)
    
    # Transaction info
    output.append(f"\n💰 {amount}  |  {date}  |  {payment_method}  |  {account}")
    output.append(f"📝 {narrative[:80]}...")
    
    # Label
    output.append(f"\n{'─'*80}")
    output.append(f"\n🏷️  LABEL: {label}")
    output.append(f"📊 Classification: {reason} ({method})")
    
    # SOP INFORMATION SECTION - ONLY FROM SOP!
    if sop_content:
        output.append(f"\n{'─'*80}")
        output.append(f"\n📚 SOP BİLGİLERİ (ONLY FROM SOP):")
        output.append(f"\n{'─'*80}")
        
        # Labeling from SOP
        if 'labeling' in sop_content:
            output.append(f"\n📝 How to Label (from SOP):")
            output.append(f'"{sop_content["labeling"]}"')
            if 'sop_page' in sop_content:
                output.append(f"\n   📄 Source: {sop_content['sop_page']}")
                output.append(f"   🔗 {sop_content['sop_link']}")
        
        # Reconciliation from SOP
        if 'reconciliation' in sop_content and sop_content['reconciliation']:
            output.append(f"\n\n📖 How to Reconcile (from SOP):")
            output.append(f'"{sop_content["reconciliation"]}"')
            if 'sop_page' in sop_content:
                output.append(f"\n   📄 Source: {sop_content['sop_page']}")
                output.append(f"   🔗 {sop_content['sop_link']}")
    
    # Business Rules (if any) - SEPARATE from SOP!
    if business_rules:
        output.append(f"\n{'─'*80}")
        output.append(f"\n⚠️  BUSINESS RULES (NOT FROM SOP):")
        output.append(f"{'─'*80}")
        for i, rule in enumerate(business_rules, 1):
            output.append(f"\n{i}. {rule['rule']}")
            output.append(f"   Reason: {rule['reason']}")
    
    output.append("\n" + "="*80 + "\n")
    
    return "\n".join(output)

if __name__ == "__main__":
    print("\n🎯 DEMO MODE\n")
    
    # Test Chase Payroll
    print(format_output(
        narrative="YOUR REF=WIRE_345SC990RKK,REC FROM=COLUMN NATIONAL ASSOCIATION BREX",
        amount="$3,998.49",
        date="10/15/2025 12:00:00am",
        payment_method="wire in",
        account="Chase Payroll Incoming Wires"
    ))
