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
            "Verify wire transfer details in Modern Treasury",
            "Match with expected incoming Risk payments",
            "Check for 1TRV code compliance",
            "Validate origination account and amount",
        ],
        "confluence_pages": [
            "Daily Bank Transaction Reconciliation",
            "Wire Transfer Procedures",
            "Risk Payment Processing",
        ],
        "frequency": "HIGH",
        "criticality": "CRITICAL",
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
        "confluence_pages": [
            "Daily Bank Transaction Reconciliation",
            "Recovery Wire Processing",
        ],
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
        ],
        "confluence_pages": [
            "International Contractor Payments",
            "ACH Payment Overview",
        ],
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
        ],
        "confluence_pages": [
            "ICP Funding Procedures",
            "Internal Transfer Reconciliation",
        ],
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
        ],
        "confluence_pages": [
            "Treasury Transfer Procedures",
            "Internal Transfer Reconciliation",
        ],
        "frequency": "MEDIUM",
        "criticality": "MEDIUM",
    },
    
    "Money Market Transfer": {
        "labeling_rules": [
            "Description: 'REMARK=100% US TREASURY CAPITAL 3163 AT NAV OF 1.0000' (definitive)",
            "Description: 'MONEY MKT MUTUAL FUND'",
        ],
        "reconciliation_steps": [
            "Verify money market account movement",
            "Match with treasury management records",
        ],
        "confluence_pages": [
            "Money Market Reconciliation",
            "Treasury Management SOPs",
        ],
        "frequency": "LOW",
        "criticality": "MEDIUM",
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
        "confluence_pages": [
            "Zero Balance Transfer SOPs",
            "Daily Bank Transaction Reconciliation",
        ],
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
        "confluence_pages": [
            "Bad Debt Processing",
            "Blueridge Operations Reconciliation",
        ],
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
        "confluence_pages": [
            "Blueridge Operations Reconciliation",
        ],
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
        ],
        "confluence_pages": [
            "Interest Reconciliation",
            "Daily Bank Transaction Reconciliation",
        ],
        "frequency": "LOW",
        "criticality": "LOW",
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
        "confluence_pages": [
            "ACH Payment Overview",
            "Daily Bank Transaction Reconciliation",
        ],
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
        "confluence_pages": [
            "Check Reconciliation",
            "Daily Bank Transaction Reconciliation",
        ],
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
        "confluence_pages": [
            "Lockbox Reconciliation",
        ],
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
        ],
        "confluence_pages": [
            "ICP Return Processing",
            "International Contractor Payment Issues",
        ],
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
        ],
        "confluence_pages": [
            "ICP Refund Processing",
        ],
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
        "confluence_pages": [
            "Payroll Tax Reconciliation",
            "State Withholding Processing",
        ],
        "frequency": "MEDIUM",
        "criticality": "HIGH",
    },
    
    "NY UI": {
        "labeling_rules": [
            "Description: 'NYS DOL UI' (New York State unemployment insurance)",
        ],
        "reconciliation_steps": [
            "Verify NY UI payment amount",
            "Match with payroll records",
        ],
        "confluence_pages": [
            "Payroll Tax Reconciliation",
            "Unemployment Insurance Processing",
        ],
        "frequency": "MEDIUM",
        "criticality": "HIGH",
    },
    
    "MT WH": {
        "labeling_rules": [
            "Description: 'STATE OF MONTANA' (Montana withholding)",
        ],
        "reconciliation_steps": [
            "Verify MT withholding tax amount",
            "Match with payroll records",
        ],
        "confluence_pages": [
            "Payroll Tax Reconciliation",
            "State Withholding Processing",
        ],
        "frequency": "LOW",
        "criticality": "HIGH",
    },
    
    "PA UI": {
        "labeling_rules": [
            "Description: 'ORIG CO NAME=KEYSTONE'",
        ],
        "reconciliation_steps": [
            "Verify PA UI payment amount",
            "Match with payroll records",
        ],
        "confluence_pages": [
            "Payroll Tax Reconciliation",
            "Unemployment Insurance Processing",
        ],
        "frequency": "LOW",
        "criticality": "HIGH",
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
        "confluence_pages": [
            "Local Tax Reconciliation",
        ],
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
        ],
        "confluence_pages": [
            "LOI Processing",
            "PNC Account Reconciliation",
        ],
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


def get_confluence_pages_for_agent(agent_name):
    """
    Get list of Confluence pages relevant to an agent.
    
    Args:
        agent_name: Name of the agent
        
    Returns:
        List of Confluence page titles, or empty list if not found
    """
    agent_info = AGENT_SOP_MAPPING.get(agent_name)
    if agent_info:
        return agent_info.get("confluence_pages", [])
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
        sop_text = "\n".join(f"- {page}" for page in info["confluence_pages"])
        
        prompt = f"Agent: {agent_name}\n\nLabeling Rules:\n{rules_text}"
        
        completion = f"""
Reconciliation Steps:
{recon_text}

Relevant SOPs:
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

