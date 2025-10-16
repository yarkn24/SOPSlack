#!/usr/bin/env python3
"""
Complete SOP Mapping - ALL labels from SOP
Extracted from: Daily Operations : How to Label & Reconcile
Updated: 10 am → 12 pm PST (noon, not midnight!)
"""

COMPLETE_SOP_MAPPING = {
    # EXISTING LABELS
    "Risk": {
        "labeling": "If the account is 'PNC Wire In, or Chase Wire In' you should label that BT as Risk. ⚠️ IMPORTANT: If the account is 'Chase Payroll Incoming Wires' and the transaction date is TODAY, DO NOT label it yet. Wait until tomorrow to label it as Risk.",
        "reconciliation": "If there is a BT that is labeled as Risk, you should wait until 12 pm PST to reach out Risk Team. You can use the risk-payments slack channel to reach the Risk Team. There are two teams that record BTs. If the account of the BT is 'recovery' you should reach out collections team through the risk-payments channel. If the account of the BT is Payroll/wireins you should reach out to the credit ops team through the risk-payments channel. (Recovery) —> Risk Channel —> collections (Payroll/wireins) —> Risk Channel —> credit ops You should link BT, company, and payroll to your message.",
        "sop_page": "Daily Operations : How to Label & Reconcile",
        "sop_link": "https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/535003232",
        "additional_sops": [
            {
                "title": "Escalating Reconciliation Issues to Cross-Functional Stakeholders",
                "link": "https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/460194134",
                "note": "For escalation procedures"
            }
        ]
    },
    
    "Recovery Wire": {
        "labeling": "If the account is 'Chase Recovery' you should label that BT as Recovery Wire",
        "reconciliation": "If there is a BT that is labeled as Risk, you should wait until 12 pm PST to reach out Risk Team. You can use the risk-payments slack channel to reach the Risk Team. There are two teams that record BTs. If the account of the BT is 'recovery' you should reach out collections team through the risk-payments channel. (Recovery) —> Risk Channel —> collections",
        "sop_page": "Daily Operations : How to Label & Reconcile",
        "sop_link": "https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/535003232",
        "additional_sops": [
            {
                "title": "Escalating Reconciliation Issues to Cross-Functional Stakeholders",
                "link": "https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/460194134",
                "note": "For escalation procedures"
            }
        ]
    },
    
    "Check": {
        "labeling": "When you see check paid as the BT's payment method, you should label that BT as Check",
        "reconciliation": "First, check the suggestions in the reconciliation queue. If you cannot locate the check in suggestions, go to the banking portal and review the check image to verify the details before reconciling.",
        "sop_page": "Daily Operations : How to Label & Reconcile",
        "sop_link": "https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/535003232",
        "additional_sops": [
            {
                "title": "Double Cashed Checks",
                "link": "https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/169411043",
                "note": "⚠️ ONLY for double-cashed check scenarios - this is a critical issue"
            }
        ]
    },
    
    "NY WH": {
        "labeling": "When you see NYS DTF WT on BT's description you should label that BT as NY WH",
        "reconciliation": "If there is a BT that the agent is NY WTH, you will see some suggested transmissions. You should reconcile it with the oldest transmission since NY WTH BTs don't give us any identifying information",
        "sop_page": "Daily Operations : How to Label & Reconcile",
        "sop_link": "https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/535003232",
        "additional_sops": [
            {
                "title": "Manual Reconciliation by Agency",
                "link": "https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/169411539",
                "note": "For agency-specific manual reconciliation"
            }
        ]
    },
    
    "OH WH": {
        "labeling": "When you see OH WH TAX on BT's description you should label that BT as OH WH",
        "reconciliation": "If there is a BT that the agent is OH WH, you will see an IN ID NO in the description. This description contains zeros at the beginning. You should copy the ID number without the zeros and paste that number to the OH WTH section in the reconciliation cleanup dashboard (redash). Then, you will have the electronic payment ID. You should enter this ID as the transmission ID and select the electronic payment as the transmission type.",
        "sop_page": "Daily Operations : How to Label & Reconcile",
        "sop_link": "https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/535003232",
        "additional_sops": [
            {
                "title": "Manual Reconciliation by Agency",
                "link": "https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/169411539",
                "note": "For agency-specific manual reconciliation"
            }
        ]
    },
    
    "CSC": {
        "labeling": "When you see CSCXXXXXX on BT's description you should label that BT as CSC",
        "reconciliation": "If there is a BT that the agent is CSC, you will see some suggested transmissions. The description of the transmission (CSC 123456) should match with the description in the transaction (DESC=CSC123456). If they match, you should also check the origination account and the amount.",
        "sop_page": "Daily Operations : How to Label & Reconcile",
        "sop_link": "https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/535003232"
    },
    
    "LOI": {
        "labeling": "When you see Remark: ACH RETURN SETTLEMENT on BT's description you should label that BT as LOI. If the description includes 'CREDIT MEMO', the BT should be labeled as 'LOI'.",
        "reconciliation": "Locate the customer reference number on the bank transaction. This field will tell you what JPA investigation ID this return is associated with. The field is limited to 10 characters - the first 6 digits is the date and you'll need to put leading zeros to make the last 6. Plug in the JPA Investigation ID into your search box in your email to locate the case. Locate the earliest email from CB Fraud Support with this investigation ID to see the original payment(s) the LOI was for. Open the attachment titled 'Agreement and Schedule for Case [XXXXXXX]' and scroll to Schedule 1 section to locate the payments. Use the individual ID(s) that starts with '6sem...' code to look up the nachas and reconcile.",
        "sop_page": "Letter of Indemnity Process and Reconciliation",
        "sop_link": "https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/298583554"
    },
    
    "Lockbox": {
        "labeling": "When you see Lockbox on the BT's description you should label that BT as Lockbox",
        "reconciliation": "Lockbox transactions are reconciled by matching with suggested transmissions. Check the lockbox deposit details and reconcile with the corresponding payments.",
        "sop_page": "Daily Operations : How to Label & Reconcile",
        "sop_link": "https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/535003232",
        "additional_sops": [
            {
                "title": "Lockbox Investigations",
                "link": "https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/169411804",
                "note": "For Lockbox-specific investigation procedures"
            }
        ]
    },
    
    "OH SDWH": {
        "labeling": "When you see OH SDWH on BT's description you should label that BT as OH SDWH",
        "reconciliation": "Ohio School District Withholding. Follow similar procedure to OH WH - check for identifying information in the description and match with suggested transmissions. May require lookup in OH reconciliation dashboard.",
        "sop_page": "Daily Operations : How to Label & Reconcile",
        "sop_link": "https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/535003232"
    },
    
    "ICP Funding": {
        "labeling": "When you see Chase International Contractor Payment as the account and 'TRANSFER FROM ACCOUNT000000807737908' in the description, you should label that BT as ICP Funding. In total, there will be 2 BTs to be labeled as ICP Funding and both of them will have 'REMARK=JPMORGAN ACCESS TRANSFER' on their description. When you see 'REMARK=JPMORGAN ACCESS TRANSFER' on BT's description label that BT as ICP Funding. There will be two ICP funding BTs, one from Chase ICP account and one from Chase Ops.",
        "reconciliation": "ICP Funding is handled like Treasury Transfer. Use the EP creator tool under the Custom Reporting flow. Use Unintended Overpayment Account as the Payment Account type and use the ZenPayroll ID as the company ID. Note which direction the transaction is for (debit/credit) and select the correct direction type for Transaction type. First, you should search the amount in your mail. If no relative email exists you should search for electronic payment. You start to reconcile with wire out. If the electronic payment with the same amount does not exist, you should use the Electronic Payment Creator Tool.",
        "sop_page": "Daily Operations : How to Label & Reconcile",
        "sop_link": "https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/535003232",
        "additional_sops": [
            {
                "title": "Unintended Overpayment Account Use Cases",
                "link": "https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/169412167",
                "note": "⭐ ICP Funding is handled like Treasury Transfer - use this SOP"
            },
            {
                "title": "Escalating Reconciliation Issues to Cross-Functional Stakeholders",
                "link": "https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/460194134",
                "note": "For escalation procedures"
            },
            {
                "title": "International Contractor Payment Funding",
                "link": "https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/169411829",
                "note": "ICP-specific funding procedures"
            },
            {
                "title": "Reconciling DLocal Transactions Manually",
                "link": "https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/169411668",
                "note": "For DLocal transactions - ONLY if description contains 'DLOCAL'"
            }
        ]
    },
    
    "NY UI": {
        "labeling": "When you see NYS DOL UI on BT's description you should label that BT as NY UI",
        "reconciliation": "State unemployment insurance transaction. Follow standard state agency reconciliation procedures. Match with suggested transmissions based on the NY DOL UI identifier in the description.",
        "sop_page": "Daily Operations : How to Label & Reconcile",
        "sop_link": "https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/535003232"
    },
    
    # NEW LABELS FROM SOP
    "Bad Debt": {
        "labeling": "When you see various transmissions with an amount less than $1.00 you should label them as Bad Debt (For Example: $0.01, $0.02, $0.03…)",
        "reconciliation": "Bad debt transactions (amounts < $1) are typically reconciled by matching with suggested micro-payments. These are often test transactions or rounding adjustments.",
        "sop_page": "Daily Operations : How to Label & Reconcile",
        "sop_link": "https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/535003232"
    },
    
    "ICP Return": {
        "labeling": "When you see Chase International Contractor Payment as the account and 'ach external' as the method you should label that BT as ICP Return",
        "reconciliation": "ICP Returns require escalation. Reach out to the appropriate team via the payment-ops-recon Slack channel. Include BT details, company information, and payment reference.",
        "sop_page": "Daily Operations : How to Label & Reconcile",
        "sop_link": "https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/535003232",
        "additional_sops": [
            {
                "title": "Escalating Reconciliation Issues to Cross-Functional Stakeholders",
                "link": "https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/460194134",
                "note": "For ICP-related escalation procedures"
            }
        ]
    },
    
    "ICP": {
        "labeling": "When you see 'ORIG CO NAME=DLOCAL' (sometimes it might be DLOCL) on BT's description label that BT as ICP",
        "reconciliation": "For DLocal (ICP) transactions, follow the manual reconciliation procedure. Check the DLocal reconciliation SOP for specific steps. If issues arise, escalate to payment-ops-recon Slack channel.",
        "sop_page": "Daily Operations : How to Label & Reconcile",
        "sop_link": "https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/535003232",
        "additional_sops": [
            {
                "title": "Reconciling DLocal Transactions Manually",
                "link": "https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/169411668",
                "note": "⭐ Primary SOP for DLocal/ICP transactions"
            },
            {
                "title": "Escalating Reconciliation Issues to Cross-Functional Stakeholders",
                "link": "https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/460194134",
                "note": "For escalation procedures"
            }
        ]
    },
    
    "NM UI": {
        "labeling": "When you see STATE OF NM DWS ENTRY DESCR: UI PAYMENT on BT's description you should label that BT as NM UI",
        "reconciliation": "New Mexico Unemployment Insurance. State UI transaction - follow standard state unemployment insurance reconciliation procedures. Match with suggested transmissions.",
        "sop_page": "Daily Operations : How to Label & Reconcile",
        "sop_link": "https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/535003232"
    },
    
    "WA ESD": {
        "labeling": "If the account is Chase Operations and the description contains STATE OF WA ESD you should label that BT as WA ESD. If the account is PNC Operations and the description contains ESD WA UI-TAX you should label that BT as WA ESD",
        "reconciliation": "Washington Employment Security Department (Unemployment). State UI transaction - follow standard state unemployment insurance reconciliation procedures. Match with suggested transmissions.",
        "sop_page": "Daily Operations : How to Label & Reconcile",
        "sop_link": "https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/535003232"
    },
    
    "IL UI": {
        "labeling": "When you see IL DEPT EMPL SEC on BT's description you should label that BT as IL UI",
        "reconciliation": "If there is a BT that is labeled as IL UI you should find the company name in the description. You should write this company name to Reconciliation Clean Up on redash. (https://redash.zp-int.com/dashboard/reconciliation-cleanup) You can find the agent payment link and electronic payment id. You should reconcile with the electronic payment ip.",
        "sop_page": "Daily Operations : How to Label & Reconcile",
        "sop_link": "https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/535003232"
    },
    
    "MT UI": {
        "labeling": "When you see MT TAX or STATE OF MONTANA on BT's description you should label that BT as MT UI",
        "reconciliation": "Montana Unemployment Insurance. State UI transaction - follow standard state unemployment insurance reconciliation procedures. Match with suggested transmissions.",
        "sop_page": "Daily Operations : How to Label & Reconcile",
        "sop_link": "https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/535003232"
    },
    
    "York Adams Tax": {
        "labeling": "When you see YORK ADAMS TAX on BT's description you should label that BT as York Adams Tax",
        "reconciliation": "Local tax transaction (York Adams area). Follow standard local tax reconciliation procedures.",
        "sop_page": "Daily Operations : How to Label & Reconcile",
        "sop_link": "https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/535003232"
    },
    
    "WA LNI": {
        "labeling": "When you see L&I or Labor&Industries on BT's description you should label that BT as WA LNI",
        "reconciliation": "WA LNI : It could be checked by the Reconciliation Cleanup board",
        "sop_page": "Daily Operations : How to Label & Reconcile",
        "sop_link": "https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/535003232"
    },
    
    "Berks Tax": {
        "labeling": "When you see Berks EIT on BT's description you should label that BT as Berks Tax",
        "reconciliation": "Local tax transaction (Berks County EIT). Follow standard local tax reconciliation procedures.",
        "sop_page": "Daily Operations : How to Label & Reconcile",
        "sop_link": "https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/535003232"
    },
    
    "Money Market Fund": {
        "labeling": "When you see MONEY MKT MUTUAL FUND on BT's description you should label that BT as Money Market Fund",
        "reconciliation": "Use the EP creator tool under the Custom Reporting flow. Use Unintended Overpayment Account as the Payment Account type and use the ZenPayroll ID as the company ID. Select the appropriate Transaction Type under Payment Record Information based on whether the transaction is debit or credit.",
        "sop_page": "Unintended Overpayment Account Use Cases",
        "sop_link": "https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/169412167"
    },
    
    "Blueridge Interest": {
        "labeling": "When you see Accrued Int. on BT's description and its bank is Blueridge, you should label that BT as Blueridge Interest",
        "reconciliation": "Use the EP creator tool under the Custom Reporting flow. Use Unintended Overpayment Account as the Payment Account type and use the ZenPayroll ID as the company ID. Select Interest Income as both the Transaction Type and Transaction Category under Payment Record Information. You will not need to fill out the Optional Payment Record field.",
        "sop_page": "Unintended Overpayment Account Use Cases",
        "sop_link": "https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/169412167"
    },
    
    "ACH Reversal": {
        "labeling": "When you see ACH CREDIT SETTLEMENT on BT's description, you should label that BT as ACH Reversal",
        "reconciliation": "ACH Reversals require investigation. Find the original payment and document the reversal reason. Escalate if needed.",
        "sop_page": "Daily Operations : How to Label & Reconcile",
        "sop_link": "https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/535003232"
    },
    
    "ACH": {
        "labeling": "When you see REMARK=EFT REVERSAL on BT's description, you should label that BT as ACH",
        "reconciliation": "If there is a BT that is labeled as ACH you should reconcile with the recommended transmission including the same description. An example for CON12345, the description of the BT is DESC:CON750119. You can find the same description in the suggested BTs' description.",
        "sop_page": "Daily Operations : How to Label & Reconcile",
        "sop_link": "https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/535003232"
    },
    
    "Interest Adjustment": {
        "labeling": "When you see REMARK=INTEREST ADJUSTMENT on BT's description, you should label that BT as Interest Adjustment",
        "reconciliation": "Use the EP creator tool under the Custom Reporting flow. Use Unintended Overpayment Account as the Payment Account type and use the ZenPayroll ID as the company ID. Select Interest Income as both the Transaction Type and Transaction Category under Payment Record Information. You will not need to fill out the Optional Payment Record field.",
        "sop_page": "Unintended Overpayment Account Use Cases",
        "sop_link": "https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/169412167"
    },
    
    "ACH Return": {
        "labeling": "When you see RTN OFFSET on BT's description, you should label that BT as ACH Return",
        "reconciliation": "ACH Returns must be researched. Check return reason code, match with original payment, and investigate. Escalate if needed.",
        "sop_page": "Daily Operations : How to Label & Reconcile",
        "sop_link": "https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/535003232"
    },
    
    "VA UI": {
        "labeling": "When you see VA. EMPLOY COMM on BT's description, you should label that BT as VA UI",
        "reconciliation": "Virginia Unemployment Insurance. State UI transaction - follow standard state unemployment insurance reconciliation procedures.",
        "sop_page": "Daily Operations : How to Label & Reconcile",
        "sop_link": "https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/535003232"
    },
    
    "Treasury Transfer": {
        "labeling": "When you see US TREASURY CAPITAL on BT's description, you should label that BT as Treasury Transfer",
        "reconciliation": "If you see any transfers created from Treasury team that relate to funds being swept out of corporate account, use the EP creator tool under the Custom Reporting flow. Use Unintended Overpayment Account as the Payment Account type and use the ZenPayroll ID as the company ID. Note which direction the transaction is for (debit/credit) and select the correct direction type for Transaction type (Debit/Credit treasury funding).",
        "sop_page": "Unintended Overpayment Account Use Cases",
        "sop_link": "https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/169412167"
    },
    
    # STATE WITHHOLDING - Additional States (not in primary SOP, follow similar patterns to NY WH/OH WH)
    "CA EDD": {
        "labeling": "When you see CA EDD on BT's description you should label that BT as CA EDD",
        "reconciliation": "State tax transaction. Similar to NY WH/OH WH - check for identifying information in description and match with suggested transmissions."
    },
    
    "TX WH": {
        "labeling": "When you see TX or Texas withholding tax on BT's description you should label that BT as TX WH",
        "reconciliation": "State tax transaction. Similar to NY WH/OH WH - match with suggested transmissions."
    },
    
    "MA WH": {
        "labeling": "When you see MA or Massachusetts withholding tax on BT's description you should label that BT as MA WH",
        "reconciliation": "State tax transaction. Similar to NY WH/OH WH - match with suggested transmissions."
    },
    
    "PA WH": {
        "labeling": "When you see PA or Pennsylvania withholding tax on BT's description you should label that BT as PA WH",
        "reconciliation": "State tax transaction. Similar to NY WH/OH WH - match with suggested transmissions."
    },
    
    "IL WH": {
        "labeling": "When you see IL or Illinois withholding tax on BT's description you should label that BT as IL WH",
        "reconciliation": "State tax transaction. Similar to NY WH/OH WH - match with suggested transmissions."
    },
    
    "NJ WH": {
        "labeling": "When you see NJ or New Jersey withholding tax on BT's description you should label that BT as NJ WH",
        "reconciliation": "State tax transaction. Similar to NY WH/OH WH - match with suggested transmissions."
    },
    
    "MI WH": {
        "labeling": "When you see MI or Michigan withholding tax on BT's description you should label that BT as MI WH",
        "reconciliation": "State tax transaction. Similar to NY WH/OH WH - match with suggested transmissions."
    },
    
    "VA WH": {
        "labeling": "When you see VA or Virginia withholding tax on BT's description you should label that BT as VA WH",
        "reconciliation": "State tax transaction. Similar to NY WH/OH WH - match with suggested transmissions."
    },
    
    "GA WH": {
        "labeling": "When you see GA or Georgia withholding tax on BT's description you should label that BT as GA WH",
        "reconciliation": "State tax transaction. Similar to NY WH/OH WH - match with suggested transmissions."
    },
    
    "NC WH": {
        "labeling": "When you see NC or North Carolina withholding tax on BT's description you should label that BT as NC WH",
        "reconciliation": "State tax transaction. Similar to NY WH/OH WH - match with suggested transmissions."
    },
    
    "MD WH": {
        "labeling": "When you see MD or Maryland withholding tax on BT's description you should label that BT as MD WH",
        "reconciliation": "State tax transaction. Similar to NY WH/OH WH - match with suggested transmissions."
    },
    
    "CO WH": {
        "labeling": "When you see CO or Colorado withholding tax on BT's description you should label that BT as CO WH",
        "reconciliation": "State tax transaction. Similar to NY WH/OH WH - match with suggested transmissions."
    },
}

# Count total labels
print(f"\n✅ Total labels in SOP: {len(COMPLETE_SOP_MAPPING)}")
print("\nLabels with reconciliation info:")
for label, info in COMPLETE_SOP_MAPPING.items():
    if info['reconciliation']:
        print(f"  - {label}")

