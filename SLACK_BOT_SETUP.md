# Slack Bot Setup Guide - Daily Reconciliation Bot

## Overview
This guide will help you set up the Daily Reconciliation Bot for Platform Operations team.

---

## Step 1: Create Slack App

1. Go to https://api.slack.com/apps
2. Click **"Create New App"**
3. Choose **"From scratch"**
4. App Name: `Daily Reconciliation Bot`
5. Pick your workspace: `Gusto`
6. Click **"Create App"**

---

## Step 2: Configure Bot Permissions

### OAuth & Permissions

1. In the left sidebar, click **"OAuth & Permissions"**
2. Scroll down to **"Scopes"**
3. Add these **Bot Token Scopes:**
   - `chat:write` - Send messages
   - `chat:write.public` - Send messages to public channels
   - `channels:read` - View basic channel info
   - `users:read` - View people in workspace

### Install to Workspace

1. Scroll to top of OAuth & Permissions page
2. Click **"Install to Workspace"**
3. Click **"Allow"**
4. **Copy the "Bot User OAuth Token"** (starts with `xoxb-`)
   - ⚠️ Save this token securely - you'll need it!

---

## Step 3: Set Up Environment Variables

Create a `.env` file in your project:

```bash
# Slack Configuration
SLACK_BOT_TOKEN=xoxb-your-token-here
SLACK_CHANNEL=#platform-operations

# Optional: For different environments
SLACK_TEST_CHANNEL=#recon-bot-testing
```

⚠️ **Security:** Add `.env` to `.gitignore` - never commit tokens!

---

## Step 4: Install Required Python Packages

```bash
pip install slack-sdk python-dotenv pandas scikit-learn xgboost
```

Save to requirements.txt:
```bash
pip freeze > requirements.txt
```

---

## Step 5: Create Slack Bot Script

File: `daily_recon_slack_bot.py`

```python
import os
from datetime import datetime
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from dotenv import load_dotenv
from slack_daily_message_template import generate_daily_recon_message

# Load environment variables
load_dotenv()

# Initialize Slack client
slack_token = os.environ.get("SLACK_BOT_TOKEN")
client = WebClient(token=slack_token)

def send_daily_message(agent_counts, high_value_icp=None, channel="#platform-operations"):
    """
    Send daily reconciliation message to Slack.
    
    Args:
        agent_counts: Dictionary with agent names and counts
        high_value_icp: List of high-value ICP transactions
        channel: Slack channel to send to
    """
    try:
        # Generate message
        message = generate_daily_recon_message(
            agent_counts=agent_counts,
            high_value_icp_transactions=high_value_icp,
            date=datetime.now()
        )
        
        # Send to Slack
        response = client.chat_postMessage(
            channel=channel,
            text=message,
            mrkdwn=True  # Enable Slack markdown formatting
        )
        
        print(f"✅ Message sent successfully to {channel}")
        print(f"   Message timestamp: {response['ts']}")
        return response
        
    except SlackApiError as e:
        print(f"❌ Error sending message: {e.response['error']}")
        return None


def test_connection():
    """Test Slack bot connection."""
    try:
        response = client.auth_test()
        print("✅ Slack Bot Connected!")
        print(f"   Bot Name: {response['user']}")
        print(f"   Team: {response['team']}")
        return True
    except SlackApiError as e:
        print(f"❌ Connection failed: {e.response['error']}")
        return False


if __name__ == "__main__":
    # Test connection
    if test_connection():
        print("\n🎉 Ready to send daily messages!")
        
        # Example usage
        example_counts = {
            'ACH': 85,
            'Check': 47,
            'Risk': 32,
            'Treasury Transfer': 18,
            'NY WH': 12,
        }
        
        example_high_value = [
            {
                'id': '58947891',
                'agent': 'Nium Payment',
                'amount': 487500.00,
                'description': 'ORIG CO NAME=NIUM INC...',
            }
        ]
        
        # Send test message to test channel
        print("\n📤 Sending test message...")
        send_daily_message(
            agent_counts=example_counts,
            high_value_icp=example_high_value,
            channel=os.environ.get("SLACK_TEST_CHANNEL", "#recon-bot-testing")
        )
```

---

## Step 6: Test the Bot

```bash
# Set environment variables
export SLACK_BOT_TOKEN="xoxb-your-token-here"
export SLACK_TEST_CHANNEL="#recon-bot-testing"

# Run test
python daily_recon_slack_bot.py
```

Expected output:
```
✅ Slack Bot Connected!
   Bot Name: daily-reconciliation-bot
   Team: Gusto
📤 Sending test message...
✅ Message sent successfully to #recon-bot-testing
```

---

## Step 7: Integrate with ML Model

File: `daily_recon_automation.py`

```python
import pandas as pd
from datetime import datetime
from predict_with_rules import predict_transactions
from slack_daily_message_template import generate_daily_recon_message
from daily_recon_slack_bot import send_daily_message

def run_daily_reconciliation():
    """
    Complete daily reconciliation workflow:
    1. Load today's transactions
    2. Predict agents
    3. Count agent occurrences
    4. Identify high-value ICP transactions
    5. Send Slack message
    """
    print("🚀 Starting daily reconciliation...")
    
    # 1. Load today's transactions (from your data source)
    today_transactions = load_todays_transactions()
    print(f"   Loaded {len(today_transactions)} transactions")
    
    # 2. Predict agents using your model
    predictions = predict_transactions(today_transactions)
    print(f"   Predicted agents for all transactions")
    
    # 3. Count agent occurrences
    agent_counts = predictions['agent'].value_counts().to_dict()
    print(f"   Found {len(agent_counts)} different agents")
    
    # 4. Identify high-value ICP transactions
    high_value_icp = []
    icp_agents = ['Nium Payment', 'ICP Return', 'ICP Refund', 'ICP Funding']
    
    for idx, row in predictions.iterrows():
        if row['agent'] in icp_agents and row['amount'] >= 300000:
            # Check for DLOCAL, WISE, NIUM in description
            desc = str(row['description']).upper()
            if any(kw in desc for kw in ['DLOCAL', 'WISE', 'NIUM']):
                high_value_icp.append({
                    'id': row['id'],
                    'agent': row['agent'],
                    'amount': row['amount'],
                    'description': row['description']
                })
    
    print(f"   Found {len(high_value_icp)} high-value ICP alerts")
    
    # 5. Send Slack message
    print("\n📤 Sending Slack message...")
    send_daily_message(
        agent_counts=agent_counts,
        high_value_icp=high_value_icp,
        channel="#platform-operations"
    )
    
    print("✅ Daily reconciliation complete!")

if __name__ == "__main__":
    run_daily_reconciliation()
```

---

## Step 8: Schedule Daily Automation

### Option A: Cron Job (Linux/Mac)

```bash
# Edit crontab
crontab -e

# Add line to run every weekday at 9 AM
0 9 * * 1-5 cd /path/to/SOPSlack && /usr/bin/python3 daily_recon_automation.py
```

### Option B: Task Scheduler (Windows)

1. Open Task Scheduler
2. Create Basic Task
3. Trigger: Daily at 9:00 AM
4. Action: Start a program
5. Program: `python`
6. Arguments: `daily_recon_automation.py`
7. Start in: `C:\path\to\SOPSlack`

### Option C: Cloud Scheduler (Production)

Use AWS Lambda, Google Cloud Functions, or Azure Functions to run on schedule.

---

## Step 9: Invite Bot to Channel

1. Go to `#platform-operations` in Slack
2. Type: `/invite @Daily Reconciliation Bot`
3. Bot will now be able to post messages!

---

## Testing Checklist

- [ ] Slack app created
- [ ] Bot token obtained
- [ ] Environment variables set
- [ ] Dependencies installed
- [ ] Connection test passed
- [ ] Test message sent successfully
- [ ] Bot invited to production channel
- [ ] Daily automation scheduled

---

## Troubleshooting

### "not_in_channel" error
**Solution:** Invite bot to channel: `/invite @Daily Reconciliation Bot`

### "invalid_auth" error
**Solution:** Check your `SLACK_BOT_TOKEN` is correct

### Markdown not rendering
**Solution:** Ensure `mrkdwn=True` in `chat_postMessage()`

### Links not clickable
**Solution:** Use Slack format: `<URL|Text>` (we already do this!)

---

## Security Best Practices

1. ✅ Never commit `.env` file
2. ✅ Use environment variables for tokens
3. ✅ Rotate tokens periodically
4. ✅ Limit bot permissions to minimum needed
5. ✅ Use separate tokens for dev/prod

---

## Next Steps

1. Test in `#recon-bot-testing` channel first
2. Get feedback from team
3. Deploy to production `#platform-operations`
4. Monitor for first week
5. Iterate based on feedback

---

**Questions?** Check Slack API docs: https://api.slack.com/

**Repository:** https://github.com/yarkn24/SOPSlack

