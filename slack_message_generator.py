#!/usr/bin/env python3
"""
Slack Message Generator
=======================
Generates formatted Slack messages from labeled transactions.
"""

import pandas as pd
import random
from datetime import datetime

# Fun facts database
FUN_FACTS = [
    ":moneybag: Financial Innovation: The concept of paper money was first used in China during the Tang Dynasty (618-907 AD). Europe didn't adopt it until the 17th century! :scroll:",
    ":bank: Did you know? The first bank in the United States was the Bank of North America, established in 1781 in Philadelphia! :classical_building:",
    ":credit_card: Credit Card History: The first credit card was introduced by Diners Club in 1950. It was initially meant for restaurant dining! :fork_and_knife:",
    ":chart_with_upwards_trend: Stock Market: The New York Stock Exchange was founded in 1792 under a buttonwood tree on Wall Street! :deciduous_tree:",
    ":coin: Ancient Currency: The first coins were minted in Lydia (modern Turkey) around 600 BC, made from electrum (gold-silver alloy)! :sparkles:",
    ":dollar: Fun Fact: The dollar sign ($) is believed to have evolved from the Spanish peso symbol! :es:",
    ":atm: ATM Innovation: The first ATM was installed in London in 1967. The inventor received a gold bar for his idea! :medal:",
    ":money_with_wings: Paper Bills: U.S. paper currency is actually made of 75% cotton and 25% linen, not paper! :yarn:",
]


def generate_slack_message(df, high_value_threshold=300000):
    """
    Generate formatted Slack message from labeled transactions.
    
    Args:
        df: DataFrame with columns: id, predicted_agent, amount, description, sop_links
        high_value_threshold: Threshold for high-value alerts (default: $300K)
    
    Returns:
        Formatted Slack message string
    """
    
    # Get current day
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    today = days[datetime.now().weekday()]
    
    # Header
    message = f":dart: Hey Platform Operations! Happy {today}! :coffee:\n"
    message += "Our AI has identified today's transactions as:\n"
    
    # Count by agent
    agent_counts = df['predicted_agent'].value_counts()
    
    # Add each agent with special markers
    for agent, count in agent_counts.items():
        message += f"• {agent}: {count} transactions"
        
        # Add warnings for specific cases
        if count > 100:
            message += " :rotating_light: Be careful for this agent - something looks broken!"
        elif count > 50:
            message += " :warning: Hmm there are many of those. Please ping leads if you need any help."
        
        message += "\n"
    
    # High-value ICP alerts
    high_value = df[df['amount'] >= high_value_threshold].copy()
    
    if len(high_value) > 0:
        message += "---\n"
        message += ":red_circle: High-Value ICP Alert:\n"
        
        for idx, row in high_value.iterrows():
            message += f"• Transaction ID: {row['id']}\n"
            message += f"  Agent: {row['predicted_agent']}\n"
            message += f"  Amount: ${row['amount']:,.2f}\n"
            desc = row['description'][:80] + "..." if len(row['description']) > 80 else row['description']
            message += f"  Description: {desc}\n"
            message += f"  :warning: This can indicate there is a batch remained unreconciled.\n"
    
    # SOP Links
    message += "---\n"
    message += ":books: Here are the suggested SOPs for those:\n"
    
    # Collect unique SOP links
    unique_sops = set()
    for sop_links in df['sop_links']:
        if pd.notna(sop_links) and 'No SOP' not in str(sop_links):
            for link in str(sop_links).split(' | '):
                unique_sops.add(link.strip())
    
    # Add standard SOPs
    standard_sops = [
        ("Daily Operations: How to Label & Reconcile", 
         "https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/535003232"),
        ("Daily Bank Transaction Reconciliation by Bank Transaction Type",
         "https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/169411126"),
        ("Letter of Indemnity Process and Reconciliation",
         "https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/298583554"),
        ("Escalating Reconciliation Issues to Cross-Functional Stakeholders",
         "https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/460194134"),
    ]
    
    for i, (title, link) in enumerate(standard_sops, 1):
        message += f"{i}. {title}\n   {link}\n"
    
    # Fun fact
    message += "---\n"
    message += random.choice(FUN_FACTS) + "\n"
    
    # Footer
    message += "Good luck with today's reconciliation! :rocket:\n"
    
    return message


def save_slack_message(df, output_file=None, high_value_threshold=300000):
    """
    Generate and save Slack message to file.
    
    Args:
        df: DataFrame with labeled transactions
        output_file: Output file path (default: ~/Downloads/slack_message_[timestamp].txt)
        high_value_threshold: Threshold for high-value alerts
    
    Returns:
        Path to saved file
    """
    import os
    
    message = generate_slack_message(df, high_value_threshold)
    
    if output_file is None:
        output_file = f"{os.path.expanduser('~')}/Downloads/slack_message_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    
    with open(output_file, 'w') as f:
        f.write(message)
    
    return output_file


if __name__ == "__main__":
    print("Slack Message Generator")
    print("=" * 80)
    print("\nThis module generates formatted Slack messages from labeled transactions.")
    print("\nUsage:")
    print("  from slack_message_generator import generate_slack_message")
    print("  message = generate_slack_message(df)")
    print("  print(message)")

