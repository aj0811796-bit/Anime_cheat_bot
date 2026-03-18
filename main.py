import requests
from PIL import Image
import imagehash
from io import BytesIO
import json
import os
import logging

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes
)

# --- SETTINGS ---
TOKEN = "8443836199:AAFL0I4sWrl-tL59ejQmCQcW-uNbrEuSFKo"
FRIEND_API = "https://axbweb-46106131f4b2.herokuapp.com/waifus"
DB_FILE = "local_db.json"

# Enable logging
logging.basicConfig(level=logging.INFO)

# Load Local Database
if os.path.exists(DB_FILE):
    with open(DB_FILE, "r") as f:
        local_memory = json.load(f)
else:
    local_memory = []

api_cache = []

# --- HELPERS ---

def save_local():
    with open(DB_FILE, "w") as f:
        json.dump(local_memory, f)

def get_hash_from_url(url):
    try:
        res = requests.get(url, timeout=5)
        img = Image.open(BytesIO(res.content)).convert("RGB")
        return str(imagehash.phash(img))
    except:
        return None

def load_friend_api():
    global api_cache
    print("🔄 Fetching Friend's API...")
    try:
        res = requests.get(FRIEND_API, timeout=10)
        data = res.json()
        for char in data:
            h = get_hash_from_url(char["image"])
            if h:
                api_cache.append({"hash": h, "name": char["name"], "anime": char["anime"]})
        print(f"✅ Friend API Loaded: {len(api_cache)}")
    except Exception as e:
        print(f"❌ Friend API Error: {e}")

# --- COMMANDS ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_name = update.effective_user.first_name
    
    keyboard = [
        [InlineKeyboardButton("SUPPORT CHANNEL ↗️", url="https://t.me/your_channel")],
        [InlineKeyboardButton("DEVELOPER ↗️", url="https://t.me/aj0811796_bit")]
    ]
    
    start_text = (
        f"📊 `{user_name.upper()}`\n"
        f"HEY {user_name.upper()} 👋\n\n"
        "**WELCOME TO ANIME CHEAT BOT**\n\n"
        "I CHECK MY FRIEND'S API AND YOUR\n"
        "PRIVATE DATABASE FOR MATCHES!\n"
        "__________________________\n\n"
        "**COMMANDS**\n\n"
        "`/waifu` → REPLY TO IMAGE\n"
        "`/add Name | Anime` → REPLY TO ADD\n"
        "__________________________\n\n"
        "**FAST • HYBRID • POWERED ⚡**"
    )
    await update.message.reply_text(start_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

async def add_character(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Only you or authorized users should use this
    if not update.message.reply_to_message or not update.message.reply_to_message.photo:
        await update.message.reply_text("❌ Reply to a photo with: `/add Name | Anime`")
        return

    try:
        raw_data = " ".join(context.args).split("|")
        name = raw_data[0].strip()
        anime = raw_data[1].strip()

        photo = update.message.reply_to_message.photo[-1]
        file = await context.bot.get_file(photo.file_id)
        
        # Hash the image
        img_data = await file.download_as_bytearray()
        img = Image.open(BytesIO(img_data)).convert("RGB")
        h = str(imagehash.phash(img))

        local_memory.append({"hash": h, "name": name, "anime": anime})
        save_local()
        await update.message.reply_text(f"✅ **ADDED TO LOCAL DB:** `{name}`")
    except:
        await update.message.reply_text("❌ Format: `/add Name | Anime` (Use the | symbol)")

async def identify(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message if update.message.photo else update.message.reply_to_message
    if not msg or not msg.photo: return

    photo = msg.photo[-1]
    file = await context.bot.get_file(photo.file_id)
    img_data = await file.download_as_bytearray()
    img = Image.open(BytesIO(img_data)).convert("RGB")
    user_hash = imagehash.phash(img)

    # Search Local First, then Friend API
    match = None
    all_data = local_memory + api_cache

    for item in all_data:
        diff = user_hash - imagehash.hex_to_hash(item["hash"])
        if diff < 10:
            match = item
            break

    if match:
        await update.message.reply_text(
            f"🎯 **MATCH FOUND!**\n\n🎭 **Name:** `{match['name']}`\n📺 **Anime:** `{match['anime']}`",
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text("❌ Not found in API or Local DB.")

# --- RUN ---

if __name__ == '__main__':
    load_friend_api()
    app = ApplicationBuilder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("add", add_character))
    app.add_handler(CommandHandler("waifu", identify))
    app.add_handler(MessageHandler(filters.PHOTO, identify))
    
    app.run_polling()
