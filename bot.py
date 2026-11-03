import telebot
from telebot import types
import logging
import sys
import os
import json
import re
import threading
import urllib.request
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
YOUTUBE_VIDEO_URL = "https://www.youtube.com/watch?v=RRTnew63j48"
GOW3_DOWNLOAD_URL = "https://drive.google.com/file/d/1bDTWecK6uI9tkWlIuS3tnZaHYDOgH6r6/view?usp=sharing"
GOW3_V4_DOWNLOAD_URL = "https://drive.google.com/file/d/105NH1hQgfnUr1GhIMOix2NkNLAKidYf1/view?usp=sharing"

SECRET_SALT = "PCPortOP_Demo_Secret_2026"
HWID_REGEX = re.compile(r"^GOW3-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}$", re.IGNORECASE)

# Data persistence file
DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bot_data.json")

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="Markdown")

# Session caches
screenshot_submitted_users = set()


# --- Cryptographic Key Engine ---

def fnv1a64(text: str) -> int:
    hash_val = 14695981039346656037
    for b in text.encode("utf-8"):
        hash_val ^= b
        hash_val = (hash_val * 1099511628211) & 0xFFFFFFFFFFFFFFFF
    return hash_val

def generate_key_for_hwid(hwid: str) -> str:
    clean_hwid = hwid.strip().upper()
    combined = f"{clean_hwid}:{SECRET_SALT}"
    h = fnv1a64(combined)
    k1 = (h >> 16) & 0xFFFF
    k2 = h & 0xFFFF
    return f"ACT-{k1:04X}-{k2:04X}"

# --- Upstash Serverless Redis Integration (Cloud DB - Survives all redeploys) ---
UPSTASH_REDIS_REST_URL = os.environ.get("UPSTASH_REDIS_REST_URL", "https://up-gobbler-246694.upstash.io")
UPSTASH_REDIS_REST_TOKEN = os.environ.get("UPSTASH_REDIS_REST_TOKEN", "gQAAAAAAA8OmAAIgcDJiMTFmNjczYzZiZDk0YTljOTQ1MGU5ZmE3MDI2MzY1MQ")

def redis_cmd(*args):
    """Executes a command against Upstash Redis via its REST API (zero pip dependencies)."""
    if not UPSTASH_REDIS_REST_URL or not UPSTASH_REDIS_REST_TOKEN:
        return None
    try:
        req = urllib.request.Request(
            UPSTASH_REDIS_REST_URL,
            data=json.dumps(args).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {UPSTASH_REDIS_REST_TOKEN}",
                "Content-Type": "application/json"
            }
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        logging.warning(f"Upstash Redis request warning: {e}")
        return None

# --- Data Persistence & Subscriber Progress Utilities ---

def load_data():
    default_data = {
        "base_subs": 150,
        "target_subs": 500,
        "claimed_users": [],
        "user_profiles": {},
        "activations": {},
        "verified_proof_users": [],
        "sub_bell_verified_users": [],
        "comment_verified_users": [],
        "pending_hwid_requests": {}
    }
    # 1. Try loading from Upstash Redis (Permanent Cloud DB)
    res = redis_cmd("GET", "pcportop_bot_data")
    if res and res.get("result"):
        try:
            data = json.loads(res["result"])
            for k, v in default_data.items():
                if k not in data:
                    data[k] = v
            return data
        except Exception as e:
            logging.error(f"Error parsing Upstash data: {e}")

    # 2. Fallback to local file cache
    if os.path.exists(DATA_FILE):
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
    # 1. Save to Upstash Redis (Cloud DB - persists permanently across restarts & deployments)
    try:
        json_str = json.dumps(data, ensure_ascii=False)
        redis_cmd("SET", "pcportop_bot_data", json_str)
    except Exception as e:
        logging.error(f"Error saving to Upstash Redis: {e}")

    # 2. Also keep local disk copy as fallback cache
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logging.error(f"Error saving local bot_data.json: {e}")

# --- Verification State Helpers (Sunk Cost Split Verification) ---

def mark_user_sub_bell_verified(user_id: int):
    data = load_data()
    if "sub_bell_verified_users" not in data:
        data["sub_bell_verified_users"] = []
    user_id_str = str(user_id)
    if user_id_str not in data["sub_bell_verified_users"]:
        data["sub_bell_verified_users"].append(user_id_str)
        save_data(data)

def is_user_sub_bell_verified(user_id: int) -> bool:
    data = load_data()
    user_id_str = str(user_id)
    return (user_id_str in data.get("sub_bell_verified_users", []) or 
            user_id_str in data.get("verified_proof_users", []))

def mark_user_comment_verified(user_id: int):
    data = load_data()
    if "comment_verified_users" not in data:
        data["comment_verified_users"] = []
    user_id_str = str(user_id)
    if user_id_str not in data["comment_verified_users"]:
        data["comment_verified_users"].append(user_id_str)
        save_data(data)

def is_user_comment_verified(user_id: int) -> bool:
    data = load_data()
    user_id_str = str(user_id)
    if user_id_str in data.get("comment_verified_users", []):
        return True
    if user_id_str in data.get("activations", {}):
        return True
    return False

def set_pending_hwid(user_id: int, hwid: str):
    data = load_data()
    if "pending_hwid_requests" not in data:
        data["pending_hwid_requests"] = {}
    data["pending_hwid_requests"][str(user_id)] = hwid
    save_data(data)

def get_pending_hwid(user_id: int) -> str:
    data = load_data()
    return data.get("pending_hwid_requests", {}).get(str(user_id))

def clear_pending_hwid(user_id: int):
    data = load_data()
    if "pending_hwid_requests" in data and str(user_id) in data["pending_hwid_requests"]:
        del data["pending_hwid_requests"][str(user_id)]
        save_data(data)

def mark_user_proof_verified(user_id: int):
    mark_user_sub_bell_verified(user_id)

def is_user_proof_verified(user_id: int) -> bool:
    return is_user_sub_bell_verified(user_id)

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

def record_activation_key(user, hwid: str, key: str):
    """Records key generation. Returns (success, key, status)"""
    data = load_data()
    if "activations" not in data:
        data["activations"] = {}
    
    user_id_str = str(user.id)
    if user_id_str not in data["activations"]:
        data["activations"][user_id_str] = {
            "username": user.username or "",
            "first_name": user.first_name or "",
            "devices": {}
        }
    
    user_record = data["activations"][user_id_str]
    clean_hwid = hwid.strip().upper()
    
    # Check if already activated for this exact HWID
    if clean_hwid in user_record["devices"]:
        return True, user_record["devices"][clean_hwid]["key"], "existing"
    
    # Rate limiting: Max 2 devices per Telegram user
    if len(user_record["devices"]) >= 2:
        return False, None, "limit_reached"
    
    # Record new device key
    user_record["devices"][clean_hwid] = {
        "key": key,
        "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    }
    save_data(data)
    return True, key, "new"

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
    btn_yt_sub = types.InlineKeyboardButton("📺 1. Subscribe & Turn On Bell (🔔)", url=YOUTUBE_CHANNEL_URL)
    btn_tg = types.InlineKeyboardButton("📢 2. Join Telegram Channel (@pcportop)", url=CHANNEL_URL)
    btn_back = types.InlineKeyboardButton("🔙 Back to Games Menu", callback_data="main_menu")
    markup.add(btn_yt_sub, btn_tg, btn_back)
    return markup

def get_verified_markup():
    markup = types.InlineKeyboardMarkup(row_width=1)
    btn_v4 = types.InlineKeyboardButton("⚡ Download GoW3 (V4 - 2X FPS & Low-End/iGPU Boost)", callback_data="gow3_v4_info")
    btn_v1 = types.InlineKeyboardButton("📥 Download GoW3 (V1 - No Crash)", callback_data="dl_gow3")
    btn_back = types.InlineKeyboardButton("🔙 Back to Games Menu", callback_data="main_menu")
    markup.add(btn_v4, btn_v1, btn_back)
    return markup

def get_post_download_markup():
    markup = types.InlineKeyboardMarkup(row_width=1)
    btn_drive = types.InlineKeyboardButton("📥 Open Google Drive (V1)", url=GOW3_DOWNLOAD_URL)
    btn_comment = types.InlineKeyboardButton("💬 Comment Specs on YouTube", url=YOUTUBE_VIDEO_URL)
    btn_back = types.InlineKeyboardButton("🔙 Back to Games Menu", callback_data="main_menu")
    markup.add(btn_drive, btn_comment, btn_back)
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
    
    activations_dict = data.get("activations", {})
    total_keys = sum(len(u.get("devices", {})) for u in activations_dict.values())
    total_active_users = len(activations_dict)
    sub_bell_count = len(data.get("sub_bell_verified_users", [])) + len(data.get("verified_proof_users", []))
    comment_count = len(data.get("comment_verified_users", []))
    
    stats_text = (
        "📊 **PCPortOP Bot Live Stats**\n\n"
        f"👥 **Unique V1 Downloaders:** `{claimed_count}`\n"
        f"🔔 **Sub+Bell Verified (Gate 1):** `{sub_bell_count}`\n"
        f"💬 **Comment Verified (Gate 2):** `{comment_count}`\n"
        f"🔑 **V4 Keys Issued:** `{total_keys}` (across `{total_active_users}` users)\n"
        f"📈 **Base Subs Config:** `{data.get('base_subs', 150)}`\n"
        f"🚀 **Current Displayed Subs:** `{current_subs}` / `{target_subs}`\n"
        f"📊 **V4 Progress:** {progress_str}\n\n"
        "⚙️ **Admin Quick Sync:**\n"
        "To update the base YouTube subscriber count, send:\n"
        "`/setsubs <number>` (e.g. `/setsubs 215`)"
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
        "1️⃣ Tap button 1 below to **Subscribe** & turn notification bell to **'All' (🔔)**.\n"
        "2️⃣ Tap button 2 to **Join** our Telegram updates channel.\n\n"
        "📸 **Send a screenshot showing you Subscribed with Bell set to All (🔔) right here to unlock the download!** 👇"
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
                
                # Check if this user had a pending HWID request and was comment verified
                pending_hwid = get_pending_hwid(user_id)
                if pending_hwid and is_user_comment_verified(user_id):
                    clear_pending_hwid(user_id)
                    key = generate_key_for_hwid(pending_hwid)
                    success, final_key, status = record_activation_key(user, pending_hwid, key)
                    if success:
                        key_text = (
                            "🎉 **Channel Joined & Verified!** 🚀\n\n"
                            "⚔️ **God of War III (V4) — Activation Key**\n\n"
                            f"🖥️ **Machine Code:** `{pending_hwid}`\n"
                            f"🔑 **Your Key:** `{final_key}` *(Tap to copy)*\n\n"
                            "📋 **How to activate:**\n"
                            "1. Rename file to **`spartanport-probe.exe`** inside game's **`bin`** folder.\n"
                            "2. Paste key into activation window.\n"
                            "3. Click **\"⚔️ UNLOCK & LAUNCH GAME\"**."
                        )
                        bot.send_message(user_id, key_text)
                        return

                welcome_text = (
                    "🎉 **Verification Successful!** 🚀\n\n"
                    "⚔️ **God of War III PC Port**\n"
                    "• 100% Crash-Proof on Intel & AMD integrated graphics.\n\n"
                    "👇 **Choose your build to download:**"
                )
                try:
                    bot.send_message(user_id, welcome_text, reply_markup=get_verified_markup())
                except Exception as e:
                    logging.info(f"Could not push instant join message to {user_id}: {e}")
    except Exception as e:
        logging.error(f"Error in chat_member_handler: {e}")

@bot.message_handler(content_types=["photo"])
def handle_screenshot(message):
    user = message.from_user
    user_id = user.id
    
    # Check if this user had a pending HWID waiting for comment proof (Gate 2)
    pending_hwid = get_pending_hwid(user_id)
    if pending_hwid:
        mark_user_comment_verified(user_id)
        clear_pending_hwid(user_id)
        
        # Check channel membership
        if not is_user_in_channel(user_id):
            join_warning = (
                "📸 **Specs Comment Screenshot Received! One Final Step:**\n\n"
                "📢 Join our official Telegram Channel **@pcportop** to receive your activation key!\n\n"
                "*(⚡ As soon as you tap Join Channel, the bot will automatically issue your key!)*"
            )
            markup = types.InlineKeyboardMarkup(row_width=1)
            markup.add(
                types.InlineKeyboardButton("📢 Join Telegram Channel (@pcportop)", url=CHANNEL_URL),
                types.InlineKeyboardButton("🔓 I've Joined — Get Activation Key", callback_data="verify_channel_after_screenshot"),
                types.InlineKeyboardButton("🔙 Back to Games Menu", callback_data="main_menu")
            )
            bot.reply_to(message, join_warning, reply_markup=markup)
            return

        key = generate_key_for_hwid(pending_hwid)
        success, final_key, status = record_activation_key(user, pending_hwid, key)
        if success:
            key_text = (
                "🎉 **Specs Comment Verified & Approved!** 🚀\n\n"
                "⚔️ **God of War III (V4) — Activation Key**\n\n"
                f"🖥️ **Machine Code:** `{pending_hwid}`\n"
                f"🔑 **Your Key:** `{final_key}` *(Tap to copy)*\n\n"
                "📋 **How to activate:**\n"
                "1. Ensure the file is renamed to **`spartanport-probe.exe`** inside your game's **`bin`** folder.\n"
                "2. Paste this key into the activation window.\n"
                "3. Click **\"⚔️ UNLOCK & LAUNCH GAME\"**.\n\n"
                "🎮 *Thank you for supporting @Samyyyyyk and PCPortOP! Enjoy smooth 60 FPS gameplay!*"
            )
            bot.reply_to(message, key_text)
            return
        elif status == "limit_reached":
            bot.reply_to(message, "⚠️ **Activation Limit Reached:** Each Telegram user can activate up to 2 PCs.")
            return

    # No pending HWID request: This is Gate 1 (Subscribe + Bell Notification)
    mark_user_sub_bell_verified(user_id)
    
    # Check if user is already in channel
    if is_user_in_channel(user_id):
        success_text = (
            "🎉 **Subscription Verified!** 🚀\n\n"
            "⚔️ **God of War III PC Port**\n"
            "• 100% Crash-Proof on Intel & AMD integrated graphics.\n\n"
            "💡 *Once you launch the game, copy your **Machine Code** (`GOW3-XXXX-XXXX`) and send it here to get your activation key!*\n\n"
            "📥 **Choose your build to download:**"
        )
        bot.reply_to(message, success_text, reply_markup=get_verified_markup())
        return

    # User has NOT joined the channel yet:
    join_warning = (
        "📸 **Subscription Screenshot Received! One Final Step:**\n\n"
        "📢 Join our official Telegram Channel **@pcportop** to unlock your GoW3 download!\n\n"
        "*(⚡ As soon as you tap Join Channel, the bot will automatically send you the download options!)*"
    )
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("📢 Join Telegram Channel (@pcportop)", url=CHANNEL_URL),
        types.InlineKeyboardButton("🔓 I've Joined — Get Downloads", callback_data="verify_channel_after_screenshot"),
        types.InlineKeyboardButton("🔙 Back to Games Menu", callback_data="main_menu")
    )
    bot.reply_to(message, join_warning, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "verify_channel_after_screenshot")
def handle_verify_channel_after_screenshot(call):
    user = call.from_user
    user_id = user.id
    if not is_user_in_channel(user_id):
        bot.answer_callback_query(call.id, text="⚠️ You haven't joined @pcportop yet! Please tap 'Join Telegram Channel' first.", show_alert=True)
        return
        
    bot.answer_callback_query(call.id, text="🎉 Channel verified!")
    
    # Check if they had a pending HWID request and were comment verified
    pending_hwid = get_pending_hwid(user_id)
    if pending_hwid and is_user_comment_verified(user_id):
        clear_pending_hwid(user_id)
        key = generate_key_for_hwid(pending_hwid)
        success, final_key, status = record_activation_key(user, pending_hwid, key)
        if success:
            key_text = (
                "🎉 **Channel Joined & Verified!** 🚀\n\n"
                "⚔️ **God of War III (V4) — Activation Key**\n\n"
                f"🖥️ **Machine Code:** `{pending_hwid}`\n"
                f"🔑 **Your Key:** `{final_key}` *(Tap to copy)*\n\n"
                "📋 **How to activate:**\n"
                "1. Ensure the file is renamed to **`spartanport-probe.exe`** inside your game's **`bin`** folder.\n"
                "2. Paste this key into the activation window.\n"
                "3. Click **\"⚔️ UNLOCK & LAUNCH GAME\"**.\n\n"
                "🎮 *Thank you for supporting @Samyyyyyk and PCPortOP! Enjoy smooth 60 FPS gameplay!*"
            )
            bot.send_message(call.message.chat.id, key_text)
            return

    success_text = (
        "🎉 **Verification Successful!** 🚀\n\n"
        "⚔️ **God of War III PC Port**\n"
        "• 100% Crash-Proof on Intel & AMD integrated graphics.\n\n"
        "👇 **Choose your build to download:**"
    )
    try:
        bot.edit_message_text(success_text, call.message.chat.id, call.message.message_id, reply_markup=get_verified_markup())
    except Exception:
        bot.send_message(call.message.chat.id, success_text, reply_markup=get_verified_markup())

@bot.callback_query_handler(func=lambda call: call.data in ["gow3_v4_info", "gow3_v3_info"])
def handle_gow3_v4_info(call):
    bot.answer_callback_query(call.id)
    current_subs, target_subs, _ = get_subscriber_stats()
    progress_str = get_progress_bar(current_subs, target_subs)
    
    v4_text = (
        "⚡ **God of War III — V4 Community Master Build**\n"
        "*(🔥 2X Performance on Intel & AMD Integrated GPUs + Anti-Overheating Thermal Lock)*\n\n"
        "✨ **What's New in V4:**\n"
        "• **2X More Optimized:** Auto-detects Intel Iris / Iris Xe / UHD & AMD Vega / Radeon APUs.\n"
        "• **Smart 720p Quality FSR 3.1 Scaling:** Cuts pixel load by 55% for buttery-smooth 50–60 FPS.\n"
        "• **Laptop Anti-Overheating Lock:** Auto-paces tick rate to prevent CPU thermal throttling & lag spikes.\n"
        "• **Zero Ghosting & Smooth Motion:** Preserves smooth camera & object motion vectors across all cutscenes.\n\n"
        "📦 **Download V4 Build:**\n"
        f"👉 [Click here to open Google Drive]({GOW3_V4_DOWNLOAD_URL})\n\n"
        "⚠️ **INSTALLATION INSTRUCTIONS:**\n"
        "1. Rename the downloaded file to: **`spartanport-probe.exe`**\n"
        "2. Paste & replace it inside your game's **`bin`** folder.\n"
        "3. Launch the game, copy your **Machine Code** (`GOW3-XXXX-XXXX`), and send it here to get your permanent activation key!\n\n"
        f"📊 **Milestone Progress:** {progress_str}"
    )
    markup = types.InlineKeyboardMarkup(row_width=1)
    btn_dl_v4 = types.InlineKeyboardButton("📥 Download V4 (Google Drive)", url=GOW3_V4_DOWNLOAD_URL)
    btn_v1 = types.InlineKeyboardButton("📥 Download V1 Legacy Build", callback_data="dl_gow3")
    btn_yt = types.InlineKeyboardButton("📺 Subscribe on YouTube", url=YOUTUBE_CHANNEL_URL)
    btn_back = types.InlineKeyboardButton("🔙 Back to Games Menu", callback_data="main_menu")
    markup.add(btn_dl_v4, btn_v1, btn_yt, btn_back)
    
    bot.edit_message_text(v4_text, call.message.chat.id, call.message.message_id, reply_markup=markup, disable_web_page_preview=True)

@bot.callback_query_handler(func=lambda call: call.data == "dl_gow3")
def handle_download_gow3(call):
    bot.answer_callback_query(call.id, text="🚀 Generating download link...")
    
    record_user_claim(call.from_user)
    
    post_dl_text = (
        "🚀 **Your GoW3 Crash-Proof Build (V1) is ready!**\n\n"
        f"📦 **[Click here to open Google Drive]({GOW3_DOWNLOAD_URL})**\n\n"
        "⚠️ **Instructions:**\n"
        "1. Rename downloaded file to: **`spartanport-probe.exe`**\n"
        "2. Paste & replace inside your game's **`bin`** folder.\n"
        "3. Launch game -> copy your **Machine Code** (`GOW3-XXXX-XXXX`) -> send it here in chat to get your permanent Activation Key!\n\n"
        "💬 *After testing, please leave a comment on the video with your PC specs! 🎮*"
    )
    bot.send_message(call.message.chat.id, post_dl_text, reply_markup=get_post_download_markup(), disable_web_page_preview=True)

# --- HWID Node-Lock Activation Handler ---

@bot.message_handler(func=lambda msg: bool(msg.text and HWID_REGEX.match(msg.text.strip())))
def handle_hwid_code(message):
    raw_hwid = message.text.strip().upper()
    user = message.from_user
    user_id = user.id
    
    # 1. Verify channel membership first
    if not is_user_in_channel(user_id):
        join_msg = (
            "📢 **Join @pcportop to Get Your Key!**\n\n"
            "To unlock the **God of War III (V4)** community build, you must be a member of our official Telegram channel.\n\n"
            "👉 Tap below to join, then send your machine code again!"
        )
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(
            types.InlineKeyboardButton("📢 Join @pcportop", url=CHANNEL_URL)
        )
        bot.reply_to(message, join_msg, reply_markup=markup)
        return
    
    # 2. Check if user has verified comment proof (Gate 2)
    if not is_user_comment_verified(user_id):
        set_pending_hwid(user_id, raw_hwid)
        proof_msg = (
            "🔒 **Almost Done! Final Step to Unlock Your Key**\n\n"
            "To generate your permanent **God of War III (V4)** Activation Key:\n\n"
            "1️⃣ Tap button 1 below to open our YouTube video.\n"
            "2️⃣ **Like the video & Comment your PC specs** *(e.g. \"Testing on Intel Iris Xe / i5 11th Gen\" or \"AMD Ryzen 5600G\")*.\n"
            "3️⃣ **Send a screenshot of your comment right here in this chat!**\n\n"
            "📸 *The instant you send the screenshot, the bot will automatically deliver your activation key!*"
        )
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(
            types.InlineKeyboardButton("🎬 1. Watch, Like & Comment Specs", url=YOUTUBE_VIDEO_URL),
            types.InlineKeyboardButton("📢 Official Channel (@pcportop)", url=CHANNEL_URL)
        )
        bot.reply_to(message, proof_msg, reply_markup=markup, disable_web_page_preview=True)
        return

    # 3. User is comment-verified: Generate matching key
    key = generate_key_for_hwid(raw_hwid)
    success, final_key, status = record_activation_key(user, raw_hwid, key)
    
    if not success and status == "limit_reached":
        limit_msg = (
            "⚠️ **Activation Limit Reached**\n\n"
            "Each Telegram member can activate up to **2 PCs**.\n"
            "If you reinstalled Windows or need help, please reach out in @pcportop."
        )
        bot.reply_to(message, limit_msg)
        return
    
    # 4. Deliver activation key
    key_msg = (
        "⚔️ **God of War III (V4) — Activation Key**\n\n"
        f"🖥️ **Machine Code:** `{raw_hwid}`\n"
        f"🔑 **Your Key:** `{final_key}` *(Tap to copy)*\n\n"
        "🎮 **How to activate:**\n"
        "1. Ensure the file is renamed to **`spartanport-probe.exe`** inside your game's **`bin`** folder.\n"
        "2. Paste this key into the activation window.\n"
        "3. Click **\"⚔️ UNLOCK & LAUNCH GAME\"**.\n\n"
        "*(The game will be permanently unlocked on your PC!)*"
    )
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("📺 Subscribe on YouTube", url=YOUTUBE_CHANNEL_URL),
        types.InlineKeyboardButton("📢 Telegram Updates Channel", url=CHANNEL_URL)
    )
    bot.reply_to(message, key_msg, reply_markup=markup)

@bot.message_handler(func=lambda msg: True)
def handle_other_messages(message):
    msg_text = (
        "👋 **Welcome to PCPortOP!**\n\n"
        "• To view all available games, send: `/start`\n"
        "• To unlock **GoW3 downloads**, tap `/start` and send a **screenshot** showing you Subscribed with the bell icon on (🔔)!\n"
        "• To get a **V4 Activation Key**, simply send your Machine Code (e.g. `GOW3-XXXX-XXXX`)."
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
