# 🤖 PCPortOP Telegram Verification Bot

Official verification & auto-delivery bot for PC game ports and custom crash-free builds.

- **Bot Username:** [@PcPortOP_bot](https://t.me/PcPortOP_bot)
- **Updates Channel:** [@pcportop](https://t.me/pcportop)

---

## ⚡ Features
1. **Multi-Game Catalog:** Interactive menu for God of War III Remastered, Bloodborne, and upcoming ports.
2. **Community Verification:** Directs users to your YouTube tutorial and Telegram channel before unlocking downloads.
3. **Automated Link Delivery:** Automatically serves the verified Google Drive link once confirmed.
4. **Cloud Health Server:** Embedded lightweight HTTP server on port `10000` to support 24/7 hosting on Render/Railway.

---

## ⏳ Cloud Spin-Up Notice (Free Tier)
> When hosted on free cloud instances (e.g., Render Free Tier), the service spins down after 15 minutes of inactivity.  
> **Cold starts may take 1–5 minutes to respond to the first `/start` request.**  
>
> 💡 *Tip: To keep the bot active 24/7 with zero delay, add the service URL to a free monitoring service like [UptimeRobot](https://uptimerobot.com) to ping it every 5 minutes.*

---

## 🚀 Deployment Options

### Option 1: Run 24/7 on Render (Recommended)
1. Push this repository to GitHub.
2. In [Render Dashboard](https://dashboard.render.com), create a **New Web Service** connected to your repo.
3. Settings:
   - **Environment:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `python bot.py`
4. Add Environment Variables:
   - `BOT_TOKEN`: Your Telegram Bot API token.
   - `DOWNLOAD_URL`: Your Google Drive download URL.

### Option 2: Run Locally (Windows)
Double-click **`start_bot.bat`**. The bot will run in a command prompt window as long as your PC is on.
