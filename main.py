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
# Global AI Search API
SAUCENAO_URL = "https://saucenao.com/search.php?db=999&output_type=2&numres=1&url="

hash_db = []

# ---------------- DATABASE LOAD ----------------

def get_hash(url):
    try:
        res = requests.get(url, timeout=5)
        img = Image.open(BytesIO(res.content)).convert("RGB")
        return imagehash.phash(img)
    except:
        return None

def load_database():
    print("🔄 Syncing with Friend's Database...")
    try:
        res = requests.get(API_URL, timeout=10)
        data = res.json()
        for char in data:
            # We use the provided image URL to create a local match map
            h = get_hash(char["image"])
            if h:
                hash_db.append({"hash": h, "name": char["name"], "anime": char["anime"]})
        print(f"✅ Private API Ready: {len(hash_db)} characters")
    except:
        print("⚠️ Private API Offline. Running in AI-ONLY mode.")

# ---------------- AI RECOGNITION ----------------

async def fetch_ai_guess(image_url):
    """This function searches the entire internet for the character name."""
    try:
        res = requests.get(f"{SAUCENAO_URL}{image_url}", timeout=10)
        data = res.json()
        if data["results"]:
            top = data["results"][0]
            return {
                "name": top["data"].get("character") or top["data"].get("title") or "Unknown",
                "source": top["data"].get("source") or "Anime/Fanart",
                "prob": top["header"]["similarity"]
            }
    except:
        return None

# ---------------- COMMANDS ----------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_name = update.effective_user.first_name
    
    keyboard = [
        [InlineKeyboardButton("📢 UPDATES", url="https://t.me/your_channel")],
        [InlineKeyboardButton("👨‍💻 DEVELOPER", url="https://t.me/aj0811796_bit")]
    ]
    
    start_text = (
        f"📊 `{user_name.upper()}`\n\n"
        "**ALPHA X UNIVERSAL AI** 🤖\n"
        "__________________________\n\n"
        "I can identify **ANY** character from\n"
        "**ANY** bot using Hybrid AI Search.\n\n"
        "🔹 **PRIVATE API:** Instant Match\n"
        "🔹 **GLOBAL AI:** Internet Search\n"
        "__________________________\n\n"
        "**SEND A PHOTO TO START**"
    )
    await update.message.reply_text(start_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

async def on_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Support both direct images and replies
    msg = update.message if update.message.photo else update.message.reply_to_message
    if not msg or not msg.photo: return
    
    photo = msg.photo[-1]
    status = await update.message.reply_text("📡 `SCANNING MULTI-VERSE...`")

    # Step 1: Download and Hash
    file = await context.bot.get_file(photo.file_id)
    file_bytes = await file.download_as_bytearray()
    img = Image.open(BytesIO(file_bytes)).convert("RGB")
    user_hash = imagehash.phash(img)

    # Step 2: Check Friend's API (Instant)
    match = None
    for item in hash_db:
        if (user_hash - item["hash"]) < 10:
            match = item
            break

    if match:
        await status.edit_text(
            f"✅ **DATABASE MATCH**\n"
            f"__________________________\n\n"
            f"👤 **NAME:** `{match['name']}`\n"
            f"📺 **ANIME:** `{match['anime']}`\n"
            f"__________________________\n"
            f"⚡ *Source: Private API*",
            parse_mode='Markdown'
        )
    else:
        # Step 3: Trigger AI Search (The "Cheat" for other bots)
        await status.edit_text("🔍 `NOT IN API. TRIGGERING GLOBAL AI...`")
        ai_res = await fetch_ai_guess(file.file_path)
        
        if ai_res and float(ai_res['prob']) > 60:
            await status.edit_text(
                f"🤖 **AI IDENTIFIED**\n"
                f"__________________________\n\n"
                f"👤 **NAME:** `{ai_res['name']}`\n"
                f"📺 **SOURCE:** `{ai_res['source']}`\n"
                f"📈 **CONFIDENCE:** `{ai_res['prob']}%`\n"
                f"__________________________\n"
                f"💡 *Tip: Tap name to copy*",
                parse_mode='Markdown'
            )
        else:
            await status.edit_text("❌ `CHARACTER UNKNOWN TO ALL SYSTEMS`")

# ---------------- MAIN ----------------

if __name__ == '__main__':
    load_database()
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO, on_image))
    app.add_handler(CommandHandler("waifu", on_image))
    
    print("🚀 Universal AI Bot is Active!")
    app.run_polling()
