import os
import logging
from contextlib import asynccontextmanager
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

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
WEBHOOK_URL = os.environ.get("WEBHOOK_URL", "").strip().rstrip("/")
PORT = int(os.environ.get("PORT", 8080))

if not BOT_TOKEN:
    raise ValueError("❌ TELEGRAM_BOT_TOKEN missing!")
if not WEBHOOK_URL:
    raise ValueError("❌ WEBHOOK_URL missing!")

WEBHOOK_PATH = "/webhook"

# Telegram App
ptb_app = Application.builder().token(BOT_TOKEN).updater(None).build()


# ---------- Handlers ----------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Welcome to *All Photo Tools Bot*!\n\n"
        "📸 Mujhe koi bhi photo bhejo, phir feature select karo.",
        parse_mode="Markdown"
    )


async def photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
    await update.message.reply_text(
        "📸 Photo mil gaya! Feature select karo:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    feature = query.data
    photo_id = context.user_data.get("photo_id")

    if not photo_id:
        await query.edit_message_text("❌ Pehle photo bhejo bhai!")
        return

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


# Register Handlers
ptb_app.add_handler(CommandHandler("start", start))
ptb_app.add_handler(MessageHandler(filters.PHOTO, photo_handler))
ptb_app.add_handler(CallbackQueryHandler(button_handler))


# ---------- Lifespan (FastAPI new way) ----------

@asynccontextmanager
async def lifespan(app: FastAPI):
    await ptb_app.initialize()
    await ptb_app.bot.set_webhook(
        url=f"{WEBHOOK_URL}{WEBHOOK_PATH}",
        drop_pending_updates=True
    )
    logger.info(f"✅ Webhook set: {WEBHOOK_URL}{WEBHOOK_PATH}")
    logger.info("🚀 Bot is LIVE!")
    yield
    await ptb_app.bot.delete_webhook()
    await ptb_app.shutdown()
    logger.info("🛑 Bot stopped.")


app = FastAPI(lifespan=lifespan)


# ---------- Routes ----------

@app.post(WEBHOOK_PATH)
async def webhook(request: Request):
    data = await request.json()
    update = Update.de_json(data, ptb_app.bot)
    await ptb_app.process_update(update)
    return Response(status_code=200)


@app.get("/")
async def health():
    return {"status": "ok", "bot": "running"}


# ---------- Run Server ----------

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT)
