# PCPortOP Telegram Verification Bot

This bot automatically manages user requests for the **God of War III PC Port 100% Crash-Proof Build**:
1. Greets users with an explanation of the fix (Intel Iris Xe / Hades / Poseidon fixes).
2. Requires them to **Watch & Like** your YouTube video, **Comment & Subscribe**, and join **`@pcportop`**.
3. Verifies their action (via screenshot or button confirmation) and delivers the Google Drive download link automatically.

---

## 🚀 How to Run Locally (On Your Windows PC)

Simply double-click:
👉 **`start_bot.bat`**

The command prompt will open and show:
```text
🤖 PCPortOP Telegram Bot is RUNNING...
```
As long as this window is open, anyone who messages `@PcPortOP_bot` will be automatically guided to your YouTube channel and given the download link.

---

## ☁️ How to Run 24/7 in the Cloud (Free)

If you don't want to keep your PC on:
1. Create a free account on [Render.com](https://render.com) or [Railway.app](https://railway.app).
2. Create a new "Background Worker".
3. Upload this `telegram_bot` folder (or push it to a private GitHub repo).
4. Start Command: `python bot.py`
The bot will run 24 hours a day, 7 days a week for free.

---

## ⚙️ Configuration

In `bot.py`:
- `BOT_TOKEN`: Your `@BotFather` API token.
- `DOWNLOAD_URL`: Your Google Drive download link.
- `YOUTUBE_URL`: `https://youtu.be/QpJfxTSHp-s`
- `TELEGRAM_CHANNEL_URL`: `https://t.me/pcportop`
