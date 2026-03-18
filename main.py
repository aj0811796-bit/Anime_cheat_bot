import requests
from PIL import Image
import imagehash
from io import BytesIO
import logging

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes
)

# Enable logging
logging.basicConfig(level=logging.INFO)

# --- SETTINGS ---
TOKEN = "8443836199:AAFL0I4sWrl-tL59ejQmCQcW-uNbrEuSFKo"
API_URL = "https://axbweb-46106131f4b2.herokuapp.com/waifus"

hash_db = []

def get_hash(url):
    try:
        res = requests.get(url, timeout=10)
        img = Image.open(BytesIO(res.content)).convert("RGB")
        return imagehash.phash(img)
    except:
        return None

def load_database():
    print("🔄 Fetching API database...")
    try:
        res = requests.get(API_URL)
        data = res.json()
        for char in data:
            h = get_hash(char["image"])
            if h:
                hash_db.append({
                    "hash": h,
                    "name": char["name"],
                    "anime": char["anime"]
                })
        print(f"✅ Database ready: {len(hash_db)}")
    except Exception as e:
        print(f"❌ Error loading DB: {e}")

def find_match(target_hash):
    best = None
    min_diff = 100
    for item in hash_db:
        diff = target_hash - item["hash"]
        if diff < min_diff:
            min_diff = diff
            best = item
    if min_diff < 10:
        return best
    return None

# --- COMMANDS ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # This gets the name of the person who clicked start
    user_name = update.effective_user.first_name
    
    keyboard = [
        [InlineKeyboardButton("SUPPORT CHANNEL ↗️", url="https://t.me/your_channel")],
        [InlineKeyboardButton("UPDATE GROUP ↗️", url="https://t.me/your_group")],
        [InlineKeyboardButton("DEVELOPER ↗️", url="https://t.me/EGOIST_6969")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Personalized start message
    start_text = (
        f"📊 `{user_name}`\n"  # This puts the user's name at the top in monospace
        f"HEY {user_name.upper()} 👋\n\n"
        "**WELCOME TO ANIME CHEAT BOT**\n\n"
        "I CAN HELP YOU FIND\n"
        "ANIME WAIFU & CHARACTER NAMES FROM\n"
        "IMAGES.\n"
        "__________________________\n\n"
        "**COMMANDS**\n\n"
        "`/waifu` → REPLY TO ANIME IMAGE\n"
        "`/name`  → GET CHARACTER NAME\n"
        "**OR SEND AN IMAGE DIRECTLY**\n"
        "__________________________\n\n"
        "**FAST • ANIME • POWERED ⚡**"
    )

    await update.message.reply_text(
        start_text,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def process_image(update, context, photo):
    file = await context.bot.get_file(photo.file_id)
    file_bytes = await file.download_as_bytearray()
    img = Image.open(BytesIO(file_bytes)).convert("RGB")
    target_hash = imagehash.phash(img)
    result = find_match(target_hash)

    if result:
        await update.message.reply_text(
            f"🎭 **Name:** `{result['name']}`\n📺 **Anime:** `{result['anime']}`",
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text("❌ Character not found.")

async def waifu_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.reply_to_message and update.message.reply_to_message.photo:
        await process_image(update, context, update.message.reply_to_message.photo[-1])
    else:
        await update.message.reply_text("Reply to an image with /waifu.")

async def handle_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await process_image(update, context, update.message.photo[-1])

# --- MAIN ---

if __name__ == '__main__':
    load_database()
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("waifu", waifu_cmd))
    app.add_handler(CommandHandler("name", waifu_cmd))
    app.add_handler(MessageHandler(filters.PHOTO, handle_image))
    
    app.run_polling()
