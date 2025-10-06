# Agent-SOP Mapping Report

**Date:** October 6, 2025  
**Total Agents in Model:** 96  
**Mapped Agents:** 21 (21.9%)  
**Unmapped Agents:** 75 (78.1%)

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
1. [Daily Bank Transaction Reconciliation by Bank Transaction Type](https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/169411126)
2. [Zero Balance Transfer Reconciliation](https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/169411752)
3. [Reconciliation Queue & Dashboard Overview](https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/169410903)

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
1. [Daily Bank Transaction Reconciliation by Bank Transaction Type](https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/169411126)
2. [Reconciliation Queue & Dashboard Overview](https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/169410903)

---

## 🟠 HIGH PRIORITY AGENTS (6)

### 3. **Nium Payment**
**Frequency:** MEDIUM | **Criticality:** HIGH

**Labeling Rules:**
- Description contains 'NIUM' (definitive)
- Account 21 (Chase International Contractor Payments)
- Payment Method 10 (ACH External)

**Confluence SOPs:**
1. [International Contractor Payment (ICP)](https://gustohq.atlassian.net/wiki/spaces/BIZT/pages/75345345)
2. [International Contractor Payments Support](https://gustohq.atlassian.net/wiki/spaces/PymtOps/pages/76384014)
3. [ACH Payment Overview](https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/168920198)

---

### 4. **ICP Funding**
**Frequency:** MEDIUM | **Criticality:** HIGH

**Labeling Rules:**
- Account 21 (Chase ICP) + 'REMARK=JPMORGAN ACCESS TRANSFER FROM' (definitive)
- Paired transactions: Same amount to/from Chase Ops
- Payment Method 8 (Unknown) - but this is expected for these transfers

**Note:** Rare but financially critical - requires paired transaction logic

**Confluence SOPs:**
1. [International Contractor Payment Funding](https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/169411829)
2. [International Contractor Payments Support](https://gustohq.atlassian.net/wiki/spaces/PymtOps/pages/76384014)

---

### 5. **NY WH** (New York Withholding Tax)
**Frequency:** MEDIUM | **Criticality:** HIGH

**Labeling Rules:**
- Description: 'NYS DTF WT' (New York State withholding tax)

**Confluence SOPs:**
1. [Daily Bank Transaction Reconciliation by Bank Transaction Type](https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/169411126)
2. [Zero Balance Transfer Reconciliation](https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/169411752)

---

### 6. **NY UI** (New York Unemployment Insurance)
**Frequency:** MEDIUM | **Criticality:** HIGH

**Labeling Rules:**
- Description: 'NYS DOL UI' (New York State unemployment insurance)

**Confluence SOPs:**
1. [Daily Bank Transaction Reconciliation by Bank Transaction Type](https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/169411126)

---

### 7. **MT WH** (Montana Withholding)
**Frequency:** LOW | **Criticality:** HIGH

**Labeling Rules:**
- Description: 'STATE OF MONTANA' (Montana withholding)

**Confluence SOPs:**
1. [Daily Bank Transaction Reconciliation by Bank Transaction Type](https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/169411126)

---

### 8. **PA UI** (Pennsylvania Unemployment Insurance)
**Frequency:** LOW | **Criticality:** HIGH

**Labeling Rules:**
- Description: 'ORIG CO NAME=KEYSTONE'

**Confluence SOPs:**
1. [Daily Bank Transaction Reconciliation by Bank Transaction Type](https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/169411126)

---

## 🟡 MEDIUM PRIORITY AGENTS (10)

### 9. **ACH**
**Frequency:** HIGH | **Criticality:** MEDIUM

**Labeling Rules:**
- Payment Method 10 (ACH External) - high confidence
- Payment Method 4 (ACH) - 97.1% confidence
- NOT Company Balance Transfer (discontinued)

**Confluence SOPs:**
1. [ACH Payment Overview](https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/168920198)
2. [Reconciliation Queue & Dashboard Overview](https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/169410903)

---

### 10. **Treasury Transfer**
**Frequency:** MEDIUM | **Criticality:** MEDIUM

**Labeling Rules:**
- Description: 'REMARK=JPMORGAN ACCESS TRANSFER' (not to/from ICP)
- Internal treasury movements

**Confluence SOPs:**
1. [Modern Treasury](https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/76385861)
2. [Zero Balance Transfer Reconciliation](https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/169411752)

---

### 11. **ZBT** (Zero Balance Transfer)
**Frequency:** MEDIUM | **Criticality:** MEDIUM

**Labeling Rules:**
- Payment Method 12 (definitive)
- Zero Balance Transfer operations

**Confluence SOPs:**
1. [Zero Balance Transfer Reconciliation](https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/169411752)

---

### 12. **Check**
**Frequency:** MEDIUM | **Criticality:** MEDIUM

**Labeling Rules:**
- Payment Method 2 (Check)
- Description contains 'check' patterns

**Confluence SOPs:**
1. [Manual Reconciliation Checks](https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/169412024)
2. [Reconciliation Queue & Dashboard Overview](https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/169410903)

---

### 13. **BRB**
**Frequency:** MEDIUM | **Criticality:** MEDIUM

**Labeling Rules:**
- Account 26 (Blueridge Operations)
- Amount > $0.50
- If description has 'check' or 'interest', label accordingly

**Confluence SOPs:**
1. [Daily Bank Transaction Reconciliation by Bank Transaction Type](https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/169411126)

---

### 14. **ICP Return**
**Frequency:** LOW | **Criticality:** MEDIUM

**Labeling Rules:**
- Description: 'TS FX ACCOUNTS RECEIVABLE'
- Description: 'JPV' followed by numbers (ticket number, e.g., 'JPV230104')

**Confluence SOPs:**
1. [International Contractor Payments Support](https://gustohq.atlassian.net/wiki/spaces/PymtOps/pages/76384014)
2. [Cancel International Contractor Payment SOP](https://gustohq.atlassian.net/wiki/spaces/PymtOps/pages/76385396)

---

### 15. **ICP Refund**
**Frequency:** LOW | **Criticality:** MEDIUM

**Labeling Rules:**
- Description contains 'WISE'
- Amount typically < $50K

**Confluence SOPs:**
1. [International Contractor Payments Support](https://gustohq.atlassian.net/wiki/spaces/PymtOps/pages/76384014)

---

### 16. **York Adams** (Local Tax)
**Frequency:** LOW | **Criticality:** MEDIUM

**Labeling Rules:**
- Description: 'York Adams Tax' or 'York Adams Tax EIT'
- Consolidated label (previously separate)

**Confluence SOPs:**
1. [Daily Bank Transaction Reconciliation by Bank Transaction Type](https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/169411126)

---

### 17. **LOI** (Letter of Indemnity)
**Frequency:** LOW | **Criticality:** MEDIUM

**Labeling Rules:**
- Description: 'CREDIT MEMO' + PNC account (e.g., Account 16)

**Confluence SOPs:**
1. [Letter of Indemnity Process and Reconciliation](https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/298583554)

---

### 18. **Money Market Transfer**
**Frequency:** LOW | **Criticality:** MEDIUM

**Labeling Rules:**
- Description: 'REMARK=100% US TREASURY CAPITAL 3163 AT NAV OF 1.0000' (definitive)
- Description: 'MONEY MKT MUTUAL FUND'

**Confluence SOPs:**
1. [Modern Treasury](https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/76385861)

---

## ⚪ LOW PRIORITY AGENTS (3)

### 19. **Bad Debt**
**Frequency:** MEDIUM | **Criticality:** LOW

**Labeling Rules:**
- Account 26 (Blueridge Operations)
- Amount < $0.50 (definitive for small amounts)
- Description: 'ITT GUSTO CORPORATE CCD'

**Confluence SOPs:**
1. [Bad Debt Write Off SOP](https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/169377977)
2. [Write Off SOP + Bad Debt Lifecycle](https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/169410711)

---

### 20. **Interest Adjustment**
**Frequency:** LOW | **Criticality:** LOW

**Labeling Rules:**
- Description: 'INTEREST ADJUSTMENT' (definitive)
- Account 28 (Blueridge Recovery) + 'INTEREST' in description

**Confluence SOPs:**
1. [Daily Bank Transaction Reconciliation by Bank Transaction Type](https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/169411126)

---

### 21. **Lockbox**
**Frequency:** LOW | **Criticality:** LOW

**Labeling Rules:**
- Description contains 'LOCKBOX' (definitive)

**Confluence SOPs:**
1. [Lockbox Investigations](https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/169411804)

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
- **Unmapped:** 75/96 agents (78.1%)

---

## 🔴 TOP UNMAPPED AGENTS (Need Immediate Attention)

### High Priority Unmapped:
1. **ACH Return**
2. **Wire Return**
3. **Risk Return**
4. **IRS / IRS Wire**
5. **Company Balance Transfer**
6. **Chase Levy / Levy**
7. **Unclaimed Property** (+ variants)

### State Tax Unmapped:
8. **IL UI, HI UI, KS Tax, KY UI, NM UI, OH WH, OK UI, VA UI, WA UI** (+ variants)

### Local Tax Unmapped:
9. **Berks EIT, HAB EIT, Lancaster WH, PA EIT** (+ variants)

### ICP Variants Unmapped:
10. **ICP, ICP ACH, ICP Credit, ICP Transfer, ICP ZBT**

---

## 🎯 NEXT STEPS

### For Fine-Tuning:
1. **Immediate:** Use these 21 agents for initial fine-tuning
2. **Phase 2:** Map top 19 high-priority unmapped agents
3. **Phase 3:** Complete full 96-agent coverage

### For Production Deployment:
1. **Slack Integration:** When agent is predicted, attach relevant Confluence SOP links
2. **Daily Operations:** Auto-suggest reconciliation procedures based on agent type
3. **Knowledge Base:** Link agents to specific SOP documentation for training

---

**Report Generated:** October 6, 2025  
**Repository:** https://github.com/yarkn24/SOPSlack

