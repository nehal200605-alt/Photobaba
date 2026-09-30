from PIL import Image, ImageDraw, ImageFont
from io import BytesIO


def resize_image(image_bytes, width, height):
    img = Image.open(BytesIO(image_bytes)).convert("RGB")
    img = img.resize((width, height), Image.LANCZOS)
    out = BytesIO()
    img.save(out, format="JPEG", quality=92)
    return out.getvalue()


def quick_resize(image_bytes, scale=0.5):
    img = Image.open(BytesIO(image_bytes)).convert("RGB")
    w, h = img.size
    img = img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)
    out = BytesIO()
    img.save(out, format="JPEG", quality=92)
    return out.getvalue()


def rotate_image(image_bytes, angle=90):
    img = Image.open(BytesIO(image_bytes)).convert("RGB")
    img = img.rotate(-angle, expand=True)
    out = BytesIO()
    img.save(out, format="JPEG", quality=92)
    return out.getvalue()


def to_jpg(image_bytes):
    img = Image.open(BytesIO(image_bytes)).convert("RGB")
    out = BytesIO()
    img.save(out, format="JPEG", quality=95)
    return out.getvalue()


def to_pdf(image_bytes):
    img = Image.open(BytesIO(image_bytes)).convert("RGB")
    out = BytesIO()
    img.save(out, format="PDF")
    return out.getvalue()


def insta_grid(image_bytes):
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


def add_watermark(image_bytes, text="© PhotoBaba"):
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
