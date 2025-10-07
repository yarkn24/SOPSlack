"""
Generate Agent-SOP Mapping Report from agent_sop_mapping.py
"""

from agent_sop_mapping import AGENT_SOP_MAPPING

def generate_markdown_report():
    """Generate the complete markdown report"""
    
    report = """# Agent-SOP Mapping Report

**Date:** October 7, 2025  
**Total Agents in Model:** 96  
**Mapped Agents:** 21 (21.9%)

---

"""
    
    # Categorize agents by criticality
    critical = []
    high = []
    medium = []
    low = []
    
    for agent_name, info in AGENT_SOP_MAPPING.items():
        criticality = info.get('criticality', 'N/A')
        if criticality == 'CRITICAL':
            critical.append((agent_name, info))
        elif criticality == 'HIGH':
            high.append((agent_name, info))
        elif criticality == 'MEDIUM':
            medium.append((agent_name, info))
        elif criticality == 'LOW':
            low.append((agent_name, info))
    
    # Helper function to format agent section
    def format_agent(num, agent_name, info):
        section = f"### {num}. **{agent_name}**\n"
        section += f"**Frequency:** {info.get('frequency', 'N/A')} | **Criticality:** {info.get('criticality', 'N/A')}\n\n"
        
        section += "**Labeling Rules:**\n"
        for rule in info['labeling_rules']:
            section += f"- {rule}\n"
        section += "\n"
        
        section += "**Reconciliation Steps:**\n"
        for step in info['reconciliation_steps']:
            section += f"- {step}\n"
        section += "\n"
        
        if 'note' in info:
            section += f"**Note:** {info['note']}\n\n"
        
        section += "**Confluence SOPs:**\n"
        links = info.get('confluence_links', [])
        for i, link in enumerate(links, 1):
            # Extract page title from URL
            if '535003232' in link:
                title = "Daily Operations: How to Label & Reconcile"
            elif '460194134' in link:
                title = "Escalating Reconciliation Issues to Cross-Functional Stakeholders"
            elif '169411126' in link:
                title = "Daily Bank Transaction Reconciliation by Bank Transaction Type"
            elif '298583554' in link:
                title = "Letter of Indemnity Process and Reconciliation"
            else:
                title = "SOP Document"
            
            # Add special notes for certain links
            note_suffix = ""
            if '460194134' in link and agent_name in ['Nium Payment', 'ICP Funding', 'ICP Return', 'ICP Refund']:
                note_suffix = " *(for >$300K)*"
            
            section += f"{i}. [{title}]({link}){note_suffix}\n"
        
        # Add "Also, suggested SOPs to check" section
        section += "\n**Also, suggested SOPs to check:**\n"
        
        # Track all unique links to avoid duplicates
        suggested_links = []
        
        # 1. Always first: Daily Operations
        suggested_links.append(("Daily Operations: How to Label & Reconcile", 
                               "https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/535003232/Daily+Operations+How+to+Label+Reconcile"))
        
        # 2. Agent-specific SOPs (unique, from main SOPs list)
        for link in links:
            if '535003232' in link:
                title = "Daily Operations: How to Label & Reconcile"
            elif '460194134' in link:
                title = "Escalating Reconciliation Issues to Cross-Functional Stakeholders"
            elif '169411126' in link:
                title = "Daily Bank Transaction Reconciliation by Bank Transaction Type"
            elif '298583554' in link:
                title = "Letter of Indemnity Process and Reconciliation"
            else:
                title = "SOP Document"
            
            # Add if not already in suggested_links
            if not any(l[1] == link for l in suggested_links):
                suggested_links.append((title, link))
        
        # 3. Default SOP at the end (Daily Bank Transaction Reconciliation) - only if not already added
        default_link = "https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/169411126/Daily+Bank+Transaction+Reconciliation+by+Bank+Transaction+Type"
        if not any(l[1] == default_link for l in suggested_links):
            suggested_links.append(("Daily Bank Transaction Reconciliation by Bank Transaction Type", default_link))
        
        # Write all unique suggested links
        for i, (title, link) in enumerate(suggested_links, 1):
            section += f"{i}. [{title}]({link})\n"
        
        section += "\n---\n\n"
        
        return section
    
    # Add CRITICAL section
    if critical:
        report += "## 🔴 CRITICAL PRIORITY AGENTS ({})\n\n".format(len(critical))
        counter = 1
        for agent_name, info in critical:
            report += format_agent(counter, agent_name, info)
            counter += 1
    
    # Add HIGH section
    if high:
        report += "## 🟠 HIGH PRIORITY AGENTS ({})\n\n".format(len(high))
        counter = 3  # Continue numbering
        for agent_name, info in high:
            report += format_agent(counter, agent_name, info)
            counter += 1
    
    # Add MEDIUM section
    if medium:
        report += "## 🟡 MEDIUM PRIORITY AGENTS ({})\n\n".format(len(medium))
        counter = 9  # Continue numbering
        for agent_name, info in medium:
            report += format_agent(counter, agent_name, info)
            counter += 1
    
    # Add LOW section
    if low:
        report += "## ⚪ LOW PRIORITY AGENTS ({})\n\n".format(len(low))
        counter = 19  # Continue numbering
        for agent_name, info in low:
            report += format_agent(counter, agent_name, info)
            counter += 1
    
    # Add summary section
    report += """## 📊 SUMMARY STATISTICS

### By Criticality:
- 🔴 **CRITICAL:** 2 agents (Risk, Recovery Wire)
- 🟠 **HIGH:** 6 agents (Nium Payment, ICP Funding, NY WH, NY UI, MT WH, PA UI)
- 🟡 **MEDIUM:** 10 agents (ACH, Treasury Transfer, ZBT, Check, BRB, ICP Return, ICP Refund, York Adams, LOI, Money Market Transfer)
- ⚪ **LOW:** 3 agents (Bad Debt, Interest Adjustment, Lockbox)

### By Frequency:
- **HIGH:** 3 agents (Risk, Recovery Wire, ACH)
- **MEDIUM:** 10 agents
- **LOW:** 8 agents

### Coverage:
- **Mapped:** 21/96 agents (21.9%)

---

## 🎯 KEY MAPPING RULES

### 🏆 **Master SOP (All Agents)**
**Daily Operations: How to Label & Reconcile** is the primary SOP for all transactions:
- [Daily Operations: How to Label & Reconcile](https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/535003232/Daily+Operations+How+to+Label+Reconcile)

This comprehensive guide covers all transaction types and labeling procedures.

### 🚨 **Escalation Rule (>$300K)**
For ICP-related agents with amounts **over $300,000**, use:
- [Escalating Reconciliation Issues to Cross-Functional Stakeholders](https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/460194134/Escalating+Reconciliation+Issues+to+Cross-Functional+Stakeholders)

**Applies to:**
- Nium Payment
- ICP Funding
- ICP Return
- ICP Refund

### 📄 **Unintended Overpayment Account Use Cases SOP**
For treasury-related transactions, refer to Unintended Overpayment Account Use Cases SOP:
- Treasury Transfer (Treasury Funding)
- Money Market Transfer
- Interest Adjustment (Interest Income)

### 🔄 **Default Baseline SOP**
All agents include as baseline:
- [Daily Bank Transaction Reconciliation by Bank Transaction Type](https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/169411126/Daily+Bank+Transaction+Reconciliation+by+Bank+Transaction+Type)

### ⚠️ **No Specific SOP Available**
These agents use general reconciliation procedures only:
- NY WH
- NY UI
- MT WH
- PA UI

---

## 🎯 NEXT STEPS FOR SLACK INTEGRATION

### When Bot Predicts Agent:
1. **Show Agent Name** (e.g., "Risk")
2. **Display Confidence** (e.g., "98.5%")
3. **Show Relevant SOP Links** (unique, no duplicates)
4. **Add Escalation Warning** (if ICP + amount >$300K)
5. **Include Quick Actions** (e.g., "View in Modern Treasury", "Check Jira Ticket")

### Example Slack Message:
```
🎯 Transaction Classified: Risk (98.5% confidence)

📋 Reconciliation Steps:
• Verify wire transfer details in Modern Treasury
• Match with expected incoming Risk payments
• Check for 1TRV code compliance

📚 Relevant SOPs:
1. Daily Operations: How to Label & Reconcile
   https://gustohq.atlassian.net/.../535003232/...
2. Escalating Reconciliation Issues to Cross-Functional Stakeholders
   https://gustohq.atlassian.net/.../460194134/...
3. Daily Bank Transaction Reconciliation by Bank Transaction Type
   https://gustohq.atlassian.net/.../169411126/...

⚡ Quick Actions:
[View in Modern Treasury] [Mark as Reconciled]
```

---

**Report Generated:** October 7, 2025  
**Repository:** https://github.com/yarkn24/SOPSlack  
**Status:** ✅ Ready for Slack Integration
"""
    
    return report

if __name__ == "__main__":
    report = generate_markdown_report()
    
    # Write to file
    with open('AGENT_SOP_MAPPING_REPORT.md', 'w') as f:
        f.write(report)
    
    print("✅ Report generated successfully!")
    print(f"📄 Written to: AGENT_SOP_MAPPING_REPORT.md")

