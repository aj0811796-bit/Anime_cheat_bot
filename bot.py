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

TOKEN = "8645355488:AAGncQJCay8CjRcDLUd9gOSAuH337swNOnE"

API_URL = "https://axbweb-46106131f4b2.herokuapp.com/waifus"

hash_db = []

# ---------------- API LOAD ----------------

def get_hash(url):
    try:
        res = requests.get(url, timeout=10)
        img = Image.open(BytesIO(res.content)).convert("RGB")
        return imagehash.phash(img)
    except:
        return None


def load_database():
    print("🔄 Fetching API database...")

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

    print("✅ Database ready:", len(hash_db))


# ---------------- MATCH SYSTEM ----------------

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


# ---------------- COMMANDS ----------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 Anime Cheat Bot Ready!\n\n"
        "Reply /waifu to image\n"
        "or send image directly"
    )


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Commands:\n"
        "/waifu (reply to image)\n"
        "/name (reply to image)\n"
        ".name (reply to image)\n\n"
        "or just send image"
    )


# ---------------- IMAGE PROCESS ----------------

async def detect_character(image_bytes):
    img = Image.open(BytesIO(image_bytes)).convert("RGB")
    target_hash = imagehash.phash(img)

    return find_match(target_hash)


async def process_image(update, context, photo):

    file = await context.bot.get_file(photo.file_id)
    file_bytes = await file.download_as_bytearray()

    result = await detect_character(file_bytes)

    if result:
        await update.message.reply_text(
            f"🎭 {result['name']}\n📺 {result['anime']}"
        )
    else:
        await update.message.reply_text("❌ Character not found")


# ---------------- COMMAND HANDLERS ----------------

async def waifu_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.message.reply_to_message and update.message.reply_to_message.photo:

        photo = update.message.reply_to_message.photo[-1]
        await process_image(update, context, photo)

    else:
        await update.message.reply_text("Reply to an image.")


async def name_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.message.reply_to_message and update.message.reply_to_message.photo:

        photo = update.message.reply_to_message.photo[-1]
        await process_image(update, context, photo)

    else:
        await update.message.reply_text("Reply to image.")


# ---------------- DIRECT IMAGE ----------------

async def handle_image(update: Update, context: ContextTypes.DEFAULT_TYPE):

    photo = update.message.photo[-1]
    await process_image(update, context, photo)


# ---------------- TEXT COMMAND (.name) ----------------

async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = update.message.text.lower()

    if text == ".name":

        if update.message.reply_to_message and update.message.reply_to_message.photo:

            photo = update.message.reply_to_message.photo[-1]
            await process_image(update, context, photo)


# ---------------- MAIN ----------------

load_database()

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("help", help_cmd))
app.add_handler(CommandHandler("waifu", waifu_cmd))
app.add_handler(CommandHandler("name", name_cmd))

app.add_handler(MessageHandler(filters.PHOTO, handle_image))
app.add_handler(MessageHandler(filters.TEXT, text_handler))

print("🚀 Bot running...")

app.run_polling()
