import os
import logging
from fastapi import FastAPI, Request, Response
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
RAILWAY_URL = os.environ.get("RAILWAY_URL")  # e.g. https://your-app.up.railway.app
WEBHOOK_PATH = f"/webhook/{BOT_TOKEN}"

app = FastAPI()
ptb_app = Application.builder().token(BOT_TOKEN).build()


# ---------- Handlers ----------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Welcome to *All Photo Tools Bot*!\n\n"
        "📸 Mujhe koi bhi photo bhejo, phir feature select karo.",
        parse_mode="Markdown"
    )


async def photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Save file_id for later use
    photo = update.message.photo[-1]
    context.user_data["photo_id"] = photo.file_id

    keyboard = [
        [InlineKeyboardButton("🖼️ BG Remove", callback_data="bg_remove"),
         InlineKeyboardButton("✨ HD Upscale 2x", callback_data="upscale")],
        [InlineKeyboardButton("🔤 Text Nikalo (OCR)", callback_data="ocr"),
         InlineKeyboardButton("📝 AI Caption", callback_data="caption")],
        [InlineKeyboardButton("🔄 Rotate", callback_data="rotate"),
         InlineKeyboardButton("📐 Quick Resize", callback_data="resize")],
        [InlineKeyboardButton("📄 PDF Banao", callback_data="pdf"),
         InlineKeyboardButton("🔲 Insta Grid", callback_data="grid")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "📸 Photo mil gaya! Feature select karo:",
        reply_markup=reply_markup
    )


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    feature = query.data
    photo_id = context.user_data.get("photo_id")

    if not photo_id:
        await query.edit_message_text("❌ Pehle photo bhejo bhai!")
        return

    # Phase 1: placeholder responses
    feature_names = {
        "bg_remove": "🖼️ BG Remove",
        "upscale": "✨ HD Upscale 2x",
        "ocr": "🔤 Text Nikalo (OCR)",
        "caption": "📝 AI Caption",
        "rotate": "🔄 Rotate",
        "resize": "📐 Quick Resize",
        "pdf": "📄 PDF Banao",
        "grid": "🔲 Insta Grid",
    }
    name = feature_names.get(feature, feature)

    await query.edit_message_text(
        f"✅ *{name}* select kiya!\n\n"
        f"⏳ Ye feature Phase 2 me add hoga. Abhi base bot ready hai.",
        parse_mode="Markdown"
    )


# ---------- Register Handlers ----------

ptb_app.add_handler(CommandHandler("start", start))
ptb_app.add_handler(MessageHandler(filters.PHOTO, photo_handler))
ptb_app.add_handler(CallbackQueryHandler(button_handler))


# ---------- FastAPI Routes ----------

@app.on_event("startup")
async def on_startup():
    await ptb_app.initialize()
    await ptb_app.bot.set_webhook(url=f"{RAILWAY_URL}{WEBHOOK_PATH}")
    await ptb_app.start()
    logger.info("Webhook set: %s%s", RAILWAY_URL, WEBHOOK_PATH)


@app.on_event("shutdown")
async def on_shutdown():
    await ptb_app.stop()
    await ptb_app.shutdown()


@app.post(WEBHOOK_PATH)
async def webhook(request: Request):
    data = await request.json()
    update = Update.de_json(data, ptb_app.bot)
    await ptb_app.process_update(update)
    return Response(status_code=200)


@app.get("/")
async def health():
    return {"status": "ok", "bot": "running"}
