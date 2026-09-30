from PIL import Image, ImageOps, ImageDraw, ImageFont
from io import BytesIO

# ---------- Resize ----------
def resize_image(image_bytes: bytes, width: int, height: int) -> bytes:
    img = Image.open(BytesIO(image_bytes)).convert("RGB")
    img = img.resize((width, height), Image.LANCZOS)
    out = BytesIO()
    img.save(out, format="JPEG", quality=92)
    return out.getvalue()

# ---------- Quick Resize (50%) ----------
def quick_resize(image_bytes: bytes, scale: float = 0.5) -> bytes:
    img = Image.open(BytesIO(image_bytes)).convert("RGB")
    w, h = img.size
    img = img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)
    out = BytesIO()
    img.save(out, format="JPEG", quality=92)
    return out.getvalue()

# ---------- Rotate ----------
def rotate_image(image_bytes: bytes, angle: int = 90) -> bytes:
    img = Image.open(BytesIO(image_bytes)).convert("RGB")
    img = img.rotate(-angle, expand=True)
    out = BytesIO()
    img.save(out, format="JPEG", quality=92)
    return out.getvalue()

# ---------- JPG Convert ----------
def to_jpg(image_bytes: bytes) -> bytes:
    img = Image.open(BytesIO(image_bytes)).convert("RGB")
    out = BytesIO()
    img.save(out, format="JPEG", quality=95)
    return out.getvalue()

# ---------- PDF Banao ----------
def to_pdf(image_bytes: bytes) -> bytes:
    img = Image.open(BytesIO(image_bytes)).convert("RGB")
    out = BytesIO()
    img.save(out, format="PDF")
    return out.getvalue()

# ---------- Insta Grid (3x3) ----------
def insta_grid(image_bytes: bytes):
    img = Image.open(BytesIO(image_bytes)).convert("RGB")
    size = max(img.size)
    square = Image.new("RGB", (size, size), (255, 255, 255))
    square.paste(img, ((size - img.width) // 2, (size - img.height) // 2))
    square = square.resize((900, 900), Image.LANCZOS)

    grid_size = 300
    parts = []
    for row in range(3):
        for col in range(3):
            box = (col * grid_size, row * grid_size,
                   (col + 1) * grid_size, (row + 1) * grid_size)
            part = square.crop(box)
            out = BytesIO()
            part.save(out, format="JPEG", quality=92)
            parts.append(out.getvalue())
    return parts

# ---------- Watermark ----------
def add_watermark(image_bytes: bytes, text: str = "© MyBot") -> bytes:
    img = Image.open(BytesIO(image_bytes)).convert("RGB")
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("arial.ttf", 40)
    except:
        font = ImageFont.load_default()

    w, h = img.size
    bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    x, y = w - tw - 20, h - th - 20

    draw.text((x + 2, y + 2), text, font=font, fill=(0, 0, 0))
    draw.text((x, y), text, font=font, fill=(255, 255, 255))

    out = BytesIO()
    img.save(out, format="JPEG", quality=92)
    return out.getvalue()

# ---------- BG Remove (rembg) ----------
_rembg_session = None

def remove_bg(image_bytes: bytes) -> bytes:
    global _rembg_session
    from rembg import remove, new_session
    if _rembg_session is None:
        _rembg_session = new_session("u2net_human_seg")
    result = remove(image_bytes, session=_rembg_session)
    return result

# ---------- BG Color (White/Blue/Red) ----------
def change_bg_color(image_bytes: bytes, color: str = "white") -> bytes:
    from rembg import remove, new_session
    global _rembg_session
    if _rembg_session is None:
        _rembg_session = new_session("u2net_human_seg")

    no_bg = remove(image_bytes, session=_rembg_session)
    fg = Image.open(BytesIO(no_bg)).convert("RGBA")

    color_map = {
        "white": (255, 255, 255),
        "blue": (0, 102, 204),
        "red": (204, 0, 0),
    }
    bg_color = color_map.get(color, (255, 255, 255))

    bg = Image.new("RGBA", fg.size, bg_color + (255,))
    combined = Image.alpha_composite(bg, fg).convert("RGB")

    out = BytesIO()
    combined.save(out, format="JPEG", quality=92)
    return out.getvalue()
