# SOPSlack

SOP (Standard Operating Procedure) management system for Atlassian products (Jira, Confluence) with Slack integration.

## Features

- 🔗 Slack integration
- 📝 Jira and Confluence integration
- 🤖 MCP (Model Context Protocol) support
- 📋 SOP management and tracking

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
