# Transaction Predictor - Usage Guide

## 🎯 What It Does

This tool predicts agent labels for bank transactions and provides:
1. **Predicted Label** (Risk, ICP, NY WH, etc.)
2. **SOP Links** (Confluence documentation)
3. **Reconciliation Steps** (how to reconcile this type)
4. **Metadata** (frequency, criticality)

---

## 📝 Usage Options

### 1. Single Transaction (Interactive)

```bash
python3 transaction_predictor.py --single
```

**Interactive prompts:**
```
Amount (e.g., $5,100.00): $5,100.00
Date (e.g., 10/14/2025): 10/14/2025
Payment Method (e.g., wire in): wire in
Account (e.g., Chase Wire In): Chase Wire In
Narrative (paste full description, then press Enter twice):
YOUR REF=POH OF 25/10/14,REC FROM=00000000730103207 CHELSEA N SARVER 5605 SCURTICE ST UNIT A LITTLETON CO 80120-1188 US,REMARK=1TRVXX9QP28C DEBIT REF POH OF
[press Enter]
```

**Output:**
```
================================================================================
🎯 TRANSACTION PREDICTION RESULT
================================================================================

📋 TRANSACTION DETAILS:
   Amount: $5,100.00
   Date: 10/14/2025
   Payment Method: wire in
   Account: Chase Wire In
   Narrative: YOUR REF=POH OF 25/10/14,REC FROM=00000000730103207 CHELSEA...

🤖 PREDICTED LABEL:
   → Risk

📚 RELEVANT SOP DOCUMENTATION:
   🔗 https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/460194134
   🔗 https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/169411126

📝 HOW TO IDENTIFY THIS TRANSACTION:
   • Description contains '1TRV' → ALWAYS Risk (definitive, overrides all other rules)
   • Account 6, 7, 9, or 18 (Chase Wire-in, PNC Wire-in, Chase Payroll Incoming Wire)
   • Payment Method 0 (Wire)

✅ RECONCILIATION STEPS:
   1. Verify wire transfer details in Modern Treasury
   2. Match with expected incoming Risk payments
   3. Check for 1TRV code compliance
   4. Validate origination account and amount

📊 METADATA:
   • Frequency: HIGH
   • Criticality: CRITICAL
================================================================================
```

---

### 2. Batch Processing (CSV)

```bash
python3 transaction_predictor.py --csv input.csv --output results.csv
```

**Input CSV Format:**
```csv
amount,date,payment_method,account,narrative
"$5,100.00","10/14/2025","wire in","Chase Wire In","YOUR REF=POH OF 25/10/14..."
"$25,000.00","10/14/2025","ACH","Chase Operations","ORIG CO NAME=NIUM INC..."
```

**Output CSV Includes:**
- All original columns
- `predicted_label` - The predicted agent
- `sop_link` - Confluence SOP URLs
- `frequency` - How often this occurs
- `criticality` - How critical this reconciliation is

**Summary Output:**
```
📂 Reading CSV file: input.csv
✅ Found 8 transactions

✅ [1/8] Risk - $5,100.00
✅ [2/8] Nium Payment - $25,000.00
...

💾 Results saved to: results.csv

================================================================================
📊 BATCH PREDICTION SUMMARY
================================================================================

Total Transactions: 8

Label Distribution:
   • Risk: 1
   • Nium Payment: 1
   • ICP Funding: 1
   ...
================================================================================
```

---

### 3. Quick Test (Default Example)

```bash
python3 transaction_predictor.py
```

Runs with a built-in example transaction to test the system.

---

## 📋 CSV Column Requirements

### Required:
- **narrative** or **description** or **desc** - Transaction description text

### Optional (will use defaults if missing):
- **amount** - Transaction amount (defaults to 0)
- **date** - Transaction date (defaults to today)
- **payment_method** - Payment type (defaults to "Unknown")
- **account** - Account name (defaults to "Unknown")

**Note:** Column names are case-insensitive and flexible.

---

## 🎯 Prediction Rules

The system uses rule-based logic to identify patterns:

| Pattern | Label |
|---------|-------|
| '1TRV' in narrative | Risk |
| 'NIUM' in narrative | Nium Payment |
| 'JPMORGAN ACCESS TRANSFER' | ICP Funding |
| 'NYS DTF WT' in narrative | NY WH |
| 'CA EMPLOYMENT' in narrative | CA WH |
| 'MONEY MARKET' in narrative | Money Market Transfer |
| 'GUSTO' or 'PAYROLL' | Payroll / Chase Payroll Incoming Wires |
| 'CHECK' in payment method | Check |
| ... and more |

If no rule matches: **"Unknown - Manual Review Required"**

---

## 💡 Examples

### Example 1: Single Risk Transaction
```bash
python3 transaction_predictor.py --single
```
Input the transaction with `1TRVXX` code → predicts **Risk**

### Example 2: Batch of 100 Transactions
```bash
python3 transaction_predictor.py --csv daily_queue.csv --output labeled_queue.csv
```
Labels all 100 transactions and saves to `labeled_queue.csv`

### Example 3: Just See Results (No Save)
```bash
python3 transaction_predictor.py --csv daily_queue.csv
```
Shows summary without saving to file

---

## 🚀 For Manager Demo

**Show this:**
1. Single transaction → detailed output with SOP steps
2. CSV batch → quick labeling of multiple transactions
3. Output CSV → ready for daily ops workflow

**Key Points:**
- ✅ Instant prediction (no manual lookup)
- ✅ SOP links automatically included
- ✅ Reconciliation steps shown
- ✅ Batch processing for daily queue
- ✅ CSV output ready for team use

---

## 📞 Questions?

Contact: yarkin.akcil@zenefits.com  
GitHub: SOPSlack/transaction_predictor.py

