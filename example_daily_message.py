"""
Example Daily Message - Realistic Scenario
===========================================
Shows what the actual Slack message looks like
"""

from slack_daily_message_template import generate_daily_recon_message

# Realistic scenario: Top 5 most frequent agents today
agent_counts = {
    'ACH': 85,              # Critical: 50+ transactions
    'Check': 47,            # Warning: 40+ transactions
    'Risk': 32,             # Normal
    'Treasury Transfer': 18, # Normal
    'NY WH': 12,            # Normal
}

# High-value ICP transactions that need attention
high_value_icp = [
    {
        'id': '58947891',
        'agent': 'Nium Payment',
        'amount': 487500.00,
        'description': 'ORIG CO NAME=NIUM INC,ORIG ID=0514672353,DESC DATE=251007,ENTRY DESCR=FW01876519',
    },
]

# Generate the message
print("=" * 80)
print("TODAY'S DAILY RECONCILIATION MESSAGE")
print("=" * 80)
print()
print(generate_daily_recon_message(agent_counts, high_value_icp))

