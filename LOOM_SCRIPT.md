# CODE7 - Loom Video Script
**Duration:** ~8-10 minutes

---

## INTRO (30 sec)
"Hi, I'm Yarkin. Today I'll walk you through CODE7, an AI-powered daily reconciliation automation system. I'll cover the architecture, the hybrid rule + ML approach, the AI tools I used to build it, and how it impacts our daily operations workflow."

---

## 1. THE PROBLEM (1 min)
**Show:** Redash query with blank "Agent" fields

"Every morning, our reconciliation queue arrives with unlabeled transactions. Before CODE7, operators would:
- Manually interpret each transaction
- Look up SOPs
- Screen for high-impact items
- Then start reconciliation

This took 30-45 minutes daily, per operator."

---

## 2. ARCHITECTURE & DATA FLOW (2 min)
**Show:** Architecture diagram or code structure

```
Redash API (Query 133695)
    ↓
code7.py (main orchestrator)
    ↓
1. Fetch unlabeled transactions
2. Apply labeling_rules.py (60% coverage)
3. predict_with_rules.py (40% ML + rules)
4. Link SOPs via sop_mappings.py
5. Generate outputs:
   - CSV: ~/Desktop/cursor_data/
   - Slack message: slack_message.txt
```

**Key Components:**
- `code7.py`: Main orchestrator
- `labeling_rules.py`: Business rule logic (ZBT, account mapping)
- `predict_with_rules.py`: Hybrid ML + rule predictor
- `sop_mappings.py`: Links agents → confluence SOPs
- `holidays.py`: Banking holiday detection
- `fun_facts.py`: Engagement layer for Slack

---

## 3. RULE LOGIC & ML COMPONENTS (2 min)
**Show:** labeling_rules.py code

"The system is 60% rule-based:
- ZBT transactions → ZBT agent (never labeled)
- Specific org accounts → mapped agents
- Payment method patterns → deterministic agents

The remaining 40% uses ML for ambiguous cases."

**Show:** predict_with_rules.py

"ML Model:
- Library: scikit-learn (RandomForest, Logistic Regression, XGBoost tested)
- Training data: Historical reconciliations (operators' past judgments)
- Features: transaction narrative, amount, payment method, org account
- First attempt: 33% accuracy (ML-only)
- Current: 98% (hybrid rules + ML)

The model learns from how experienced operators previously resolved ambiguous cases."

---

## 4. AI ASSISTANTS USED (1 min)
**Show:** Cursor IDE or conversation history

"I built this entirely using Cursor AI Agent:
- Code generation and iteration
- Rule logic refinement
- ML model training and validation
- Error debugging and optimization
- Documentation

Key prompts I used:
1. 'Create a hybrid rule + ML predictor for transaction labeling'
2. 'Add business rule: never label ZBT transactions'
3. 'Optimize for ambiguous transaction narratives'
4. 'Generate Slack-friendly output with SOPs linked'
5. 'Add banking holiday detection and fun facts'

I'll share the full prompt export separately."

---

## 5. VALIDATION & RESULTS (1.5 min)
**Show:** Validation output or metrics

"Validation approach:
- Split historical data: 70% train, 15% validation, 15% test
- Baseline: Random guessing (~7% accuracy, 14 agents)
- Rule-based only: ~60% coverage
- ML-only: 33% accuracy
- Hybrid (rules + ML): 98% accuracy

Real-world validation:
- Testing with daily ops team this week
- Measuring: prediction acceptance rate, time saved, manual corrections
- Target: 10 hours/week saved across team"

---

## 6. OUTPUT CONSUMPTION (1 min)
**Show:** CSV file and Slack message

"Outputs:
1. CSV file: Pre-labeled queue with columns:
   - Agent (predicted)
   - SOP Link (auto-mapped)
   - Impact Flag (high-priority items)

2. Slack message: Daily summary with:
   - Transaction counts by agent
   - High-impact alerts
   - SOP links
   - Fun fact for engagement
   - Banking holiday awareness

Currently: CSV generated locally, shared manually
Future: Direct Slack bot integration (pending IT)"

---

## 7. WORKFLOW IMPACT (1 min)
**Show:** Before/after comparison

"Before CODE7:
- Operator starts with blank queue
- 30-45 min manual labeling
- SOP lookup/escalation
- Manual screening for priorities
- Then reconciliation

After CODE7:
- Pre-labeled queue ready at day start
- Operators verify vs build from scratch
- SOPs already linked
- High-impact items flagged
- Straight to reconciliation

Estimated savings: 1-2 hours/day per operator"

---

## CLOSING (30 sec)
"That's CODE7 - a hybrid AI system that codifies operator expertise and applies it consistently to new transactions each morning. Happy to answer any questions or dive deeper into any component.

All code, prompts, and documentation are in the GitHub repo: SOPSlack"

---

## DEMO CHECKLIST:
- [ ] Show Redash query (blank agents)
- [ ] Walk through code7.py
- [ ] Show labeling_rules.py logic
- [ ] Show predict_with_rules.py ML model
- [ ] Show Cursor AI conversations
- [ ] Show CSV output example
- [ ] Show Slack message format
- [ ] Show validation metrics

---

**Recording Tips:**
1. Keep it conversational, not scripted
2. Show actual code, not just talk about it
3. Demonstrate the output (CSV + Slack message)
4. Be honest about current state (local, not full IT integration yet)
5. Emphasize the hybrid approach and iteration process


