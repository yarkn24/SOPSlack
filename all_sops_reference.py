#!/usr/bin/env python3
"""
ALL SOPs Reference - Complete list of available SOPs
"""

# MAIN 3 SOPs (Primary - used for labeling and reconciliation)
MAIN_SOPS = {
    "daily_operations": {
        "title": "Daily Operations : How to Label & Reconcile",
        "url": "https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/535003232",
        "purpose": "Primary SOP for labeling and reconciliation instructions"
    },
    "letter_of_indemnity": {
        "title": "Letter of Indemnity Process and Reconciliation",
        "url": "https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/298583554",
        "purpose": "LOI-specific reconciliation process"
    },
    "unintended_overpayment": {
        "title": "Unintended Overpayment Account Use Cases",
        "url": "https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/169412167",
        "purpose": "Treasury, Money Market, Interest payments reconciliation"
    }
}

# ADDITIONAL SOPs (Reference - for specific scenarios and escalations)
ADDITIONAL_SOPS = {
    "manual_reconciliation_checks": {
        "title": "Manual Reconciliation Checks",
        "url": "https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/169412024",
        "purpose": "Additional manual reconciliation procedures"
    },
    "escalating_issues": {
        "title": "Escalating Reconciliation Issues to Cross-Functional Stakeholders",
        "url": "https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/460194134",
        "purpose": "When to escalate and who to contact"
    },
    "repayment_reporter": {
        "title": "Repayment Reporter Tool SOP",
        "url": "https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/76383876",
        "purpose": "Repayment reconciliation tool usage"
    },
    "double_cashed_checks": {
        "title": "Double Cashed Checks",
        "url": "https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/169411043",
        "purpose": "Handling double-cashed check scenarios"
    },
    "lockbox_investigations": {
        "title": "Lockbox Investigations",
        "url": "https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/169411804",
        "purpose": "Lockbox-specific investigation procedures"
    },
    "icp_funding": {
        "title": "International Contractor Payment Funding",
        "url": "https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/169411829",
        "purpose": "ICP-specific funding and reconciliation"
    },
    "reconciling_dlocal": {
        "title": "Reconciling DLocal Transactions Manually",
        "url": "https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/169411668",
        "purpose": "DLocal/ICP manual reconciliation"
    },
    "microvariance_adjuster": {
        "title": "Microvariance Adjuster Tool",
        "url": "https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/76385735",
        "purpose": "Handling microvariances and Bad Debt"
    },
    "blueridge_microvariance": {
        "title": "Unreconciled Transactions Due to Blueridge Ops Microvariance Write-offs",
        "url": "https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/433849552",
        "purpose": "Blueridge-specific microvariance handling"
    },
    "modern_treasury": {
        "title": "Modern Treasury",
        "url": "https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/76385861",
        "purpose": "Modern Treasury platform usage"
    }
}

print("=" * 80)
print("ALL AVAILABLE SOPs")
print("=" * 80)

print("\n📌 MAIN 3 SOPs (Primary):")
for key, sop in MAIN_SOPS.items():
    print(f"\n  ✅ {sop['title']}")
    print(f"     {sop['url']}")
    print(f"     Purpose: {sop['purpose']}")

print("\n\n📚 ADDITIONAL SOPs (Reference):")
for key, sop in ADDITIONAL_SOPS.items():
    print(f"\n  • {sop['title']}")
    print(f"    {sop['url']}")
    print(f"    Purpose: {sop['purpose']}")

print("\n" + "=" * 80)
print(f"Total: {len(MAIN_SOPS)} Main SOPs + {len(ADDITIONAL_SOPS)} Additional SOPs")
print("=" * 80)

