#!/usr/bin/env python3
"""
CODE7 Test - Static CSV ile Slack Message Oluştur
===================================================
"""

import pandas as pd
from slack_message_generator import generate_slack_message

# Static CSV oku
csv_file = "/Users/yarkin.akcil/Desktop/cursor_data/redash_agents_20251008_091835.csv"
df = pd.read_csv(csv_file)

print(f"📊 Loaded {len(df)} transactions from static file\n")

# Slack message oluştur
print("📱 Generating Slack message...\n")
slack_message = generate_slack_message(df)

print("="*80)
print("SLACK MESSAGE PREVIEW")
print("="*80)
print(slack_message)
print("="*80)

# Dosyaya kaydet
output_file = f"/Users/yarkin.akcil/Desktop/cursor_data/slack_message_test_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.txt"
with open(output_file, 'w') as f:
    f.write(slack_message)

print(f"\n✅ Saved to: {output_file}")




