# TAO Security Bot

Telegram bot for monitoring login attempts on CoreVista.

## Features
- Test login on https://corevista-netgoogle.lovable.app
- Security preferences (Password Error, Block Visitor, SMS Prompt, etc.)
- Alerts on failures

## Commands
- `/start` - Start bot
- `/status` - Show current security settings
- `/toggle <option>` - Toggle settings (e.g. `/toggle password_error`)

## Local Run
```bash
cp .env.example .env
pip install -r requirements.txt
playwright install chromium
python bot.py