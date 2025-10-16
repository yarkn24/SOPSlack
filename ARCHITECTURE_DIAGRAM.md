# CODE7 - System Architecture Diagram

---

## HIGH-LEVEL ARCHITECTURE

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          CODE7 SYSTEM OVERVIEW                           │
│                   AI-Powered Daily Reconciliation Automation             │
└─────────────────────────────────────────────────────────────────────────┘

                                    ┌──────────────┐
                                    │   REDASH     │
                                    │  Query 133695│
                                    │              │
                                    │ Unlabeled    │
                                    │ Transactions │
                                    └──────┬───────┘
                                           │
                                           │ API Call
                                           │ (JSON)
                                           ▼
                    ┌─────────────────────────────────────────┐
                    │         code7.py (Orchestrator)         │
                    │  • Fetch data from Redash               │
                    │  • Coordinate prediction pipeline       │
                    │  • Generate outputs (CSV + Slack)       │
                    └─────────────────┬───────────────────────┘
                                      │
                    ┌─────────────────┼───────────────────┐
                    │                 │                   │
                    ▼                 ▼                   ▼
        ┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐
        │ labeling_rules.py│ │predict_with_rules│ │  sop_mappings.py │
        │                  │ │      .py         │ │                  │
        │ Business Rules   │ │  Hybrid ML+Rules │ │ Agent → SOP URLs │
        │                  │ │                  │ │                  │
        │ • ZBT skip logic │ │ • RandomForest   │ │ • ICP → SOP_URL  │
        │ • Org account map│ │ • Feature eng.   │ │ • ZBT → SOP_URL  │
        │ • Payment rules  │ │ • Confidence     │ │ • All agents     │
        │                  │ │                  │ │                  │
        │ Coverage: ~60%   │ │ Coverage: ~40%   │ │ All predictions  │
        └──────────────────┘ └──────────────────┘ └──────────────────┘
                    │                 │                   │
                    └─────────────────┼───────────────────┘
                                      │
                                      │ Predicted Labels
                                      │ + SOPs Linked
                                      ▼
                    ┌─────────────────────────────────────────┐
                    │        ENRICHMENT LAYER                 │
                    ├─────────────────┬───────────────────────┤
                    │  holidays.py    │    fun_facts.py       │
                    │                 │                       │
                    │ • US Bank       │ • 50+ finance facts   │
                    │   holidays      │ • Usage tracking      │
                    │ • Weekend check │ • Daily rotation      │
                    │ • Special msgs  │ • Engagement          │
                    └─────────────────┴───────────────────────┘
                                      │
                                      │ Enriched Data
                                      ▼
                    ┌─────────────────────────────────────────┐
                    │          OUTPUT GENERATION              │
                    └─────────────────┬───────────────────────┘
                                      │
                            ┌─────────┴─────────┐
                            │                   │
                            ▼                   ▼
                ┌─────────────────────┐  ┌──────────────────────┐
                │   CSV OUTPUT        │  │  SLACK MESSAGE       │
                │                     │  │                      │
                │ File: daily_recon   │  │ File: slack_message  │
                │   _YYYYMMDD_HHMMSS  │  │   _YYYYMMDD_HHMMSS   │
                │   .csv              │  │   .txt               │
                │                     │  │                      │
                │ Location:           │  │ Location:            │
                │ ~/Desktop/cursor    │  │ ~/Desktop/cursor     │
                │   _data/            │  │   _data/             │
                │                     │  │                      │
                │ Columns:            │  │ Content:             │
                │ • All Redash fields │  │ • Daily summary      │
                │ • ml_pred (agent)   │  │ • Counts by agent    │
                │ • sop_link (URL)    │  │ • High-impact alerts │
                │ • impact_flag       │  │ • SOP links          │
                │                     │  │ • Fun fact/holiday   │
                └─────────────────────┘  └──────────────────────┘
                            │                   │
                            │                   │
                            ▼                   ▼
                ┌─────────────────────┐  ┌──────────────────────┐
                │  DAILY OPS TEAM     │  │  #daily-recon        │
                │                     │  │  Slack Channel       │
                │ • Download CSV      │  │                      │
                │ • Verify predictions│  │ • Copy-paste message │
                │ • Start recon work  │  │ • Team visibility    │
                └─────────────────────┘  └──────────────────────┘
```

---

## DETAILED COMPONENT ARCHITECTURE

### 1. DATA INGESTION LAYER

```
┌─────────────────────────────────────────────────────┐
│              REDASH API INTEGRATION                 │
└─────────────────────────────────────────────────────┘

Input: Redash Query 133695
Endpoint: https://redash.zp-int.com/api/queries/133695/results.json
Auth: API Key (REDASH_API_KEY in .env)

Response Format:
{
  "query_result": {
    "data": {
      "rows": [
        {
          "transaction_id": "12345",
          "transaction_narrative": "Payment for services",
          "amount": 1500.00,
          "payment_method": "Wire Transfer",
          "org_account": "ZenPayroll Operations, Inc",
          "date": "2025-10-14",
          "agent": ""  ← BLANK - to be predicted
        },
        ...
      ]
    }
  }
}

↓ Fetched by code7.py
↓ Converted to pandas DataFrame
↓ Cleaned and normalized
```

---

### 2. PREDICTION PIPELINE

```
┌─────────────────────────────────────────────────────┐
│           HYBRID PREDICTION ARCHITECTURE            │
└─────────────────────────────────────────────────────┘

For each transaction:

    Step 1: Apply Business Rules (labeling_rules.py)
    ├─ Check ZBT skip logic
    │  if 'zbt' in org_account.lower():
    │      return None  # Skip per policy
    │
    ├─ Check org account mapping
    │  if org_account in ORG_ACCOUNT_MAP:
    │      return ORG_ACCOUNT_MAP[org_account]
    │
    ├─ Check payment method rules
    │  if payment_method == "Wire" and amount > 10000:
    │      return "ICP Agent"
    │
    └─ If no rule matches → proceed to Step 2

    Step 2: ML Prediction (predict_with_rules.py)
    ├─ Feature Engineering
    │  ├─ transaction_narrative → TF-IDF (100 features)
    │  ├─ amount → log-scaled + buckets
    │  ├─ payment_method → one-hot encoding
    │  └─ org_account → label encoding
    │
    ├─ Model Inference
    │  model = RandomForestClassifier(n_estimators=100)
    │  prediction, confidence = model.predict_proba(features)
    │
    └─ Confidence Threshold
       if confidence < 0.5:
           return "MANUAL_REVIEW"
       else:
           return prediction

    Step 3: SOP Linking (sop_mappings.py)
    └─ Map predicted agent → Confluence SOP URL

    Step 4: Impact Flagging
    └─ Check if high-priority (ICP batch, large amount, etc.)

Result:
    transaction['ml_pred'] = predicted_agent
    transaction['sop_link'] = sop_url
    transaction['impact_flag'] = 'HIGH' | 'NORMAL' | 'LOW'
```

---

### 3. ML MODEL ARCHITECTURE

```
┌─────────────────────────────────────────────────────┐
│         MACHINE LEARNING PIPELINE DETAIL            │
└─────────────────────────────────────────────────────┘

Training Phase (predict_with_rules.py):

    Historical Data (2,000 transactions)
           ↓
    Split: 70% train | 15% val | 15% test
           ↓
    ┌──────────────────────────────────────┐
    │     FEATURE ENGINEERING              │
    ├──────────────────────────────────────┤
    │ 1. Text Features                     │
    │    • TF-IDF on transaction_narrative │
    │    • Max features: 100               │
    │    • Stop words removed              │
    │                                      │
    │ 2. Numerical Features                │
    │    • amount (log-scaled)             │
    │    • amount_bucket (categorical)     │
    │                                      │
    │ 3. Categorical Features              │
    │    • payment_method (one-hot)        │
    │    • org_account (label encoded)     │
    │                                      │
    │ 4. Cross Features                    │
    │    • payment × org_account           │
    │    • amount_bucket × payment_method  │
    └──────────────────────────────────────┘
           ↓
    ┌──────────────────────────────────────┐
    │      MODEL SELECTION                 │
    ├──────────────────────────────────────┤
    │ Tested:                              │
    │ • Random Forest ✓ (best)             │
    │ • Logistic Regression                │
    │ • XGBoost                            │
    │ • SVM                                │
    │                                      │
    │ Winner: RandomForestClassifier       │
    │ • n_estimators: 100                  │
    │ • max_depth: 15                      │
    │ • min_samples_split: 5               │
    │ • class_weight: balanced             │
    └──────────────────────────────────────┘
           ↓
    ┌──────────────────────────────────────┐
    │       VALIDATION                     │
    ├──────────────────────────────────────┤
    │ Metrics:                             │
    │ • Accuracy: 98.6%                    │
    │ • Precision: 97.2%                   │
    │ • Recall: 96.8%                      │
    │ • F1 Score: 97.0%                    │
    │                                      │
    │ Baselines:                           │
    │ • Random: 7% (14 classes)            │
    │ • Rules-only: 60%                    │
    │ • ML-only V1: 33%                    │
    │ • Hybrid V4: 98.6% ✓                 │
    └──────────────────────────────────────┘
           ↓
    Model saved for inference

Inference Phase:
    New transaction → features → model.predict() → agent + confidence
```

---

### 4. OUTPUT GENERATION ARCHITECTURE

```
┌─────────────────────────────────────────────────────┐
│            OUTPUT FORMATTING PIPELINE               │
└─────────────────────────────────────────────────────┘

Predicted DataFrame (with ml_pred, sop_link, impact_flag)
           ↓
    ┌─────────────┴──────────────┐
    │                            │
    ▼                            ▼
┌──────────────┐        ┌──────────────┐
│ CSV EXPORT   │        │SLACK MESSAGE │
└──────────────┘        └──────────────┘
    │                            │
    │ Format:                    │ Format:
    │ • UTF-8 encoding           │ • Markdown-friendly
    │ • All columns              │ • Emoji icons
    │ • Timestamp in filename    │ • Bullet lists
    │ • Excel-compatible         │ • Hyperlinked SOPs
    │                            │ • Date header
    │ Location:                  │
    │ ~/Desktop/cursor_data/     │ Location:
    │ daily_recon_YYYYMMDD_      │ ~/Desktop/cursor_data/
    │   HHMMSS.csv               │ slack_message_YYYYMMDD_
    │                            │   HHMMSS.txt
    │                            │
    │ Columns:                   │ Sections:
    │ • transaction_id           │ • Header (date)
    │ • transaction_narrative    │ • Summary counts
    │ • amount                   │ • Agent breakdown
    │ • payment_method           │ • High-impact alerts
    │ • org_account              │ • SOP links
    │ • date                     │ • Fun fact/holiday
    │ • ml_pred ← PREDICTED      │ • Footer (instructions)
    │ • sop_link ← LINKED        │
    │ • impact_flag ← FLAGGED    │
    │                            │
    ▼                            ▼
┌──────────────┐        ┌──────────────┐
│  OPERATIONS  │        │    SLACK     │
│    TEAM      │        │   CHANNEL    │
│              │        │              │
│ Download CSV │        │ Copy-paste   │
│ Verify preds │        │ to #daily-   │
│ Start recon  │        │   recon      │
└──────────────┘        └──────────────┘
```

---

## DATA FLOW SEQUENCE DIAGRAM

```
┌─────────┐     ┌──────────┐     ┌───────────┐     ┌─────────┐
│  USER   │     │  code7   │     │  Redash   │     │  Model  │
└────┬────┘     └────┬─────┘     └─────┬─────┘     └────┬────┘
     │               │                  │                 │
     │ run code7.py  │                  │                 │
     │──────────────>│                  │                 │
     │               │                  │                 │
     │               │ API request      │                 │
     │               │─────────────────>│                 │
     │               │                  │                 │
     │               │ unlabeled data   │                 │
     │               │<─────────────────│                 │
     │               │                  │                 │
     │               │ apply rules      │                 │
     │               │─────────┐        │                 │
     │               │         │        │                 │
     │               │<────────┘        │                 │
     │               │ 60% labeled      │                 │
     │               │                  │                 │
     │               │ predict remaining│                 │
     │               │─────────────────────────────────>│
     │               │                  │                 │
     │               │ ML predictions   │                 │
     │               │<─────────────────────────────────│
     │               │ 40% labeled      │                 │
     │               │                  │                 │
     │               │ link SOPs        │                 │
     │               │─────────┐        │                 │
     │               │         │        │                 │
     │               │<────────┘        │                 │
     │               │ all linked       │                 │
     │               │                  │                 │
     │               │ generate outputs │                 │
     │               │─────────┐        │                 │
     │               │         │        │                 │
     │               │<────────┘        │                 │
     │               │ CSV + Slack txt  │                 │
     │               │                  │                 │
     │ CSV ready     │                  │                 │
     │<──────────────│                  │                 │
     │               │                  │                 │
     │ open & verify │                  │                 │
     │──────────────>│                  │                 │
     │               │                  │                 │
```

---

## FILE STRUCTURE & DEPENDENCIES

```
SOPSlack/
│
├── code7.py ◄─────────────────── Main orchestrator
│   ├── imports: pandas, requests, datetime
│   ├── calls: labeling_rules, predict_with_rules, sop_mappings
│   ├── calls: holidays, fun_facts
│   └── outputs: CSV, Slack message text
│
├── labeling_rules.py ◄─────────── Business rule logic (60% coverage)
│   └── imports: pandas
│
├── predict_with_rules.py ◄─────── ML model (40% coverage)
│   ├── imports: sklearn, pandas, numpy, pickle
│   └── trained_model.pkl (saved model file)
│
├── sop_mappings.py ◄────────────── Agent → SOP URL mappings
│   └── Simple dictionary, no dependencies
│
├── holidays.py ◄────────────────── Banking holiday calendar
│   └── imports: datetime
│
├── fun_facts.py ◄───────────────── Engagement content
│   └── imports: random, json
│
├── .env ◄───────────────────────── API keys & tokens (not in git)
│   ├── REDASH_API_KEY
│   └── SLACK_ACCESS_TOKEN (future use)
│
├── .gitignore ◄─────────────────── Security (excludes .env, etc.)
│
└── ~/Desktop/cursor_data/ ◄────── Output directory
    ├── daily_recon_*.csv
    ├── slack_message_*.txt
    └── fun_facts_used.json
```

---

## TECHNOLOGY STACK

```
┌────────────────────────────────────────────────────┐
│              TECHNOLOGY COMPONENTS                 │
├────────────────────────────────────────────────────┤
│                                                    │
│ LANGUAGE:          Python 3.9+                     │
│                                                    │
│ CORE LIBRARIES:                                    │
│ • pandas           Data manipulation               │
│ • scikit-learn     ML models & preprocessing       │
│ • requests         HTTP API calls                  │
│ • numpy            Numerical operations            │
│                                                    │
│ ML COMPONENTS:                                     │
│ • RandomForestClassifier  Primary model            │
│ • TfidfVectorizer         Text feature extraction  │
│ • StandardScaler          Numerical normalization  │
│ • LabelEncoder            Categorical encoding     │
│                                                    │
│ DATA SOURCE:                                       │
│ • Redash API      Query execution platform         │
│                                                    │
│ OUTPUT FORMATS:                                    │
│ • CSV             Excel-compatible data            │
│ • Text/Markdown   Slack message format             │
│                                                    │
│ FUTURE INTEGRATION:                                │
│ • Slack SDK       Direct bot posting               │
│ • Cron            Automated scheduling             │
│                                                    │
│ DEVELOPMENT TOOLS:                                 │
│ • Cursor AI       Code generation & iteration      │
│ • Git             Version control                  │
│ • GitHub          Repository hosting               │
│                                                    │
└────────────────────────────────────────────────────┘
```

---

## SECURITY & CONFIGURATION

```
Environment Variables (.env):
├── REDASH_API_KEY      → Redash query access
└── SLACK_ACCESS_TOKEN  → Future bot integration (not yet used)

Security Measures:
├── .env excluded from git (.gitignore)
├── API keys never hardcoded
├── Sensitive data not logged
└── Output files local-only (not pushed to git)
```

---

This architecture enables:
✓ Modularity (easy to update rules or swap ML models)
✓ Testability (each component can be tested independently)
✓ Scalability (can handle growing transaction volumes)
✓ Maintainability (clear separation of concerns)
✓ Extensibility (easy to add new features or integrations)


