import requests
from PIL import Image
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

# --- CONFIGURATION ---
TOKEN = "8443836199:AAFL0I4sWrl-tL59ejQmCQcW-uNbrEuSFKo"
# We use SauceNAO as the "Search Engine" to get the text answer
SAUCENAO_URL = "https://saucenao.com/search.php?db=999&output_type=2&numres=1&url="

# ---------------- SEARCH ENGINE ----------------

async def auto_search_web(image_url):
    """
    This function acts like a 'Google Search' in the background.
    It sends the image to a global AI and returns the text result.
    """
    try:
        # Search the web for this specific image
        res = requests.get(f"{SAUCENAO_URL}{image_url}", timeout=15)
        data = res.json()
        
        if data and "results" in data and len(data["results"]) > 0:
            result = data["results"][0]
            # Extract the specific character and anime names
            char_name = result["data"].get("character") or result["data"].get("title") or "Unknown"
            anime_source = result["data"].get("source") or "Anime/Fanart"
            confidence = result["header"].get("similarity", "0")
            
            return {
                "name": char_name,
                "anime": anime_source,
                "confidence": confidence
            }
    except Exception as e:
        print(f"Search Error: {e}")
    return None

# ---------------- COMMANDS ----------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_name = update.effective_user.first_name
    
    keyboard = [
        [InlineKeyboardButton("📢 UPDATES", url="https://t.me/your_channel")],
        [InlineKeyboardButton("👤 DEVELOPER", url="https://t.me/aj0811796-bit")]
    ]
    
    start_text = (
        f"📊 `{user_name.upper()}`\n\n"
        "**ALPHA X AUTO-SEARCH AI** 🤖\n"
        "__________________________\n\n"
        "I DON'T NEED A DATABASE.\n"
        "SEND ME ANY ANIME IMAGE OR FAN-ART,\n"
        "AND I WILL SEARCH THE WEB FOR YOU!\n"
        "__________________________\n\n"
        "**JUST SEND THE PHOTO TO START**"
    )
    await update.message.reply_text(
        start_text, 
        reply_markup=InlineKeyboardMarkup(keyboard), 
        parse_mode='Markdown'
    )

async def handle_image_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Support both direct photos and replies
    msg = update.message if update.message.photo else update.message.reply_to_message
    if not msg or not msg.photo:
        return

    # Use the highest quality version of the photo
    photo = msg.photo[-1]
    status_msg = await update.message.reply_text("📡 `SEARCHING GLOBAL WEB...`", parse_mode='Markdown')

    # 1. Get the direct image path from Telegram
    file = await context.bot.get_file(photo.file_id)
    image_url = file.file_path

    # 2. Perform the Background Search
    result = await auto_search_web(image_url)

    if result and float(result['confidence']) > 55:
        # 3. Deliver the text answer directly
        response = (
            f"✅ **CHARACTER IDENTIFIED**\n"
            f"__________________________\n\n"
            f"👤 **NAME:** `{result['name']}`\n"
            f"📺 **ANIME:** `{result['anime']}`\n\n"
            f"📈 **MATCH:** `{result['confidence']}%` Accuracy\n"
            f"__________________________\n\n"
            f"💡 *Tap name to copy instantly!*"
        )
        await status_msg.edit_text(response, parse_mode='Markdown')
    else:
        await status_msg.edit_text("❌ `SORRY, NO MATCH FOUND ON THE WEB.`", parse_mode='Markdown')

# ---------------- RUN BOT ----------------

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO, handle_image_search))
    app.add_handler(CommandHandler("waifu", handle_image_search))
    app.add_handler(CommandHandler("name", handle_image_search))
    
    print("🚀 Auto-Search Bot is LIVE on StackHost!")
    app.run_polling()
