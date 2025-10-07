"""
Slack Daily Reconciliation Message Template
============================================
Generates daily message for Platform Operations team
Based on predicted agents and their counts.

Author: Yarkin Akcil
Date: October 7, 2025
"""

from datetime import datetime
from agent_sop_mapping import AGENT_SOP_MAPPING


def is_us_banking_holiday(date=None):
    """
    Check if a given date is a US banking holiday.
    
    Args:
        date: datetime object (default: today)
    
    Returns:
        Tuple: (is_holiday, holiday_name)
    """
    if date is None:
        date = datetime.now()
    
    month = date.month
    day = date.day
    weekday = date.weekday()  # Monday=0, Sunday=6
    
    # Fixed date holidays
    fixed_holidays = {
        (1, 1): "New Year's Day",
        (7, 4): "Independence Day",
        (11, 11): "Veterans Day",
        (12, 25): "Christmas Day",
    }
    
    if (month, day) in fixed_holidays:
        return True, fixed_holidays[(month, day)]
    
    # Floating holidays (calculated)
    # Martin Luther King Jr. Day: 3rd Monday of January
    if month == 1 and weekday == 0:
        if 15 <= day <= 21:
            return True, "Martin Luther King Jr. Day"
    
    # Presidents' Day: 3rd Monday of February
    if month == 2 and weekday == 0:
        if 15 <= day <= 21:
            return True, "Presidents' Day"
    
    # Memorial Day: Last Monday of May
    if month == 5 and weekday == 0:
        if day >= 25:
            return True, "Memorial Day"
    
    # Labor Day: 1st Monday of September
    if month == 9 and weekday == 0:
        if day <= 7:
            return True, "Labor Day"
    
    # Columbus Day: 2nd Monday of October
    if month == 10 and weekday == 0:
        if 8 <= day <= 14:
            return True, "Columbus Day"
    
    # Thanksgiving: 4th Thursday of November
    if month == 11 and weekday == 3:  # Thursday
        if 22 <= day <= 28:
            return True, "Thanksgiving"
    
    return False, None


def get_daily_greeting(date=None):
    """
    Get personalized greeting based on day of week and holidays.
    
    Args:
        date: datetime object (default: today)
    
    Returns:
        String with greeting
    """
    if date is None:
        date = datetime.now()
    
    # Check for US banking holiday
    is_holiday, holiday_name = is_us_banking_holiday(date)
    
    if is_holiday:
        return f"🎉 Happy {holiday_name}! 🎉"
    
    # Regular day greetings
    day_names = [
        "Monday", "Tuesday", "Wednesday", "Thursday", 
        "Friday", "Saturday", "Sunday"
    ]
    
    day_name = day_names[date.weekday()]
    
    # Special messages for each day
    day_messages = {
        "Monday": "Happy Monday! ☕",
        "Tuesday": "Happy Tuesday! 💪",
        "Wednesday": "Happy Wednesday! 🐪",  # Hump day
        "Thursday": "Happy Thursday! 🎯",
        "Friday": "Happy Friday! 🎊",
        "Saturday": "Happy Saturday! 🌞",
        "Sunday": "Happy Sunday! 🌅",
    }
    
    return day_messages.get(day_name, f"Happy {day_name}!")


def generate_daily_recon_message(agent_counts, high_value_icp_transactions=None, date=None):
    """
    Generate daily reconciliation message for Slack.
    
    Args:
        agent_counts: Dictionary with agent names as keys and counts as values
                     Example: {'Risk': 15, 'LOI': 3, 'NY WH': 42, 'ACH': 150}
        high_value_icp_transactions: List of dicts with high-value ICP details
                     Example: [{'agent': 'Nium Payment', 'amount': 450000, 
                               'description': 'DLOCAL PAYMENT', 'id': '12345'}]
        date: datetime object (default: today)
    
    Returns:
        String with formatted Slack message
    """
    
    if date is None:
        date = datetime.now()
    
    # Get personalized greeting
    greeting = get_daily_greeting(date)
    
    message = f"🎯 **Hey Platform Operations! {greeting}**\n\n"
    message += "Our AI has identified today's transactions as:\n\n"
    
    # Sort agents by count (descending)
    sorted_agents = sorted(agent_counts.items(), key=lambda x: x[1], reverse=True)
    
    # Collect all unique SOPs
    all_sops = set()
    
    # List each agent with counts and warnings
    for agent_name, count in sorted_agents:
        message += f"• **{agent_name}**: {count} transaction{'s' if count != 1 else ''}"
        
        # Warning for 40+ transactions
        if count >= 40 and count < 50:
            message += " ⚠️ _Hmm there are many of those. Please ping leads if you need any help._"
        
        # Critical warning for 50+ transactions
        elif count >= 50:
            message += " 🚨 **Be careful for this agent - something looks broken!**"
        
        message += "\n"
        
        # Collect SOPs for this agent
        agent_info = AGENT_SOP_MAPPING.get(agent_name)
        if agent_info:
            confluence_links = agent_info.get('confluence_links', [])
            for link in confluence_links:
                all_sops.add(link)
    
    message += "\n"
    
    # Special warning for high-value ICP transactions
    if high_value_icp_transactions:
        message += "---\n\n"
        message += "🔴 **High-Value ICP Alert:**\n\n"
        
        for txn in high_value_icp_transactions:
            agent = txn.get('agent', 'Unknown')
            amount = txn.get('amount', 0)
            description = txn.get('description', '')
            txn_id = txn.get('id', 'N/A')
            
            # Check if it's ICP-related (but not ICP Funding or Treasury Transfer)
            is_icp_related = any(keyword in description.upper() for keyword in ['DLOCAL', 'WISE', 'NIUM'])
            is_not_funding = agent not in ['ICP Funding', 'Treasury Transfer']
            is_high_value = amount >= 300000
            
            if is_icp_related and is_not_funding and is_high_value:
                message += f"• **Transaction ID:** {txn_id}\n"
                message += f"  **Agent:** {agent}\n"
                message += f"  **Amount:** ${amount:,.2f}\n"
                message += f"  **Description:** {description[:100]}...\n"
                message += f"  ⚠️ _This can indicate there is a batch remained unreconciled._\n\n"
    
    # Add suggested SOPs section
    message += "---\n\n"
    message += "📚 **Here are the suggested SOPs for those:**\n\n"
    
    # Always add Daily Operations first (Slack hyperlink format: <URL|Text>)
    message += "1. <https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/535003232/Daily+Operations+How+to+Label+Reconcile|Daily Operations: How to Label & Reconcile>\n"
    
    # Add all unique SOPs collected from agents
    counter = 2
    sop_titles = {
        '460194134': 'Escalating Reconciliation Issues to Cross-Functional Stakeholders',
        '169411126': 'Daily Bank Transaction Reconciliation by Bank Transaction Type',
        '298583554': 'Letter of Indemnity Process and Reconciliation',
    }
    
    # Add unique SOPs (excluding Daily Operations which we already added)
    for sop_link in sorted(all_sops):
        if '535003232' in sop_link:  # Skip Daily Operations (already added)
            continue
        
        # Get title
        title = None
        for page_id, page_title in sop_titles.items():
            if page_id in sop_link:
                title = page_title
                break
        
        if not title:
            title = "SOP Document"
        
        message += f"{counter}. <{sop_link}|{title}>\n"
        counter += 1
    
    # Always add Daily Bank Transaction Reconciliation at the end if not already present
    daily_recon_link = "https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/169411126/Daily+Bank+Transaction+Reconciliation+by+Bank+Transaction+Type"
    if daily_recon_link not in all_sops:
        message += f"{counter}. <{daily_recon_link}|Daily Bank Transaction Reconciliation by Bank Transaction Type>\n"
    
    message += "\n_Good luck with today's reconciliation! 🚀_"
    
    return message


# Example usage
if __name__ == "__main__":
    # Example data
    example_counts = {
        'Risk': 15,
        'LOI': 3,
        'NY WH': 42,
        'ACH': 150,
        'Treasury Transfer': 25,
        'Check': 8,
    }
    
    example_high_value_icp = [
        {
            'id': '58947234',
            'agent': 'Nium Payment',
            'amount': 450000,
            'description': 'ORIG CO NAME=NIUM INC,ORIG ID=0514672353,DESC DATE=251002',
        },
        {
            'id': '58947890',
            'agent': 'ICP Return',
            'amount': 380000,
            'description': 'WISE PAYMENTS LIMITED - TS FX ACCOUNTS RECEIVABLE',
        },
    ]
    
    print("=" * 80)
    print("EXAMPLE SLACK MESSAGE")
    print("=" * 80)
    print()
    print(generate_daily_recon_message(example_counts, example_high_value_icp))

