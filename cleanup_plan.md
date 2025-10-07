# Cleanup Plan - Files Analysis

## ✅ KEEP (Production & Essential Files)

### Core ML & Prediction
1. `ultra_fast_training.py` - **FINAL** training script (98.64% accuracy)
2. `predict_with_rules.py` - Prediction engine with hybrid rules
3. `data_mapping.py` - Text ↔ Number mapping (Redash ↔ ML)

### Data Processing
4. `save_data_in_redash_format.py` - Convert training data to Redash format
5. `redash_auto_fetch.py` - Fetch data from Redash API

### Slack Integration
6. `daily_recon_slack_bot.py` - Slack bot implementation
7. `slack_daily_message_template.py` - Message template generator
8. `full_example_message.py` - Full example for testing
9. `example_daily_message.py` - Example scenarios

### SOP & Documentation
10. `agent_sop_mapping.py` - Agent → SOP mapping (21 agents)
11. `generate_report.py` - Generate SOP mapping report

### Confluence
12. `gemini_confluence_bot.py` - Confluence integration

### Documentation
13. `AI_PROJECT_SUMMARY.md` - Project documentation
14. `AGENT_SOP_MAPPING_REPORT.md` - SOP mapping report
15. `SLACK_BOT_SETUP.md` - Slack bot setup guide
16. `README.md` - Main readme

---

## ❌ DELETE (Old/Unused Files)

### Old Training Scripts (Superseded by ultra_fast_training.py)
1. `compare_3_algorithms.py` - Experimental
2. `fast_iterative_training.py` - Old iteration
3. `final_95_training.py` - Old target (95%)
4. `final_training_with_rules.py` - Old version
5. `fresh_training.py` - Old version
6. `full_pipeline_to_90.py` - Old target (90%)
7. `hybrid_heuristic_ml.py` - Old approach
8. `iterative_98_training.py` - Old iteration
9. `memory_efficient_training.py` - Old optimization
10. `multi_algorithm_training.py` - Experimental
11. `perfect_rules_training.py` - Old approach
12. `push_to_95.py` - Old target

### Old/Unused Utilities
13. `compare_data_formats.py` - One-time analysis
14. `convert_all_to_redash_format.py` - Not used (save_data_in_redash_format.py is used)
15. `daily_automation_complete.py` - Duplicate/incomplete
16. `labeling_rules.py` - Old rules (integrated into ultra_fast_training.py)
17. `list_all_agents.py` - One-time utility
18. `ml_prediction_api.py` - API version (not deployed)
19. `redash_csv_loader.py` - Old version (redash_auto_fetch.py is used)
20. `redash_data_loader.py` - Old version (redash_auto_fetch.py is used)

---

## 📊 SUMMARY

**Keep:** 16 files (production + documentation)  
**Delete:** 20 files (old/experimental/duplicate)

**Space saved:** ~200KB of unused code
