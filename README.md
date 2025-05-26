# README.md

## Necromunda Discord Bot

A Discord bot designed to assist in managing and playing Necromunda campaigns, including campaign creation, gang registration via Yaktribe, and more.

### Features

- Create and manage Necromunda campaigns
- Register player gangs using Yaktribe links

### Prerequisites

- Python 3.8+
- A Discord bot token (create one via the Discord Developer Portal)

### Installation

```bash
git clone https://github.com/sludemann/necromunda-discord-bot.git
cd necromunda-discord-bot
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Running the Bot

1. Replace `'YOUR_BOT_TOKEN'` in `necromunda_discord_bot.py` with your actual bot token.
2. Run the bot:

```bash
python necromunda_discord_bot.py
```

### Commands

- `!ping` – Check if the bot is responsive
- `!create_campaign <name>` – Create a new campaign
- `!register_gang <campaign_id> <yaktribe_url>` – Register your gang with a campaign using your Yaktribe link

### To Do

- Add commands to create campaigns and register gangs
- Integrate with Yaktribe data
- Track gang stats and campaign progress

### License

MIT
