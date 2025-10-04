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

## MCP Atlassian Integration

This project provides access to Atlassian services using MCP (Model Context Protocol).

### MCP Server Setup

1. Install MCP server packages:
```bash
npm install -g @modelcontextprotocol/server-atlassian
```

2. Configure the MCP configuration file (`mcp.json`):
```json
{
  "mcpServers": {
    "atlassian": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-atlassian"],
      "env": {
        "ATLASSIAN_URL": "https://your-domain.atlassian.net",
        "ATLASSIAN_EMAIL": "your-email@example.com",
        "ATLASSIAN_API_TOKEN": "your-api-token"
      }
    }
  }
}
```

3. Test the MCP server:
```bash
npx @modelcontextprotocol/server-atlassian
```

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
├── .env.example        # Example environment variables
├── requirements.txt    # Python dependencies
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
