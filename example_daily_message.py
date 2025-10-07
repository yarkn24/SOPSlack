"""
Example Daily Message - Realistic Scenario
===========================================
Shows what the actual Slack message looks like
"""

from datetime import datetime
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

# Example 1: Regular Monday
print("=" * 80)
print("EXAMPLE 1: REGULAR MONDAY")
print("=" * 80)
print()
monday = datetime(2025, 10, 6)  # Monday
print(generate_daily_recon_message(agent_counts, high_value_icp, date=monday))

print("\n\n")

# Example 2: Friday
print("=" * 80)
print("EXAMPLE 2: FRIDAY")
print("=" * 80)
print()
friday = datetime(2025, 10, 10)  # Friday
print(generate_daily_recon_message(agent_counts, high_value_icp, date=friday))

print("\n\n")

# Example 3: Independence Day (July 4th)
print("=" * 80)
print("EXAMPLE 3: INDEPENDENCE DAY (US BANKING HOLIDAY)")
print("=" * 80)
print()
independence_day = datetime(2025, 7, 4)  # July 4th
print(generate_daily_recon_message(agent_counts, high_value_icp, date=independence_day))

print("\n\n")

# Example 4: Day before Independence Day (July 3rd)
print("=" * 80)
print("EXAMPLE 4: DAY BEFORE INDEPENDENCE DAY (JULY 3RD)")
print("=" * 80)
print()
july_3rd = datetime(2025, 7, 3)  # Day before July 4th
print(generate_daily_recon_message(agent_counts, high_value_icp, date=july_3rd))

print("\n\n")

# Example 5: Day before Thanksgiving
print("=" * 80)
print("EXAMPLE 5: DAY BEFORE THANKSGIVING")
print("=" * 80)
print()
day_before_thanksgiving = datetime(2025, 11, 26)  # Nov 26 (Thanksgiving is Nov 27, 2025)
print(generate_daily_recon_message(agent_counts, high_value_icp, date=day_before_thanksgiving))

print("\n\n")

# Example 6: Today (actual date)
print("=" * 80)
print("EXAMPLE 6: TODAY (ACTUAL DATE)")
print("=" * 80)
print()
print(generate_daily_recon_message(agent_counts, high_value_icp))

