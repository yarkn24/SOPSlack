# 🚀 CODE7 Slack Bot - Quick Start

## ⚡ TL;DR (Too Long; Didn't Read)

```bash
# 1. Get token from IT Ops
export SLACK_BOT_TOKEN='xoxb-your-token-here'

# 2. Test it
python3 code7_slack_bot.py --test

# 3. Use it daily
./daily_recon_bot.sh
```

---

## 📝 What You Need to Do NOW

### 1️⃣ **Post to IT Ops** (Copy-paste this):

```
Hi IT Ops! 👋

Richard Eickholt approved our Daily Reconciliation Slack Bot.

Please create a Slack Bot with these settings:
- Name: "Daily Reconciliation Bot" or "CODE7 Bot"
- Channels: #mytests (test), #platform-ops-recon (production)
- Permissions: chat:write, channels:read

Share the Bot Token (xoxb-...) with me securely.

Approved by: Richard Eickholt
Thank you! 🙏
```

### 2️⃣ **When Token Arrives**

```bash
# Add to ~/.zshrc
echo 'export SLACK_BOT_TOKEN="xoxb-YOUR-TOKEN-HERE"' >> ~/.zshrc
source ~/.zshrc
```

### 3️⃣ **Test It**

```bash
cd ~/Documents/GitHub/SOPSlack
python3 code7_slack_bot.py --test --dry-run  # Preview first
python3 code7_slack_bot.py --test            # Send to #mytests
```

### 4️⃣ **Go Live**

```bash
./daily_recon_bot.sh  # Production mode
```

---

## 🎯 Daily Usage (After Setup)

### Option A: Automated Script (RECOMMENDED)
```bash
./daily_recon_bot.sh          # Runs CODE7 + Posts to Slack
```

### Option B: Manual Steps
```bash
# Step 1: Fetch & classify
python3 code7.py

# Step 2: Post to Slack
python3 code7_slack_bot.py --prod
```

---

## 🔍 Commands Cheat Sheet

| Command | What It Does |
|---------|-------------|
| `python3 code7.py` | Fetch from Redash, classify transactions, save CSV |
| `python3 code7_slack_bot.py --test` | Post to #mytests |
| `python3 code7_slack_bot.py --prod` | Post to #platform-ops-recon |
| `python3 code7_slack_bot.py --dry-run` | Preview message (don't send) |
| `./daily_recon_bot.sh` | Full automation (fetch + post) |
| `./daily_recon_bot.sh --test` | Full automation (test mode) |

---

## 🆘 Troubleshooting

| Error | Fix |
|-------|-----|
| "SLACK_BOT_TOKEN not found" | `export SLACK_BOT_TOKEN='xoxb-...'` |
| "not_in_channel" | `/invite @Daily Reconciliation Bot` in Slack |
| "CSV file not found" | Run `python3 code7.py` first |
| "invalid_auth" | Token expired - get new one from IT Ops |

---

## 📞 Need Help?

- **Platform Ops:** @Richard Eickholt
- **Technical:** @Yarkin
- **IT Support:** #itops channel

---

## ✅ Setup Checklist

- [ ] IT Ops request submitted
- [ ] Bot token received
- [ ] Token configured (`export SLACK_BOT_TOKEN=...`)
- [ ] Test successful (`--test`)
- [ ] Production working (`--prod`)

---

**Ready to Go!** 🎉


