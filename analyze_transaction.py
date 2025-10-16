#!/usr/bin/env python3
"""
Single Transaction Analyzer with Real SOP Content
"""

import sys

def predict_label(narrative, amount, payment_method, account, date):
    """Rule-based prediction - account-based rules have priority."""
    desc = str(narrative).upper()
    acc = str(account).upper()
    
    # PRIORITY 1: Account-based rules
    if 'CHASE PAYROLL INCOMING WIRES' in acc:
        # Check if Brex pattern exists
        if 'BREX' in desc and 'GUSTO' in desc:
            return 'Brex Payroll', 'rule-based', "Chase Payroll + BREX + GUSTO pattern"
        return 'Chase Payroll Incoming Wires', 'rule-based', "Account is Chase Payroll Incoming Wires"
    elif 'PNC WIRE IN' in acc or 'CHASE WIRE IN' in acc:
        return 'Risk', 'rule-based', "Account is PNC Wire In or Chase Wire In"
    
    # PRIORITY 2: Description patterns
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
        return 'MT UI', 'rule-based', "Description contains 'STATE OF MONTANA'"
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
        return 'LOI', 'rule-based', "Description indicates Letter of Indemnity"
    else:
        return 'Unknown', 'ml-needed', "No pattern match - would use ML"

def get_sop_content(label):
    """Get SOP text for label."""
    
    sop_data = {
        "Risk": {
            "labeling": """If the account is 'PNC Wire In, or Chase Wire In' you should label that BT as Risk

Please surface the wires to #risk-payments
For Chase Wire Ins - please tag @credit-ops""",
            "reconciliation": """If there is a BT that is labeled as Risk, you should wait until 10 am PST to reach out Risk Team. You can use the risk-payments slack channel to reach the Risk Team.

There are two teams that record BTs. If the account of the BT is 'recovery' you should reach out collections team through the risk-payments channel. If the account of the BT is Payroll/wireins you should reach out to the credit ops team through the risk-payments channel.

(Recovery) —> Risk Channel —> collections
(Payroll/wireins) —> Risk Channel —> credit ops

You should link BT, company, and payroll to your message."""
        },
        
        "Brex Payroll": {
            "labeling": """If there is a BT that is labeled as Brex and the payment direction is credit, you should find the relevant EP and reconcile with it. If the payment direction is debit you should escalate this BT to the payment-ops-recon Slack channel.""",
            "reconciliation": """Find the relevant electronic payment (EP) and reconcile with it. For debit transactions, escalate to #payment-ops-recon channel."""
        },
    }
    
    return sop_data.get(label, {})

def get_sop_links(label):
    """Get SOP links."""
    
    links = {
        "Risk": [
            ("Daily Operations : How to Label & Reconcile", 
             "https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/535003232"),
            ("Escalating Reconciliation Issues to Cross-Functional Stakeholders",
             "https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/460194134"),
        ],
    }
    
    default = [
        ("Daily Operations : How to Label & Reconcile",
         "https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/535003232"),
    ]
    
    return links.get(label, default)

def format_output(narrative, amount, payment_method, account, date, bt_id=""):
    """Format output."""
    
    label, method, reason = predict_label(narrative, amount, payment_method, account, date)
    sop_content = get_sop_content(label)
    sop_links = get_sop_links(label)
    
    output = []
    output.append("\n" + "="*80)
    if bt_id:
        output.append(f"TRANSACTION ANALYSIS - BT #{bt_id}")
    else:
        output.append("TRANSACTION ANALYSIS")
    output.append("="*80)
    
    output.append(f"\n💰 {amount}  |  {date}  |  {payment_method}  |  {account}")
    output.append(f"📝 {narrative[:100]}...")
    
    output.append(f"\n{'─'*80}")
    output.append(f"\n🏷️  LABEL: {label}")
    output.append(f"📊 Classification: {reason} ({method})")
    
    if sop_content and 'labeling' in sop_content:
        output.append(f"\n{'─'*80}")
        output.append(f"\n📝 LABELING GUIDANCE (from SOP):")
        output.append(f'\n"{sop_content["labeling"]}"')
    
    if sop_content and 'reconciliation' in sop_content and sop_content['reconciliation']:
        output.append(f"\n{'─'*80}")
        output.append(f"\n📖 HOW TO RECONCILE (from SOP):")
        output.append(f'\n"{sop_content["reconciliation"]}"')
    
    output.append(f"\n{'─'*80}")
    output.append(f"\n📚 REFERENCE SOPs:")
    for title, url in sop_links:
        output.append(f"\n• {title}")
        output.append(f"  {url}")
    
    output.append("\n" + "="*80 + "\n")
    
    return "\n".join(output)

if __name__ == "__main__":
    # Transaction 1: Brex Payroll
    print("\n🎯 ANALYZING 3 TRANSACTIONS:\n")
    
    print(format_output(
        narrative="YOUR REF=WIRE_345SC990RKK,REC FROM=COLUMN NATIONAL ASSOCIATION BREX SAN FRANCISCO CA US,FED ID=121145349,B/O CUSTOMER=/868890190533595 1/CONVOI VENTURES MANAGEMENT, LLC 2/336 E UNIVERSITY PKWY 3/US/OREM,84058,UT,B/O BANK=ABA/121145349 COLUMN NATIONAL ASSOCIATION BREX SAN FRANCISCO CA US,REMARK=/URI/GUSTO, OCT 1 - 15 DEBIT REF WMSG_345SCGFDGM+",
        amount="$3,998.49",
        date="10/15/2025 12:00:00am",
        payment_method="wire in",
        account="Chase Payroll Incoming Wires",
        bt_id="59321936"
    ))
    
    # Transaction 2: Risk
    print(format_output(
        narrative="DateTime: 1014250603WIRE TRANSFER IN ISO 003YJKORIGINATOR: DETERMINED BY DESIGN LLC AC/9868417016ADDR:712 H ST NE # 1866 WASHINGTON DC 20002 US SNDBNK:MANUFACTURERS & TRADERS TRUST CO ABA:022000046CTY:BUFFALO ST/PR:NY CTRY:US ORG BNK:M&T BankADDR:One M&T Plaza Buffalo NY 14240 USARFB:NOTPROVIDED AMT/CUR: 14800.00 USD STTLMTDATE:10142025 CHG:SHAR OBI:payroll BBI:payrollBENEFICIARY:Gusto Inc AC/1077770489",
        amount="$14,800.00",
        date="10/14/2025 12:00:00am",
        payment_method="wire in",
        account="PNC Wire In",
        bt_id="59317875"
    ))
    
    # Transaction 3: Risk
    print(format_output(
        narrative="DateTime: 1014251119WIRE TRANSFER IN ISO 0026MSORIGINATOR: 1/ALL TOGATHER WE CAN LLC AC/325207451140ADDR:2/1331 N CAHUENGA BLVD APT 3313",
        amount="$10.00",
        date="10/14/2025 12:00:00am",
        payment_method="wire in",
        account="PNC Wire In",
        bt_id="59317785"
    ))

