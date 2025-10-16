#!/usr/bin/env python3
"""
Clean Transaction Predictor with Real SOP Content
Each label has ONLY its own labeling and reconciliation guidance
"""

def predict_label(narrative, amount, payment_method, account, date):
    """Rule-based prediction - account-based rules have priority."""
    desc = str(narrative).upper()
    acc = str(account).upper()
    
    # PRIORITY 1: Account-based rules (most specific)
    if 'CHASE RECOVERY' in acc:
        return 'Recovery Wire', 'rule-based', "Account is Chase Recovery"
    elif 'CHASE PAYROLL INCOMING WIRES' in acc:
        # Business rule: Don't label if TODAY, label as Risk if 1+ days old
        return 'Risk (UNLABELED if TODAY)', 'rule-based', "Account is Chase Payroll Incoming Wires - Risk label but keep UNLABELED if transaction date is TODAY, label as Risk if 1+ days old"
    elif 'PNC WIRE IN' in acc or 'CHASE WIRE IN' in acc:
        return 'Risk', 'rule-based', "Account is PNC Wire In or Chase Wire In"
    
    # PRIORITY 2: Description-based patterns
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
        # No rule match - use ML model
        ml_prediction = predict_with_ml(narrative, amount, payment_method, account)
        return ml_prediction, 'ml-based', "No clear rule pattern - predicted using ML model"

def predict_with_ml(narrative, amount, payment_method, account):
    """
    Predict using ML model (simplified).
    In production, this would load the actual trained model.
    """
    # For now, return a placeholder
    # In production, this would use the actual XGBoost/RandomForest model
    return "ML Prediction (model not loaded)"

def get_sop_content(label):
    """
    Get ONLY the relevant SOP text for this specific label.
    Source: Daily Operations : How to Label & Reconcile (Confluence)
    """
    
    sop_data = {
        "Recovery Wire": {
            "labeling": """If the account is 'Chase Recovery' you should label that BT as Recovery Wire

Please surface the wires to #risk-payments
For Chase Recovery Wire Ins - please tag @collections""",
            "reconciliation": """If there is a BT from Chase Recovery account, reach out to collections team through the risk-payments channel.

You should link BT, company, and payroll to your message."""
        },
        
        "Risk (UNLABELED if TODAY)": {
            "labeling": """If the account is 'Chase Payroll Incoming Wires' - leave it unlabeled if transaction date is TODAY. Label as Risk if 1+ days old.

Please surface the wires to #risk-payments
For Chase Payroll wires - please tag @credit-ops""",
            "reconciliation": """If there is a BT that is labeled as Risk, you should wait until 10 am PST to reach out Risk Team. You can use the risk-payments slack channel to reach the Risk Team.

There are two teams that record BTs. If the account of the BT is 'recovery' you should reach out collections team through the risk-payments channel. If the account of the BT is Payroll/wireins you should reach out to the credit ops team through the risk-payments channel.

(Recovery) —> Risk Channel —> collections
(Payroll/wireins) —> Risk Channel —> credit ops

You should link BT, company, and payroll to your message."""
        },
        
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
        
        "NY WH": {
            "labeling": """When you see NYS DTF WT on BT's description you should label that BT as NY WH""",
            "reconciliation": """If there is a BT that the agent is NY WTH, you will see some suggested transmissions. You should reconcile it with the oldest transmission since NY WTH BTs don't give us any identifying information"""
        },
        
        "OH WH": {
            "labeling": """When you see OH WH TAX on BT's description you should label that BT as OH WH""",
            "reconciliation": """If there is a BT that the agent is OH WH, you will see an IN ID NO in the description. This description contains zeros at the beginning. You should copy the ID number without the zeros and paste that number to the OH WTH section in the reconciliation cleanup dashboard (redash).

Then, you will have the electronic payment ID. You should enter this ID as the transmission ID and select the electronic payment as the transmission type."""
        },
        
        "OH SDWH": {
            "labeling": """When you see OH SDWH on BT's description you should label that BT as OH SDWH""",
            "reconciliation": None
        },
        
        "NY UI": {
            "labeling": """When you see NYS DOL UI on BT's description you should label that BT as NY UI""",
            "reconciliation": None
        },
        
        "MT UI": {
            "labeling": """When you see MT TAX or STATE OF MONTANA on BT's description you should label that BT as MT UI""",
            "reconciliation": None
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
            "reconciliation": """First, you should search the amount in your mail. If no relative email exists you should search for electronic payment. You start to reconcile with wire out. If the electronic payment with the same amount does not exist, you should use the Electronic Payment Creator Tool."""
        },
        
        "Money Market Fund": {
            "labeling": """When you see MONEY MKT MUTUAL FUND on BT's description you should label that BT as Money Market Fund""",
            "reconciliation": None
        },
        
        "Treasury Transfer": {
            "labeling": """When you see US TREASURY CAPITAL on BT's description, you should label that BT as Treasury Transfer""",
            "reconciliation": None
        },
        
        "CSC": {
            "labeling": """When you see CSCXXXXXX on BT's description you should label that BT as CSC.""",
            "reconciliation": """If there is a BT that the agent is CSC, you will see some suggested transmissions. The description of the transmission (CSC 123456) should match with the description in the transaction (DESC=CSC123456). If they match, you should also check the origination account and the amount."""
        },
        
        "Lockbox": {
            "labeling": """When you see Lockbox on the BT's description you should label that BT as Lockbox""",
            "reconciliation": None
        },
        
        "LOI": {
            "labeling": """When you see Remark: ACH RETURN SETTLEMENT on BT's description you should label that BT as LOI
If the description includes "CREDIT MEMO", the BT should be labeled as "LOI".""",
            "reconciliation": None
        },
    }
    
    return sop_data.get(label, {})

def get_sop_links(label):
    """Get SOP reference links for this label."""
    
    links = {
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
        "LOI": [
            ("Daily Operations : How to Label & Reconcile",
             "https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/535003232"),
            ("Letter of Indemnity Process and Reconciliation",
             "https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/298583554"),
        ],
    }
    
    # Default for all others
    default = [
        ("Daily Operations : How to Label & Reconcile",
         "https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/535003232"),
    ]
    
    return links.get(label, default)

def format_output(narrative, amount, payment_method, account, date):
    """Format clean output with SOP content."""
    
    label, method, reason = predict_label(narrative, amount, payment_method, account, date)
    sop_content = get_sop_content(label)
    sop_links = get_sop_links(label)
    
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
    
    # Labeling guidance from SOP
    if sop_content and 'labeling' in sop_content:
        output.append(f"\n{'─'*80}")
        output.append(f"\n📝 LABELING GUIDANCE (from SOP):")
        output.append(f'\n"{sop_content["labeling"]}"')
        output.append(f"\nSource: Daily Operations : How to Label & Reconcile")
        output.append(f"Link: https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/535003232")
    
    # Reconciliation guidance from SOP
    if sop_content and 'reconciliation' in sop_content and sop_content['reconciliation']:
        output.append(f"\n{'─'*80}")
        output.append(f"\n📖 HOW TO RECONCILE (from SOP):")
        output.append(f'\n"{sop_content["reconciliation"]}"')
        output.append(f"\nSource: Daily Operations : How to Label & Reconcile")
        output.append(f"Link: https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/535003232")
    
    # SOP links
    output.append(f"\n{'─'*80}")
    output.append(f"\n📚 REFERENCE SOPs:")
    for title, url in sop_links:
        output.append(f"\n• {title}")
        output.append(f"  {url}")
    
    output.append("\n" + "="*80 + "\n")
    
    return "\n".join(output)

if __name__ == "__main__":
    print("\n🎯 DEMO MODE\n")
    
    result = format_output(
        narrative="YOUR REF=POH OF 25/10/14,REC FROM=00000000730103207 CHELSEA N SARVER 5605 SCURTICE ST UNIT A LITTLETON CO 80120-1188 US,REMARK=1TRVXX9QP28C DEBIT REF POH OF",
        amount="$5,100.00",
        date="10/14/2025 12:00:00am",
        payment_method="wire in",
        account="Chase Wire In"
    )
    
    print(result)

