"""
Full Example Daily Message
===========================
Shows a complete, realistic daily reconciliation message
"""

from datetime import datetime
from slack_daily_message_template import generate_daily_recon_message

# Realistic scenario: Busy day with various agents
agent_counts = {
    'ACH': 127,              # Critical: 50+ transactions - Something broken!
    'Check': 48,             # Warning: 40+ transactions - Need help
    'Risk': 35,              # Normal - high volume
    'Treasury Transfer': 28, # Normal
    'NY WH': 18,             # Normal
    'ICP Funding': 12,       # Normal
    'Recovery Wire': 8,      # Normal
    'LOI': 5,                # Normal
    'ZBT': 4,                # Normal
    'Nium Payment': 2,       # Normal
}

# High-value ICP transactions that need attention
high_value_icp = [
    {
        'id': '58947891',
        'agent': 'Nium Payment',
        'amount': 487500.00,
        'description': 'ORIG CO NAME=NIUM INC,ORIG ID=0514672353,DESC DATE=251007,ENTRY DESCR=FW01876519,ENTRY CLASS=CCD',
    },
    {
        'id': '58948123',
        'agent': 'ICP Return',
        'amount': 325000.00,
        'description': 'WISE PAYMENTS LIMITED - TS FX ACCOUNTS RECEIVABLE - JPV240815',
    },
]

# Generate for a Thursday
print("=" * 80)
print("FULL EXAMPLE: BUSY THURSDAY WITH HOLIDAY WARNING")
print("=" * 80)
print()

# July 3rd, 2025 (Thursday before Independence Day)
july_3rd = datetime(2025, 7, 3)
message = generate_daily_recon_message(agent_counts, high_value_icp, date=july_3rd)

print(message)
print()
print("=" * 80)
print(f"Message length: {len(message)} characters")
print(f"Number of agents: {len(agent_counts)}")
print(f"Number of high-value alerts: {len(high_value_icp)}")
print("=" * 80)

