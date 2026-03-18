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

# --- CONFIG ---
TOKEN = "8443836199:AAFL0I4sWrl-tL59ejQmCQcW-uNbrEuSFKo"
API_URL = "https://axbweb-46106131f4b2.herokuapp.com/waifus"
# SauceNAO API for backup (AI/Custom images)
SAUCENAO_URL = "https://saucenao.com/search.php?db=999&output_type=2&numres=1&url="

hash_db = []

# ---------------- DATABASE LOAD ----------------

def get_hash(url):
    try:
        res = requests.get(url, timeout=10)
        img = Image.open(BytesIO(res.content)).convert("RGB")
        return imagehash.phash(img)
    except:
        return None

def load_database():
    print("📊 Loading Friend's Database...")
    try:
        res = requests.get(API_URL)
        data = res.json()
        for char in data:
            h = get_hash(char["image"])
            if h:
                hash_db.append({"hash": h, "name": char["name"], "anime": char["anime"]})
        print(f"✅ Database ready: {len(hash_db)}")
    except Exception as e:
        print(f"❌ Error loading API: {e}")

# ---------------- SEARCH LOGIC ----------------

def find_in_db(target_hash):
    best = None
    min_diff = 100
    for item in hash_db:
        diff = target_hash - item["hash"]
        if diff < min_diff:
            min_diff = diff
            best = item
    return best if min_diff < 10 else None

async def search_backup_ai(image_url):
    try:
        res = requests.get(f"{SAUCENAO_URL}{image_url}")
        data = res.json()
        if data["results"]:
            result = data["results"][0]
            name = result["data"].get("character") or result["data"].get("title") or "Unknown"
            source = result["data"].get("source") or "Web/AI"
            return {"name": name, "anime": source, "method": "AI Guess 🤖"}
    except:
        return None
    return None

# ---------------- HANDLERS ----------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_name = update.effective_user.first_name
    keyboard = [
        [InlineKeyboardButton("SUPPORT CHANNEL ↗️", url="https://t.me/your_channel")],
        [InlineKeyboardButton("DEVELOPER ↗️", url="https://t.me/aj0811796-bit")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    start_text = (
        f"📊 `{user_name}`\n"
        f"HEY {user_name.upper()} 👋\n\n"
        "**HYBRID ANIME CHEAT BOT**\n\n"
        "I USE A PRIVATE API + AI SEARCH\n"
        "TO FIND ANY CHARACTER INSTANTLY.\n"
        "__________________________\n\n"
        "**COMMANDS**\n\n"
        "`/waifu` → FIND CHARACTER\n"
        "**OR SEND IMAGE DIRECTLY**\n"
        "__________________________\n\n"
        "**POWERED BY PRIVATE API & AI ⚡**"
    )
    await update.message.reply_text(start_text, reply_markup=reply_markup, parse_mode='Markdown')

async def process_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo = update.message.photo[-1] if update.message.photo else update.message.reply_to_message.photo[-1]
    status = await update.message.reply_text("Scanning databases... 🔍")

    # 1. Try Friend's API first (Local Hash)
    file = await context.bot.get_file(photo.file_id)
    file_bytes = await file.download_as_bytearray()
    img = Image.open(BytesIO(file_bytes)).convert("RGB")
    target_hash = imagehash.phash(img)

    match = find_in_db(target_hash)

    if match:
        await status.edit_text(
            f"🎯 **API MATCH FOUND!**\n\n"
            f"🎭 **Name:** `{match['name']}`\n"
            f"📺 **Anime:** `{match['anime']}`",
            parse_mode='Markdown'
        )
    else:
        # 2. If API fails, try AI Backup (SauceNAO)
        await status.edit_text("Not in API. Trying AI Search... 🌐")
        ai_match = await search_backup_ai(file.file_path)

        if ai_match:
            await status.edit_text(
                f"🤖 **AI GUESS (Backup):**\n\n"
                f"🎭 **Name:** `{ai_match['name']}`\n"
                f"📺 **Source:** `{ai_match['anime']}`",
                parse_mode='Markdown'
            )
        else:
            await status.edit_text("❌ Character not found in API or AI Database.")

# ---------------- MAIN ----------------

if __name__ == '__main__':
    load_database()
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("waifu", process_image))
    app.add_handler(CommandHandler("name", process_image))
    app.add_handler(MessageHandler(filters.PHOTO, process_image))
    
    print("🚀 Hybrid Bot is Running on StackHost!")
    app.run_polling()
