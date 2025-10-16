#!/usr/bin/env python3
"""
Wikipedia-Style Transaction Predictor
Clean, concise, business-focused
"""

import sys
import os

# Load real SOP content
def load_sop_content(filename):
    """Load SOP text file."""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return f.read()
    except:
        return None

def predict_label(narrative, amount, payment_method, account, date):
    """Rule-based prediction - no changes to logic."""
    desc = str(narrative).upper()
    amt = float(str(amount).replace('$', '').replace(',', '')) if amount else 0
    
    # Rule matching
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
    elif '1HIOSDWH' in desc or 'OHSDWHTX' in desc:
        return 'OH SDWH', 'rule-based', "Description contains '1HIOSDWH' or 'OHSDWHTX'"
    elif 'OH WH TAX' in desc:
        return 'OH WH', 'rule-based', "Description contains 'OH WH TAX'"
    elif 'STATE OF MONTANA' in desc or 'MT TAX' in desc:
        return 'MT UI', 'rule-based', "Description contains 'STATE OF MONTANA' or 'MT TAX'"
    elif 'CHECK' in payment_method.upper():
        return 'Check', 'rule-based', "Payment method is 'Check'"
    elif 'MONEY MARKET' in desc or 'MONEY MKT' in desc:
        return 'Money Market Transfer', 'rule-based', "Description contains 'MONEY MARKET'"
    elif 'TREASURY' in desc:
        return 'Treasury Transfer', 'rule-based', "Description contains 'TREASURY'"
    elif 'CSC' in desc:
        return 'CSC', 'rule-based', "Description contains 'CSC' (Child Support Credits)"
    elif 'LOCKBOX' in desc:
        return 'Lockbox', 'rule-based', "Description contains 'LOCKBOX'"
    elif 'ACH RETURN SETTLEMENT' in desc or 'CREDIT MEMO' in desc:
        return 'LOI', 'rule-based', "Description indicates Letter of Indemnity"
    else:
        return 'Unknown', 'ml-needed', "No clear pattern match - would use ML model"

def get_sop_exact_text(label):
    """Get exact text from SOP for label and reconciliation."""
    sop_texts = {
        "Risk": {
            "labeling": """If the account is 'PNC Wire In, or Chase Wire In' you should label that BT as Risk

But sometimes even the account of the bank transaction is Chase Recovery or Chase Payroll Incoming Wires it might not be a risk item.

Please surface the wires to #risk-payments
For Chase Wire Ins - please tag @credit-ops""",
            "reconciliation": """If there is a BT that is labeled as Risk, you should wait until 10 am PST to reach out Risk Team. You can use the risk-payments slack channel to reach the Risk Team.

There are two teams that record BTs. If the account of the BT is 'recovery' you should reach out collections team through the risk-payments channel. If the account of the BT is Payroll/wireins you should reach out to the credit ops team through the risk-payments channel.

(Recovery) —> Risk Channel —> collections
(Payroll/wireins) —> Risk Channel —> credit ops

You should link BT, company, and payroll to your message."""
        },
        
        "NY WH": {
            "labeling": """When you see NYS DTF WT on BT's description you should label that BT as NY WH""",
            "reconciliation": """If there is a BT that the agent is NY WTH, you will see some suggested transmissions. You should reconcile it with the oldest transmission since NY WTH BTs don't give us any identifying information"""
        },
        
        "OH WH": {
            "labeling": """When you see OH WH TAX on BT's description you should label that BT as OH WH""",
            "reconciliation": """If there is a BT that the agent is OH WH, you will see an IN ID NO in the description. This description contains zeros at the beginning. You should copy the ID number without the zeros and paste that number to the OH WTH section in the reconciliation cleanup dashboard (redash).

Then, you will have the electronic payment ID. You should enter this ID as the transmission ID and select the electronic payment as the transmission type."""
        },
        
        "Check": {
            "labeling": """When you see check paid as the BT's payment method, you should label that BT as Check""",
            "reconciliation": """If there is a BT that the agent is Check, you will see a customer reference number. This number contains zeros at the beginning. You should copy this number without the zeros and paste that number to the "Mastertax Check Numbers" at the Mastertax Check Tracker and also select the relevant bank account. With this tool, you import check. This check will appear as a check payment. That check payment may appear as a suggested transmission in the reconciliation queue. If it will not appear, you should find it in the check payments section.

You should enter the same check number to the check number section in the check payment filter. You should copy that ID and select check payment as the transmission type and reconcile."""
        },
        
        "ICP Funding": {
            "labeling": """When you see Chase International Contractor Payment as the account and "TRANSFER FROM ACCOUNT000000807737908" in the description, you should label that BT as ICP Funding.

There will be a corresponding BT that has the same amount and "TRANSFER TO ACCOUNT000000771015119" in the description. Label that BT as ICP Funding.

In total, there will be 2 BTs to be labeled as ICP Funding and both of them will have "REMARK=JPMORGAN ACCESS TRANSFER" on their description.""",
            "reconciliation": """Two bank transactions with matching amounts must be reconciled together as paired ICP Funding transactions."""
        },
    }
    
    return sop_texts.get(label, {})

def get_sop_references(label):
    """Get SOP references for label."""
    sops = {
        "Risk": [
            ("Daily Operations : How to Label & Reconcile", 
             "https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/535003232"),
            ("Escalating Reconciliation Issues to Cross-Functional Stakeholders",
             "https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/460194134"),
        ],
        "NY WH": [
            ("Daily Operations : How to Label & Reconcile",
             "https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/535003232"),
            ("Manual Reconciliation by Agency",
             "https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/169411539"),
        ],
        "OH WH": [
            ("Daily Operations : How to Label & Reconcile",
             "https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/535003232"),
            ("Manual Reconciliation by Agency",
             "https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/169411539"),
        ],
        "OH SDWH": [
            ("Daily Operations : How to Label & Reconcile",
             "https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/535003232"),
        ],
        "NY UI": [
            ("Daily Operations : How to Label & Reconcile",
             "https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/535003232"),
        ],
        "MT UI": [
            ("Daily Operations : How to Label & Reconcile",
             "https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/535003232"),
        ],
        "Check": [
            ("Daily Operations : How to Label & Reconcile",
             "https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/535003232"),
            ("Manual Reconciliation Checks",
             "https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/169412024"),
        ],
        "ICP Funding": [
            ("Daily Operations : How to Label & Reconcile",
             "https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/535003232"),
            ("International Contractor Payment Funding",
             "https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/169411829"),
        ],
        "Money Market Transfer": [
            ("Daily Operations : How to Label & Reconcile",
             "https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/535003232"),
        ],
        "Treasury Transfer": [
            ("Daily Operations : How to Label & Reconcile",
             "https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/535003232"),
        ],
        "CSC": [
            ("Daily Operations : How to Label & Reconcile",
             "https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/535003232"),
        ],
        "Lockbox": [
            ("Daily Operations : How to Label & Reconcile",
             "https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/535003232"),
            ("Lockbox Investigations",
             "https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/169411804"),
        ],
        "LOI": [
            ("Daily Operations : How to Label & Reconcile",
             "https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/535003232"),
            ("Letter of Indemnity Process and Reconciliation",
             "https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/298583554"),
        ],
    }
    
    # Default SOPs if not found
    default = [
        ("Daily Operations : How to Label & Reconcile",
         "https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/535003232"),
        ("Daily Bank Transaction Reconciliation by Bank Transaction Type",
         "https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/169411126"),
    ]
    
    return sops.get(label, default)

def format_output(narrative, amount, payment_method, account, date):
    """Format Wikipedia-style output."""
    
    label, method, reason = predict_label(narrative, amount, payment_method, account, date)
    
    output = []
    output.append("\n" + "="*80)
    output.append("TRANSACTION ANALYSIS")
    output.append("="*80)
    
    # Transaction summary
    output.append(f"\n💰 ${amount}  |  {date}  |  {payment_method}  |  {account}")
    output.append(f"📝 {narrative[:80]}...")
    
    # Label prediction
    output.append(f"\n{'─'*80}")
    output.append(f"\n🏷️  LABEL: {label}")
    output.append(f"\n📊 Classification: {reason} ({method})")
    
    # Get SOP exact texts
    sop_content = get_sop_exact_text(label)
    
    # Labeling guidance from SOP
    if sop_content and 'labeling' in sop_content:
        output.append(f"\n{'─'*80}")
        output.append(f"\n📝 LABELING GUIDANCE (from SOP):")
        output.append(f'\n   "{sop_content["labeling"]}"')
    
    # Reconciliation guidance from SOP
    if sop_content and 'reconciliation' in sop_content:
        output.append(f"\n{'─'*80}")
        output.append(f"\n📖 HOW TO RECONCILE (from SOP):")
        output.append(f'\n   "{sop_content["reconciliation"]}"')
    
    # SOP References
    sops = get_sop_references(label)
    output.append(f"\n{'─'*80}")
    output.append(f"\n📚 REFERENCE SOPs:")
    for title, url in sops:
        output.append(f"\n   • {title}")
        output.append(f"     {url}")
    
    output.append("\n" + "="*80 + "\n")
    
    return "\n".join(output)

if __name__ == "__main__":
    # Test with example
    print("\n🎯 DEMO MODE\n")
    
    result = format_output(
        narrative="YOUR REF=POH OF 25/10/14,REC FROM=00000000730103207 CHELSEA N SARVER 5605 SCURTICE ST UNIT A LITTLETON CO 80120-1188 US,REMARK=1TRVXX9QP28C DEBIT REF POH OF",
        amount="$5,100.00",
        date="10/14/2025 12:00:00am",
        payment_method="wire in",
        account="Chase Wire In"
    )
    
    print(result)

