import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters
)
from telegram.request import HTTPXRequest

from config import BOT_TOKEN, WEBHOOK_URL, PORT
import tools

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# User ka current photo + mode store
user_data_store = {}

# ---------- /start ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 *Welcome to All Photo Tools Bot!* 🛠️\n\n"
        "📸 Mujhe koi bhi photo bhej!\n"
        "Main tumhe 12+ tools dunga.\n\n"
        "_Powered by AI_ ⚡",
        parse_mode="Markdown"
    )

# ---------- Photo receive ----------
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    photo = update.message.photo[-1]
    file = await photo.get_file()
    image_bytes = await file.download_as_bytearray()

    user_data_store[user_id] = {"image": bytes(image_bytes)}

    keyboard = [
        [InlineKeyboardButton("🖼️ BG Remove", callback_data="bg_remove"),
         InlineKeyboardButton("🎨 BG White/Blue/Red", callback_data="bg_color")],
        [InlineKeyboardButton("🪪 Passport Photo", callback_data="passport"),
         InlineKeyboardButton("💧 Watermark", callback_data="watermark")],
        [InlineKeyboardButton("✨ HD Upscale 2x", callback_data="upscale"),
         InlineKeyboardButton("🔤 Text Nikalo (OCR)", callback_data="ocr")],
        [InlineKeyboardButton("📐 Custom Size", callback_data="custom_size"),
         InlineKeyboardButton("⚡ Quick Resize", callback_data="quick_resize")],
        [InlineKeyboardButton("📄 PDF Banao", callback_data="pdf"),
         InlineKeyboardButton("🔲 Insta Grid (9 Parts)", callback_data="grid")],
        [InlineKeyboardButton("🔄 JPG | Rotate", callback_data="rotate")],
        [InlineKeyboardButton("📝 AI Caption", callback_data="caption")],
    ]
    await update.message.reply_text(
        "📸 Photo mil gaya! Feature select karo:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ---------- Button Handler ----------
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
        # ---------- Quick Resize ----------
        if data == "quick_resize":
            result = tools.quick_resize(img, 0.5)
            await query.message.reply_document(
                document=result, filename="quick_resize.jpg",
                caption="⚡ 50% Quick Resize Done!"
            )

        # ---------- Rotate ----------
        elif data == "rotate":
            result = tools.rotate_image(img, 90)
            await query.message.reply_document(
                document=result, filename="rotated.jpg",
                caption="🔄 90° Rotate Done!"
            )

        # ---------- JPG ----------
        elif data == "jpg":
            result = tools.to_jpg(img)
            await query.message.reply_document(
                document=result, filename="converted.jpg",
                caption="✅ JPG Convert Done!"
            )

        # ---------- PDF ----------
        elif data == "pdf":
            result = tools.to_pdf(img)
            await query.message.reply_document(
                document=result, filename="output.pdf",
                caption="📄 PDF Banaya!"
            )

        # ---------- Grid ----------
        elif data == "grid":
            parts = tools.insta_grid(img)
            for i, part in enumerate(parts, 1):
                await query.message.reply_document(
                    document=part, filename=f"grid_{i}.jpg"
                )
            await query.message.reply_text("🔲 9 Parts Grid Ready!")

        # ---------- Watermark ----------
        elif data == "watermark":
            result = tools.add_watermark(img, "© AllPhotoTools")
            await query.message.reply_document(
                document=result, filename="watermark.jpg",
                caption="💧 Watermark Lagaya!"
            )

        # ---------- Custom Size ----------
        elif data == "custom_size":
            user_data_store[user_id]["awaiting"] = "custom_size"
            await query.message.reply_text(
                "📐 Width x Height bhej (jaise: `800x600`)",
                parse_mode="Markdown"
            )

        # ---------- Baaki features (Phase 2) ----------
        else:
            await query.message.reply_text(
                f"🚧 Ye feature jald aa raha hai: *{data}*",
                parse_mode="Markdown"
            )

    except Exception as e:
        logger.error(f"Error: {e}")
        await query.message.reply_text(f"❌ Error: {e}")

# ---------- Text Handler (Custom Size ke liye) ----------
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.strip()

    if user_id in user_data_store and user_data_store[user_id].get("awaiting") == "custom_size":
        try:
            w, h = text.lower().split("x")
            w, h = int(w.strip()), int(h.strip())
            img = user_data_store[user_id]["image"]
            result = tools.resize_image(img, w, h)
            user_data_store[user_id]["awaiting"] = None
            await update.message.reply_document(
                document=result, filename=f"resized_{w}x{h}.jpg",
                caption=f"📐 {w}x{h} Resize Done!"
            )
        except Exception as e:
            await update.message.reply_text("❌ Format galat! `800x600` aise bhej.")
