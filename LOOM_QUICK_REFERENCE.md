# CODE7 - Loom Recording Quick Reference

**For recording preparation and demo walkthrough**

---

## 🎬 RECORDING CHECKLIST

### Before You Start Recording
- [ ] Open Cursor IDE with SOPSlack project
- [ ] Have terminal ready in project directory
- [ ] Open example CSV output
- [ ] Open example Slack message
- [ ] Have Redash query page ready in browser
- [ ] Close unnecessary windows/notifications
- [ ] Test audio/video quality

### Files to Show On Screen
1. `code7.py` (main)
2. `labeling_rules.py` (business rules)
3. `predict_with_rules.py` (ML model)
4. `sop_mappings.py` (SOP links)
5. Example CSV output
6. Example Slack message
7. Cursor conversation history (prompts)

---

## 🎯 KEY TALKING POINTS (8-10 min)

### 1. PROBLEM (1 min)
**Show:** Redash with blank "Agent" fields

**Say:**
> "Every morning, our recon queue arrives with blank agent fields. Operators used to spend 30-45 minutes manually labeling, looking up SOPs, and screening for priorities before they could even start reconciliation work. CODE7 automates this setup phase."

---

### 2. SOLUTION OVERVIEW (1 min)
**Show:** Architecture diagram

**Say:**
> "CODE7 is a hybrid system: 60% rule-based for deterministic cases, 40% ML for ambiguous patterns. It predicts agent labels, links SOPs, and flags high-impact items. Operators start their day with a pre-populated queue instead of building from scratch."

---

### 3. ARCHITECTURE WALKTHROUGH (2 min)
**Show:** `code7.py` code structure

**Say:**
> "The system fetches unlabeled transactions from Redash API, applies business rules first for clear cases like ZBT transactions or specific account patterns. For ambiguous cases, it uses a RandomForest model trained on historical operator judgments. Then it links the relevant SOP for each agent and generates both CSV and Slack outputs."

**Show flow:**
```
Redash → code7.py → Rules (60%) → ML (40%) → SOP Linking → Outputs
```

---

### 4. BUSINESS RULES (1.5 min)
**Show:** `labeling_rules.py`

**Point out specific examples:**
```python
# ZBT Skip Rule
if 'zbt' in org_account.lower():
    return None  # Business policy

# Org Account Mapping  
ORG_ACCOUNT_MAP = {
    "ZenPayroll Operations, Inc": "ICP Agent",
    ...
}

# Payment Method Rules
if payment_method == "Wire Transfer" and amount > 10000:
    return "ICP Agent"
```

**Say:**
> "These rules codify our existing reconciliation policies. They're deterministic and cover about 60% of daily transactions. This part could theoretically be done with SQL, which is why we use rules not ML here."

---

### 5. ML MODEL (2 min)
**Show:** `predict_with_rules.py`

**Say:**
> "For the remaining 40% - ambiguous transaction narratives, new patterns, cross-field interpretations - we use machine learning. The model learns from how experienced operators previously resolved similar cases."

**Show key components:**
- Feature engineering (TF-IDF on narratives)
- Model selection (RandomForest won)
- Hybrid logic (rules first, then ML)

**Say:**
> "First attempt was ML-only at 33% accuracy - not usable. After multiple iterations, adding rules, improving features, the hybrid approach reached 98%. This wasn't 'throw ML at the problem' - it was systematic testing to find what works."

**Show validation results:**
```
Baseline: 7% (random guessing, 14 classes)
Rules-only: 60% coverage
ML-only V1: 33% accuracy
Hybrid V4: 98.6% accuracy ✓
```

---

### 6. AI DEVELOPMENT PROCESS (1.5 min)
**Show:** Cursor conversation history

**Say:**
> "I built this entirely with Cursor AI Agent. Here's the iterative process:"

**Walk through key prompts:**
1. "Fetch data from Redash and label agents"
2. "Add business rule: never label ZBT transactions"
3. "Create hybrid predictor: rules first, then ML"
4. "Link SOPs to each agent prediction"
5. "Generate Slack-friendly output"
6. "Add banking holiday detection"

**Say:**
> "Prompt engineering was critical. Starting with specific examples and business context worked far better than vague requests. I'll share the full prompt export showing this iteration."

---

### 7. OUTPUTS (1 min)
**Show:** Example CSV file in Excel/Numbers

**Say:**
> "The CSV contains all original transaction fields plus three predicted columns: agent, SOP link, and impact flag."

**Show:** Example Slack message

**Say:**
> "The Slack message gives a daily summary with counts, high-impact alerts, SOP links, and a fun fact for engagement. Currently manual copy-paste, but IT integration is in progress."

---

### 8. BUSINESS IMPACT (1 min)
**Show:** Before/after comparison slide/notes

**Say:**
> "Before CODE7, operators started with a blank queue and built everything manually. After, they start with predictions and just verify. Estimated savings: 1-2 hours per operator, per day - that's about 10 hours per week across the team."

**Show validation plan:**
> "We're currently testing with the team to measure actual prediction acceptance rates, time saved, and manual corrections needed. Those real-world metrics will validate the business value."

---

## 🎤 DEMO SCRIPT (Optional Live Run)

If showing live execution:

```bash
# Terminal commands to demonstrate

# 1. Quick check mode (3 sec response)
python3 code7.py --quick

# Expected output:
# ✅ 23 transactions - Tuesday, October 14, 2025
# Run: python3 code7.py

# 2. Full processing (demo, may take 30-60 sec)
python3 code7.py

# Expected output:
# 🚀 CODE7 Starting...
# 📊 Found 23 transactions
# 🤖 Applying rules...
# 🧠 ML predictions...
# 🔗 Linking SOPs...
# ✅ Complete!
# 📁 CSV: ~/Desktop/cursor_data/daily_recon_20251014_153022.csv
# 💬 Slack: ~/Desktop/cursor_data/slack_message_20251014_153022.txt

# 3. Open outputs
open ~/Desktop/cursor_data/
```

---

## 📊 KEY METRICS TO MENTION

### Technical Performance
- **Accuracy:** 98.6%
- **Prediction time:** 0.7ms per transaction
- **Coverage:** 100% (rules + ML combined)
- **Baseline improvement:** 33% → 98% through iteration

### Business Impact (Estimated)
- **Labeling time:** 30-45 min → ~5 min
- **Queue screening:** 20-30 min → 0 min
- **SOP lookup:** 15-30 min → 0 min
- **Total savings:** 1-2 hrs/operator/day
- **Weekly savings:** ~10 hrs across team

### Development Efficiency
- **Time to build:** ~5 weeks (with Cursor AI)
- **Est. manual coding time:** 60-80 hours
- **AI-generated code:** ~85%
- **Iterations needed:** 4 major versions

---

## 🎯 CLOSING STATEMENT

**Say:**
> "CODE7 demonstrates how AI can augment operational workflows - not replacing human judgment, but codifying expert knowledge and applying it consistently. The hybrid approach was key: rules for deterministic cases, ML for ambiguity. This isn't just a technical experiment - it's designed to save real time and improve consistency in daily operations. I'll follow up with measured validation metrics once testing is complete. Happy to answer any questions."

---

## ❓ ANTICIPATED QUESTIONS & ANSWERS

### Q: "Why not just write more rules?"
**A:** "We tried - rules cover ~60%. The remaining cases involve pattern recognition across narratives and multiple fields that are hard to capture in if/else logic. ML excels at this."

### Q: "How do you handle when the model is wrong?"
**A:** "Operators verify all predictions - it's a starting point, not autopilot. Even wrong predictions are faster to correct than starting from scratch. We'll measure correction rates during testing."

### Q: "What's the IT integration timeline?"
**A:** "CSV and Slack text work today and provide the core value. Full bot integration requires IT approval for tokens - that's in progress but not blocking the system's usability."

### Q: "How do you keep the model up to date?"
**A:** "Future plan: Active learning where operator corrections feed back into retraining. For now, we'll retrain quarterly as we accumulate more data."

### Q: "What if a new transaction type appears?"
**A:** "If it doesn't match rules or ML predicts with low confidence, it's flagged for manual review. Operators add a new rule or the case becomes training data for the model."

---

## 📦 DELIVERABLES TO MENTION

1. **Loom Video** (this recording)
2. **Written Summary** (`CODE7_DEVELOPMENT_SUMMARY.md`)
3. **Architecture Diagram** (`ARCHITECTURE_DIAGRAM.md`)
4. **Prompt Exports** (`CURSOR_PROMPTS_EXPORT.md`)
5. **All Source Code** (GitHub: SOPSlack)
6. **Validation Metrics** (in progress, will follow up)

---

## ⏱️ TIME ALLOCATION

| Section | Duration | Running Total |
|---------|----------|---------------|
| Intro | 0:30 | 0:30 |
| Problem | 1:00 | 1:30 |
| Architecture | 2:00 | 3:30 |
| Business Rules | 1:30 | 5:00 |
| ML Model | 2:00 | 7:00 |
| AI Development | 1:30 | 8:30 |
| Outputs | 1:00 | 9:30 |
| Impact | 1:00 | 10:30 |
| Closing | 0:30 | 11:00 |

**Target:** 10-11 minutes total

---

## 💡 TIPS FOR RECORDING

1. **Speak clearly and conversationally** - not scripted
2. **Show code, don't just talk about it** - visuals matter
3. **Use mouse/cursor to highlight** what you're discussing
4. **Pause briefly between sections** - makes editing easier
5. **If you mess up, just pause and restart that section** - edit later
6. **Demo the actual outputs** - CSV and Slack message
7. **Be honest about current state** - local outputs, IT integration pending
8. **Emphasize the iteration** - 33% → 98% shows real engineering
9. **Keep energy up** - enthusiasm is contagious
10. **End with clear next steps** - validation metrics coming

---

**Ready to record? You've got this! 🚀**


