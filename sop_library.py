#!/usr/bin/env python3
"""
SOP Library - Real Confluence content for each agent
Maps agents to actual SOP text excerpts
"""

# Real SOP excerpts from "Daily Operations : How to Label & Reconcile"
# Source: https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/535003232

SOP_EXCERPTS = {
    "Risk": {
        "sop_title": "Daily Operations : How to Label & Reconcile",
        "sop_url": "https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/535003232",
        "section": "Risk",
        "exact_text": """Risk
If the account is 'Chase Recovery' you should label that BT as Recovery Wire
If the account is 'PNC Wire In, or Chase Wire In' you should label that BT as Risk
If the account is 'Chase Payroll Incoming Wires' - leave it unlabeled

But sometimes even the account of the bank transaction is Chase Recovery or Chase Payroll Incoming Wires it might not be a risk item.

Please surface the wires to #risk-payments
For Chase Recovery Wire Ins - please tag @collections 
For Chase Wire Ins - please tag @credit-ops

How to Reconcile:
If there is a BT that is labeled as Risk, you should wait until 10 am PST to reach out Risk Team. You can use the risk-payments slack channel to reach the Risk Team.

There are two teams that record BTs. If the account of the BT is 'recovery' you should reach out collections team through the risk-payments channel. If the account of the BT is Payroll/wireins you should reach out to the credit ops team through the risk-payments channel.

(Recovery) —> Risk Channel —> collections
(Payroll/wireins) —> Risk Channel —> credit ops

You should link BT, company, and payroll to your message."""
    },
    
    "NY WH": {
        "sop_title": "Daily Operations : How to Label & Reconcile",
        "sop_url": "https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/535003232",
        "section": "NY WH",
        "exact_text": """NY WH
When you see NYS DTF WT on BT's description you should label that BT as NY WH

How to Reconcile:
If there is a BT that the agent is NY WTH, you will see some suggested transmissions. You should reconcile it with the oldest transmission since NY WTH BTs don't give us any identifying information"""
    },
    
    "OH WH": {
        "sop_title": "Daily Operations : How to Label & Reconcile",
        "sop_url": "https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/535003232",
        "section": "OH WH",
        "exact_text": """OH WH
When you see OH WH TAX on BT's description you should label that BT as OH WH

How to Reconcile:
If there is a BT that the agent is OH WH, you will see an IN ID NO in the description. This description contains zeros at the beginning. You should copy the ID number without the zeros and paste that number to the OH WTH section in the reconciliation cleanup dashboard (redash).

Then, you will have the electronic payment ID. You should enter this ID as the transmission ID and select the electronic payment as the transmission type."""
    },
    
    "OH SDWH": {
        "sop_title": "Daily Operations : How to Label & Reconcile",
        "sop_url": "https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/535003232",
        "section": "OH SDWH",
        "exact_text": """OH SDWH
When you see OH SDWH on BT's description you should label that BT as OH SDWH"""
    },
    
    "NY UI": {
        "sop_title": "Daily Operations : How to Label & Reconcile",
        "sop_url": "https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/535003232",
        "section": "NY UI",
        "exact_text": """NY UI
When you see NYS DOL UI on BT's description you should label that BT as NY UI"""
    },
    
    "MT UI": {
        "sop_title": "Daily Operations : How to Label & Reconcile",
        "sop_url": "https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/535003232",
        "section": "MT UI",
        "exact_text": """MT UI
When you see MT TAX or STATE OF MONTANA on BT's description you should label that BT as MT UI"""
    },
    
    "Check": {
        "sop_title": "Daily Operations : How to Label & Reconcile",
        "sop_url": "https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/535003232",
        "section": "Check",
        "exact_text": """Check
When you see check paid as the BT's payment method, you should label that BT as Check

How to Reconcile:
If there is a BT that the agent is Check, you will see a customer reference number. This number contains zeros at the beginning. You should copy this number without the zeros and paste that number to the "Mastertax Check Numbers" at the Mastertax Check Tracker and also select the relevant bank account. With this tool, you import check. This check will appear as a check payment. That check payment may appear as a suggested transmission in the reconciliation queue. If it will not appear, you should find it in the check payments section.

You should enter the same check number to the check number section in the check payment filter. You should copy that ID and select check payment as the transmission type and reconcile."""
    },
    
    "ICP Funding": {
        "sop_title": "Daily Operations : How to Label & Reconcile",
        "sop_url": "https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/535003232",
        "section": "ICP",
        "exact_text": """ICP
When you see Chase International Contractor Payment as the account and "ach external" as the method you should label that BT as ICP Return.

When you see Chase International Contractor Payment as the account and "TRANSFER FROM ACCOUNT000000807737908" in the description, you should label that BT as ICP Funding.

There will be a corresponding BT that has the same amount and "TRANSFER TO ACCOUNT000000771015119" in the description. Label that BT as ICP Funding.

In total, there will be 2 BTs to be labeled as ICP Funding and both of them will have "REMARK=JPMORGAN ACCESS TRANSFER" on their description.

When you see "ORIG CO NAME=DLOCAL" (sometimes it might be DLOCL) on BT's description label that BT as ICP too.

When you see "REMARK=JPMORGAN ACCESS TRANSFER" on Bt's description label that BT as ICP Funding. There will be two ICP funding BTs, one from Chase ICP account and one from Chase Ops."""
    },
    
    "LOI": {
        "sop_title": "Daily Operations : How to Label & Reconcile",
        "sop_url": "https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/535003232",
        "section": "LOI",
        "exact_text": """LOI
When you see Remark: ACH RETURN SETTLEMENT on BT's description you should label that BT as LOI
If the description includes "CREDIT MEMO", the BT should be labeled as "LOI"."""
    },
    
    "CSC": {
        "sop_title": "Daily Operations : How to Label & Reconcile",
        "sop_url": "https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/535003232",
        "section": "CSC (Child Support Credits)",
        "exact_text": """CSC (Child Support Credits)
When you see CSCXXXXXX on BT's description you should label that BT as CSC.

How to Reconcile:
If there is a BT that the agent is CSC, you will see some suggested transmissions. The description of the transmission (CSC 123456) should match with the description in the transaction (DESC=CSC123456). If they match, you should also check the origination account and the amount."""
    },
    
    "Money Market Transfer": {
        "sop_title": "Daily Operations : How to Label & Reconcile",
        "sop_url": "https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/535003232",
        "section": "Money Market Fund",
        "exact_text": """Money Market Fund
When you see MONEY MKT MUTUAL FUND on BT's description you should label that BT as Money Market Fund"""
    },
    
    "Treasury Transfer": {
        "sop_title": "Daily Operations : How to Label & Reconcile",
        "sop_url": "https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/535003232",
        "section": "Treasury Transfer",
        "exact_text": """Treasury Transfer
When you see US TREASURY CAPITAL on BT's description, you should label that BT as Treasury Transfer"""
    },
    
    "ACH": {
        "sop_title": "Daily Operations : How to Label & Reconcile",
        "sop_url": "https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/535003232",
        "section": "ACH",
        "exact_text": """ACH
When you see REMARK=EFT REVERSAL on BT's description, you should label that BT as ACH

How to Reconcile:
If there is a BT that is labeled as ACH you should reconcile with the recommended transmission including the same description. An example for CON12345, the description of the BT is DESC:CON750119. You can find the same description in the suggested BTs' description."""
    }
}

def get_sop_for_label(label):
    """Get SOP excerpt for a given label."""
    return SOP_EXCERPTS.get(label)

def get_all_labels():
    """Get all available labels with SOPs."""
    return list(SOP_EXCERPTS.keys())

