#!/usr/bin/env python3
"""
Show Example Descriptions for Worst Performing Agents
======================================================
"""

import pandas as pd

# Load data
df = pd.read_csv('/Users/yarkin.akcil/Downloads/Unrecon_2025_10_05_updated.csv', low_memory=False)
df['amount'] = df['amount'] / 100
df['date'] = pd.to_datetime(df['date'], format='mixed')
df = df[df['date'] >= '2024-10-01'].copy()  # Validation set

# Top problem agents
problem_agents = [
    'ACH Transaction',
    'Company Balance Transfers',
    'MT UI',
    'OH SDWH',
    'ICP Return',
    'Canary Payments',
    'York Adams',
    'LOI',
    'Treasury Transfer'
]

print("=" * 120)
print("EXAMPLE DESCRIPTIONS FOR WORST PERFORMING AGENTS")
print("=" * 120)
print()

for agent in problem_agents:
    agent_data = df[df['agent'] == agent]
    
    if len(agent_data) == 0:
        continue
    
    print("=" * 120)
    print(f"AGENT: {agent} ({len(agent_data)} transactions)")
    print("=" * 120)
    print()
    
    # Get 5 unique descriptions
    unique_descriptions = agent_data['description'].unique()[:5]
    
    for i, desc in enumerate(unique_descriptions, 1):
        # Find a row with this description
        row = agent_data[agent_data['description'] == desc].iloc[0]
        
        print(f"Example {i}:")
        print(f"  ID: {row['id']}")
        print(f"  Amount: ${row['amount']:,.2f}")
        print(f"  Payment Method: {row['payment_method']}")
        print(f"  Account: {row['origination_account_id']}")
        print(f"  Description: {desc[:200]}")
        if len(desc) > 200:
            print(f"               ...{desc[-100:]}")
        print()
    
    print()

