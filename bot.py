import telebot
from telebot import types
import logging

# Configure Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# --- Configuration ---
BOT_TOKEN = "8355770693:AAF5Amxsq_p5BCBH9-D1VM3KTdy3g7Abm1E"
DOWNLOAD_URL = "https://drive.google.com/file/d/1UIO6dNy72uMxKjJEaTpGc_l4FpF-t9hC/view?usp=sharing"
YOUTUBE_URL = "https://youtu.be/QpJfxTSHp-s"
TELEGRAM_CHANNEL_URL = "https://t.me/pcportop"

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="Markdown")

def get_welcome_markup():
    markup = types.InlineKeyboardMarkup(row_width=1)
    btn_video = types.InlineKeyboardButton("📺 1. Watch & Like Video on YouTube", url=YOUTUBE_URL)
    btn_channel = types.InlineKeyboardButton("📢 2. Join Our Telegram Channel (@pcportop)", url=TELEGRAM_CHANNEL_URL)
    btn_verified = types.InlineKeyboardButton("✅ 3. I Have Liked, Subscribed & Commented", callback_data="claim_file")
    markup.add(btn_video, btn_channel, btn_verified)
    return markup

def get_download_markup():
    markup = types.InlineKeyboardMarkup(row_width=1)
    btn_download = types.InlineKeyboardButton("📥 Download God of War III Fix (Google Drive)", url=DOWNLOAD_URL)
    btn_channel = types.InlineKeyboardButton("📢 Join @pcportop for Future Game Fixes", url=TELEGRAM_CHANNEL_URL)
    markup.add(btn_download, btn_channel)
    return markup

@bot.message_handler(commands=["start", "help"])
def send_welcome(message):
    user_name = message.from_user.first_name or "Gamer"
    welcome_text = (
        f"👋 **Hey {user_name}! Welcome to PCPortOP!**\n\n"
        f"🎮 You are getting the **God of War III PC Port - 100% Crash-Proof Optimized Build**!\n\n"
        f"⚡ **What this fix includes:**\n"
        f"• Completely fixes the **Hades boss fight & death cutscene crash**\n"
        f"• Prevents Poseidon water & dynamic streaming crashes\n"
        f"• Fully optimized for **Intel Iris Xe, Intel UHD, Arc & AMD Vega** iGPUs\n"
        f"• Rock-solid 60+ FPS performance on laptops and low-spec PCs\n\n"
        f"--- \n"
        f"🔒 **To unlock the download file, please complete these 2 quick steps:**\n"
        f"1️⃣ **Like, Comment & Subscribe** on our YouTube video.\n"
        f"2️⃣ **Join** our Telegram channel `@pcportop`.\n\n"
        f"👇 Click the buttons below to complete, then tap **Verify**:"
    )
    bot.send_message(message.chat.id, welcome_text, reply_markup=get_welcome_markup())

@bot.callback_query_handler(func=lambda call: call.data == "claim_file")
def handle_claim(call):
    bot.answer_callback_query(call.id, text="Checking status...")
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    btn_link = types.InlineKeyboardButton("🚀 Unlock Download Link Now", callback_data="deliver_link")
    btn_video = types.InlineKeyboardButton("📺 Open YouTube Video (Subscribe & Comment)", url=YOUTUBE_URL)
    markup.add(btn_link, btn_video)

    msg = (
        "⭐ **Almost Done!**\n\n"
        "Please make sure you have:\n"
        "1. **Subscribed** to the channel\n"
        "2. **Liked** and left a **Comment** on the video\n"
        "3. Joined **@pcportop**\n\n"
        "📸 *You can send a screenshot here to confirm, or click below to unlock your file immediately:*"
    )
    bot.send_message(call.message.chat.id, msg, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "deliver_link")
def handle_deliver(call):
    bot.answer_callback_query(call.id, text="Verified! Here is your download!")
    deliver_file(call.message.chat.id)

@bot.message_handler(content_types=["photo"])
def handle_screenshot(message):
    bot.reply_to(
        message,
        "🎉 **Screenshot received! Thank you for supporting the channel!**"
    )
    deliver_file(message.chat.id)

@bot.message_handler(func=lambda msg: True)
def handle_any_message(message):
    send_welcome(message)

def deliver_file(chat_id):
    success_text = (
        "🎉 **Access Granted! Here is your download:**\n\n"
        "📦 **God of War III PC Port - 100% Crash-Proof iGPU Build**\n"
        "• Tested and verified on Intel Iris Xe / UHD / AMD Vega\n"
        "• No crashes at Hades, Poseidon, or asset transitions\n"
        "• Smooth 60+ FPS stability\n\n"
        "👉 **Click the button below to download the file directly from Google Drive:**"
    )
    bot.send_message(chat_id, success_text, reply_markup=get_download_markup())

if __name__ == "__main__":
    import sys
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    print("=" * 50)
    print("[*] PCPortOP Telegram Bot (@PcPortOP_bot) is RUNNING...")
    print("Press Ctrl+C to stop.")
    print("=" * 50)
    try:
        bot.infinity_polling(timeout=20, long_polling_timeout=20)
    except Exception as e:
        logging.error(f"Bot error: {e}")
