#!/usr/bin/env python3
"""
Slack Message Generator
=======================
Generates formatted Slack messages from labeled transactions.
"""

import pandas as pd
import random
import json
import os
from datetime import datetime

# VARIED FUN FACTS - 50% Finance, 50% Everything Else!
FUN_FACTS = [
    # Finance & Banking (50%)
    ":moneybag: The concept of paper money was first used in China during the Tang Dynasty (618-907 AD)! :scroll:",
    ":dollar: Roman soldiers were paid in salt - that's where the word 'salary' comes from! :salt:",
    ":atm: The first ATM was installed in London in 1967. The inventor got a gold bar as reward! :medal:",
    ":credit_card: The first credit card (Diners Club, 1950) was meant only for restaurants! :fork_and_knife:",
    ":chart_with_upwards_trend: The NYSE was founded in 1792 under a buttonwood tree on Wall Street! :deciduous_tree:",
    ":bank: The first U.S. bank opened in Philadelphia in 1781 - Bank of North America! :classical_building:",
    ":coin: The first coins (600 BC) were made in Turkey from electrum (gold-silver mix)! :sparkles:",
    ":money_with_wings: U.S. paper money is 75% cotton, 25% linen - not actually paper! :yarn:",
    ":heavy_dollar_sign: Hungary had inflation so bad in 1946 that prices doubled every 15 hours! :chart_with_downwards_trend:",
    ":scales: Double-entry bookkeeping was invented in 1494 by Italian mathematician Luca Pacioli! :it:",
    ":receipt: The first paper check was used in ancient Persia around 321 BC! :writing_hand:",
    ":briefcase: The first stock exchange opened in Amsterdam in 1602 for Dutch East India Company! :netherlands:",
    ":closed_lock_with_key: Swiss banking secrecy laws started in 1713! :switzerland:",
    ":revolving_hearts: Bitcoin's creator, Satoshi Nakamoto, identity remains unknown! :detective:",
    ":classical_building: The Fed was created after a secret 1913 meeting on Jekyll Island! :island:",
    
    # Science & Discovery (20%)
    ":telescope: Galileo discovered Jupiter's 4 largest moons in 1610! Changed everything! :milky_way:",
    ":atom_symbol: John Dalton discovered the atom in 1808, but we didn't see one until 1981! :microscope:",
    ":apple: Newton's apple incident (1666) led to the theory of gravity! :green_apple:",
    ":dna: DNA's double helix was discovered in 1953 by Watson & Crick! :test_tube:",
    ":bulb: Edison tested 3,000+ designs before perfecting the light bulb! :zap:",
    ":scroll: Archimedes shouted 'Eureka!' discovering water displacement in his bath! :bathtub:",
    
    # History & Philosophy (15%)
    ":classical_building: Aristotle tutored Alexander the Great and founded the first university! :books:",
    ":pyramid: The Great Pyramid was Earth's tallest structure for 3,800 years! :egypt:",
    ":books: Alexandria's Library held 700,000 scrolls before burning! :fire:",
    ":boat: Cleopatra lived closer to Moon landing than to Great Pyramid construction! :calendar:",
    ":musical_note: The shortest war (Anglo-Zanzibar, 1896) lasted 38-45 minutes! :hourglass:",
    
    # Space (10%)
    ":rocket: Voyager 1 (launched 1977) is 15 billion miles away and still transmitting! :satellite:",
    ":moon: 600 million people watched Neil Armstrong's first Moon steps! :tv:",
    ":ringed_planet: Saturn's rings are billions of ice chunks, some tiny as sand! :snowflake:",
    ":clock3: A day on Venus (243 Earth days) is longer than its year! :dizzy_face:",
    
    # Nature & Random (5%)
    ":honey_pot: Honey never spoils! 3,000-year-old honey from Egypt was still edible! :bee:",
    ":octopus: Octopuses have 3 hearts and blue blood! :ocean:",
    ":earth_americas: More trees on Earth than stars in Milky Way! (3T vs 400B) :evergreen_tree:",
    ":rainbow: Rainbows are full circles - we just see arcs from ground! :sunny:",
    ":coffee: Coffee was discovered by a shepherd whose goats ate berries and got energetic! :goat:",
    ":computer: The first computer bug was an actual moth found in 1947! :bug:",
]

# Greeting variations - Dynamic & Creative!
GREETINGS = [
    "Hey Platform Operations! Happy {day}! :coffee:",
    "Good morning Platform Ops! Happy {day}! :sunrise:",
    "Hello team! Happy {day}! :wave:",
    "Yo Platform Operations! Happy {day}! :fire:",
    "Hey folks! Happy {day}! :rocket:",
    "Morning Platform Ops! Happy {day}! :sunny:",
    "Greetings Platform Ops! Hope your {day} is going great! :star2:",
    "What's up team! Happy {day}! :sunglasses:",
    "Hey everyone! Happy {day}! Let's do this! :muscle:",
    "Good vibes Platform Ops! Happy {day}! :sparkles:",
]

# Banking Holidays (US Federal Holidays when banks are closed)
BANKING_HOLIDAYS = {
    # Fixed dates
    (1, 1): {
        "name": "New Year's Day",
        "message": "Happy New Year's Day! :tada: Today is a banking holiday - banks are closed! :bank:",
        "fact": "New Year's Day has been a federal banking holiday since 1870. Banks close to give employees time to celebrate and recover from New Year's Eve festivities. Fun fact: The first organized New Year's celebration dates back 4,000 years to ancient Babylon!"
    },
    (7, 4): {
        "name": "Independence Day",
        "message": "Happy Independence Day! :flag-us::fireworks: Today is a banking holiday - banks are closed! :bank:",
        "fact": "Independence Day celebrates the signing of the Declaration of Independence on July 4, 1776. Banks have been closed on this day since it became a federal holiday in 1870. Over 150 million hot dogs are consumed on this day!"
    },
    (11, 11): {
        "name": "Veterans Day",
        "message": "Happy Veterans Day! :military_medal: Today is a banking holiday - banks are closed to honor our veterans! :bank:",
        "fact": "Veterans Day honors all military veterans who served in the US Armed Forces. Originally called Armistice Day, it marks the end of WWI on November 11, 1918, at 11 AM. Banks close to honor those who served!"
    },
    (12, 25): {
        "name": "Christmas Day",
        "message": "Merry Christmas! :christmas_tree::gift: Today is a banking holiday - banks are closed! :bank:",
        "fact": "Christmas has been a federal banking holiday since 1870. Banks close nationwide, making it one of the few days with zero banking transactions. Fun fact: The tradition of Christmas trees started in Germany in the 16th century!"
    },
    
    # Variable dates (approximate - these need calendar checking)
    (1, 20): {
        "name": "Martin Luther King Jr. Day",
        "message": "Happy MLK Day! :fist: Today is a banking holiday - banks are closed to honor Dr. King! :bank:",
        "fact": "MLK Day honors civil rights leader Dr. Martin Luther King Jr. It became a federal banking holiday in 1986, making it the newest banking holiday. It's observed on the third Monday in January, near Dr. King's birthday (January 15)!"
    },
    (2, 17): {
        "name": "Presidents' Day",
        "message": "Happy Presidents' Day! :flag-us: Today is a banking holiday - banks are closed! :bank:",
        "fact": "Presidents' Day honors George Washington (Feb 22) and Abraham Lincoln (Feb 12). Celebrated on the third Monday in February, banks close nationwide. Fun fact: Washington's birthday was the first individual's birthday to become a federal holiday!"
    },
    (5, 26): {
        "name": "Memorial Day", 
        "message": "Happy Memorial Day! :flag-us: Today is a banking holiday - banks are closed to honor the fallen! :bank:",
        "fact": "Memorial Day honors those who died serving in the US military. Originally called Decoration Day after the Civil War, it became a federal banking holiday in 1971. Always observed on the last Monday in May!"
    },
    (6, 19): {
        "name": "Juneteenth",
        "message": "Happy Juneteenth! :star: Today is a banking holiday - banks are closed! :bank:",
        "fact": "Juneteenth commemorates the end of slavery in the US on June 19, 1865. It became a federal banking holiday in 2021, making it the newest addition! Banks across America close to honor this important day in US history!"
    },
    (9, 1): {
        "name": "Labor Day",
        "message": "Happy Labor Day! :hammer_and_wrench: Today is a banking holiday - banks are closed! :bank:",
        "fact": "Labor Day honors American workers and their contributions. Banks close on the first Monday in September. Fun fact: The first Labor Day was celebrated in 1882, and it became a federal banking holiday in 1894!"
    },
    (10, 13): {
        "name": "Columbus Day",
        "message": "Happy Columbus Day! :boat: Today is a banking holiday - banks are closed! :bank:",
        "fact": "Columbus Day commemorates Christopher Columbus's arrival in the Americas in 1492. Banks close on the second Monday in October. Note: Many states now observe Indigenous Peoples' Day instead!"
    },
    (11, 27): {
        "name": "Thanksgiving",
        "message": "Happy Thanksgiving! :turkey: Today is a banking holiday - banks are closed! :bank:",
        "fact": "Thanksgiving became a federal banking holiday in 1870. Celebrated on the fourth Thursday in November, it's one of the busiest travel days. Banks close so employees can enjoy turkey and family time!"
    },
}


def get_banking_holiday_message():
    """Check if today is a banking holiday and return special message"""
    today = datetime.now()
    month = today.month
    day = today.day
    
    holiday = BANKING_HOLIDAYS.get((month, day))
    if holiday:
        return holiday["message"]
    return None


def get_special_day_message():
    """Get special message if today is a notable day (non-banking holidays)"""
    today = datetime.now()
    month = today.month
    day = today.day
    
    # Fun Days (non-banking holidays)
    special_days = {
        (2, 14): "Happy Valentine's Day! :heart: We love good recons!",
        (3, 14): "Happy Pi Day! :pie: 3.14159... transactions to reconcile!",
        (3, 17): "Happy St. Patrick's Day! :four_leaf_clover: Luck of the Irish for today's recons!",
        (4, 1): "Happy April Fools! :clown_face: But these transactions are 100% real!",
        (4, 22): "Happy Earth Day! :earth_americas: Sustainable reconciliation practices!",
        (5, 4): "May the Fourth be with you! :jedi: Strong recon skills you have!",
        (10, 3): "Happy Mean Girls Day! :pink_heart: On Wednesdays we wear pink and reconcile!",
        (10, 31): "Happy Halloween! :jack_o_lantern: These transactions aren't scary... or are they?",
        (12, 31): "Happy New Year's Eve! :champagne: Finishing the year strong!",
    }
    
    return special_days.get((month, day), None)


def get_tomorrow_holiday_reminder():
    """Get reminder about tomorrow's holiday (1 day before)"""
    today = datetime.now()
    # Check tomorrow
    from datetime import timedelta
    tomorrow = today + timedelta(days=1)
    month = tomorrow.month
    day = tomorrow.day
    
    # Check if tomorrow is a BANKING HOLIDAY first (priority!)
    banking_holiday = BANKING_HOLIDAYS.get((month, day))
    if banking_holiday:
        return f":bank::calendar: Tomorrow is {banking_holiday['name']} - a banking holiday! " + banking_holiday['fact']
    
    # Non-banking holidays (fun days)
    fun_holidays = {
        (2, 14): ":calendar: Tomorrow is Valentine's Day! A day to celebrate love and appreciation for the people we care about. Fun fact: Americans spend over $20 billion on Valentine's Day!",
        (3, 14): ":calendar: Tomorrow is Pi Day! Mathematicians celebrate π (3.14159...) on March 14 (3/14). Fun fact: It's also Albert Einstein's birthday!",
        (3, 17): ":calendar: Tomorrow is St. Patrick's Day! Originally celebrating Ireland's patron saint, it's now a global celebration of Irish culture. Fun fact: Chicago dyes its river green!",
        (4, 1): ":calendar: Tomorrow is April Fools' Day! A day of pranks and jokes celebrated in many countries. The origin is unclear, but it's been around since the 1500s!",
        (4, 22): ":calendar: Tomorrow is Earth Day! Founded in 1970, it's now a global movement to support environmental protection. Over 1 billion people participate worldwide!",
        (5, 4): ":calendar: Tomorrow is May 4th! Star Wars fans celebrate with 'May the Fourth be with you' (a play on 'May the Force be with you'). It's become an unofficial Star Wars Day!",
        (10, 3): ":calendar: Tomorrow is Mean Girls Day! In the movie, Aaron asks Cady what day it is: 'It's October 3rd.' It's become a pop culture phenomenon!",
        (10, 31): ":calendar: Tomorrow is Halloween! Originating from ancient Celtic harvest festivals, it's now celebrated with costumes and candy. Americans spend over $10 billion on Halloween!",
        (12, 31): ":calendar: Tomorrow is New Year's Eve! The last day of the year, celebrated with parties and countdowns to midnight. It's time to reflect on the past year and prepare for the new one!",
    }
    
    return fun_holidays.get((month, day), None)


# Track used fun facts to ensure uniqueness
USED_FACTS_FILE = os.path.join(os.path.dirname(__file__), 'used_fun_facts.json')

def get_unique_fun_fact():
    """
    Get a unique fun fact that hasn't been used recently.
    Tracks usage in JSON file to avoid repetition.
    """
    # Load used facts
    try:
        with open(USED_FACTS_FILE, 'r') as f:
            used_facts = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        used_facts = []
    
    # Find unused facts
    unused_facts = [f for f in FUN_FACTS if f not in used_facts]
    
    # If all used, reset!
    if not unused_facts:
        print("   🔄 All fun facts used! Resetting for variety...")
        used_facts = []
        unused_facts = FUN_FACTS.copy()
    
    # Select random unused fact
    selected_fact = random.choice(unused_facts)
    
    # Mark as used
    used_facts.append(selected_fact)
    
    # Save updated list
    with open(USED_FACTS_FILE, 'w') as f:
        json.dump(used_facts, f, indent=2)
    
    return selected_fact

# Warning messages for high count (>100)
HIGH_COUNT_WARNINGS = [
    ":rotating_light: Be careful for this agent - something looks broken!",
    ":rotating_light: Whoa! That's a lot! Please investigate this agent.",
    ":rotating_light: Alert! Unusually high volume - might need attention!",
    ":rotating_light: This seems unusual! Better check what's going on.",
    ":rotating_light: High volume alert! Something might be off here.",
]

# Warning messages for medium count (>50)
MEDIUM_COUNT_WARNINGS = [
    ":warning: Hmm there are many of those. Please ping leads if you need any help.",
    ":warning: That's quite a few! Reach out to leads if needed.",
    ":warning: Higher than usual. Feel free to ask for assistance!",
    ":warning: Notable volume today. Don't hesitate to reach out!",
    ":warning: A bit more than typical. Leads are here to help!",
]

# High-value alert messages
HIGH_VALUE_ALERTS = [
    ":warning: This can indicate there is a batch remained unreconciled.",
    ":warning: High-value transaction! Please verify batch reconciliation.",
    ":warning: Alert: Check if this is part of an unreconciled batch.",
    ":warning: Attention needed: Verify batch completion status.",
    ":warning: Important: Ensure all related batches are reconciled.",
]

# Closing messages
CLOSING_MESSAGES = [
    "Good luck with today's reconciliation! :rocket:",
    "Happy reconciling! You've got this! :muscle:",
    "Let's crush it today! :fire:",
    "Have a great reconciliation day! :star2:",
    "Rock those recons! :guitar:",
    "May the recon force be with you! :jedi:",
]

# Header emojis
HEADER_EMOJIS = [":dart:", ":target:", ":bullseye:", ":direct_hit:"]


def generate_slack_message(df, high_value_threshold=300000):
    """
    Generate formatted Slack message from labeled transactions.
    VARIED & CREATIVE - Each message is unique!
    
    Args:
        df: DataFrame with columns: id, predicted_agent, amount, description, sop_links
        high_value_threshold: Threshold for high-value alerts (default: $300K)
    
    Returns:
        Formatted Slack message string
    """
    
    # Get current day
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    today = days[datetime.now().weekday()]
    
    # PRIORITY 1: Check if today is a BANKING HOLIDAY (most important!)
    banking_holiday = get_banking_holiday_message()
    
    # PRIORITY 2: Check for other special days
    special_day = get_special_day_message()
    
    # Header with random greeting and emoji
    header_emoji = random.choice(HEADER_EMOJIS)
    
    if banking_holiday:
        # Banking holiday - use funny message
        message = f"{header_emoji} {banking_holiday}\n"
    elif special_day:
        # Use special day message
        message = f"{header_emoji} {special_day}\n"
    else:
        # Use regular greeting
        greeting = random.choice(GREETINGS).format(day=today)
        message = f"{header_emoji} {greeting}\n"
    
    message += "Our AI has identified today's transactions as:\n"
    
    # Count by agent (exclude empty/unlabeled)
    labeled_df = df[df['predicted_agent'].notna() & (df['predicted_agent'] != '')]
    agent_counts = labeled_df['predicted_agent'].value_counts()
    
    # Add each agent with special markers (RANDOMIZED warnings!)
    for agent, count in agent_counts.items():
        message += f"• {agent}: {count} transactions"
        
        # Add warnings for specific cases - VARIED each time!
        if count > 100:
            message += " " + random.choice(HIGH_COUNT_WARNINGS)
        elif count > 50:
            message += " " + random.choice(MEDIUM_COUNT_WARNINGS)
        
        message += "\n"
    
    # High-value alerts (EXCLUDING Treasury Transfers!)
    # Filter for important high-value transactions only
    high_value = df[df['amount'] >= high_value_threshold].copy()
    
    # Exclude Treasury Transfer and internal movements from alerts
    excluded_agents = ['Treasury Transfer', 'Money Market Transfer', 'ZBT', 'ICP Funding']
    high_value = high_value[~high_value['predicted_agent'].isin(excluded_agents)]
    
    if len(high_value) > 0:
        message += "---\n"
        message += ":red_circle: High-Value Transaction Alert:\n"
        
        for idx, row in high_value.iterrows():
            message += f"• Transaction ID: {row['id']}\n"
            message += f"  Agent: {row['predicted_agent']}\n"
            message += f"  Amount: ${row['amount']:,.2f}\n"
            desc = row['description'][:80] + "..." if len(row['description']) > 80 else row['description']
            message += f"  Description: {desc}\n"
            # VARIED warning message each time!
            message += f"  {random.choice(HIGH_VALUE_ALERTS)}\n"
    
    # Unlabeled Transactions (only show if any exist)
    unlabeled_df = df[(df['predicted_agent'].isna()) | (df['predicted_agent'] == '')]
    if len(unlabeled_df) > 0:
        message += "---\n"
        message += ":warning: *Unlabeled Transactions*\n"
        message += f"Total: {len(unlabeled_df)} transaction(s) not labeled due to business rules\n\n"
        
        # Group by labeling_comment if available
        if 'labeling_comment' in unlabeled_df.columns:
            comment_counts = unlabeled_df[unlabeled_df['labeling_comment'].notna()]['labeling_comment'].value_counts()
            for reason, count in comment_counts.items():
                if reason:  # Only show non-empty reasons
                    message += f"• {count} transaction(s): {reason}\n"
    
    # SOP Links - INTELLIGENTLY SELECTED by AI based on agent mapping!
    message += "---\n"
    message += ":books: Suggested SOPs (precisely tailored by AI for today's agents):\n"
    
    # Collect unique SOP links from agent mapping
    unique_sops = set()
    for sop_links in df['sop_links']:
        if pd.notna(sop_links) and 'No SOP' not in str(sop_links):
            for link in str(sop_links).split(' | '):
                unique_sops.add(link.strip())
    
    # Add core SOPs that are always relevant
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
    
    # Fun fact OR tomorrow's holiday info (SMART!)
    message += "---\n"
    
    # Check if tomorrow is a special day
    tomorrow_holiday = get_tomorrow_holiday_reminder()
    
    if tomorrow_holiday:
        # Use historical fact about tomorrow's holiday instead of random fun fact
        message += tomorrow_holiday + "\n"
    else:
        # Use regular unique fun fact
        message += get_unique_fun_fact() + "\n"
    
    # Footer (RANDOMIZED closing message!)
    message += random.choice(CLOSING_MESSAGES) + "\n"
    
    return message


def save_slack_message(df, output_file=None, high_value_threshold=300000):
    """
    Generate and save Slack message to file.
    
    Args:
        df: DataFrame with labeled transactions
        output_file: Output file path (default: ~/Desktop/cursor_data/slack_message_[timestamp].txt)
        high_value_threshold: Threshold for high-value alerts
    
    Returns:
        Path to saved file
    """
    import os
    
    message = generate_slack_message(df, high_value_threshold)
    
    if output_file is None:
        output_dir = f"{os.path.expanduser('~')}/Desktop/cursor_data"
        os.makedirs(output_dir, exist_ok=True)
        output_file = f"{output_dir}/slack_message_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    
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

