# Cursor AI - Prompt Export & Development Conversations

**Project:** CODE7 - Daily Reconciliation Automation  
**AI Assistant:** Cursor Agent (Claude Sonnet 4.5)  
**Development Period:** September - October 2025

---

## DEVELOPMENT PHASES & KEY PROMPTS

### PHASE 1: Initial Data Fetching (Week 1)

**Prompt 1:**
```
Redashten buldugun datayi cek agentlari labella ve benimle download yapmam icin paylas

[Translation: Fetch data from Redash, label the agents, and share for download]
```

**Context:** First iteration - needed basic Redash integration  
**Output:** Initial `code7.py` with:
- Redash API authentication
- Query execution
- Data fetching
- Basic CSV export

**Prompt 2:**
```
output yaparken payment method ve org account mappinge sadik kal rakam degul sadece text kullan mappinge gore

[Translation: When outputting, follow payment method and org account mappings using text not numbers]
```

**Context:** Output formatting was using codes instead of readable names  
**Output:** Enhanced output logic to use human-readable text mappings

---

### PHASE 2: Business Rule Implementation (Week 2)

**Prompt 3:**
```
Create labeling rules based on business reconciliation policies:
1. Never label ZBT transactions (they handle their own)
2. Map org accounts to specific agents
3. Use payment method patterns for classification
4. Make it maintainable and easy to update
```

**Output:** `labeling_rules.py` created with:
```python
def should_skip_transaction(row):
    """Business rule: Skip ZBT transactions"""
    if 'zbt' in str(row.get('org_account', '')).lower():
        return True
    return False

ORG_ACCOUNT_MAP = {
    "ZenPayroll Operations, Inc": "ICP Agent",
    "ZP Labs, Inc": "Revolut Agent",
    # ... mappings
}
```

**Prompt 4:**
```
Add specific account number patterns:
- Accounts starting with "8888" → Mercury Agent
- Accounts containing "revolut" → Revolut Agent
- Wire transfers over $10,000 → ICP Agent
```

**Output:** Pattern-based rules added to `labeling_rules.py`

---

### PHASE 3: ML Model Development (Week 3)

**Prompt 5:**
```
The rules cover only about 60% of transactions. Build an ML model for the remaining ambiguous cases:
- Use transaction narrative (text)
- Include amount, payment method, org account as features
- Train on historical reconciliations
- Compare multiple algorithms (Random Forest, XGBoost, Logistic Regression)
- Show which performs best
```

**Output:** `predict_with_rules.py` created with:
- TF-IDF vectorization for narratives
- Feature engineering pipeline
- Model comparison framework
- Initial accuracy: 33% (ML-only, not good enough)

**Prompt 6:**
```
The ML-only accuracy is too low (33%). Create a hybrid approach:
1. First, try to apply business rules
2. If no rule matches, use ML model
3. If ML confidence < 50%, flag for manual review
4. Return the predicted agent + confidence score
```

**Output:** Hybrid prediction logic implemented:
```python
def predict_with_hybrid(transaction):
    # Try rules first
    rule_result = apply_rules(transaction)
    if rule_result:
        return rule_result, 1.0  # 100% confidence
    
    # Fall back to ML
    ml_prediction, confidence = ml_model.predict(transaction)
    if confidence < 0.5:
        return "MANUAL_REVIEW", confidence
    
    return ml_prediction, confidence
```

**Result:** Accuracy jumped to 82%

**Prompt 7:**
```
Still not accurate enough. Let's improve feature engineering:
1. Add TF-IDF on transaction narratives
2. Create cross-field features (payment_method × org_account patterns)
3. Normalize amount into buckets
4. Include day-of-week and month features
5. Retrain and validate
```

**Output:** Enhanced feature engineering → **98% accuracy achieved**

---

### PHASE 4: Output Generation & SOP Linking (Week 4)

**Prompt 8:**
```
For each predicted agent, automatically link the relevant SOP from Confluence. 
Create a mapping dictionary of:
- Agent name → Confluence SOP URL

Also add a column to the CSV output with the linked SOP for each transaction.
```

**Output:** `sop_mappings.py` created:
```python
SOP_MAPPING = {
    "ICP Agent": "https://confluence.zenefits.com/display/accounting/ICP+Reconciliation+SOP",
    "ZBT Agent": "https://confluence.zenefits.com/display/accounting/ZBT+Reconciliation+SOP",
    # ... all agents
}
```

**Prompt 9:**
```
Generate a Slack-friendly daily summary message that includes:
1. Header with current date
2. Total transaction count
3. Breakdown by predicted agent
4. Highlight high-impact items (ICP batches, large amounts)
5. Include SOP links for each agent category
6. Add a finance fun fact for engagement
7. Format for easy copy-paste to Slack
```

**Output:** Enhanced `code7.py` with `generate_slack_message()` function

---

### PHASE 5: Engagement & Polish (Week 5)

**Prompt 10:**
```
Add US banking holiday detection using the Federal Reserve calendar:
- New Year's Day
- MLK Day
- Presidents' Day
- Memorial Day
- Independence Day
- Labor Day
- Thanksgiving
- Christmas

If today is a holiday or weekend, show a special celebratory message instead of "no transactions."
```

**Output:** `holidays.py` created with banking holiday logic

**Prompt 11:**
```
Create a collection of 50+ finance and accounting fun facts. 
Track which facts have been used (store in a local file) so we don't repeat.
Pull a random unused fact each day for the Slack message.
```

**Output:** `fun_facts.py` with fact library and usage tracking

**Prompt 12:**
```
The Cursor Slack Agent times out when running the full processing. 
Add a --quick flag that:
- Only checks if data exists in Redash
- Returns transaction count
- Exits immediately (no prediction, no CSV)
- Should complete in under 3 seconds
```

**Output:** Quick check mode added to `code7.py`:
```python
if args.quick:
    count = len(fetch_transaction_count())
    print(f"✅ {count} transactions found")
    exit(0)
```

---

### PHASE 6: Error Handling & Bug Fixes

**Prompt 13:**
```
Error: AttributeError: Can only use .str accessor with string values!
This happens when Redash returns 0 transactions on weekends.
Fix: Check if dataframe is empty before applying string operations.
```

**Output:** Added empty dataframe check:
```python
if len(df) == 0:
    print("⚠️ No transactions today")
    exit(0)
```

**Prompt 14:**
```
Error: KeyError: 'ml_pred' when using a static CSV file
Fix: When loading from file (not Redash), assume it's raw data and run predictions.
Add argparse to distinguish between modes.
```

**Output:** Added argument parsing and mode detection

**Prompt 15:**
```
The validation test in predict_with_rules.py runs every time the module is imported,
causing long delays. Fix: Move validation code inside if __name__ == "__main__"
```

**Output:** Refactored to run validation only when script is executed directly

---

### PHASE 7: Output Location & Organization

**Prompt 16:**
```
Change output directory from ~/Downloads/ to ~/Desktop/cursor_data/
Also create the directory if it doesn't exist.
Move any existing output files to the new location.
```

**Output:** Updated all output paths, added directory creation logic

---

### PHASE 8: Slack Integration Attempts

**Prompt 17:**
```
Create a Slack bot that:
1. Posts the daily summary to #daily-recon channel
2. Uses Slack SDK
3. Handles token refresh (xoxe tokens)
4. Runs on schedule
```

**Output:** `daily_recon_slack_bot.py` created (requires IT approval for bot token)

**Prompt 18:**
```
The bot integration is moving slowly with IT. 
For now, just generate the Slack message as a text file that can be copy-pasted.
Keep the CSV output working independently.
```

**Output:** Interim solution - text file generation for manual posting

---

## PROMPT ENGINEERING PATTERNS THAT WORKED

### 1. Iterative Refinement
Start broad, then refine based on results:
```
Initial: "Create an ML model"
After testing: "ML accuracy is 33%, too low. Try hybrid approach."
After iteration: "Add cross-field features to improve accuracy."
```

### 2. Specific Examples
Provide concrete examples in prompts:
```
Good: "If account starts with '8888' → Mercury Agent"
Bad: "Add some account rules"
```

### 3. Context First
Explain the problem before requesting the solution:
```
"Operators spend 30-45 min labeling daily. Build a system that predicts 
labels so they only verify instead of build from scratch."
```

### 4. Incremental Complexity
Build features one at a time, test, then add more:
```
Week 1: Fetch data
Week 2: Add rules
Week 3: Add ML
Week 4: Add outputs
Week 5: Polish
```

### 5. Error-Driven Development
When errors occur, provide the full error message:
```
"Error: AttributeError: Can only use .str accessor with string values!
This happens when dataframe is empty. Fix by checking length first."
```

---

## PROMPT ENGINEERING PATTERNS THAT DIDN'T WORK

### 1. Too Vague
```
❌ "Make the model better"
✅ "Improve accuracy by adding TF-IDF features on transaction narratives"
```

### 2. Too Many Changes At Once
```
❌ "Add ML, SOP linking, Slack output, and holiday detection"
✅ [Break into 4 separate prompts, one per feature]
```

### 3. Assuming Context Without Providing It
```
❌ "Add the ZBT rule"
✅ "Add business rule: Never label ZBT transactions because they handle 
    their own reconciliations per policy"
```

---

## DEVELOPMENT METRICS

**Total Prompts Used:** ~50+  
**Code Generated by AI:** ~85% of final codebase  
**Manual Edits:** ~15% (business-specific mappings, URLs, configuration)  
**Iterations on Core Model:** 4 major versions  
**Time Saved vs Manual Coding:** Estimated 60-80 hours

---

## KEY TAKEAWAYS FOR FUTURE PROJECTS

1. **Start Simple:** Basic data fetching → rules → ML → polish
2. **Test Continuously:** Every major change should be tested immediately
3. **Provide Context:** Explain the business problem, not just technical requirements
4. **Use Examples:** Concrete examples > abstract descriptions
5. **Iterate:** First version rarely works perfectly - refine based on results
6. **Document as You Go:** Easier to record prompts during development than after

---

## SAMPLE CONVERSATION FLOW

**Me:** "Fetch data from Redash and create CSV output"  
**Cursor:** [Generates code7.py with API integration]  

**Me:** "Test fails - API key not found"  
**Cursor:** [Adds .env file support and environment variable loading]  

**Me:** "Output has codes instead of readable names"  
**Cursor:** [Updates mapping to use text labels]  

**Me:** "Add business rule: Never label ZBT"  
**Cursor:** [Creates labeling_rules.py with ZBT skip logic]  

**Me:** "Rules only cover 60%, need ML for the rest"  
**Cursor:** [Builds predict_with_rules.py with ML model]  

**Me:** "Accuracy is only 33%, not good enough"  
**Cursor:** [Implements hybrid rules + ML approach → 82%]  

**Me:** "Still need higher accuracy for production"  
**Cursor:** [Enhances feature engineering → 98%]  

**Me:** "Link SOPs to each agent prediction"  
**Cursor:** [Creates sop_mappings.py and adds SOP column to CSV]  

**Me:** "Generate Slack message format"  
**Cursor:** [Adds Slack message generation with formatting]  

**Me:** "Celebrate holidays instead of showing 'no data' warning"  
**Cursor:** [Creates holidays.py with special messages]  

**Me:** "Make Slack messages more engaging"  
**Cursor:** [Adds fun_facts.py with daily rotation]  

**Result:** Fully functional AI-powered reconciliation automation system

---

**Note:** Full conversation history with timestamps available in Cursor IDE history.  
This export contains the key prompts that shaped the development direction.


