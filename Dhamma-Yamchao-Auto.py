"""
ธรรมะยามเช้า - สติ : สร้างวิดีโอแนวตั้ง แล้วโพสต์ขึ้นเพจ Facebook โดยตรง (ไม่ผ่าน Make)

ขั้นตอน: Gemini เขียนข้อความ -> เสียงพากย์ไทย (edge-tts / gTTS / เงียบ) -> Pillow วาดภาพ -> ffmpeg ทำวิดีโอ -> Graph API โพสต์

Secrets ใน GitHub: FB_PAGE_ID + FB_PAGE_TOKEN (หรือ FACEBOOK_PAGE_ID + FACEBOOK_PAGE_ACCESS_TOKEN), GEMINI_API_KEY (ไม่บังคับ)
"""
import asyncio
import datetime
import json
import os
import random
import subprocess
import sys

import requests
from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1920
OUT_DIR = "out"
FONT_CANDIDATES = [
    "/usr/share/fonts/opentype/tlwg/Loma-Bold.otf",
    "/usr/share/fonts/truetype/tlwg/Loma-Bold.ttf",
    "/usr/share/fonts/truetype/noto/NotoSansThai-Bold.ttf",
]
GEMINI_MODELS = ["gemini-2.5-flash", "gemini-2.0-flash"]

TOPICS = [
    ("สติ 1 นาที ก่อนเริ่มวัน", "ตื่นเช้ามา หายใจลึก ๆ 1 ครั้ง แล้วบอกตัวเองว่า วันนี้เราจะมีสติ"),
    ("โกรธแล้วทำไงให้ใจเย็น", "เวลาโกรธ อย่าเพิ่งพูด ให้นับ 1-10 แล้วหายใจออกช้า ๆ"),
    ("โดนนินทา จะวางใจยังไง", "คำพูดคนอื่นคือเสียงลม ผ่านมาแล้วก็ผ่านไป อย่าเก็บมาแบก"),
    ("ทำดีแล้วไม่ได้ดี ทำไม", "ทำดีไม่ต้องรอผล เหมือนปลูกต้นไม้ รดน้ำทุกวัน วันหนึ่งมันโตเอง"),
    ("เหนื่อยงาน ท้อแล้ว", "เหนื่อยก็พักได้ ไม่ต้องฝืน ใจที่สงบ งานก็จะเบาลง"),
    ("ให้อภัยวันนี้ แล้วหลับสบาย", "ก่อนนอน วางทุกเรื่องลง ให้อภัยตัวเองและคนอื่น แล้วหลับอย่างสบายใจ"),
    ("เวรกรรมมีจริงไหม", "กรรมคือการกระทำ ทำอะไรไว้ ก็จะได้รับสิ่งนั้นกลับมา"),
]


def log(msg):
    print(msg, flush=True)


# ---------- 1) ข้อความ ----------
def gemini_text(title, seed):
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        return None
    prompt = (
        f"เขียนข้อคิดธรรมะยามเช้าภาษาไทย 1 ข้อ สำหรับเพจ 'ธรรมะยามเช้า - สติ' หัวข้อวันนี้: {title} "
        f"(แนวคิดตั้งต้น: {seed}) อ่านแล้วอบอุ่น ไม่อ้างว่าเป็นพุทธพจน์ถ้าไม่แน่ใจ "
        "ความยาว 2-3 ประโยค รวมไม่เกิน 160 ตัวอักษร ไม่ใส่อีโมจิ ไม่ใส่เครื่องหมายคำพูด "
        'ตอบเป็น JSON เท่านั้น รูปแบบ {"text": "..."}'
    )
    for model in GEMINI_MODELS:
        try:
            r = requests.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
                headers={"x-goog-api-key": key, "Content-Type": "application/json"},
                json={
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {"responseMimeType": "application/json", "temperature": 1.0},
                },
                timeout=60,
            )
            r.raise_for_status()
            raw = r.json()["candidates"][0]["content"]["parts"][0]["text"]
            text = json.loads(raw)["text"].strip()
            if 10 <= len(text) <= 300:
                log(f"Gemini ({model}) OK")
                return text
        except Exception as e:  # noqa: BLE001
            log(f"Gemini {model} ใช้ไม่ได้: {e}")
    return None


def get_topic():
    return TOPICS[datetime.date.today().toordinal() % len(TOPICS)]


def get_text(title, seed):
    t = gemini_text(title, seed)
    if t:
        return t
    log("ใช้ข้อความสำรอง")
    return seed


# ---------- 2) เสียง ----------
def make_audio(text, path):
    try:
        import edge_tts

        async def run():
            await edge_tts.Communicate(text, "th-TH-PremwadeeNeural", rate="-10%").save(path)

        asyncio.run(run())
        if os.path.getsize(path) > 1000:
            log("เสียง: edge-tts")
            return True
    except Exception as e:  # noqa: BLE001
        log(f"edge-tts ใช้ไม่ได้: {e}")
    try:
        from gtts import gTTS

        gTTS(text=text, lang="th").save(path)
        if os.path.getsize(path) > 1000:
            log("เสียง: gTTS")
            return True
    except Exception as e:  # noqa: BLE001
        log(f"gTTS ใช้ไม่ได้: {e}")
    log("ไม่มีเสียง จะทำวิดีโอเงียบ")
    return False


def audio_duration(path):
    out = subprocess.check_output(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=nw=1:nk=1", path], text=True)
    return float(out.strip())


# ---------- 3) ภาพ ----------
def load_font(size):
    for p in FONT_CANDIDATES:
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    raise RuntimeError("ไม่พบฟอนต์ไทย (ติดตั้ง fonts-thai-tlwg)")


def tokens(text):
    try:
        from pythainlp.tokenize import word_tokenize
        return word_tokenize(text, engine="newmm", keep_whitespace=True)
    except Exception:  # noqa: BLE001
        # ไม่มี pythainlp: ตัดบรรทัดตามช่องว่างเท่านั้น (คำไทยจะไม่ถูกตัดกลางคำ)
        parts = text.split(" ")
        return [p + (" " if i < len(parts) - 1 else "") for i, p in enumerate(parts)]


def wrap(draw, text, font, max_w):
    lines, cur = [], ""
    for tok in tokens(text):
        test = cur + tok
        if draw.textlength(test, font=font) <= max_w:
            cur = test
        else:
            if cur.strip():
                lines.append(cur.strip())
            cur = tok.lstrip()
            while draw.textlength(cur, font=font) > max_w:  # คำเดียวยาวเกินบรรทัด
                k = len(cur)
                while k > 1 and draw.textlength(cur[:k], font=font) > max_w:
                    k -= 1
                lines.append(cur[:k])
                cur = cur[k:]
    if cur.strip():
        lines.append(cur.strip())
    return lines


def make_image(text, path):
    # ไล่สีท้องฟ้ายามเช้า (บนม่วงอ่อน -> ล่างส้มทอง)
    top, bottom = (58, 52, 110), (240, 160, 90)
    img = Image.new("RGB", (W, H))
    px = ImageDraw.Draw(img)
    for y in range(H):
        t = y / (H - 1)
        px.line([(0, y), (W, y)], fill=tuple(int(top[i] + (bottom[i] - top[i]) * t) for i in range(3)))
    # ดวงอาทิตย์
    sun = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(sun)
    for r, a in [(330, 40), (250, 70), (180, 255)]:
        sd.ellipse([W // 2 - r, 1350 - r, W // 2 + r, 1350 + r], fill=(255, 226, 170, a))
    img = Image.alpha_composite(img.convert("RGBA"), sun).convert("RGB")
    d = ImageDraw.Draw(img)

    title_font = load_font(54)
    d.text((W // 2, 170), "ธรรมะยามเช้า - สติ", font=title_font, fill=(255, 236, 200), anchor="mm")

    size = 76
    while True:
        font = load_font(size)
        lines = wrap(d, text, font, W - 200)
        line_h = int(size * 1.6)
        if len(lines) * line_h <= 900 or size <= 48:
            break
        size -= 4
    y = 520 + (900 - len(lines) * line_h) // 2
    for ln in lines:
        d.text((W // 2 + 3, y + 3), ln, font=font, fill=(40, 30, 70), anchor="mt")
        d.text((W // 2, y), ln, font=font, fill=(255, 255, 255), anchor="mt")
        y += line_h
    img.save(path)


# ---------- 4) วิดีโอ ----------
def make_video(img, audio, out):
    if audio:
        dur = audio_duration(audio) + 1.5
        cmd = ["ffmpeg", "-y", "-loop", "1", "-i", img, "-i", audio,
               "-c:v", "libx264", "-tune", "stillimage", "-r", "25", "-pix_fmt", "yuv420p",
               "-c:a", "aac", "-b:a", "128k", "-af", "apad", "-t", f"{dur:.2f}",
               "-movflags", "+faststart", out]
    else:
        cmd = ["ffmpeg", "-y", "-loop", "1", "-i", img, "-f", "lavfi", "-i",
               "anullsrc=r=44100:cl=stereo", "-c:v", "libx264", "-tune", "stillimage",
               "-r", "25", "-pix_fmt", "yuv420p", "-c:a", "aac", "-t", "15",
               "-movflags", "+faststart", out]
    subprocess.run(cmd, check=True, capture_output=True)


# ---------- 5) โพสต์ ----------
def post_to_facebook(video, caption):
    page_id = os.environ.get("FB_PAGE_ID") or os.environ.get("FACEBOOK_PAGE_ID")
    token = os.environ.get("FB_PAGE_TOKEN") or os.environ.get("FACEBOOK_PAGE_ACCESS_TOKEN")
    if not page_id or not token:
        log("ไม่พบ Secrets ของ Facebook (FB_PAGE_ID/FB_PAGE_TOKEN หรือ FACEBOOK_PAGE_ID/FACEBOOK_PAGE_ACCESS_TOKEN)")
        sys.exit(1)
    with open(video, "rb") as f:
        r = requests.post(
            f"https://graph-video.facebook.com/v21.0/{page_id}/videos",
            data={"description": caption, "access_token": token},
            files={"source": f},
            timeout=900,
        )
    log(f"Facebook ตอบ {r.status_code}: {r.text}")
    if r.status_code != 200:
        sys.exit(1)


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    title, seed = get_topic()
    log(f"หัวข้อ: {title}")
    text = get_text(title, seed)
    log(f"ข้อความ: {text}")
    audio_path = os.path.join(OUT_DIR, "voice.mp3")
    has_audio = make_audio(text, audio_path)
    img_path = os.path.join(OUT_DIR, "frame.png")
    make_image(text, img_path)
    video_path = os.path.join(OUT_DIR, "dhamma.mp4")
    make_video(img_path, audio_path if has_audio else None, video_path)
    log(f"สร้างวิดีโอแล้ว {os.path.getsize(video_path) // 1024} KB")

    if os.environ.get("DRY_RUN") == "1":
        log("DRY_RUN: ข้ามการโพสต์")
        return
    caption = (f"{title} | ธรรมะยามเช้า - สติ\n\n{text}\n\n"
               "เช้านี้ ขอให้ใจสงบ มีสติ และมีความสุข 🙏\n\n#ธรรมะยามเช้า #สติ #ธรรมะ #AI")
    post_to_facebook(video_path, caption)


if __name__ == "__main__":
    main()
