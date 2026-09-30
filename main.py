import os
import logging
from io import BytesIO
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Response
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters
)

import tools

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
WEBHOOK_URL = os.environ.get("WEBHOOK_URL", "").strip().rstrip("/")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()
PORT = int(os.environ.get("PORT", 8080))

if not BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN missing!")
if not WEBHOOK_URL:
    raise ValueError("WEBHOOK_URL missing!")

WEBHOOK_PATH = "/webhook"

gemini_model = None
if GEMINI_API_KEY:
    try:
        import google.generativeai as genai
        genai.configure(api_key=GEMINI_API_KEY)
        gemini_model = genai.GenerativeModel("gemini-1.5-flash")
        logger.info("Gemini loaded")
    except Exception as e:
        logger.warning(f"Gemini init failed: {e}")

ptb_app = Application.builder().token(BOT_TOKEN).updater(None).build()
user_data_store = {}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Welcome to *All Photo Tools Bot!* 🛠️\n\n"
        "📸 Mujhe koi bhi photo bhej!\n"
        "Main tumhe 7 tools dunga.\n\n"
        "_Powered by AI_ ⚡",
        parse_mode="Markdown"
    )


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    photo = update.message.photo[-1]
    file = await photo.get_file()
    image_bytes = await file.download_as_bytearray()

    user_data_store[user_id] = {"image": bytes(image_bytes), "awaiting": None}

    keyboard = [
        [InlineKeyboardButton("🔤 Text Nikalo (OCR)", callback_data="ocr"),
         InlineKeyboardButton("📝 AI Caption", callback_data="caption")],
        [InlineKeyboardButton("🔄 Rotate", callback_data="rotate"),
         InlineKeyboardButton("📐 Quick Resize", callback_data="quick_resize")],
        [InlineKeyboardButton("📄 PDF Banao", callback_data="pdf"),
         InlineKeyboardButton("🔲 Insta Grid", callback_data="grid")],
        [InlineKeyboardButton("💧 Watermark", callback_data="watermark")],
        [InlineKeyboardButton("🖼️ BG Remove (soon)", callback_data="soon")],
    ]
    await update.message.reply_text(
        "📸 Photo mil gaya! Feature select karo:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    data = query.data

    if user_id not in user_data_store or "image" not in user_data_store[user_id]:
        await query.message.reply_text("❌ Pehle photo bhej bhai!")
        return

    img = user_data_store[user_id]["image"]

    try:
        if data == "quick_resize":
            result = tools.quick_resize(img, 0.5)
            await query.message.reply_document(
                document=result, filename="quick_resize.jpg",
                caption="⚡ 50% Quick Resize Done!"
            )

        elif data == "rotate":
            result = tools.rotate_image(img, 90)
            await query.message.reply_document(
                document=result, filename="rotated.jpg",
                caption="🔄 90° Rotate Done!"
            )

        elif data == "pdf":
            result = tools.to_pdf(img)
            await query.message.reply_document(
                document=result, filename="output.pdf",
                caption="📄 PDF Banaya!"
            )

        elif data == "grid":
            parts = tools.insta_grid(img)
            for i, part in enumerate(parts, 1):
                await query.message.reply_document(
                    document=part, filename=f"grid_{i}.jpg"
                )
            await query.message.reply_text("🔲 9 Parts Grid Ready!")

        elif data == "watermark":
            result = tools.add_watermark(img, "© PhotoBaba")
            await query.message.reply_document(
                document=result, filename="watermark.jpg",
                caption="💧 Watermark Lagaya!"
            )

        elif data == "ocr":
            if not gemini_model:
                await query.message.reply_text("❌ GEMINI_API_KEY set nahi hai!")
                return
            await query.message.reply_text("🔤 Text nikala ja raha hai...")
            from PIL import Image as PILImage
            pil_img = PILImage.open(BytesIO(img))
            response = gemini_model.generate_content([
                "Extract all text from this image. Return only the text.",
                pil_img
            ])
            text = response.text.strip() or "(Koi text nahi mila)"
            await query.message.reply_text(f"🔤 *Extracted Text:*\n\n{text}", parse_mode="Markdown")

        elif data == "caption":
            if not gemini_model:
                await query.message.reply_text("❌ GEMINI_API_KEY set nahi hai!")
                return
            await query.message.reply_text("📝 AI caption bana raha hai...")
            from PIL import Image as PILImage
            pil_img = PILImage.open(BytesIO(img))
            response = gemini_model.generate_content([
                "Write a short, catchy Instagram caption for this photo in Hinglish.",
                pil_img
            ])
            await query.message.reply_text(f"📝 *AI Caption:*\n\n{response.text.strip()}", parse_mode="Markdown")

        else:
            await query.message.reply_text("🚧 Ye feature jald aa raha hai!")

    except Exception as e:
        logger.error(f"Error: {e}")
        await query.message.reply_text(f"❌ Error: {str(e)[:200]}")


ptb_app.add_handler(CommandHandler("start", start))
ptb_app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
ptb_app.add_handler(CallbackQueryHandler(button_handler))


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


app = FastAPI(lifespan=lifespan)


@app.post(WEBHOOK_PATH)
async def webhook(request: Request):
    data = await request.json()
    update = Update.de_json(data, ptb_app.bot)
    await ptb_app.process_update(update)
    return Response(status_code=200)


@app.get("/")
async def health():
    return {"status": "ok", "bot": "running"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT)
