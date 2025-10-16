"""
Agent-SOP Mapping
=================
Maps each agent to its labeling rules and reconciliation SOP articles.
This will be used for:
1. Slack notifications (which SOP to follow)
2. Fine-tuning the ML model with SOP context
3. Daily operations guidance

Author: Yarkin Akcil
Date: October 6, 2025
"""

AGENT_SOP_MAPPING = {
    
    # ============================================================
    # WIRE TRANSFERS & INTERNATIONAL PAYMENTS
    # ============================================================
    
    "Risk": {
        "labeling_rules": [
            "Description contains '1TRV' → ALWAYS Risk (definitive, overrides all other rules)",
            "Account 6, 7, 9, or 18 (Chase Wire-in, PNC Wire-in, Chase Payroll Incoming Wire)",
            "Payment Method 0 (Wire)",
        ],
        "reconciliation_steps": [
            "Open Modern Treasury and navigate to 'Incoming Wires' section",
            "Search for the transaction using the 1TRV reference code from the bank narrative",
            "Verify that the wire transfer matches an expected Risk payment in the system",
            "Check that the origination account matches the approved Risk sender list",
            "Validate that the amount matches the expected payment amount (within $0.01 tolerance)",
            "If matched: Mark transaction as 'Risk' and link to the Modern Treasury payment ID",
            "If unmatched: Escalate to Risk team via #risk-operations channel with transaction details",
            "Document any discrepancies in the transaction comments section",
        ],
        "sop_section": "Wire Transfer Reconciliation → Risk Payments (1TRV Code)",
        "sop_quote": "All transactions containing '1TRV' code in the description MUST be labeled as Risk, regardless of account or payment method. These are wire transfers from Risk's international payment processor and require validation in Modern Treasury before reconciliation.",
        "confluence_links": [            "https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/460194134/Escalating+Reconciliation+Issues+to+Cross-Functional+Stakeholders",
            "https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/169411126/Daily+Bank+Transaction+Reconciliation+by+Bank+Transaction+Type",
        ],
        "frequency": "HIGH",
        "criticality": "CRITICAL",
        "typical_amount_range": "$1,000 - $50,000",
        "escalation_threshold": "> $100,000 or unmatched transaction",
    },
    
    "Recovery Wire": {
        "labeling_rules": [
            "Account 28 (Chase Recovery Wire-in) AND no '1TRV' in description",
            "Large amounts (typically >$25K) to Recovery account",
            "Payment Method 0 (Wire)",
        ],
        "reconciliation_steps": [
            "Verify recovery wire in Modern Treasury",
            "Match with expected recovery payments",
            "Check if mistakenly sent to wrong account (if 1TRV present, should be Risk)",
        ],
        "confluence_links": [            "https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/460194134/Escalating+Reconciliation+Issues+to+Cross-Functional+Stakeholders",
            "https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/169411126/Daily+Bank+Transaction+Reconciliation+by+Bank+Transaction+Type",],
        "frequency": "HIGH",
        "criticality": "CRITICAL",
    },
    
    "Nium Payment": {
        "labeling_rules": [
            "Description contains 'NIUM' (definitive)",
            "Account 21 (Chase International Contractor Payments)",
            "Payment Method 10 (ACH External)",
        ],
        "reconciliation_steps": [
            "Verify Nium payment details",
            "Match with contractor payment records",
            "Check for proper NIUM descriptor",
            "If amount > $300K, escalate using Cross-Functional Stakeholders process",
        ],
        "confluence_links": [            "https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/460194134/Escalating+Reconciliation+Issues+to+Cross-Functional+Stakeholders",
            "https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/169411126/Daily+Bank+Transaction+Reconciliation+by+Bank+Transaction+Type",],
        "frequency": "MEDIUM",
        "criticality": "HIGH",
    },
    
    # ============================================================
    # TREASURY & ICP OPERATIONS
    # ============================================================
    
    "ICP Funding": {
        "labeling_rules": [
            "Account 21 (Chase ICP) + 'REMARK=JPMORGAN ACCESS TRANSFER FROM' (definitive)",
            "Paired transactions: Same amount to/from Chase Ops",
            "Payment Method 8 (Unknown) - but this is expected for these transfers",
        ],
        "reconciliation_steps": [
            "Verify paired transaction exists with matching amount",
            "Confirm both legs of the transfer (ICP → Ops, Ops → ICP)",
            "Match with internal funding records",
            "If amount > $300K, escalate using Cross-Functional Stakeholders process",
        ],
        "confluence_links": [            "https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/460194134/Escalating+Reconciliation+Issues+to+Cross-Functional+Stakeholders",
            "https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/169411126/Daily+Bank+Transaction+Reconciliation+by+Bank+Transaction+Type",],
        "frequency": "MEDIUM",
        "criticality": "HIGH",
        "note": "Rare but financially critical - requires paired transaction logic",
    },
    
    "Treasury Transfer": {
        "labeling_rules": [
            "Description: 'REMARK=JPMORGAN ACCESS TRANSFER' (not to/from ICP)",
            "Internal treasury movements",
        ],
        "reconciliation_steps": [
            "Verify treasury transfer authorization",
            "Match with internal transfer records",
            "Confirm both sides of transfer",
            "Check Unintended Overpayment Account Use Cases SOP for treasury funding",
        ],
        "confluence_links": [            "https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/169411126/Daily+Bank+Transaction+Reconciliation+by+Bank+Transaction+Type",],
        "frequency": "MEDIUM",
        "criticality": "MEDIUM",
        "note": "Unintended Overpayment Account Use Cases SOP applies for Treasury Funding",
    },
    
    "Money Market Transfer": {
        "labeling_rules": [
            "Description: 'REMARK=100% US TREASURY CAPITAL 3163 AT NAV OF 1.0000' (definitive)",
            "Description: 'MONEY MKT MUTUAL FUND'",
        ],
        "reconciliation_steps": [
            "Verify money market account movement",
            "Match with treasury management records",
            "Check Unintended Overpayment Account Use Cases SOP",
        ],
        "confluence_links": [            "https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/169411126/Daily+Bank+Transaction+Reconciliation+by+Bank+Transaction+Type",],
        "frequency": "LOW",
        "criticality": "MEDIUM",
        "note": "Unintended Overpayment Account Use Cases SOP applies",
    },
    
    "ZBT": {
        "labeling_rules": [
            "Payment Method 12 (definitive - this is ZBT by definition)",
            "Zero Balance Transfer operations",
        ],
        "reconciliation_steps": [
            "Verify ZBT sweep configuration",
            "Match with expected balance transfers",
        ],
        "confluence_links": [            "https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/169411126/Daily+Bank+Transaction+Reconciliation+by+Bank+Transaction+Type",],
        "frequency": "MEDIUM",
        "criticality": "MEDIUM",
    },
    
    # ============================================================
    # BLUERIDGE ACCOUNTS (26 & 28)
    # ============================================================
    
    "Bad Debt": {
        "labeling_rules": [
            "Account 26 (Blueridge Operations)",
            "Amount < $0.50 (definitive for small amounts)",
            "Description: 'ITT GUSTO CORPORATE CCD'",
        ],
        "reconciliation_steps": [
            "Verify bad debt classification",
            "Match with bad debt records",
            "Confirm amount threshold",
        ],
        "confluence_links": [            "https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/169411126/Daily+Bank+Transaction+Reconciliation+by+Bank+Transaction+Type",],
        "frequency": "MEDIUM",
        "criticality": "LOW",
    },
    
    "BRB": {
        "labeling_rules": [
            "Account 26 (Blueridge Operations)",
            "Amount > $0.50",
            "If description has 'check' or 'interest', label accordingly",
        ],
        "reconciliation_steps": [
            "Verify BRB transaction details",
            "Match with Blueridge records",
        ],
        "confluence_links": [            "https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/169411126/Daily+Bank+Transaction+Reconciliation+by+Bank+Transaction+Type",],
        "frequency": "MEDIUM",
        "criticality": "MEDIUM",
    },
    
    "Interest Adjustment": {
        "labeling_rules": [
            "Description: 'INTEREST ADJUSTMENT' (definitive)",
            "Account 28 (Blueridge Recovery) + 'INTEREST' in description",
        ],
        "reconciliation_steps": [
            "Verify interest adjustment calculation",
            "Match with bank interest records",
            "Check Unintended Overpayment Account Use Cases SOP for Interest Income",
        ],
        "confluence_links": [            "https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/169411126/Daily+Bank+Transaction+Reconciliation+by+Bank+Transaction+Type",],
        "frequency": "LOW",
        "criticality": "LOW",
        "note": "Unintended Overpayment Account Use Cases SOP applies for Interest Income",
    },
    
    # ============================================================
    # ACH OPERATIONS
    # ============================================================
    
    "ACH": {
        "labeling_rules": [
            "Payment Method 10 (ACH External) - high confidence",
            "Payment Method 4 (ACH) - 97.1% confidence",
            "NOT Company Balance Transfer (discontinued)",
        ],
        "reconciliation_steps": [
            "Verify ACH transaction details",
            "Match with expected ACH payments",
            "Check payment method classification",
        ],
        "confluence_links": [            "https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/169411126/Daily+Bank+Transaction+Reconciliation+by+Bank+Transaction+Type",],
        "frequency": "HIGH",
        "criticality": "MEDIUM",
    },
    
    # ============================================================
    # CHECK OPERATIONS
    # ============================================================
    
    "Check": {
        "labeling_rules": [
            "Payment Method 2 (Check)",
            "Description contains 'check' patterns",
        ],
        "reconciliation_steps": [
            "Verify check number and amount",
            "Match with check register",
            "Confirm payee information",
        ],
        "confluence_links": [            "https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/169411126/Daily+Bank+Transaction+Reconciliation+by+Bank+Transaction+Type",],
        "frequency": "MEDIUM",
        "criticality": "MEDIUM",
    },
    
    "Lockbox": {
        "labeling_rules": [
            "Description contains 'LOCKBOX' (definitive)",
        ],
        "reconciliation_steps": [
            "Verify lockbox deposit details",
            "Match with lockbox reports",
        ],
        "confluence_links": [            "https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/169411126/Daily+Bank+Transaction+Reconciliation+by+Bank+Transaction+Type",],
        "frequency": "LOW",
        "criticality": "LOW",
    },
    
    # ============================================================
    # ICP OPERATIONS
    # ============================================================
    
    "ICP Return": {
        "labeling_rules": [
            "Description: 'TS FX ACCOUNTS RECEIVABLE'",
            "Description: 'JPV' followed by numbers (ticket number, e.g., 'JPV230104')",
        ],
        "reconciliation_steps": [
            "Verify ICP return reason",
            "Match with original ICP transaction",
            "Check ticket number in Jira",
            "If amount > $300K, escalate using Cross-Functional Stakeholders process",
        ],
        "confluence_links": [            "https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/460194134/Escalating+Reconciliation+Issues+to+Cross-Functional+Stakeholders",
            "https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/169411126/Daily+Bank+Transaction+Reconciliation+by+Bank+Transaction+Type",],
        "frequency": "LOW",
        "criticality": "MEDIUM",
    },
    
    "ICP Refund": {
        "labeling_rules": [
            "Description contains 'WISE'",
            "Amount typically < $50K",
        ],
        "reconciliation_steps": [
            "Verify refund reason and amount",
            "Match with original ICP payment",
            "If amount > $300K, escalate using Cross-Functional Stakeholders process",
        ],
        "confluence_links": [            "https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/460194134/Escalating+Reconciliation+Issues+to+Cross-Functional+Stakeholders",
            "https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/169411126/Daily+Bank+Transaction+Reconciliation+by+Bank+Transaction+Type",],
        "frequency": "LOW",
        "criticality": "MEDIUM",
    },
    
    # ============================================================
    # TAX & PAYROLL WITHHOLDINGS
    # ============================================================
    
    "NY WH": {
        "labeling_rules": [
            "Description: 'NYS DTF WT' (New York State withholding tax)",
        ],
        "reconciliation_steps": [
            "Verify NY withholding tax amount",
            "Match with payroll records",
        ],
        "confluence_links": [            "https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/169411126/Daily+Bank+Transaction+Reconciliation+by+Bank+Transaction+Type",],
        "frequency": "MEDIUM",
        "criticality": "HIGH",
        "note": "No specific SOP available - use general reconciliation procedures",
    },
    
    "NY UI": {
        "labeling_rules": [
            "Description: 'NYS DOL UI' (New York State unemployment insurance)",
        ],
        "reconciliation_steps": [
            "Verify NY UI payment amount",
            "Match with payroll records",
        ],
        "confluence_links": [            "https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/169411126/Daily+Bank+Transaction+Reconciliation+by+Bank+Transaction+Type",],
        "frequency": "MEDIUM",
        "criticality": "HIGH",
        "note": "No specific SOP available - use general reconciliation procedures",
    },
    
    "MT WH": {
        "labeling_rules": [
            "Description: 'STATE OF MONTANA' (Montana withholding)",
        ],
        "reconciliation_steps": [
            "Verify MT withholding tax amount",
            "Match with payroll records",
        ],
        "confluence_links": [            "https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/169411126/Daily+Bank+Transaction+Reconciliation+by+Bank+Transaction+Type",],
        "frequency": "LOW",
        "criticality": "HIGH",
        "note": "No specific SOP available - use general reconciliation procedures",
    },
    
    "PA UI": {
        "labeling_rules": [
            "Description: 'ORIG CO NAME=KEYSTONE'",
        ],
        "reconciliation_steps": [
            "Verify PA UI payment amount",
            "Match with payroll records",
        ],
        "confluence_links": [            "https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/169411126/Daily+Bank+Transaction+Reconciliation+by+Bank+Transaction+Type",],
        "frequency": "LOW",
        "criticality": "HIGH",
        "note": "No specific SOP available - use general reconciliation procedures",
    },
    
    "Unclaimed Property": {
        "labeling_rules": [
            "Description: 'GUSTOCUSTDEP' AND 'PRFUND' (Gusto Customer Deposit Pre-funding)",
            "Account 3 (Chase Operations)",
            "Payment Method 4 (ACH Transaction)",
            "Entry Description: 'PAYROLL' or 'CORP PAY'",
        ],
        "reconciliation_steps": [
            "Verify unclaimed property transmission records",
            "Match with state-specific unclaimed property batches (NY, PA, etc.)",
            "Check if manual transmission generation is required",
            "Reconcile with Electronic Payment records in Modern Treasury",
        ],
        "confluence_links": [
            "https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/169411126/Daily+Bank+Transaction+Reconciliation+by+Bank+Transaction+Type",
        ],
        "frequency": "MEDIUM",
        "criticality": "HIGH",
        "note": "Often requires manual reconciliation. Check with Amanda Wong or Platform Ops team if transmission generation needed.",
    },
    
    "York Adams": {
        "labeling_rules": [
            "Description: 'York Adams Tax' or 'York Adams Tax EIT'",
            "Consolidated label (previously separate)",
        ],
        "reconciliation_steps": [
            "Verify York Adams tax payment",
            "Match with local tax records",
        ],
        "confluence_links": [            "https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/169411126/Daily+Bank+Transaction+Reconciliation+by+Bank+Transaction+Type",],
        "frequency": "LOW",
        "criticality": "MEDIUM",
    },
    
    # ============================================================
    # PNC OPERATIONS
    # ============================================================
    
    "LOI": {
        "labeling_rules": [
            "Description: 'CREDIT MEMO' + PNC account (e.g., Account 16)",
        ],
        "reconciliation_steps": [
            "Verify LOI (Letter of Indemnity) details",
            "Match with PNC credit memo records",
            "Follow Letter of Indemnity Process and Reconciliation SOP",
        ],
        "confluence_links": [            "https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/298583554/Letter+of+Indemnity+Process+and+Reconciliation",
            "https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/169411126/Daily+Bank+Transaction+Reconciliation+by+Bank+Transaction+Type",],
        "frequency": "LOW",
        "criticality": "MEDIUM",
    },
    
}


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def get_agent_sop(agent_name):
    """
    Get SOP information for a specific agent.
    
    Args:
        agent_name: Name of the agent
        
    Returns:
        Dictionary with SOP info, or None if not found
    """
    return AGENT_SOP_MAPPING.get(agent_name)


def get_confluence_links_for_agent(agent_name):
    """
    Get list of Confluence links relevant to an agent.
    
    Args:
        agent_name: Name of the agent
        
    Returns:
        List of Confluence URLs, or empty list if not found
    """
    agent_info = AGENT_SOP_MAPPING.get(agent_name)
    if agent_info:
        return agent_info.get("confluence_links", [])
    return []


def get_all_agents():
    """Get list of all mapped agents."""
    return list(AGENT_SOP_MAPPING.keys())


def get_critical_agents():
    """Get list of agents with CRITICAL criticality."""
    return [
        agent for agent, info in AGENT_SOP_MAPPING.items()
        if info.get("criticality") == "CRITICAL"
    ]


def export_for_fine_tuning():
    """
    Export agent-SOP mapping in a format suitable for fine-tuning.
    Returns a list of training examples.
    """
    training_examples = []
    
    for agent_name, info in AGENT_SOP_MAPPING.items():
        # Create a prompt-completion pair
        rules_text = "\n".join(f"- {rule}" for rule in info["labeling_rules"])
        recon_text = "\n".join(f"- {step}" for step in info["reconciliation_steps"])
        sop_text = "\n".join(f"- {link}" for link in info.get("confluence_links", []))
        
        prompt = f"Agent: {agent_name}\n\nLabeling Rules:\n{rules_text}"
        
        completion = f"""
Reconciliation Steps:
{recon_text}

Relevant SOP Links:
{sop_text}

Frequency: {info.get('frequency', 'N/A')}
Criticality: {info.get('criticality', 'N/A')}
"""
        if 'note' in info:
            completion += f"\nNote: {info['note']}"
        
        training_examples.append({
            "agent": agent_name,
            "prompt": prompt,
            "completion": completion.strip()
        })
    
    return training_examples


if __name__ == "__main__":
    print("=" * 80)
    print("AGENT-SOP MAPPING SUMMARY")
    print("=" * 80)
    print(f"\nTotal Agents Mapped: {len(AGENT_SOP_MAPPING)}")
    print(f"Critical Agents: {len(get_critical_agents())}")
    print("\nAgents:")
    for i, agent in enumerate(get_all_agents(), 1):
        info = AGENT_SOP_MAPPING[agent]
        print(f"{i:2d}. {agent:30s} | Freq: {info.get('frequency', 'N/A'):6s} | Crit: {info.get('criticality', 'N/A')}")
    
    print("\n" + "=" * 80)
    print("FINE-TUNING EXPORT SAMPLE")
    print("=" * 80)
    
    examples = export_for_fine_tuning()
    print(f"\nGenerated {len(examples)} training examples")
    print("\nSample (first agent):")
    print("-" * 80)
    print("PROMPT:")
    print(examples[0]["prompt"])
    print("\nCOMPLETION:")
    print(examples[0]["completion"])

