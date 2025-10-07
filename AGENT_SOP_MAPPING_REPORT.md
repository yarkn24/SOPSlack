# Agent-SOP Mapping Report

**Date:** October 7, 2025  
**Total Agents in Model:** 96  
**Mapped Agents:** 21 (21.9%)

---

## 🔴 CRITICAL PRIORITY AGENTS (2)

### 1. **Risk**
**Frequency:** HIGH | **Criticality:** CRITICAL

**Labeling Rules:**
- Description contains '1TRV' → ALWAYS Risk (definitive, overrides all other rules)
- Account 6, 7, 9, or 18 (Chase Wire-in, PNC Wire-in, Chase Payroll Incoming Wire)
- Payment Method 0 (Wire)

**Reconciliation Steps:**
- Verify wire transfer details in Modern Treasury
- Match with expected incoming Risk payments
- Check for 1TRV code compliance
- Validate origination account and amount

**Confluence SOPs:**
1. [Escalating Reconciliation Issues to Cross-Functional Stakeholders](https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/460194134/Escalating+Reconciliation+Issues+to+Cross-Functional+Stakeholders)
2. [Daily Bank Transaction Reconciliation by Bank Transaction Type](https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/169411126/Daily+Bank+Transaction+Reconciliation+by+Bank+Transaction+Type)

---

### 2. **Recovery Wire**
**Frequency:** HIGH | **Criticality:** CRITICAL

**Labeling Rules:**
- Account 28 (Chase Recovery Wire-in) AND no '1TRV' in description
- Large amounts (typically >$25K) to Recovery account
- Payment Method 0 (Wire)

**Reconciliation Steps:**
- Verify recovery wire in Modern Treasury
- Match with expected recovery payments
- Check if mistakenly sent to wrong account (if 1TRV present, should be Risk)

**Confluence SOPs:**
1. [Escalating Reconciliation Issues to Cross-Functional Stakeholders](https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/460194134/Escalating+Reconciliation+Issues+to+Cross-Functional+Stakeholders)
2. [Daily Bank Transaction Reconciliation by Bank Transaction Type](https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/169411126/Daily+Bank+Transaction+Reconciliation+by+Bank+Transaction+Type)

---

## 🟠 HIGH PRIORITY AGENTS (6)

### 3. **Nium Payment**
**Frequency:** MEDIUM | **Criticality:** HIGH

**Labeling Rules:**
- Description contains 'NIUM' (definitive)
- Account 21 (Chase International Contractor Payments)
- Payment Method 10 (ACH External)

**Reconciliation Steps:**
- Verify Nium payment details
- Match with contractor payment records
- Check for proper NIUM descriptor
- **If amount > $300K, escalate using Cross-Functional Stakeholders process**

**Confluence SOPs:**
1. [Escalating Reconciliation Issues to Cross-Functional Stakeholders](https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/460194134/Escalating+Reconciliation+Issues+to+Cross-Functional+Stakeholders) *(for >$300K)*
2. [Daily Bank Transaction Reconciliation by Bank Transaction Type](https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/169411126/Daily+Bank+Transaction+Reconciliation+by+Bank+Transaction+Type)

---

### 4. **ICP Funding**
**Frequency:** MEDIUM | **Criticality:** HIGH

**Labeling Rules:**
- Account 21 (Chase ICP) + 'REMARK=JPMORGAN ACCESS TRANSFER FROM' (definitive)
- Paired transactions: Same amount to/from Chase Ops
- Payment Method 8 (Unknown) - but this is expected for these transfers

**Reconciliation Steps:**
- Verify paired transaction exists with matching amount
- Confirm both legs of the transfer (ICP → Ops, Ops → ICP)
- Match with internal funding records
- **If amount > $300K, escalate using Cross-Functional Stakeholders process**

**Note:** Rare but financially critical - requires paired transaction logic

**Confluence SOPs:**
1. [Escalating Reconciliation Issues to Cross-Functional Stakeholders](https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/460194134/Escalating+Reconciliation+Issues+to+Cross-Functional+Stakeholders) *(for >$300K)*
2. [Daily Bank Transaction Reconciliation by Bank Transaction Type](https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/169411126/Daily+Bank+Transaction+Reconciliation+by+Bank+Transaction+Type)

---

### 5. **NY WH** (New York Withholding Tax)
**Frequency:** MEDIUM | **Criticality:** HIGH

**Labeling Rules:**
- Description: 'NYS DTF WT' (New York State withholding tax)

**Reconciliation Steps:**
- Verify NY withholding tax amount
- Match with payroll records

**Note:** No specific SOP available - use general reconciliation procedures

**Confluence SOPs:**
1. [Daily Bank Transaction Reconciliation by Bank Transaction Type](https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/169411126/Daily+Bank+Transaction+Reconciliation+by+Bank+Transaction+Type)

---

### 6. **NY UI** (New York Unemployment Insurance)
**Frequency:** MEDIUM | **Criticality:** HIGH

**Labeling Rules:**
- Description: 'NYS DOL UI' (New York State unemployment insurance)

**Reconciliation Steps:**
- Verify NY UI payment amount
- Match with payroll records

**Note:** No specific SOP available - use general reconciliation procedures

**Confluence SOPs:**
1. [Daily Bank Transaction Reconciliation by Bank Transaction Type](https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/169411126/Daily+Bank+Transaction+Reconciliation+by+Bank+Transaction+Type)

---

### 7. **MT WH** (Montana Withholding)
**Frequency:** LOW | **Criticality:** HIGH

**Labeling Rules:**
- Description: 'STATE OF MONTANA' (Montana withholding)

**Reconciliation Steps:**
- Verify MT withholding tax amount
- Match with payroll records

**Note:** No specific SOP available - use general reconciliation procedures

**Confluence SOPs:**
1. [Daily Bank Transaction Reconciliation by Bank Transaction Type](https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/169411126/Daily+Bank+Transaction+Reconciliation+by+Bank+Transaction+Type)

---

### 8. **PA UI** (Pennsylvania Unemployment Insurance)
**Frequency:** LOW | **Criticality:** HIGH

**Labeling Rules:**
- Description: 'ORIG CO NAME=KEYSTONE'

**Reconciliation Steps:**
- Verify PA UI payment amount
- Match with payroll records

**Note:** No specific SOP available - use general reconciliation procedures

**Confluence SOPs:**
1. [Daily Bank Transaction Reconciliation by Bank Transaction Type](https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/169411126/Daily+Bank+Transaction+Reconciliation+by+Bank+Transaction+Type)

---

## 🟡 MEDIUM PRIORITY AGENTS (10)

### 9. **ACH**
**Frequency:** HIGH | **Criticality:** MEDIUM

**Labeling Rules:**
- Payment Method 10 (ACH External) - high confidence
- Payment Method 4 (ACH) - 97.1% confidence
- NOT Company Balance Transfer (discontinued)

**Reconciliation Steps:**
- Verify ACH transaction details
- Match with expected ACH payments
- Check payment method classification

**Confluence SOPs:**
1. [Daily Bank Transaction Reconciliation by Bank Transaction Type](https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/169411126/Daily+Bank+Transaction+Reconciliation+by+Bank+Transaction+Type)

---

### 10. **Treasury Transfer**
**Frequency:** MEDIUM | **Criticality:** MEDIUM

**Labeling Rules:**
- Description: 'REMARK=JPMORGAN ACCESS TRANSFER' (not to/from ICP)
- Internal treasury movements

**Reconciliation Steps:**
- Verify treasury transfer authorization
- Match with internal transfer records
- Confirm both sides of transfer
- Check Unintended Overpayment Account Use Cases SOP for treasury funding

**Note:** Unintended Overpayment Account Use Cases SOP applies for Treasury Funding

**Confluence SOPs:**
1. [Daily Bank Transaction Reconciliation by Bank Transaction Type](https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/169411126/Daily+Bank+Transaction+Reconciliation+by+Bank+Transaction+Type)

---

### 11. **ZBT** (Zero Balance Transfer)
**Frequency:** MEDIUM | **Criticality:** MEDIUM

**Labeling Rules:**
- Payment Method 12 (definitive)
- Zero Balance Transfer operations

**Reconciliation Steps:**
- Verify ZBT sweep configuration
- Match with expected balance transfers

**Confluence SOPs:**
1. [Daily Bank Transaction Reconciliation by Bank Transaction Type](https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/169411126/Daily+Bank+Transaction+Reconciliation+by+Bank+Transaction+Type)

---

### 12. **Check**
**Frequency:** MEDIUM | **Criticality:** MEDIUM

**Labeling Rules:**
- Payment Method 2 (Check)
- Description contains 'check' patterns

**Reconciliation Steps:**
- Verify check number and amount
- Match with check register
- Confirm payee information

**Confluence SOPs:**
1. [Daily Bank Transaction Reconciliation by Bank Transaction Type](https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/169411126/Daily+Bank+Transaction+Reconciliation+by+Bank+Transaction+Type)

---

### 13. **BRB**
**Frequency:** MEDIUM | **Criticality:** MEDIUM

**Labeling Rules:**
- Account 26 (Blueridge Operations)
- Amount > $0.50
- If description has 'check' or 'interest', label accordingly

**Reconciliation Steps:**
- Verify BRB transaction details
- Match with Blueridge records

**Confluence SOPs:**
1. [Daily Bank Transaction Reconciliation by Bank Transaction Type](https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/169411126/Daily+Bank+Transaction+Reconciliation+by+Bank+Transaction+Type)

---

### 14. **ICP Return**
**Frequency:** LOW | **Criticality:** MEDIUM

**Labeling Rules:**
- Description: 'TS FX ACCOUNTS RECEIVABLE'
- Description: 'JPV' followed by numbers (ticket number, e.g., 'JPV230104')

**Reconciliation Steps:**
- Verify ICP return reason
- Match with original ICP transaction
- Check ticket number in Jira
- **If amount > $300K, escalate using Cross-Functional Stakeholders process**

**Confluence SOPs:**
1. [Escalating Reconciliation Issues to Cross-Functional Stakeholders](https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/460194134/Escalating+Reconciliation+Issues+to+Cross-Functional+Stakeholders) *(for >$300K)*
2. [Daily Bank Transaction Reconciliation by Bank Transaction Type](https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/169411126/Daily+Bank+Transaction+Reconciliation+by+Bank+Transaction+Type)

---

### 15. **ICP Refund**
**Frequency:** LOW | **Criticality:** MEDIUM

**Labeling Rules:**
- Description contains 'WISE'
- Amount typically < $50K

**Reconciliation Steps:**
- Verify refund reason and amount
- Match with original ICP payment
- **If amount > $300K, escalate using Cross-Functional Stakeholders process**

**Confluence SOPs:**
1. [Escalating Reconciliation Issues to Cross-Functional Stakeholders](https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/460194134/Escalating+Reconciliation+Issues+to+Cross-Functional+Stakeholders) *(for >$300K)*
2. [Daily Bank Transaction Reconciliation by Bank Transaction Type](https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/169411126/Daily+Bank+Transaction+Reconciliation+by+Bank+Transaction+Type)

---

### 16. **York Adams** (Local Tax)
**Frequency:** LOW | **Criticality:** MEDIUM

**Labeling Rules:**
- Description: 'York Adams Tax' or 'York Adams Tax EIT'
- Consolidated label (previously separate)

**Reconciliation Steps:**
- Verify York Adams tax payment
- Match with local tax records

**Confluence SOPs:**
1. [Daily Bank Transaction Reconciliation by Bank Transaction Type](https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/169411126/Daily+Bank+Transaction+Reconciliation+by+Bank+Transaction+Type)

---

### 17. **LOI** (Letter of Indemnity)
**Frequency:** LOW | **Criticality:** MEDIUM

**Labeling Rules:**
- Description: 'CREDIT MEMO' + PNC account (e.g., Account 16)

**Reconciliation Steps:**
- Verify LOI (Letter of Indemnity) details
- Match with PNC credit memo records
- Follow Letter of Indemnity Process and Reconciliation SOP

**Confluence SOPs:**
1. [Letter of Indemnity Process and Reconciliation](https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/298583554/Letter+of+Indemnity+Process+and+Reconciliation)
2. [Daily Bank Transaction Reconciliation by Bank Transaction Type](https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/169411126/Daily+Bank+Transaction+Reconciliation+by+Bank+Transaction+Type)

---

### 18. **Money Market Transfer**
**Frequency:** LOW | **Criticality:** MEDIUM

**Labeling Rules:**
- Description: 'REMARK=100% US TREASURY CAPITAL 3163 AT NAV OF 1.0000' (definitive)
- Description: 'MONEY MKT MUTUAL FUND'

**Reconciliation Steps:**
- Verify money market account movement
- Match with treasury management records
- Check Unintended Overpayment Account Use Cases SOP

**Note:** Unintended Overpayment Account Use Cases SOP applies

**Confluence SOPs:**
1. [Daily Bank Transaction Reconciliation by Bank Transaction Type](https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/169411126/Daily+Bank+Transaction+Reconciliation+by+Bank+Transaction+Type)

---

## ⚪ LOW PRIORITY AGENTS (3)

### 19. **Bad Debt**
**Frequency:** MEDIUM | **Criticality:** LOW

**Labeling Rules:**
- Account 26 (Blueridge Operations)
- Amount < $0.50 (definitive for small amounts)
- Description: 'ITT GUSTO CORPORATE CCD'

**Reconciliation Steps:**
- Verify bad debt classification
- Match with bad debt records
- Confirm amount threshold

**Confluence SOPs:**
1. [Daily Bank Transaction Reconciliation by Bank Transaction Type](https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/169411126/Daily+Bank+Transaction+Reconciliation+by+Bank+Transaction+Type)

---

### 20. **Interest Adjustment**
**Frequency:** LOW | **Criticality:** LOW

**Labeling Rules:**
- Description: 'INTEREST ADJUSTMENT' (definitive)
- Account 28 (Blueridge Recovery) + 'INTEREST' in description

**Reconciliation Steps:**
- Verify interest adjustment calculation
- Match with bank interest records
- Check Unintended Overpayment Account Use Cases SOP for Interest Income

**Note:** Unintended Overpayment Account Use Cases SOP applies for Interest Income

**Confluence SOPs:**
1. [Daily Bank Transaction Reconciliation by Bank Transaction Type](https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/169411126/Daily+Bank+Transaction+Reconciliation+by+Bank+Transaction+Type)

---

### 21. **Lockbox**
**Frequency:** LOW | **Criticality:** LOW

**Labeling Rules:**
- Description contains 'LOCKBOX' (definitive)

**Reconciliation Steps:**
- Verify lockbox deposit details
- Match with lockbox reports

**Confluence SOPs:**
1. [Daily Bank Transaction Reconciliation by Bank Transaction Type](https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/169411126/Daily+Bank+Transaction+Reconciliation+by+Bank+Transaction+Type)

---

## 📊 SUMMARY STATISTICS

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

### 🔄 **Default Reconciliation SOP**
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
1. Escalating Reconciliation Issues to Cross-Functional Stakeholders
   https://gustohq.atlassian.net/.../460194134/...
2. Daily Bank Transaction Reconciliation by Bank Transaction Type
   https://gustohq.atlassian.net/.../169411126/...

⚡ Quick Actions:
[View in Modern Treasury] [Mark as Reconciled]
```

---

**Report Generated:** October 7, 2025  
**Repository:** https://github.com/yarkn24/SOPSlack  
**Status:** ✅ Ready for Slack Integration
