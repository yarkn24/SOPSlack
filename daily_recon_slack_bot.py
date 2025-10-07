"""
Daily Reconciliation Slack Bot
===============================
Sends daily reconciliation messages to Slack channel.

Author: Yarkin Akcil
Date: October 7, 2025
"""

import os
from datetime import datetime
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from slack_daily_message_template import generate_daily_recon_message


class ReconciliationBot:
    """Slack bot for daily reconciliation messages."""
    
    def __init__(self, token=None):
        """
        Initialize Slack bot.
        
        Args:
            token: Slack bot token (if not provided, reads from environment)
        """
        self.token = token or os.environ.get("SLACK_BOT_TOKEN")
        if not self.token:
            raise ValueError("SLACK_BOT_TOKEN not found in environment variables")
        
        self.client = WebClient(token=self.token)
    
    def test_connection(self):
        """
        Test Slack bot connection.
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            response = self.client.auth_test()
            print("✅ Slack Bot Connected!")
            print(f"   Bot Name: {response['user']}")
            print(f"   Team: {response['team']}")
            print(f"   User ID: {response['user_id']}")
            return True
        except SlackApiError as e:
            print(f"❌ Connection failed: {e.response['error']}")
            return False
    
    def send_daily_message(self, agent_counts, high_value_icp=None, 
                          channel="#platform-operations", date=None):
        """
        Send daily reconciliation message to Slack.
        
        Args:
            agent_counts: Dictionary with agent names and counts
            high_value_icp: List of high-value ICP transactions
            channel: Slack channel to send to
            date: Date for the message (default: today)
        
        Returns:
            Response from Slack API or None if failed
        """
        try:
            # Generate message
            message = generate_daily_recon_message(
                agent_counts=agent_counts,
                high_value_icp_transactions=high_value_icp,
                date=date
            )
            
            # Send to Slack
            response = self.client.chat_postMessage(
                channel=channel,
                text=message,
                mrkdwn=True,  # Enable Slack markdown formatting
                unfurl_links=False,  # Don't show link previews
                unfurl_media=False
            )
            
            print(f"✅ Message sent successfully to {channel}")
            print(f"   Message timestamp: {response['ts']}")
            return response
            
        except SlackApiError as e:
            print(f"❌ Error sending message: {e.response['error']}")
            if e.response['error'] == 'not_in_channel':
                print(f"   💡 Tip: Invite bot to channel: /invite @Daily Reconciliation Bot")
            return None
    
    def send_test_message(self, channel="#recon-bot-testing"):
        """
        Send a test message with example data.
        
        Args:
            channel: Slack channel for testing
        
        Returns:
            Response from Slack API or None if failed
        """
        print(f"📤 Sending test message to {channel}...")
        
        # Example data
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
                'description': 'ORIG CO NAME=NIUM INC,ORIG ID=0514672353,DESC DATE=251007',
            }
        ]
        
        return self.send_daily_message(
            agent_counts=example_counts,
            high_value_icp=example_high_value,
            channel=channel
        )


def main():
    """Main function for testing the bot."""
    print("=" * 80)
    print("SLACK BOT SETUP TEST")
    print("=" * 80)
    print()
    
    # Check for token
    if not os.environ.get("SLACK_BOT_TOKEN"):
        print("❌ SLACK_BOT_TOKEN not found in environment variables")
        print()
        print("To set it:")
        print("  export SLACK_BOT_TOKEN='xoxb-your-token-here'")
        print()
        print("Or create a .env file:")
        print("  SLACK_BOT_TOKEN=xoxb-your-token-here")
        print("  SLACK_TEST_CHANNEL=#recon-bot-testing")
        return
    
    # Initialize bot
    try:
        bot = ReconciliationBot()
    except ValueError as e:
        print(f"❌ Error: {e}")
        return
    
    # Test connection
    print("🔌 Testing connection...")
    if not bot.test_connection():
        return
    
    print()
    
    # Get test channel from environment or use default
    test_channel = os.environ.get("SLACK_TEST_CHANNEL", "#recon-bot-testing")
    
    # Send test message
    print(f"📤 Sending test message to {test_channel}...")
    response = bot.send_test_message(channel=test_channel)
    
    if response:
        print()
        print("=" * 80)
        print("✅ SUCCESS! Bot is working correctly.")
        print("=" * 80)
        print()
        print("Next steps:")
        print("1. Check the test message in Slack")
        print("2. Invite bot to #platform-operations:")
        print("   /invite @Daily Reconciliation Bot")
        print("3. Run daily automation script")
    else:
        print()
        print("=" * 80)
        print("❌ FAILED! Check error messages above.")
        print("=" * 80)


if __name__ == "__main__":
    main()

