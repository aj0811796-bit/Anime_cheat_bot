import json
import requests
from PIL import Image
import imagehash
from io import BytesIO

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes
)

TOKEN = "PASTE_YOUR_BOT_TOKEN_HERE"

# Load database
with open("database.json", "r", encoding="utf-8") as f:
    db = json.load(f)

hash_db = []

def get_hash(url):
    try:
        res = requests.get(url, timeout=10)
        img = Image.open(BytesIO(res.content)).convert("RGB")
        return imagehash.phash(img)
    except:
        return None

print("🔄 Processing database images...")

for char in db:
    h = get_hash(char["image"])
    if h:
        hash_db.append({
            "hash": h,
            "name": char["name"],
            "anime": char["anime"]
        })

print("✅ Database ready:", len(hash_db))


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


# 🔹 START COMMAND
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 Anime Cheat Bot Ready!\n\n"
        "📸 Send or reply to an image\n"
        "I will detect the character 🔥"
    )


# 🔹 HELP COMMAND
async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📖 Commands:\n"
        "/start - Start bot\n"
        "/help - Help menu\n\n"
        "📸 Just send or reply to image to cheat 😈"
    )


# 🔹 IMAGE HANDLER (MAIN CHEAT)
async def handle_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo = update.message.photo[-1]

    file = await context.bot.get_file(photo.file_id)
    file_bytes = await file.download_as_bytearray()

    img = Image.open(BytesIO(file_bytes)).convert("RGB")
    target_hash = imagehash.phash(img)

    result = find_match(target_hash)

    if result:
        await update.message.reply_text(
            f"🎭 {result['name']}\n📺 {result['anime']}"
        )
    else:
        await update.message.reply_text("❌ Character not found")


# 🔹 MAIN
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("help", help_cmd))
app.add_handler(MessageHandler(filters.PHOTO, handle_image))

print("🚀 Bot is running...")
app.run_polling()
