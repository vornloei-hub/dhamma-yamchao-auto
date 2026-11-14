"""
ธรรมะยามเช้า - สติ : สร้างวิดีโอแนวตั้งแบบเคลื่อนไหว (ข้อความขึ้นทีละประโยคตรงกับเสียงพากย์
+ ดนตรีประกอบที่สังเคราะห์เอง ไม่ติดลิขสิทธิ์) แล้วโพสต์ขึ้นเพจ Facebook อัตโนมัติ

ขั้นตอน: Gemini เขียนบท -> edge-tts พากย์ทีละประโยค -> Pillow วาดเฟรม (ดวงอาทิตย์/ดาว/แสงลอย)
         -> ffmpeg รวมภาพ + เสียงพากย์ + ดนตรี -> Graph API โพสต์

ใช้ได้ 2 รอบต่อวัน: SLOT=morning (06:00) และ SLOT=evening (18:00)
Secrets: FB_PAGE_ID + FB_PAGE_TOKEN, GEMINI_API_KEY (ไม่บังคับ แต่แนะนำ)
"""
import asyncio
import datetime
import json
import math
import os
import random
import subprocess
import sys

import requests
from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1920
FPS = 25
OUT_DIR = "out"
FONT_CANDIDATES = [
    "/usr/share/fonts/opentype/tlwg/Loma-Bold.otf",
    "/usr/share/fonts/truetype/tlwg/Loma-Bold.ttf",
    "/usr/share/fonts/truetype/noto/NotoSansThai-Bold.ttf",
]
GEMINI_MODELS = ["gemini-2.5-flash", "gemini-2.0-flash"]
PAGE_NAME = "ธรรมะยามเช้า - สติ"

# รอบเช้า / รอบเย็น: สีท้องฟ้า, เสียง, คอร์ดดนตรี
THEMES = {
    "morning": {
        "name": "ธรรมะยามเช้า - สติ",
        "top": (58, 52, 110), "bottom": (240, 160, 90), "sun": (255, 226, 170),
        "voice": "th-TH-PremwadeeNeural",
        "chord": [220.0, 277.18, 329.63, 110.0],      # A minor/major ลอยๆ นุ่ม
        "closing": "เช้านี้ ขอให้ใจสงบ มีสติ และมีความสุข",
        "hashtag": "#ธรรมะยามเช้า",
    },
    "evening": {
        "name": "ธรรมะก่อนนอน - วางใจ",
        "top": (22, 24, 64), "bottom": (120, 70, 120), "sun": (230, 210, 255),
        "voice": "th-TH-PremwadeeNeural",
        "chord": [196.0, 233.08, 293.66, 98.0],       # G minor ลอยๆ สงบ
        "closing": "คืนนี้ ขอให้วางทุกเรื่อง แล้วหลับให้สบายใจ",
        "hashtag": "#ธรรมะก่อนนอน",
    },
}

# บทสำรอง (ใช้เมื่อ Gemini ใช้ไม่ได้) : (หัวข้อ, [ประโยคสั้น ๆ])
TOPICS = [
    ("สติ 1 นาที ก่อนเริ่มวัน", ["ตื่นเช้ามา หายใจลึก ๆ หนึ่งครั้ง", "รู้ว่าลมเข้า รู้ว่าลมออก", "แค่นี้ ใจก็กลับมาอยู่กับปัจจุบัน"]),
    ("โกรธแล้วทำไงให้ใจเย็น", ["เวลาโกรธ อย่าเพิ่งพูด", "ให้นับหนึ่งถึงสิบ แล้วหายใจออกช้า ๆ", "ความโกรธจะลดลง เหมือนไฟที่ขาดฟืน"]),
    ("โดนนินทา จะวางใจยังไง", ["คำพูดของคนอื่น คือเสียงลม", "ผ่านมาแล้วก็ผ่านไป", "อย่าเก็บมาแบกไว้ในใจ"]),
    ("ทำดีแล้วไม่ได้ดี ทำไม", ["ทำดีไม่ต้องรอผล", "เหมือนปลูกต้นไม้ รดน้ำทุกวัน", "วันหนึ่งมันก็โตเอง"]),
    ("เหนื่อยงาน ท้อแล้ว", ["เหนื่อยก็พักได้ ไม่ต้องฝืน", "ใจที่สงบ งานก็จะเบาลง", "พักให้พอ แล้วค่อยไปต่อ"]),
    ("ให้อภัยวันนี้ แล้วหลับสบาย", ["ก่อนนอน วางทุกเรื่องลง", "ให้อภัยตัวเองและคนอื่น", "แล้วหลับอย่างสบายใจ"]),
    ("เวรกรรมมีจริงไหม", ["กรรมคือการกระทำ", "ทำอะไรไว้ ก็ได้รับสิ่งนั้นกลับมา", "เริ่มทำดีวันนี้ ยังไม่สายเกินไป"]),
    ("ปล่อยวางไม่ใช่ปล่อยทิ้ง", ["ปล่อยวาง คือรู้ว่าอะไรควบคุมได้", "ทำส่วนของเราให้ดีที่สุด", "ส่วนที่เหลือ ปล่อยให้เป็นไปตามเหตุ"]),
    ("ความสุขอยู่ใกล้กว่าที่คิด", ["ความสุขไม่ได้อยู่ไกล", "มันอยู่ในลมหายใจที่เรากำลังหายใจ", "หยุดสักนิด แล้วรับรู้ว่าวันนี้ยังมีลม"]),
    ("ทุกอย่างไม่เที่ยง", ["ความทุกข์ไม่อยู่กับเราตลอดไป", "ความสุขก็เช่นกัน", "เห็นแบบนี้ ใจจะเบาลง"]),
    ("พูดดี มีเมตตา", ["คำพูดดี ๆ ไม่เสียเงินสักบาท", "แต่เปลี่ยนวันของใครบางคนได้", "วันนี้ลองพูดดี ๆ กับใครสักคน"]),
    ("เมตตาตัวเองบ้าง", ["เราดูแลคนอื่นมามากแล้ว", "อย่าลืมให้อภัยตัวเองด้วย", "คนที่ผิดพลาดได้ ก็เรียนรู้ได้"]),
    ("ใจเป็นนาย กายเป็นบ่าว", ["ใจที่นิ่ง นำพาทุกอย่างให้นิ่ง", "ฝึกใจวันละนิด", "สักวันจะเห็นผลที่ชัดเจน"]),
    ("อยู่กับปัจจุบัน", ["อดีตผ่านไปแล้ว อนาคตยังมาไม่ถึง", "สิ่งที่มีจริงคือตอนนี้", "ใส่ใจกับสิ่งที่ทำอยู่ ตรงหน้า"]),
]


def log(msg):
    print(msg, flush=True)


# ---------- 1) บท ----------
def gemini_script(title_hint, seed_lines, theme_name):
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        return None
    prompt = (
        f"เขียนบทคลิปสั้นธรรมะภาษาไทยสำหรับเพจ '{theme_name}' หัวข้อ: {title_hint} "
        f"(แนวคิดตั้งต้น: {' / '.join(seed_lines)}) "
        "แบ่งเป็น 4-5 ประโยคสั้น ๆ แต่ละประโยคไม่เกิน 45 ตัวอักษร อ่านแล้วอบอุ่น เข้าใจง่าย มีภาพเปรียบเทียบ 1 ภาพ "
        "ประโยคแรกเปิดด้วยคำถามหรือสถานการณ์ที่คนเจอจริง ประโยคสุดท้ายเป็นข้อคิดที่เอาไปทำได้ทันที "
        "ไม่อ้างว่าเป็นพุทธพจน์ถ้าไม่แน่ใจ ไม่ใส่อีโมจิ ไม่ใส่เครื่องหมายคำพูด "
        'ตอบเป็น JSON เท่านั้น รูปแบบ {"title": "หัวข้อสั้น", "lines": ["...", "..."]}'
    )
    for model in GEMINI_MODELS:
        try:
            r = requests.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
                headers={"x-goog-api-key": key, "Content-Type": "application/json"},
                json={"contents": [{"parts": [{"text": prompt}]}],
                      "generationConfig": {"responseMimeType": "application/json", "temperature": 1.0}},
                timeout=60,
            )
            r.raise_for_status()
            raw = r.json()["candidates"][0]["content"]["parts"][0]["text"]
            data = json.loads(raw)
            lines = [str(x).strip() for x in data["lines"] if str(x).strip()]
            title = str(data.get("title") or title_hint).strip()
            if 3 <= len(lines) <= 6 and all(4 <= len(x) <= 90 for x in lines):
                log(f"Gemini ({model}) OK")
                return title, lines
        except Exception as e:  # noqa: BLE001
            log(f"Gemini {model} ใช้ไม่ได้: {e}")
    return None


def pick_topic(slot):
    n = datetime.date.today().toordinal() * 2 + (0 if slot == "morning" else 1)
    return TOPICS[n % len(TOPICS)]


# ---------- 2) เสียง ----------
def probe(path):
    out = subprocess.check_output(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=nw=1:nk=1", path], text=True)
    return float(out.strip())


def tts_line(text, path, voice):
    try:
        import edge_tts

        async def run():
            await edge_tts.Communicate(text, voice, rate="-12%").save(path)

        asyncio.run(run())
        if os.path.getsize(path) > 1000:
            return "edge-tts"
    except Exception as e:  # noqa: BLE001
        log(f"edge-tts ใช้ไม่ได้: {e}")
    try:
        from gtts import gTTS

        gTTS(text=text, lang="th").save(path)
        if os.path.getsize(path) > 1000:
            return "gTTS"
    except Exception as e:  # noqa: BLE001
        log(f"gTTS ใช้ไม่ได้: {e}")
    return None


def build_voice(lines, voice, closing):
    """พากย์ทีละประโยค แล้วต่อเป็นไฟล์เดียวพร้อมจังหวะเว้นวรรค คืน (path, timeline, total)"""
    lead, gap, tail = 2.0, 1.0, 3.5
    texts = list(lines) + [closing]
    segs, timeline, t = [], [], lead
    for i, tx in enumerate(texts):
        mp3 = os.path.join(OUT_DIR, f"line{i}.mp3")
        engine = tts_line(tx, mp3, voice)
        if engine:
            dur = probe(mp3)
            log(f"เสียง {i + 1}/{len(texts)} ({engine}) {dur:.1f}s")
        else:
            mp3, dur = None, max(2.5, len(tx) * 0.12)
            log(f"เสียง {i + 1}: ไม่มีเสียง ใช้เวลาประมาณ {dur:.1f}s")
        slot = dur + (gap if i < len(texts) - 1 else tail)
        wav = os.path.join(OUT_DIR, f"slot{i}.wav")
        if mp3:
            cmd = ["ffmpeg", "-y", "-i", mp3, "-ar", "44100", "-ac", "2",
                   "-af", "apad", "-t", f"{slot:.3f}", wav]
        else:
            cmd = ["ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
                   "-t", f"{slot:.3f}", wav]
        subprocess.run(cmd, check=True, capture_output=True)
        segs.append(wav)
        timeline.append((t, t + dur))
        t += slot
    # ช่วงเงียบตอนเปิดคลิป
    lead_wav = os.path.join(OUT_DIR, "lead.wav")
    subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
                    "-t", f"{lead:.2f}", lead_wav], check=True, capture_output=True)
    lst = os.path.join(OUT_DIR, "list.txt")
    with open(lst, "w") as f:
        for p in [lead_wav] + segs:
            f.write(f"file '{os.path.abspath(p)}'\n")
    voice_wav = os.path.join(OUT_DIR, "voice.wav")
    subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", voice_wav],
                   check=True, capture_output=True)
    return voice_wav, timeline, t


# ---------- 3) ภาพเคลื่อนไหว ----------
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
            while draw.textlength(cur, font=font) > max_w:
                k = len(cur)
                while k > 1 and draw.textlength(cur[:k], font=font) > max_w:
                    k -= 1
                lines.append(cur[:k])
                cur = cur[k:]
    if cur.strip():
        lines.append(cur.strip())
    return lines


def text_layer(text, max_h=760, start=84):
    """วาดข้อความกลางภาพบนเลเยอร์โปร่งใส พร้อมเงา"""
    layer = Image.new("RGBA", (W, max_h), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    size = start
    while True:
        font = load_font(size)
        lines = wrap(d, text, font, W - 180)
        if len(lines) > 1:  # จัดบรรทัดให้สมดุล ไม่ให้เหลือคำโดดท้ายบรรทัด
            lo, hi, cnt = 300, W - 180, len(lines)
            while hi - lo > 12:
                mid = (lo + hi) // 2
                if len(wrap(d, text, font, mid)) == cnt:
                    hi = mid
                else:
                    lo = mid
            lines = wrap(d, text, font, hi)
        lh = int(size * 1.65)
        if len(lines) * lh <= max_h - 20 or size <= 44:
            break
        size -= 4
    y = (max_h - len(lines) * lh) // 2
    for ln in lines:
        d.text((W // 2 + 3, y + 4), ln, font=font, fill=(30, 20, 60, 190), anchor="mt")
        d.text((W // 2, y), ln, font=font, fill=(255, 255, 255, 255), anchor="mt")
        y += lh
    return layer


def make_background(theme):
    top, bottom = theme["top"], theme["bottom"]
    img = Image.new("RGB", (W, H))
    px = ImageDraw.Draw(img)
    for y in range(H):
        t = y / (H - 1)
        px.line([(0, y), (W, y)], fill=tuple(int(top[i] + (bottom[i] - top[i]) * t) for i in range(3)))
    # เนินเขาไกล ๆ ให้ภาพมีมิติ
    hills = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    hd = ImageDraw.Draw(hills)
    for base, amp, col in [(1640, 90, (40, 30, 80, 150)), (1740, 70, (28, 20, 60, 210)), (1830, 50, (18, 12, 40, 255))]:
        pts = [(0, H)]
        for x in range(0, W + 20, 20):
            pts.append((x, base + int(amp * math.sin(x / 170.0 + base) + amp * 0.4 * math.sin(x / 70.0))))
        pts.append((W, H))
        hd.polygon(pts, fill=col)
    return Image.alpha_composite(img.convert("RGBA"), hills).convert("RGB")


def make_sun(theme):
    size = 900
    sun = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    sd = ImageDraw.Draw(sun)
    c = size // 2
    col = theme["sun"]
    for r, a in [(440, 18), (380, 28), (320, 40), (250, 70), (170, 255)]:
        sd.ellipse([c - r, c - r, c + r, c + r], fill=col + (a,))
    return sun


def make_sprite(r):
    s = Image.new("RGBA", (r * 2, r * 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(s)
    for rr, a in [(r, 40), (int(r * 0.6), 90), (int(r * 0.3), 220)]:
        d.ellipse([r - rr, r - rr, r + rr, r + rr], fill=(255, 245, 210, a))
    return s


def ease(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


def render_frames(theme, title, lines, closing, timeline, total, proc):
    bg = make_background(theme)
    sun = make_sun(theme)
    sprites = [make_sprite(r) for r in (10, 16, 24)]
    rnd = random.Random(7)
    parts = [(rnd.random() * W, rnd.random() * H, rnd.choice([0, 1, 2]),
              20 + rnd.random() * 40, rnd.random() * 6.28) for _ in range(34)]

    title_layer = Image.new("RGBA", (W, 200), (0, 0, 0, 0))
    td = ImageDraw.Draw(title_layer)
    td.text((W // 2 + 2, 102), theme["name"], font=load_font(52), fill=(30, 20, 60, 170), anchor="mm")
    td.text((W // 2, 100), theme["name"], font=load_font(52), fill=(255, 236, 200, 255), anchor="mm")
    head_layer = text_layer(title, max_h=300, start=70)
    layers = [text_layer(t) for t in lines] + [text_layer(closing, start=76)]
    n = len(layers)
    # ช่วงโชว์ข้อความของแต่ละประโยค: เริ่มก่อนเสียง 0.2s ค้างจนก่อนประโยคถัดไป
    shows = []
    for i, (s, e) in enumerate(timeline):
        start = s - 0.25
        end = (timeline[i + 1][0] - 0.25) if i + 1 < n else total
        shows.append((start, end))

    nframes = int(total * FPS)
    for f in range(nframes):
        t = f / FPS
        frame = bg.copy()
        # ดวงอาทิตย์/ดวงจันทร์ค่อย ๆ ลอยขึ้น + หายใจเบา ๆ
        prog = t / total
        sy = 1500 - 120 * ease(prog * 1.2) + 6 * math.sin(t * 1.2)
        pulse = 1.0 + 0.015 * math.sin(t * 1.6)
        s2 = sun if abs(pulse - 1) < 1e-6 else sun.resize((int(900 * pulse), int(900 * pulse)))
        frame.paste(s2, (W // 2 - s2.width // 2, int(sy) - s2.height // 2), s2)
        # แสงลอยขึ้นช้า ๆ
        for (px_, py_, k, sp, ph) in parts:
            y = (py_ - t * sp) % H
            x = px_ + 18 * math.sin(t * 0.6 + ph)
            tw = 0.55 + 0.45 * math.sin(t * 1.8 + ph)
            sp_img = sprites[k]
            if tw > 0.35:
                frame.paste(sp_img, (int(x) - sp_img.width // 2, int(y) - sp_img.height // 2), sp_img)
        rgba = frame.convert("RGBA")
        # ชื่อเพจ
        a_title = ease(t / 1.2)
        tl = title_layer if a_title >= 0.99 else _fade(title_layer, a_title, 0)
        rgba.alpha_composite(tl, (0, 110))
        # หัวข้อ (ช่วงเปิดคลิป จนถึงประโยคแรก)
        if t < shows[0][0] + 0.4:
            a = ease((t - 0.4) / 0.9) * (1 - ease((t - (shows[0][0] - 0.2)) / 0.5))
            if a > 0.01:
                hl = _fade(head_layer, a, int((1 - a) * 24))
                rgba.alpha_composite(hl, (0, 760))
        # ประโยคเนื้อหา
        for i, (st, en) in enumerate(shows):
            if st - 0.1 <= t <= en + 0.1:
                a_in = ease((t - st) / 0.7)
                a_out = 1 - ease((t - (en - 0.5)) / 0.5) if i < n - 1 else 1.0
                a = a_in * a_out
                if a > 0.01:
                    ly = _fade(layers[i], a, int((1 - a_in) * 30))
                    rgba.alpha_composite(ly, (0, 560))
        # ปิดท้ายค่อย ๆ มืดลง
        if t > total - 1.2:
            dark = Image.new("RGBA", (W, H), (0, 0, 0, int(255 * ease((t - (total - 1.2)) / 1.2))))
            rgba.alpha_composite(dark)
        proc.stdin.write(rgba.convert("RGB").tobytes())


def _fade(layer, a, dy):
    r, g, b, al = layer.split()
    al = al.point(lambda v: int(v * a))
    out = Image.merge("RGBA", (r, g, b, al))
    if dy:
        canvas = Image.new("RGBA", layer.size, (0, 0, 0, 0))
        canvas.paste(out, (0, dy))
        return canvas
    return out


# ---------- 4) วิดีโอ + ดนตรีประกอบ (สังเคราะห์เอง) ----------
def pad_expr(freqs):
    parts = []
    for i, fq in enumerate(freqs):
        amp = 0.16 if i == len(freqs) - 1 else 0.10
        parts.append(f"{amp}*sin(2*PI*{fq}*t)+{amp * 0.4:.3f}*sin(2*PI*{fq * 2.003:.3f}*t)")
    return "+".join(parts)


def make_video(theme, title, lines, closing, voice_wav, timeline, total, out):
    dur = f"{total:.2f}"
    cmd = [
        "ffmpeg", "-y",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
        "-i", voice_wav,
        "-f", "lavfi", "-i", f"aevalsrc={pad_expr(theme['chord'])}:s=44100:d={dur}",
        "-filter_complex",
        "[2:a]tremolo=f=0.18:d=0.35,lowpass=f=1400,aecho=0.8:0.7:700|1100:0.35|0.25,"
        f"volume=0.55,afade=t=in:d=3,afade=t=out:st={total - 3:.2f}:d=3[m];"
        "[1:a]highpass=f=80,volume=1.6[v];"
        "[m][v]amix=inputs=2:duration=longest:dropout_transition=0,"
        "loudnorm=I=-16:TP=-1.5:LRA=11[a]",
        "-map", "0:v", "-map", "[a]",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "21", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "160k", "-t", dur, "-movflags", "+faststart", out,
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        render_frames(theme, title, lines, closing, timeline, total, proc)
        proc.stdin.close()
        err = proc.stderr.read().decode("utf-8", "ignore")
        if proc.wait() != 0:
            log(err[-2000:])
            raise RuntimeError("ffmpeg ล้มเหลว")
    except BrokenPipeError:
        log(proc.stderr.read().decode("utf-8", "ignore")[-2000:])
        raise


# ---------- 5) โพสต์ ----------
def post_to_facebook(video, caption):
    page_id = os.environ.get("FB_PAGE_ID") or os.environ.get("FACEBOOK_PAGE_ID")
    token = os.environ.get("FB_PAGE_TOKEN") or os.environ.get("FACEBOOK_PAGE_ACCESS_TOKEN")
    if not page_id or not token:
        log("ไม่พบ Secrets ของ Facebook (FB_PAGE_ID/FB_PAGE_TOKEN)")
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


def detect_slot():
    s = (os.environ.get("SLOT") or "").strip().lower()
    if s in THEMES:
        return s
    hour_th = (datetime.datetime.utcnow() + datetime.timedelta(hours=7)).hour
    return "morning" if hour_th < 12 else "evening"


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    slot = detect_slot()
    theme = THEMES[slot]
    title, seed_lines = pick_topic(slot)
    log(f"รอบ: {slot} | หัวข้อ: {title}")
    got = gemini_script(title, seed_lines, theme["name"])
    if got:
        title, lines = got
    else:
        log("ใช้บทสำรอง")
        lines = seed_lines
    for ln in lines:
        log(f"  - {ln}")

    voice_wav, timeline, total = build_voice(lines, theme["voice"], theme["closing"])
    video_path = os.path.join(OUT_DIR, "dhamma.mp4")
    make_video(theme, title, lines, theme["closing"], voice_wav, timeline, total, video_path)
    log(f"สร้างวิดีโอแล้ว {os.path.getsize(video_path) // 1024} KB ยาว {total:.0f} วินาที")

    if os.environ.get("DRY_RUN") == "1":
        log("DRY_RUN: ข้ามการโพสต์")
        return
    caption = (f"{title} | {theme['name']}\n\n" + "\n".join(lines) +
               f"\n\n{theme['closing']} 🙏\n\n{theme['hashtag']} #สติ #ธรรมะ #AI")
    post_to_facebook(video_path, caption)


if __name__ == "__main__":
    main()
