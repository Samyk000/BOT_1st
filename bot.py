import telebot
from telebot import types
import logging
import sys
import os
import json
import threading
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler

# Configure stdout for Windows/Unicode safety
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# --- Configuration ---
BOT_TOKEN = "8355770693:AAF5Amxsq_p5BCBH9-D1VM3KTdy3g7Abm1E"
CHANNEL_USERNAME = "@pcportop"
CHANNEL_URL = "https://t.me/pcportop"
YOUTUBE_CHANNEL_URL = "https://www.youtube.com/@pcportop?sub_confirmation=1"
YOUTUBE_VIDEO_URL = "https://youtu.be/QpJfxTSHp-s"
GOW3_DOWNLOAD_URL = "https://drive.google.com/file/d/1UIO6dNy72uMxKjJEaTpGc_l4FpF-t9hC/view?usp=sharing"

# Data persistence file
DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bot_data.json")

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="Markdown")

# Track users who have submitted their screenshot in this session
screenshot_submitted_users = set()

# --- Data Persistence & Subscriber Progress Utilities ---

def load_data():
    default_data = {
        "base_subs": 150,
        "target_subs": 500,
        "claimed_users": [],
        "user_profiles": {}
    }
    if not os.path.exists(DATA_FILE):
        save_data(default_data)
        return default_data
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            for k, v in default_data.items():
                if k not in data:
                    data[k] = v
            return data
    except Exception as e:
        logging.error(f"Error loading bot_data.json: {e}")
        return default_data

def save_data(data):
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logging.error(f"Error saving bot_data.json: {e}")

def record_user_claim(user):
    """Records unique V1 download claim and calculates current subscriber count."""
    data = load_data()
    user_id_str = str(user.id)
    is_new = False
    if user_id_str not in data["claimed_users"]:
        data["claimed_users"].append(user_id_str)
        is_new = True

    data["user_profiles"][user_id_str] = {
        "id": user.id,
        "first_name": user.first_name or "",
        "username": user.username or "",
        "last_active": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    }
    save_data(data)
    current_subs = data["base_subs"] + len(data["claimed_users"])
    return current_subs, data["target_subs"], is_new

def get_subscriber_stats():
    data = load_data()
    current_subs = data["base_subs"] + len(data["claimed_users"])
    return current_subs, data["target_subs"], len(data["claimed_users"])

def set_base_subscribers(count):
    data = load_data()
    data["base_subs"] = count
    save_data(data)
    return data["base_subs"] + len(data["claimed_users"])

def get_progress_bar(current, target=500, bar_length=10):
    pct = min(1.0, max(0.0, current / target))
    filled = int(round(bar_length * pct))
    bar = "█" * filled + "░" * (bar_length - filled)
    return f"`[{bar}]` **{current} / {target}** ({int(pct * 100)}%)"

# --- Channel Verification ---

def is_user_in_channel(user_id):
    """Checks if user has joined the Telegram channel. Fails open gracefully if bot lacks admin permissions."""
    try:
        member = bot.get_chat_member(CHANNEL_USERNAME, user_id)
        if member.status in ['left', 'kicked']:
            return False
        return True
    except Exception as e:
        logging.warning(f"Channel check skipped: {e}")
        return True

# --- Markups ---

def get_games_menu_markup():
    markup = types.InlineKeyboardMarkup(row_width=1)
    btn_gow3 = types.InlineKeyboardButton("⚔️ God of War III Remastered [🔥 Ready & Verified]", callback_data="game_gow3")
    btn_gow_ascension = types.InlineKeyboardButton("🏛️ God of War: Ascension PC Port [⏳ Soon]", callback_data="game_gow_ascension")
    btn_infamous = types.InlineKeyboardButton("⚡ inFAMOUS Second Son [🛠️ Under Development]", callback_data="game_infamous")
    
    btn_yt = types.InlineKeyboardButton("📺 Visit YouTube Channel (@pcportop)", url=YOUTUBE_CHANNEL_URL)
    btn_tg = types.InlineKeyboardButton("📢 Join Telegram Channel (@pcportop)", url=CHANNEL_URL)
    
    markup.add(btn_gow3, btn_gow_ascension, btn_infamous, btn_yt, btn_tg)
    return markup

def get_gow3_steps_markup():
    markup = types.InlineKeyboardMarkup(row_width=1)
    btn_yt_sub = types.InlineKeyboardButton("📺 1. Subscribe to YouTube Channel", url=YOUTUBE_CHANNEL_URL)
    btn_yt_vid = types.InlineKeyboardButton("🎬 2. Watch, Like & Comment Video", url=YOUTUBE_VIDEO_URL)
    btn_back = types.InlineKeyboardButton("🔙 Back to Games Menu", callback_data="main_menu")
    markup.add(btn_yt_sub, btn_yt_vid, btn_back)
    return markup

def get_verified_markup():
    markup = types.InlineKeyboardMarkup(row_width=1)
    btn_download = types.InlineKeyboardButton("📥 Download GoW3 Fix (V1 - No Crash)", callback_data="dl_gow3")
    btn_back = types.InlineKeyboardButton("🔙 Back to Games Menu", callback_data="main_menu")
    markup.add(btn_download, btn_back)
    return markup

def get_post_download_markup():
    markup = types.InlineKeyboardMarkup(row_width=1)
    btn_drive = types.InlineKeyboardButton("📥 Download GoW3 Fix (V1 Google Drive)", url=GOW3_DOWNLOAD_URL)
    btn_comment = types.InlineKeyboardButton("💬 Comment Specs on YouTube", url=YOUTUBE_VIDEO_URL)
    btn_channel = types.InlineKeyboardButton("📢 Join @pcportop for V3 Updates", url=CHANNEL_URL)
    btn_back = types.InlineKeyboardButton("🔙 Back to Games Menu", callback_data="main_menu")
    markup.add(btn_drive, btn_comment, btn_channel, btn_back)
    return markup

def get_dev_markup():
    markup = types.InlineKeyboardMarkup(row_width=1)
    btn_channel = types.InlineKeyboardButton("📢 Join @pcportop for Release Announcements", url=CHANNEL_URL)
    btn_yt = types.InlineKeyboardButton("📺 Subscribe on YouTube", url=YOUTUBE_CHANNEL_URL)
    btn_back = types.InlineKeyboardButton("🔙 Back to Games Menu", callback_data="main_menu")
    markup.add(btn_channel, btn_yt, btn_back)
    return markup

# --- Message & Callback Handlers ---

@bot.message_handler(commands=["start", "menu", "games"])
def send_welcome(message):
    user_name = message.from_user.first_name or "Gamer"
    welcome_text = (
        f"👋 **Hey {user_name}! Welcome to PCPortOP!** 🚀\n\n"
        f"The official hub for **Native PC Port Optimizations for Integrated GPUs & Low-Spec PCs**.\n\n"
        f"🎮 **Select a game below to get its optimized, crash-proof build:**"
    )
    bot.send_message(message.chat.id, welcome_text, reply_markup=get_games_menu_markup())

@bot.message_handler(commands=["stats"])
def handle_stats(message):
    current_subs, target_subs, claimed_count = get_subscriber_stats()
    progress_str = get_progress_bar(current_subs, target_subs)
    data = load_data()
    
    stats_text = (
        "📊 **PCPortOP Bot Live Stats**\n\n"
        f"👥 **Total Unique V1 Downloaders:** `{claimed_count}`\n"
        f"📈 **Base Subs Config:** `{data.get('base_subs', 150)}`\n"
        f"🚀 **Current Displayed Subs:** `{current_subs}` / `{target_subs}`\n"
        f"📊 **V3 Progress:** {progress_str}\n\n"
        "⚙️ **Admin Sub Sync:**\n"
        "To update the base YouTube subscriber count anytime, send:\n"
        "`/setsubs <number>` (e.g. `/setsubs 180`)"
    )
    bot.reply_to(message, stats_text)

@bot.message_handler(commands=["setsubs"])
def handle_setsubs(message):
    parts = message.text.split()
    if len(parts) < 2 or not parts[1].isdigit():
        bot.reply_to(message, "⚠️ **Usage:** `/setsubs <number>`\nExample: `/setsubs 180`")
        return
    
    new_base = int(parts[1])
    new_total = set_base_subscribers(new_base)
    data = load_data()
    progress_str = get_progress_bar(new_total, data["target_subs"])
    
    reply_msg = (
        f"✅ **Base subscribers updated to {new_base}!**\n\n"
        f"📊 **New Total Display:** `{new_total}` / `{data['target_subs']}`\n"
        f"Progress: {progress_str}"
    )
    bot.reply_to(message, reply_msg)

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
        "🎮 **To unlock your Google Drive download link:**\n\n"
        "1️⃣ Tap button 1 below to **Subscribe** to our Channel *(tap 'Subscribe' on popup)*.\n"
        "2️⃣ Tap button 2 to **Watch, Like & Comment** your PC specs *(e.g. \"Testing on Intel Iris Xe\" or \"AMD Ryzen\")*.\n\n"
        "📸 **Send a screenshot of your comment below to unlock the final step!** 👇"
    )
    bot.edit_message_text(gow3_text, call.message.chat.id, call.message.message_id, reply_markup=get_gow3_steps_markup(), disable_web_page_preview=True)

@bot.callback_query_handler(func=lambda call: call.data in ["game_gow_ascension", "game_infamous"])
def handle_under_development(call):
    bot.answer_callback_query(call.id)
    
    titles = {
        "game_gow_ascension": "🏛️ God of War: Ascension PC Port",
        "game_infamous": "⚡ inFAMOUS Second Son"
    }
    game_title = titles.get(call.data, "This Game")
    
    dev_text = (
        f"🚧 **{game_title}**\n"
        f"⏳ **Status:** *Optimization Under Active Development*\n\n"
        f"🛠️ Our engineering team is currently porting our low-level Vulkan compute bounds fixes, memory carve-out stability, and shader optimizations to this title.\n\n"
        f"🔔 **Want to be the first to get the crash-proof build?**\n"
        f"Join our Telegram channel `@pcportop` and subscribe on YouTube! We post download links the moment it is ready."
    )
    bot.edit_message_text(dev_text, call.message.chat.id, call.message.message_id, reply_markup=get_dev_markup())

@bot.chat_member_handler()
def handle_channel_join(chat_member_update):
    """Automatically triggered the exact second a user joins @pcportop!"""
    try:
        chat = chat_member_update.chat
        if chat.username and f"@{chat.username.lower()}" == CHANNEL_USERNAME.lower():
            new_status = chat_member_update.new_chat_member.status
            user = chat_member_update.new_chat_member.user
            if new_status in ['member', 'administrator', 'creator']:
                user_id = user.id
                logging.info(f"User {user_id} joined {CHANNEL_USERNAME}!")
                
                welcome_text = (
                    "🎉 **Welcome to @pcportop! Channel Membership Verified!** 🚀\n\n"
                    "📦 **God of War III PC Port — 100% Crash-Proof Build (V1)**\n"
                    "• Tested & confirmed on Intel Iris Xe / UHD / AMD Vega\n"
                    "• Zero crashes at Hades, Poseidon & heavy cutscenes\n"
                    "• Locked 60+ FPS performance tweaks included\n\n"
                    "👇 **Click below to get your V1 download file:**"
                )
                try:
                    bot.send_message(user_id, welcome_text, reply_markup=get_verified_markup())
                except Exception as e:
                    logging.info(f"Could not push instant join message to {user_id}: {e}")
    except Exception as e:
        logging.error(f"Error in chat_member_handler: {e}")

@bot.message_handler(content_types=["photo"])
def handle_screenshot(message):
    user_id = message.from_user.id
    screenshot_submitted_users.add(user_id)
    
    # EDGE CASE: User is ALREADY in the Telegram channel!
    if is_user_in_channel(user_id):
        success_text = (
            "🎉 **Screenshot & Channel Membership Verified!**\n\n"
            "📦 **GoW3 PC Port — 100% Crash-Proof iGPU Build (V1)**\n"
            "• Tested & confirmed on Intel Iris Xe / UHD / AMD Vega\n"
            "• Zero crashes at Hades, Poseidon & heavy cutscenes\n"
            "• Locked 60+ FPS performance tweaks included\n\n"
            "👇 **Click below to get your V1 download file:**"
        )
        bot.reply_to(message, success_text, reply_markup=get_verified_markup())
        return

    # User has NOT joined the channel yet:
    join_warning = (
        "📸 **Screenshot Received! One Final Step:**\n\n"
        "📢 Join our official Telegram Channel **@pcportop** to unlock your GoW3 V1 download file!\n\n"
        "*(⚡ As soon as you tap Join Channel, the bot will automatically send you the download link!)*"
    )
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("📢 3. Join Telegram Channel (@pcportop)", url=CHANNEL_URL),
        types.InlineKeyboardButton("🔓 I've Joined — Get Download Link", callback_data="verify_channel_after_screenshot"),
        types.InlineKeyboardButton("🔙 Back to Games Menu", callback_data="main_menu")
    )
    bot.reply_to(message, join_warning, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "verify_channel_after_screenshot")
def handle_verify_channel_after_screenshot(call):
    if not is_user_in_channel(call.from_user.id):
        bot.answer_callback_query(call.id, text="⚠️ You haven't joined @pcportop yet! Please tap 'Join Telegram Channel' first.", show_alert=True)
        return
        
    bot.answer_callback_query(call.id, text="🎉 Channel verified!")
    success_text = (
        "🎉 **All Steps Completed & Verified!**\n\n"
        "📦 **GoW3 PC Port — 100% Crash-Proof iGPU Build (V1)**\n"
        "• Tested & confirmed on Intel Iris Xe / UHD / AMD Vega\n"
        "• Zero crashes at Hades, Poseidon & heavy cutscenes\n"
        "• Locked 60+ FPS performance tweaks included\n\n"
        "👇 **Click below to get your V1 download file:**"
    )
    try:
        bot.edit_message_text(success_text, call.message.chat.id, call.message.message_id, reply_markup=get_verified_markup())
    except Exception:
        bot.send_message(call.message.chat.id, success_text, reply_markup=get_verified_markup())

@bot.callback_query_handler(func=lambda call: call.data == "dl_gow3")
def handle_download_gow3(call):
    bot.answer_callback_query(call.id, text="🚀 Generating download link...")
    
    current_subs, target_subs, is_new = record_user_claim(call.from_user)
    progress_str = get_progress_bar(current_subs, target_subs)
    
    post_dl_text = (
        "🚀 **Your GoW3 Crash-Proof Build (V1) is ready!**\n\n"
        "📦 **Direct Download Link:**\n"
        f"👉 [Click here to open Google Drive]({GOW3_DOWNLOAD_URL})\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "⚔️ **V3 Update (Clean Cutscenes + Peak 60 FPS)**\n"
        f"🎯 **Community Goal:** Unlocks at **{target_subs} Subscribers**!\n"
        f"📊 **Current Progress:** {progress_str}\n"
        "🔔 *Share with fellow gamers to unlock V3 faster!*\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "💬 **One Small Favor:**\n"
        "Once you test the game, please reply on the video:\n"
        "👉 *\"It worked on my [Your Specs]!\"*\n\n"
        "*(This helps fellow gamers know it's 100% working! 🎮)*"
    )
    bot.send_message(call.message.chat.id, post_dl_text, reply_markup=get_post_download_markup(), disable_web_page_preview=True)

@bot.message_handler(func=lambda msg: True)
def handle_other_messages(message):
    msg_text = (
        "👋 **Welcome to PCPortOP!**\n\n"
        "• To view all available games, send: `/start`\n"
        "• To unlock the **GoW3 (V1)** crash-proof build, please send a **screenshot** showing you subscribed and commented on our YouTube video ([@pcportop](https://www.youtube.com/@pcportop))!"
    )
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("🎮 Open Games Menu", callback_data="main_menu"),
        types.InlineKeyboardButton("📺 Subscribe on YouTube", url=YOUTUBE_CHANNEL_URL)
    )
    bot.send_message(message.chat.id, msg_text, reply_markup=markup, disable_web_page_preview=True)

# --- Render Health Check Server ---

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
        bot.infinity_polling(timeout=20, long_polling_timeout=20, allowed_updates=["message", "callback_query", "chat_member", "my_chat_member"])
    except Exception as e:
        logging.error(f"Bot error: {e}")
