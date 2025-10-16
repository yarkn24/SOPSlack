# Daily Reconciliation Workflow

## Quick Manual Workflow (30 seconds)

### Morning Routine:

1. **Run CODE7**
   ```bash
   cd ~/Documents/GitHub/SOPSlack
   python3 code7.py
   ```
   
2. **Copy Slack Message**
   ```bash
   # Get latest Slack message
   cat ~/Desktop/cursor_data/slack_message_*.txt | pbcopy
   ```

3. **Post to Slack**
   - Go to `#platform-ops-recon`
   - Paste the message (Cmd+V)
   - Done! ✅

---

## Automated Workflow (Future - Requires Slack Bot)

Once Eric approves the Slack bot:

```bash
# Set up token (one time)
export SLACK_BOT_TOKEN='xoxb-your-token-here'
echo 'export SLACK_BOT_TOKEN="xoxb-..."' >> ~/.zshrc

# Run automated
python3 daily_recon_slack_bot.py --prod
```

---

## Quick Check (2 seconds)

Just check if there are transactions:

```bash
./code7
```

Output:
```
⚠️ No Transactions - Saturday, Oct 11, 2025
📊 Weekend/Holiday
✅ CODE7 Complete
```

---

## Cron Job (Future Automation)

Add to crontab:
```bash
# Run every weekday at 9 AM
0 9 * * 1-5 cd ~/Documents/GitHub/SOPSlack && python3 daily_recon_slack_bot.py --prod
```

---

## Files Generated

All outputs saved to: `~/Desktop/cursor_data/`

- `redash_agents_YYYYMMDD_HHMMSS.csv` - Transaction data with predictions
- `slack_message_YYYYMMDD_HHMMSS.txt` - Ready-to-post Slack message

---

## Troubleshooting

### No transactions?
- **Weekend/Holiday** - Banks are closed
- **Too early** - Data not posted yet
- **Check Redash**: https://redash.zp-int.com/queries/133695

### Need to update rules?
Edit: `predict_with_rules.py`

### Wrong predictions?
Check: `agent_sop_mapping.py` for SOP links

---

## Contact

Questions? Ping Platform Operations team or check Confluence SOPs.




