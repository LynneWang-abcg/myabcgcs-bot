# MyAbcgCS Telegram Bot

Telegram Bot for recording customer messages, translating non-simplified-Chinese text into simplified Chinese, and tracking each item as a requirement or problem with a processing status.

## Features

- Receive pasted or forwarded text messages.
- Keep simplified Chinese text as-is.
- Translate other text to simplified Chinese through the free MyMemory translation API.
- Save each item in SQLite.
- Classify each item with Telegram buttons:
  - Requirement
  - Problem
- Track status with Telegram buttons:
  - Unprocessed
  - In progress
  - Done
- Use `/list` to view open items.
- Use `/search keyword` to search history.

## Render Setup

1. Push this project to GitHub.
2. Create a new Render Web Service from the GitHub repository.
3. Use the included `render.yaml` settings.
4. Add environment variables:

```text
TELEGRAM_BOT_TOKEN=your token from BotFather
PUBLIC_URL=https://your-render-service-name.onrender.com
```

Render generates `WEBHOOK_SECRET` automatically.

## Notes

SQLite data on Render free web services may not be permanent after redeploys. This is fine for the first test version. For real long-term use, move storage to a managed database later.
