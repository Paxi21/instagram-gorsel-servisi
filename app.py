from flask import Flask, request, send_file, jsonify
import requests
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
from io import BytesIO
import random
import textwrap
import os

app = Flask(__name__)

# ── Tasarım şablonları – her gün farklı ──
SABLONLAR = [
    {
        "isim": "karanlik_dramatik",
        "karanlik": 0.55,
        "overlay_renk": (0, 0, 0, 180),
        "yazi_renk": (255, 255, 255),
        "vurgu_renk": (255, 210, 50),
        "font_boyut": 90,
        "alt_serit": True,
    },
    {
        "isim": "mor_estetik",
        "karanlik": 0.60,
        "overlay_renk": (40, 0, 80, 160),
        "yazi_renk": (255, 255, 255),
        "vurgu_renk": (200, 100, 255),
        "font_boyut": 85,
        "alt_serit": True,
    },
    {
        "isim": "beyaz_minimal",
        "karanlik": 0.65,
        "overlay_renk": (0, 0, 0, 200),
        "yazi_renk": (255, 255, 255),
        "vurgu_renk": (255, 255, 255),
        "font_boyut": 80,
        "alt_serit": False,
    },
    {
        "isim": "turuncu_enerji",
        "karanlik": 0.50,
        "overlay_renk": (80, 30, 0, 150),
        "yazi_renk": (255, 255, 255),
        "vurgu_renk": (255, 140, 0),
        "font_boyut": 88,
        "alt_serit": True,
    },
    {
        "isim": "mavi_derin",
        "karanlik": 0.58,
        "overlay_renk": (0, 20, 60, 170),
        "yazi_renk": (255, 255, 255),
        "vurgu_renk": (80, 180, 255),
        "font_boyut": 82,
        "alt_serit": True,
    },
]

# Windows fontları (Railway'de fallback kullanılır)
FONT_LISTESI = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
]

def font_yukle(boyut):
    for yol in FONT_LISTESI:
        try:
            return ImageFont.truetype(yol, boyut)
        except:
            continue
    return ImageFont.load_default()

def gorsel_olustur(image_url: str, gorselsoz: str, baslik: str) -> BytesIO:
    W, H = 1080, 1080

    # Sablon seç (her gün farklı)
    sablon = random.choice(SABLONLAR)

    # Fotoğrafı indir
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(image_url, headers=headers, timeout=15)
        foto = Image.open(BytesIO(r.content)).convert("RGB")
        foto = foto.resize((W, H), Image.LANCZOS)
    except:
        foto = Image.new("RGB", (W, H), (20, 20, 40))

    # Karartma
    karanlik = Image.new("RGB", (W, H), (0, 0, 0))
    img = Image.blend(foto, karanlik, alpha=sablon["karanlik"])
    img = img.filter(ImageFilter.GaussianBlur(radius=0.8))

    # Overlay
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ov_draw = ImageDraw.Draw(overlay)

    if sablon["alt_serit"]:
        ov_draw.rectangle([0, H - 450, W, H], fill=sablon["overlay_renk"])
    else:
        # Tam ekran hafif overlay
        ov_draw.rectangle([0, 0, W, H], fill=(0, 0, 0, 100))

    img = img.convert("RGBA")
    img = Image.alpha_composite(img, overlay).convert("RGB")
    draw = ImageDraw.Draw(img)

    # ── Ana söz (ortada, büyük) ──
    font_buyuk = font_yukle(sablon["font_boyut"])
    font_orta  = font_yukle(42)
    font_kucuk = font_yukle(28)

    satirlar = textwrap.wrap(gorselsoz, width=16)
    toplam_h = len(satirlar) * (sablon["font_boyut"] + 15)

    if sablon["alt_serit"]:
        y_pos = (H // 2) - (toplam_h // 2) - 80
    else:
        y_pos = (H // 2) - (toplam_h // 2)

    for satir in satirlar:
        bbox = draw.textbbox((0, 0), satir, font=font_buyuk)
        tw = bbox[2] - bbox[0]
        x = (W - tw) // 2
        # Gölge
        draw.text((x + 3, y_pos + 3), satir, font=font_buyuk, fill=(0, 0, 0))
        # Ana yazı
        draw.text((x, y_pos), satir, font=font_buyuk, fill=sablon["yazi_renk"])
        y_pos += sablon["font_boyut"] + 15

    # ── Dekoratif çizgi ──
    vurgu = sablon["vurgu_renk"]
    cizgi_y = y_pos + 20
    draw.rectangle([W//2 - 80, cizgi_y, W//2 + 80, cizgi_y + 4], fill=vurgu)

    # ── Alt başlık ──
    if sablon["alt_serit"]:
        baslik_satirlar = textwrap.wrap(baslik, width=30)
        y_alt = H - 380
        for satir in baslik_satirlar:
            bbox = draw.textbbox((0, 0), satir, font=font_orta)
            tw = bbox[2] - bbox[0]
            draw.text(((W - tw) // 2, y_alt), satir, font=font_orta, fill=vurgu)
            y_alt += 55

    # ── Tarih sol alt ──
    from datetime import datetime
    tarih = datetime.now().strftime("%d.%m.%Y")
    draw.text((50, H - 55), tarih, font=font_kucuk, fill=(180, 180, 180))

    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf


@app.route("/gorsel", methods=["POST"])
def gorsel_endpoint():
    try:
        data = request.get_json()
        image_url = data.get("image_url", "")
        gorselsoz = data.get("gorselsoz", "Başarı Bir Alışkanlıktır")
        baslik    = data.get("baslik", "")

        buf = gorsel_olustur(image_url, gorselsoz, baslik)
        return send_file(buf, mimetype="image/png", download_name="post.png")

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/", methods=["GET"])
def health():
    return jsonify({"status": "ok", "message": "Gorsel servisi calisiyor!"})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
