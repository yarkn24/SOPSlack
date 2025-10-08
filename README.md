# SOPSlack

Intelligent transaction classification and Slack messaging system with AI-powered agent prediction and comprehensive SOP management.

## 🚀 Quick Start - CODE7

The complete automated pipeline:

```bash
python3 code7.py
```

**What it does:**
1. Fetches 40 transactions from Redash
2. Predicts agents with 99% accuracy (Rule + ML hybrid)
3. Maps SOP links from Confluence
4. Generates CSV report
5. Creates intelligent Slack message

**Output:** Two files in Downloads:
- `redash_agents_[timestamp].csv` - Transaction details
- `slack_message_[timestamp].txt` - Ready-to-send message

## ✨ Key Features

### 🤖 AI-Powered Classification
- **99.03% accuracy** agent prediction
- **97.5%** handled by rule-based system (instant)
- XGBoost fallback for edge cases
- Comprehensive 30+ agent support

### 💬 Intelligent Slack Messages
- **Unique every day** - never repeats
- 10 random greetings × 4 header emojis
- 40 unique fun facts (tracked, no repeats)
- Smart high-value alerts (excludes Treasury/ZBT)
- Dynamic warnings (randomized messages)

### 🏦 Banking Holiday System
- **11 US Federal Banking Holidays** tracked
- **TODAY is holiday** → Positive celebration message
- **TOMORROW is holiday** → Educational 3-sentence fact
- Complete calendar coverage (New Year's to Christmas)
- Work-appropriate tone (no triggering language)

### 🚫 Agent Labeling Business Rules
- **ZBT (Zero Balance Transfer)** → Never labeled (business rule)
- **Account 6 (Chase Payroll Incoming Wires)** → TODAY transactions skipped (Risk, needs T+1)
- **Account 9 (Chase Wire In)** → Normal labeling (different from Account 6!)
- **CSV Output** → Unlabeled transactions have blank predicted_agent + labeling_comment
- **Slack Message** → "Unlabeled Transactions" section only appears if unlabeled exist

### 📚 SOP Management
- Confluence integration
- Agent-to-SOP mapping
- Clickable links in messages
- 30+ agent procedures tracked

---

## 🏦 Banking Holidays (Complete List)

The system automatically detects and announces all 11 US Federal Banking Holidays:

| Month | Date | Holiday | Banks Closed |
|-------|------|---------|--------------|
| January | 1st | New Year's Day | ✅ |
| January | 3rd Monday | Martin Luther King Jr. Day | ✅ |
| February | 3rd Monday | Presidents' Day | ✅ |
| May | Last Monday | Memorial Day | ✅ |
| June | 19th | Juneteenth | ✅ |
| July | 4th | Independence Day | ✅ |
| September | 1st Monday | Labor Day | ✅ |
| October | 2nd Monday | Columbus Day* | ✅ |
| November | 11th | Veterans Day | ✅ |
| November | 4th Thursday | Thanksgiving | ✅ |
| December | 25th | Christmas Day | ✅ |

\* *Note: Many states also observe Indigenous Peoples' Day*

### Banking Holiday Messages

**Example: Christmas Day**
```
🎯 Merry Christmas! 🎄🎁 Today is a banking holiday - banks are closed! 🏦

   Our AI has identified today's transactions as...
```

**Example: Day Before Thanksgiving**
```
🎯 Good morning Platform Ops! Happy Wednesday!

   [transaction list]

   🏦📅 Tomorrow is Thanksgiving - a banking holiday!
   Thanksgiving became a federal banking holiday in 1870. Celebrated on the 
   fourth Thursday in November, it's one of the busiest travel days. Banks 
   close so employees can enjoy turkey and family time!
```

---

## 📊 Message Variety Statistics

Every Slack message is **unique** thanks to:

| Component | Variations | Example |
|-----------|------------|---------|
| Greetings | 10 | "Good morning Platform Ops!", "Hey team!", etc. |
| Header Emojis | 4 | 🎯, 🎪, 🏹, 🔥 |
| High-Count Warnings | 5 | "Wow, that's a lot!", "Heads up!", etc. |
| Medium-Count Warnings | 5 | "Keep an eye on...", "Notable activity..." |
| High-Value Alerts | 5 | "Big money alert!", "High-value transactions!" |
| Closing Messages | 6 | "Have a great day!", "Let's balance those books!" |
| Fun Facts | 40 | Finance, science, history, space (never repeats!) |
| Banking Holidays | 11 | Special messages + educational facts |
| Special Days | 8 | Valentine's, Pi Day, Halloween, etc. |

**Total possible combinations:** 10 × 4 × 5 × 5 × 5 × 6 × 40 = **2,400,000+ unique messages!**

---

## 🎯 Example Slack Message

```
🎯 Good morning Platform Ops! Happy Tuesday!

Our AI has identified today's transactions as:
• BAI Reconciliation: 8
• York Adams Tax EIT: 5
• ACH: 3 ⚠️ Keep an eye on this agent!
• Treasury Upload: 2
• Bad Debt: 1

💰 High-value transactions detected (excluding Treasury/ZBT): 2 transactions worth $45,230.00

📚 Here are the relevant SOPs (AI-tailored):
   • BAI Reconciliation: https://confluence.../BAI+Reconciliation
   • York Adams Tax EIT: https://confluence.../York+Adams+Tax
   [...]

💡 The Federal Reserve processes 175 million ACH transactions daily worth 
   over $51 billion! That's like moving the GDP of a small country every day!

Have a great day! 🚀
```

---

## 🚫 Agent Labeling Business Rules (Detailed)

### Rule 1: ZBT (Zero Balance Transfer)
**Never label ZBT transactions**

```
Reasoning: Business policy - ZBT transactions require special handling
Impact: 
  - CSV: predicted_agent column = BLANK
  - CSV: labeling_comment = "ZBT transactions are never labeled (business rule)"
  - Slack: If any ZBT unlabeled → Shows in "Unlabeled Transactions" section
```

### Rule 2: Chase Payroll Incoming Wires (Account 6)
**TODAY transactions are NOT labeled (need T+1 settlement)**

```
Account Details:
  - Account ID: 6
  - Account Name: Chase Incoming Wires (PAYROLL WIRE ACCOUNT)
  - NOT the same as Account 9 (Chase Wire In - normal wires)

Reasoning: Risk agent classification requires T+1 settlement verification

Impact:
  - TODAY transactions → NOT labeled
  - Yesterday+ transactions → Labeled normally (as Risk)
  - CSV: predicted_agent = BLANK for today's transactions
  - CSV: labeling_comment = "Account 6 - same-day transactions not labeled (Risk, needs T+1)"
  - Slack: Shows in "Unlabeled Transactions" section if any exist

Example:
  - Transaction date: 2025-10-08 (TODAY)
  - Current date: 2025-10-08
  - Result: NOT labeled (wait until tomorrow)
  
  - Transaction date: 2025-10-07 (YESTERDAY)
  - Current date: 2025-10-08
  - Result: Labeled as Risk (normal processing)
```

### Rule 3: 1-Day Lag Context
**Reconciliation data is typically 1 day behind**

```
Background Information:
  - Reconciliation data reflects transactions from 1 day ago
  - Banking holidays can extend this lag
  - Example: Friday transaction → Monday holiday → Appears Tuesday

Impact on Users:
  - This is normal business practice
  - No action needed from CODE7 users
  - Rules automatically account for this timing
```

### Unlabeled Transactions in Slack

**Section only appears if unlabeled transactions exist**

```
Example (when unlabeled exist):
---
⚠️ *Unlabeled Transactions*
Total: 5 transaction(s) not labeled due to business rules

• 3 transaction(s): ZBT transactions are never labeled (business rule)
• 2 transaction(s): Account 6 - same-day transactions not labeled (Risk, needs T+1)
---

Example (when NO unlabeled):
  [Section not shown at all]
```

---

## 📊 CSV Output Format

Every CSV includes these columns:

| Column | Description | Example |
|--------|-------------|---------|
| `id` | Transaction ID | 12345678 |
| `date` | Transaction date | 2025-10-08 |
| `amount` | Dollar amount | 1500.00 |
| `payment_method` | Text method | wire_in |
| `account` | Text account name | Chase Incoming Wires |
| `description` | Transaction description | JPMORGAN... |
| `predicted_agent` | **Agent prediction** (blank if unlabeled) | Risk |
| `sop_links` | Confluence URLs (blank if unlabeled) | https://... |
| `prediction_method` | Rule-based or ML-based | Rule-based |
| `labeling_comment` | Why unlabeled (if applicable) | Account 6 - same-day... |

---

## Requirements

- Python 3.8+
- Node.js 18+
- Slack Workspace
- Atlassian account (Jira/Confluence)

## Installation

### 1. Clone the repository
```bash
git clone https://github.com/yarkn24/SOPSlack.git
cd SOPSlack
```

### 2. Install Python dependencies
```bash
pip install -r requirements.txt
```

### 3. Set up environment variables
Create a `.env` file:
```env
SLACK_BOT_TOKEN=xoxb-your-token
SLACK_SIGNING_SECRET=your-signing-secret
JIRA_URL=https://your-domain.atlassian.net
JIRA_EMAIL=your-email@example.com
JIRA_API_TOKEN=your-jira-api-token
CONFLUENCE_URL=https://your-domain.atlassian.net/wiki
CONFLUENCE_API_TOKEN=your-confluence-api-token
```

### 4. Start the MCP Server
```bash
python mcp_server.py
```

## 📊 What the Bot Knows

The bot has access to **67+ Confluence pages** in the Platform Operations space, including:

- ✅ **Reconciliations & Reporting** (21 pages)
  - BAI File Reconciliations
  - Daily Bank Transaction Reconciliation
  - Modern Treasury integration
  - All reconciliation tools and SOPs

- ✅ **Payment Investigations** (11 pages)
  - How to review investigations
  - Payment investigation hashtags
  - Write-off procedures
  - Quality assurance

- ✅ **Internal Knowledge Base** (3 pages)
  - ACH Payment Overview
  - Financial Audit Cleanup
  - Incident Response Framework

- ✅ **Manual Checks** (2 pages)
  - Customer Cash Completeness Checks
  - Manual Reconciliation Checks

**Total:** 67 pages covering all Platform Operations procedures

## 🔧 Technical Architecture

### Components

1. **Slack Bot** (`gemini_confluence_bot.py`)
   - Listens for mentions and slash commands
   - Handles user interactions

2. **Confluence Search**
   - Uses Atlassian Python API
   - Searches Platform Operations space with CQL
   - Retrieves page content

3. **Gemini AI**
   - Analyzes Confluence documentation
   - Generates contextual answers
   - Cites sources

4. **Response Formatter**
   - Presents answers in Slack markdown
   - Includes clickable links to sources

### Data Flow

```
User Question (Slack)
    ↓
Confluence Search (CQL)
    ↓
Retrieve Documentation
    ↓
Gemini AI (Context + Question)
    ↓
Formatted Answer + Sources
    ↓
Slack Response
```

## 💰 Cost Estimate

### Gemini API (Free Tier)
- **Included:** 15 requests/minute, 1M tokens/month
- **Cost after free tier:** $0.15 per 1M input tokens, $0.60 per 1M output tokens

**Typical usage:**
- Question: ~100 tokens
- Confluence context: ~10,000 tokens  
- Answer: ~500 tokens
- **Cost per question: ~$0.002** (0.2 cents)

**Monthly estimate:**
- 50 questions/day = 1,500 questions/month
- **Cost: ~$3/month** (well within free tier)

## 🔒 Security

- ✅ All tokens stored in `.env` (gitignored)
- ✅ Confluence API uses secure OAuth tokens
- ✅ Socket Mode (no public webhooks needed)
- ✅ Bot only accesses Platform Operations space

## MCP Atlassian Integration (Optional)

This project uses [sooperset/mcp-atlassian](https://github.com/sooperset/mcp-atlassian), a Python-based MCP server that provides read/write access to Atlassian tools (Confluence, Jira).

### MCP Server Setup

1. Install MCP Atlassian:
```bash
pip3 install mcp-atlassian
```

2. Configure environment variables in `.env`:
```env
# Jira Configuration
JIRA_URL=https://your-domain.atlassian.net
JIRA_EMAIL=your-email@example.com
JIRA_API_TOKEN=your-jira-api-token

# Confluence Configuration
CONFLUENCE_URL=https://your-domain.atlassian.net
CONFLUENCE_EMAIL=your-email@example.com
CONFLUENCE_API_TOKEN=your-confluence-api-token
```

3. Configure MCP in `mcp.json`:
```json
{
  "mcpServers": {
    "atlassian": {
      "command": "python3",
      "args": ["-m", "mcp_atlassian"],
      "env": {
        "JIRA_URL": "https://your-domain.atlassian.net",
        "JIRA_EMAIL": "your-email@example.com",
        "JIRA_API_TOKEN": "your-jira-api-token",
        "CONFLUENCE_URL": "https://your-domain.atlassian.net",
        "CONFLUENCE_EMAIL": "your-email@example.com",
        "CONFLUENCE_API_TOKEN": "your-confluence-api-token"
      }
    }
  }
}
```

4. Verify installation:
```bash
pip3 show mcp-atlassian
```

### Running MCP Server

The MCP server runs automatically when configured in your AI assistant (Claude Desktop, Cursor, etc.).

**For local use:**
1. Copy `mcp.json` to `mcp.local.json`
2. Add your actual credentials to `mcp.local.json`
3. Configure your AI assistant to use `mcp.local.json`

**Note:** `mcp.local.json` and `.env` are in `.gitignore` for security - your credentials won't be pushed to GitHub.

### Authentication Options

MCP Atlassian supports three authentication methods:
- **API Token** (Recommended): Use Atlassian API tokens for Cloud instances
- **Personal Access Token (PAT)**: For Jira/Confluence Server/Data Center
- **OAuth 2.0**: For user-specific authentication with `--oauth-setup` flag

**Note**: Make sure to use the full Atlassian URL format (e.g., `https://your-domain.atlassian.net` for Jira Cloud)

## Usage

### Slack Commands

- `/sop create` - Create a new SOP
- `/sop list` - List all SOPs
- `/sop search [search term]` - Search for SOPs
- `/sop sync` - Synchronize with Jira and Confluence

### API Endpoints

- `GET /api/sops` - Get all SOPs
- `POST /api/sops` - Create a new SOP
- `GET /api/sops/:id` - Get a specific SOP
- `PUT /api/sops/:id` - Update an SOP
- `DELETE /api/sops/:id` - Delete an SOP

## Project Structure

```
SOPSlack/
├── src/
│   ├── slack/          # Slack integration
│   ├── atlassian/      # Jira and Confluence integration
│   ├── mcp/            # MCP server configuration
│   └── api/            # REST API
├── tests/              # Test files
├── config/             # Configuration files
├── docs/               # Documentation
├── env.example         # Example environment variables
├── requirements.txt    # Python dependencies
├── mcp.json            # MCP server configuration
└── README.md           # This file
```

## Contributing

1. Fork the project
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

MIT License

## Contact

Project Owner - [@yarkn24](https://github.com/yarkn24)

Project Link: [https://github.com/yarkn24/SOPSlack](https://github.com/yarkn24/SOPSlack)
