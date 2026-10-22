"""Image/PDF loading and the offline Tesseract OCR fallback."""
import io
import os

from PIL import Image, ImageOps


def to_images(data: bytes):
    """Turn an upload (image or PDF) into a list of RGB PIL images."""
    if data[:4] == b"%PDF":
        from pdf2image import convert_from_bytes
        last = int(os.getenv("MAX_PDF_PAGES", "3"))
        return [p.convert("RGB") for p in convert_from_bytes(data, dpi=200, last_page=last)]
    img = Image.open(io.BytesIO(data))
    return [ImageOps.exif_transpose(img).convert("RGB")]


def preprocess(img: Image.Image) -> Image.Image:
    """Grayscale + upscale + contrast: cheap steps that help Tesseract on phone photos."""
    gray = ImageOps.grayscale(img)
    if gray.width < 1600:
        factor = 1600 / gray.width
        gray = gray.resize((int(gray.width * factor), int(gray.height * factor)), Image.LANCZOS)
    return ImageOps.autocontrast(gray, cutoff=2)


def to_jpeg_bytes(img: Image.Image, max_side=2000) -> bytes:
    img = img.copy()
    img.thumbnail((max_side, max_side))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=88)
    return buf.getvalue()


def tesseract_text(pages) -> str:
    import pytesseract
    lang = os.getenv("TESS_LANG", "kan+eng")
    out = [pytesseract.image_to_string(preprocess(p), lang=lang, config="--oem 1 --psm 3") for p in pages]
    return "\n\n".join(t.strip() for t in out if t.strip())
