from flask import Flask, request, send_file, jsonify
import requests
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from io import BytesIO
import random
import textwrap
import os
import base64
from datetime import datetime

app = Flask(__name__)

SABLONLAR = [
    {"karanlik": 0.55, "overlay_renk": (0,0,0,180), "yazi_renk": (255,255,255), "vurgu_renk": (255,210,50), "font_boyut": 90},
    {"karanlik": 0.60, "overlay_renk": (40,0,80,160), "yazi_renk": (255,255,255), "vurgu_renk": (200,100,255), "font_boyut": 85},
    {"karanlik": 0.65, "overlay_renk": (0,0,0,200), "yazi_renk": (255,255,255), "vurgu_renk": (255,255,255), "font_boyut": 80},
    {"karanlik": 0.50, "overlay_renk": (80,30,0,150), "yazi_renk": (255,255,255), "vurgu_renk": (255,140,0), "font_boyut": 88},
    {"karanlik": 0.58, "overlay_renk": (0,20,60,170), "yazi_renk": (255,255,255), "vurgu_renk": (80,180,255), "font_boyut": 82},
]

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

def gorsel_olustur(image_url, gorselsoz, baslik):
    W, H = 1080, 1080
    sablon = random.choice(SABLONLAR)

    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(image_url, headers=headers, timeout=15)
        foto = Image.open(BytesIO(r.content)).convert("RGB")
        foto = foto.resize((W, H), Image.LANCZOS)
    except:
        foto = Image.new("RGB", (W, H), (20, 20, 40))

    karanlik = Image.new("RGB", (W, H), (0, 0, 0))
    img = Image.blend(foto, karanlik, alpha=sablon["karanlik"])
    img = img.filter(ImageFilter.GaussianBlur(radius=0.8))

    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ov_draw = ImageDraw.Draw(overlay)
    ov_draw.rectangle([0, H-450, W, H], fill=sablon["overlay_renk"])
    img = img.convert("RGBA")
    img = Image.alpha_composite(img, overlay).convert("RGB")
    draw = ImageDraw.Draw(img)

    font_buyuk = font_yukle(sablon["font_boyut"])
    font_orta  = font_yukle(42)
    font_kucuk = font_yukle(28)

    satirlar = textwrap.wrap(gorselsoz, width=16)
    toplam_h = len(satirlar) * (sablon["font_boyut"] + 15)
    y_pos = (H // 2) - (toplam_h // 2) - 80

    for satir in satirlar:
        bbox = draw.textbbox((0,0), satir, font=font_buyuk)
        tw = bbox[2] - bbox[0]
        x = (W - tw) // 2
        draw.text((x+3, y_pos+3), satir, font=font_buyuk, fill=(0,0,0))
        draw.text((x, y_pos), satir, font=font_buyuk, fill=sablon["yazi_renk"])
        y_pos += sablon["font_boyut"] + 15

    vurgu = sablon["vurgu_renk"]
    draw.rectangle([W//2-80, y_pos+20, W//2+80, y_pos+24], fill=vurgu)

    baslik_satirlar = textwrap.wrap(baslik, width=30)
    y_alt = H - 380
    for satir in baslik_satirlar:
        bbox = draw.textbbox((0,0), satir, font=font_orta)
        tw = bbox[2] - bbox[0]
        draw.text(((W-tw)//2, y_alt), satir, font=font_orta, fill=vurgu)
        y_alt += 55

    tarih = datetime.now().strftime("%d.%m.%Y")
    draw.text((50, H-55), tarih, font=font_kucuk, fill=(180,180,180))

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
        
        # Base64 olarak döndür
        img_base64 = base64.b64encode(buf.getvalue()).decode("utf-8")
        return jsonify({"image_base64": img_base64, "status": "ok"})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/", methods=["GET"])
def health():
    return jsonify({"status": "ok", "message": "Gorsel servisi calisiyor!"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
