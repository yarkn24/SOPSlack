#!/bin/bash
################################################################################
# CODE7 Daily Reconciliation Bot
# ================================
# Runs CODE7 and posts results to Slack automatically.
#
# Usage:
#   ./daily_recon_bot.sh            # Production mode (posts to #platform-ops-recon)
#   ./daily_recon_bot.sh --test     # Test mode (posts to #mytests)
#
# Schedule with cron:
#   0 9 * * 1-5 cd /path/to/SOPSlack && ./daily_recon_bot.sh  # Mon-Fri at 9 AM
#
# Author: Yarkin Akcil
# Date: October 2025
################################################################################

# Exit on error
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Parse arguments
MODE="prod"
if [ "$1" == "--test" ]; then
    MODE="test"
    echo -e "${YELLOW}⚙️  TEST MODE ENABLED${NC}"
fi

# Check for SLACK_BOT_TOKEN
if [ -z "$SLACK_BOT_TOKEN" ]; then
    echo -e "${RED}❌ Error: SLACK_BOT_TOKEN not set${NC}"
    echo ""
    echo "Please set your Slack bot token:"
    echo "  export SLACK_BOT_TOKEN='xoxb-your-token-here'"
    echo ""
    echo "Or add to ~/.zshrc:"
    echo "  echo 'export SLACK_BOT_TOKEN=\"xoxb-your-token-here\"' >> ~/.zshrc"
    echo "  source ~/.zshrc"
    exit 1
fi

echo ""
echo "================================================================================"
echo -e "${BLUE}🤖 CODE7 DAILY RECONCILIATION BOT${NC}"
echo "================================================================================"
echo ""
echo "📅 Date: $(date '+%Y-%m-%d %H:%M:%S')"
echo "📍 Directory: $SCRIPT_DIR"
echo "🔧 Mode: ${MODE^^}"
echo ""

# Step 1: Run CODE7
echo "================================================================================"
echo -e "${BLUE}STEP 1/2: Running CODE7 (Fetch & Classify Transactions)${NC}"
echo "================================================================================"
echo ""

if python3 code7.py; then
    echo ""
    echo -e "${GREEN}✅ CODE7 completed successfully${NC}"
else
    echo ""
    echo -e "${RED}❌ CODE7 failed! Check errors above.${NC}"
    exit 1
fi

# Step 2: Send to Slack
echo ""
echo "================================================================================"
echo -e "${BLUE}STEP 2/2: Sending Results to Slack${NC}"
echo "================================================================================"
echo ""

if [ "$MODE" == "test" ]; then
    CHANNEL="#mytests"
    python3 code7_slack_bot.py --test
else
    CHANNEL="#platform-ops-recon"
    python3 code7_slack_bot.py --prod
fi

if [ $? -eq 0 ]; then
    echo ""
    echo "================================================================================"
    echo -e "${GREEN}✅ SUCCESS! Message posted to $CHANNEL${NC}"
    echo "================================================================================"
    echo ""
    echo "📊 Files saved to: ~/Desktop/cursor_data/"
    echo "📝 Check Slack for the message!"
    echo ""
else
    echo ""
    echo "================================================================================"
    echo -e "${RED}❌ FAILED to send Slack message${NC}"
    echo "================================================================================"
    echo ""
    echo "Possible issues:"
    echo "  - Bot not added to channel (use: /invite @Bot)"
    echo "  - Invalid SLACK_BOT_TOKEN"
    echo "  - Network issues"
    echo ""
    exit 1
fi

echo "✅ Daily reconciliation bot completed at $(date '+%H:%M:%S')"
echo ""


