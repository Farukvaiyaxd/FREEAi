# Telegram BIN Bot - GitHub + Railway Template

This repo contains a minimal Telegram bot that calls an external BIN API (`https://smartxen.vercel.app/gen?bin=...`) and returns formatted results.
It's prepared to be deployed on Railway and stored on GitHub.

## Files
- `bot.py` - main bot implementation (uses `pyTelegramBotAPI` / `telebot`)
- `requirements.txt` - Python dependencies
- `Procfile` - Railway worker declaration

## Setup (Railway)
1. Create a new Railway project and link your GitHub repository.
2. Set environment variable in Railway project settings:
   - `TELEGRAM_BOT_TOKEN` = your bot token (from BotFather)
3. Deploy. Railway will run the `worker` defined in `Procfile`.

## Local testing
- Install deps: `pip install -r requirements.txt`
- Export your token locally:
  - Linux/macOS: `export TELEGRAM_BOT_TOKEN="12345:ABC..."
  - Windows (PowerShell): `$env:TELEGRAM_BOT_TOKEN = "12345:ABC..."`
- Run: `python bot.py`

## Notes & Security
- The bot uses the external API at `smartxen.vercel.app`. Ensure you trust that API and follow its terms.
- The bot escapes API output for HTML safety but **do not** log or expose full card numbers or any sensitive data.
- Keep your `TELEGRAM_BOT_TOKEN` secret.