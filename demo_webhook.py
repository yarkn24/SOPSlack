"""
Demo Webhook for Manager Meeting
==================================
Quick demo using Incoming Webhook (no OAuth needed!)

Usage:
    export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/..."
    python demo_webhook.py
"""

import requests
import os
from datetime import datetime
from slack_daily_message_template import generate_daily_recon_message

# Example data for demo
demo_agent_counts = {
    'ACH': 85,
    'Check': 47,
    'Risk': 32,
    'Treasury Transfer': 18,
    'NY WH': 12,
    'LOI': 8,
    'Recovery Wire': 15,
    'Nium Payment': 6,
}

demo_high_value_icp = [
    {
        'id': '58947234',
        'agent': 'Nium Payment',
        'amount': 487500,
        'description': 'ORIG CO NAME=NIUM INC...',
    },
]

# Generate message
message = generate_daily_recon_message(
    agent_counts=demo_agent_counts,
    high_value_icp_transactions=demo_high_value_icp,
    date=datetime.now()
)

# Add demo header
demo_message = f"""
🎯 **DEMO - Daily Reconciliation Bot**
_This is a live demonstration of our automated reconciliation system_

---

{message}

---

💡 **Demo Info:**
• ML Model: 98.64% accuracy (XGBoost)
• Prediction speed: <1 second per transaction
• Data source: Redash API (auto-refresh)
• Agent-SOP mapping: 21 agents covered
"""

# Send to Slack
webhook_url = os.environ.get('SLACK_WEBHOOK_URL')

if not webhook_url:
    print("❌ SLACK_WEBHOOK_URL not set!")
    print("\nSet it like this:")
    print('export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/YOUR/WEBHOOK/URL"')
    exit(1)

print("📤 Sending demo message to Slack...")
print(f"   Webhook: {webhook_url[:50]}...")

response = requests.post(
    webhook_url,
    json={'text': demo_message}
)

if response.status_code == 200:
    print("✅ Demo message sent successfully!")
    print("\n🎉 Check your Slack channel!")
else:
    print(f"❌ Error: {response.status_code}")
    print(f"   Response: {response.text}")

