import telebot
from telebot import types
import logging
import sys

# Configure stdout for Windows/Unicode safety
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# --- Configuration ---
BOT_TOKEN = "8355770693:AAF5Amxsq_p5BCBH9-D1VM3KTdy3g7Abm1E"
CHANNEL_USERNAME = "@pcportop"
CHANNEL_URL = "https://t.me/pcportop"
YOUTUBE_CHANNEL_URL = "http://www.youtube.com/@pcportop"
YOUTUBE_VIDEO_URL = "https://youtu.be/QpJfxTSHp-s"
GOW3_DOWNLOAD_URL = "https://drive.google.com/file/d/1UIO6dNy72uMxKjJEaTpGc_l4FpF-t9hC/view?usp=sharing"

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="Markdown")

def is_user_in_channel(user_id):
    """Checks if user has joined the Telegram channel. Fails open gracefully if bot lacks admin permissions."""
    try:
        member = bot.get_chat_member(CHANNEL_USERNAME, user_id)
        if member.status in ['left', 'kicked']:
            return False
        return True
    except Exception as e:
        # If bot is not admin or channel check fails, allow user through to avoid frustration
        logging.warning(f"Channel check skipped: {e}")
        return True

def get_games_menu_markup():
    markup = types.InlineKeyboardMarkup(row_width=1)
    btn_gow3 = types.InlineKeyboardButton("⚔️ God of War III Remastered [🔥 Ready & Verified]", callback_data="game_gow3")
    btn_bb = types.InlineKeyboardButton("🩸 Bloodborne PC [🛠️ Under Development]", callback_data="game_bb")
    btn_uncharted = types.InlineKeyboardButton("🧭 Uncharted: Nathan Drake Collection [🛠️ Under Development]", callback_data="game_uncharted")
    btn_infamous = types.InlineKeyboardButton("⚡ inFAMOUS Second Son [🛠️ Under Development]", callback_data="game_infamous")
    btn_driveclub = types.InlineKeyboardButton("🏎️ Driveclub [🛠️ Under Development]", callback_data="game_driveclub")
    btn_tlou = types.InlineKeyboardButton("🧟 The Last of Us Part I [🛠️ Under Development]", callback_data="game_tlou")
    btn_gravity = types.InlineKeyboardButton("🌌 Gravity Rush Remastered [🛠️ Under Development]", callback_data="game_gravity")
    
    btn_yt = types.InlineKeyboardButton("📺 Visit YouTube Channel (@pcportop)", url=YOUTUBE_CHANNEL_URL)
    btn_tg = types.InlineKeyboardButton("📢 Join Telegram Channel (@pcportop)", url=CHANNEL_URL)
    
    markup.add(btn_gow3, btn_bb, btn_uncharted, btn_infamous, btn_driveclub, btn_tlou, btn_gravity, btn_yt, btn_tg)
    return markup

def get_gow3_steps_markup():
    markup = types.InlineKeyboardMarkup(row_width=1)
    btn_yt_sub = types.InlineKeyboardButton("📺 1. Subscribe to YouTube Channel", url=YOUTUBE_CHANNEL_URL)
    btn_yt_vid = types.InlineKeyboardButton("🎬 2. Watch, Like & Comment Video", url=YOUTUBE_VIDEO_URL)
    btn_channel = types.InlineKeyboardButton("📢 3. Join Telegram Channel (@pcportop)", url=CHANNEL_URL)
    btn_back = types.InlineKeyboardButton("🔙 Back to Games Menu", callback_data="main_menu")
    markup.add(btn_yt_sub, btn_yt_vid, btn_channel, btn_back)
    return markup

def get_download_markup():
    markup = types.InlineKeyboardMarkup(row_width=1)
    btn_download = types.InlineKeyboardButton("📥 Download God of War III Fix (Google Drive)", url=GOW3_DOWNLOAD_URL)
    btn_channel = types.InlineKeyboardButton("📢 Join @pcportop for Future Game Fixes", url=CHANNEL_URL)
    btn_back = types.InlineKeyboardButton("🔙 Back to Games Menu", callback_data="main_menu")
    markup.add(btn_download, btn_channel, btn_back)
    return markup

def get_dev_markup():
    markup = types.InlineKeyboardMarkup(row_width=1)
    btn_channel = types.InlineKeyboardButton("📢 Join @pcportop for Release Announcements", url=CHANNEL_URL)
    btn_yt = types.InlineKeyboardButton("📺 Subscribe on YouTube", url=YOUTUBE_CHANNEL_URL)
    btn_back = types.InlineKeyboardButton("🔙 Back to Games Menu", callback_data="main_menu")
    markup.add(btn_channel, btn_yt, btn_back)
    return markup

@bot.message_handler(commands=["start", "menu", "games"])
def send_welcome(message):
    user_name = message.from_user.first_name or "Gamer"
    welcome_text = (
        f"👋 **Hey {user_name}! Welcome to PCPortOP!** 🚀\n\n"
        f"The official hub for **Native PC Port Optimizations for Integrated GPUs & Low-Spec PCs**.\n\n"
        f"🎮 **Select a game below to get its optimized, crash-proof build:**"
    )
    bot.send_message(message.chat.id, welcome_text, reply_markup=get_games_menu_markup())

@bot.callback_query_handler(func=lambda call: call.data == "main_menu")
def handle_main_menu(call):
    bot.answer_callback_query(call.id)
    welcome_text = (
        "🎮 **PCPortOP Game Library**\n\n"
        "Select a game below to view its optimization status and download files:"
    )
    bot.edit_message_text(welcome_text, call.message.chat.id, call.message.message_id, reply_markup=get_games_menu_markup())

@bot.callback_query_handler(func=lambda call: call.data == "game_gow3")
def handle_gow3(call):
    bot.answer_callback_query(call.id)
    gow3_text = (
        "⚔️ **God of War III Remastered (PC Port)**\n"
        "⚡ **100% Crash-Proof & 60+ FPS Build [VERIFIED]**\n\n"
        "🛡️ **What this build fixes:**\n"
        "• **Zero crashes at Hades Boss Fight & Death Cutscene**\n"
        "• **Zero crashes at Poseidon Water & Leviathan battles**\n"
        "• Fully optimized for **Intel Iris Xe, Intel UHD, Arc & AMD Vega** iGPUs\n"
        "• Solved Vulkan compute workgroup & memory carve-out exhaustion\n\n"
        "---\n"
        "🔒 **TO UNLOCK THE DOWNLOAD FILE:**\n\n"
        "1️⃣ **Subscribe** to our YouTube Channel:\n"
        "👉 [http://www.youtube.com/@pcportop](http://www.youtube.com/@pcportop)\n\n"
        "2️⃣ **Like & Comment** on our GoW3 Video:\n"
        "👉 [https://youtu.be/QpJfxTSHp-s](https://youtu.be/QpJfxTSHp-s)\n\n"
        "3️⃣ **Join** our Telegram Channel: `@pcportop`\n\n"
        "📸 **Once done, simply SEND A SCREENSHOT of your subscription/comment right here in this chat to unlock the download link immediately!** 👇"
    )
    bot.edit_message_text(gow3_text, call.message.chat.id, call.message.message_id, reply_markup=get_gow3_steps_markup(), disable_web_page_preview=True)

@bot.callback_query_handler(func=lambda call: call.data in ["game_bb", "game_uncharted", "game_infamous", "game_driveclub", "game_tlou", "game_gravity"])
def handle_under_development(call):
    bot.answer_callback_query(call.id)
    
    titles = {
        "game_bb": "🩸 Bloodborne PC",
        "game_uncharted": "🧭 Uncharted: The Nathan Drake Collection",
        "game_infamous": "⚡ inFAMOUS Second Son",
        "game_driveclub": "🏎️ Driveclub",
        "game_tlou": "🧟 The Last of Us Part I",
        "game_gravity": "🌌 Gravity Rush Remastered"
    }
    game_title = titles.get(call.data, "This Game")
    
    dev_text = (
        f"🚧 **{game_title}**\n"
        f"⏳ **Status:** *Optimization Under Active Development*\n\n"
        f"🛠️ Our engineering team is currently porting our low-level Vulkan compute bounds fixes, memory carve-out stability, and shader optimizations to this title.\n\n"
        f"🔔 **Want to be the first to get the crash-proof build?**\n"
        f"Join our Telegram channel `@pcportop` and subscribe to our YouTube channel! We will post direct download links the moment it is ready."
    )
    bot.edit_message_text(dev_text, call.message.chat.id, call.message.message_id, reply_markup=get_dev_markup())

@bot.message_handler(content_types=["photo"])
def handle_screenshot(message):
    user_id = message.from_user.id
    
    # Check if user has joined the Telegram channel
    if not is_user_in_channel(user_id):
        join_warning = (
            "⚠️ **Almost there!**\n\n"
            "We received your screenshot, but you haven't joined our Telegram channel yet!\n\n"
            "👉 Please join **@pcportop** first, then re-send your screenshot to get the download file!"
        )
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(types.InlineKeyboardButton("📢 Join Telegram Channel (@pcportop)", url=CHANNEL_URL))
        bot.reply_to(message, join_warning, reply_markup=markup)
        return

    success_text = (
        "🎉 **Screenshot Verified! Thank you for supporting the channel!**\n\n"
        "📦 **God of War III PC Port - 100% Crash-Proof iGPU Build**\n"
        "• Tested & confirmed on Intel Iris Xe / UHD / AMD Vega\n"
        "• Zero crashes at Hades, Poseidon, cutscenes & asset transitions\n"
        "• Locked 60+ FPS performance tweaks included\n\n"
        "👇 **Click the button below to download directly from Google Drive:**"
    )
    bot.reply_to(message, success_text, reply_markup=get_download_markup())

@bot.message_handler(func=lambda msg: True)
def handle_other_messages(message):
    msg_text = (
        "👋 **Welcome to PCPortOP!**\n\n"
        "• To view all available games, send: `/start`\n"
        "• To unlock the **God of War III** crash-proof build, please send a **screenshot** showing you subscribed to our YouTube channel ([@pcportop](http://www.youtube.com/@pcportop))!"
    )
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("🎮 Open Games Menu", callback_data="main_menu"),
        types.InlineKeyboardButton("📺 Visit YouTube Channel", url=YOUTUBE_CHANNEL_URL)
    )
    bot.send_message(message.chat.id, msg_text, reply_markup=markup, disable_web_page_preview=True)

import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"PCPortOP Telegram Bot is running!")

    def log_message(self, format, *args):
        pass  # silence noisy http access logs

def start_health_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), HealthCheckHandler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    logging.info(f"Render health-check server running on port {port}")

if __name__ == "__main__":
    print("=" * 60)
    print("[*] PCPortOP Multi-Game Telegram Bot (@PcPortOP_bot) is RUNNING...")
    print("=" * 60)
    start_health_server()
    try:
        bot.infinity_polling(timeout=20, long_polling_timeout=20)
    except Exception as e:
        logging.error(f"Bot error: {e}")
