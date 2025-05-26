# Necromunda Discord Bot

A modular Discord bot for managing and playing _Necromunda_ campaigns.

## Features

- Campaign creation, listing, and deletion (server-specific and user-authenticated)
- Gang registration, listing, and deletion
- Dice rolling with support for standard RPG notation

### Prerequisites

- Python 3.8+
- A Discord bot token (from [Discord Developer Portal](https://discord.com/developers/applications))

### Installation

```bash
git clone https://github.com/yourusername/necromunda-discord-bot.git
cd necromunda-discord-bot
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
```

### Configuration

Create a `.env` file with:

```
DISCORD_BOT_TOKEN=your_token_here
```

### Running

```bash
python discord_bot.py
```

### Commands

**Text Commands:**

- `!ping` – Bot health check
- `!create_campaign <name>` – Create a campaign
- `!register_gang <campaign_id> <yaktribe_url>` – Register a gang

**Slash Commands:**

- `/campaign create <name>` – Create a campaign
- `/campaign list` – List campaigns for the server
- `/campaign delete <id>` – Delete a campaign (only by the creator)
- `/gang register <campaign_id> <yaktribe_url>` – Register a gang
- `/gang list <campaign_id>` – List gangs in a campaign
- `/gang mine` – View all gangs registered by the current user, including campaign info
- `/gang delete <id>` – Delete a gang (only by the owner)
- `/dice roll <formula>` – Roll dice using expressions like `2d6+3`

### File Structure

```fs
cogs/             # Command modules
  campaigns.py    # Campaign commands
  gangs.py        # Gang commands
  dice.py         # Dice commands

db/               # Database modules
  __init__.py     # DB connection, schema version tracking
  campaigns.py    # Campaign DB logic
  gangs.py        # Gang DB logic

discord_bot.py    # Main bot entry point
```

### License

MIT
