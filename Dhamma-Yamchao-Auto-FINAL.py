import os, datetime, sys, subprocess, urllib.request, urllib.parse, uuid

PAGE_ID = os.environ.get("FACEBOOK_PAGE_ID", "1338551616018917")
TOKEN = os.environ.get("FACEBOOK_PAGE_ACCESS_TOKEN", "")
DRY_RUN = os.environ.get("DRY_RUN", "0") == "1" or "--dry-run" in sys.argv

TOPICS = [
    ("สติ 1 นาที ก่อนเริ่มวัน", "ตื่นเช้ามา หายใจลึกๆ 1 ครั้ง แล้วบอกตัวเองว่า วันนี้เราจะมีสติ"),
    ("โกรธแล้วทำไงให้ใจเย็น", "เวลาโกรธ อย่าเพิ่งพูด ให้นับ 1-10 แล้วหายใจออกช้าๆ"),
    ("โดนนินทา จะวางใจยังไง", "คำพูดคนอื่นคือเสียงลม ผ่านมาแล้วก็ผ่านไป อย่าเก็บมาแบก"),
    ("ทำดีแล้วไม่ได้ดี ทำไม", "ทำดีไม่ต้องรอผล เหมือนปลูกต้นไม้ รดน้ำทุกวัน วันนึงมันโตเอง"),
    ("เหนื่อยงาน ท้อแล้ว", "เหนื่อยก็พักได้ ไม่ต้องฝืน ใจที่สงบ งานก็จะเบาลง"),
    ("ให้อภัยวันนี้ แล้วหลับสบาย", "ก่อนนอน วางทุกเรื่องลง ให้อภัยตัวเองและคนอื่น แล้วหลับอย่างสบายใจ"),
    ("เวรกรรมมีจริงไหม", "กรรมคือการกระทำ ทำอะไรไว้ ก็จะได้รับสิ่งนั้นกลับมา"),
]
idx = datetime.date.today().toordinal() % len(TOPICS)
title, message = TOPICS[idx]
caption = f"""เล่าสู่กัน... เช้านี้ | {title} | ธรรมะยามเช้า - สติ [AI]

{message}

เช้านี้ ขอให้ใจสงบ มีสติ และมีความสุข
ธรรมะสั้นๆ เพื่อเริ่มวันใหม่ด้วยใจที่เบา

#ธรรมะยามเช้า #สติ #เล่าสู่กัน #AI
"""
print(caption, flush=True)
if DRY_RUN:
    print("DRY_RUN=1 ไม่โพสต์จริง")
    raise SystemExit(0)
if not TOKEN:
    print("ERROR: ไม่มี FACEBOOK_PAGE_ACCESS_TOKEN")
    raise SystemExit(1)

def post_text():
    print("โพสต์แบบตัวอักษรสำรอง...", flush=True)
    url = f"https://graph.facebook.com/v21.0/{PAGE_ID}/feed"
    data = urllib.parse.urlencode({"message": caption, "access_token": TOKEN}).encode()
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/x-www-form-urlencoded"}, method="POST")
    with urllib.request.urlopen(req, timeout=30) as r:
        print(f"Facebook ตอบ {r.status}: {r.read().decode()}", flush=True)
        print("DONE - โพสต์ตัวอักษรแล้ว", flush=True)

def post_video():
    from PIL import Image, ImageDraw, ImageFont
    W, H = 1080, 1920
    img = Image.new("RGB", (W, H), (255, 243, 210))
    draw = ImageDraw.Draw(img)
    for y in range(H):
        r = int(255 - (y/H)*40); g = int(243 - (y/H)*80); b = int(210 - (y/H)*60)
        draw.line([(0, y), (W, y)], fill=(r, g, b))
    draw.ellipse([(W//2-180, 180, W//2+180, 540)], fill=(255, 200, 80), outline=(255, 180, 0), width=6)
    def font(size):
        for p in ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"]:
            try: return ImageFont.truetype(p, size)
            except: pass
        return ImageFont.load_default()
    draw.text((W//2, 700), "Dhamma Yamchao - Sati", font=font(60), fill=(80, 40, 0), anchor="mm")
    draw.text((W//2, 820), "Lao Su Kan...", font=font(52), fill=(120, 60, 0), anchor="mm")
    draw.text((W//2, 1000), title, font=font(64), fill=(60, 30, 0), anchor="mm")
    draw.text((W//2, 1250), message[:60], font=font(38), fill=(80, 50, 10), anchor="mm")
    draw.text((W//2, 1750), "[AI] Dhamma for new day", font=font(34), fill=(120, 80, 0), anchor="mm")
    img.save("dhamma.jpg", quality=92)
    print("สร้างรูปแล้ว", flush=True)
    cmd = ["ffmpeg", "-y", "-loop", "1", "-i", "dhamma.jpg", "-t", "15", "-vf", "scale=1080:1920,format=yuv420p", "-c:v", "libx264", "-r", "25", "dhamma.mp4"]
    res = subprocess.run(cmd, capture_output=True, text=True)
    print(res.stderr[-1500:], flush=True)
    if res.returncode != 0:
        raise RuntimeError("ffmpeg พัง")
    print("สร้างวีดีโอแล้ว", flush=True)
    boundary = uuid.uuid4().hex
    def part(name, value):
        return f"--{boundary}\r\nContent-Disposition: form-data; name=\"{name}\"\r\n\r\n{value}\r\n".encode("utf-8")
    body = b""
    body += part("description", caption)
    body += part("access_token", TOKEN)
    with open("dhamma.mp4", "rb") as f:
        video_bytes = f.read()
    body += f"--{boundary}\r\nContent-Disposition: form-data; name=\"source\"; filename=\"dhamma.mp4\"\r\nContent-Type: video/mp4\r\n\r\n".encode() + video_bytes + f"\r\n--{boundary}--\r\n".encode()
    url = f"https://graph.facebook.com/v21.0/{PAGE_ID}/videos"
    req = urllib.request.Request(url, data=body, headers={"Content-Type": f"multipart/form-data; boundary={boundary}"}, method="POST")
    with urllib.request.urlopen(req, timeout=120) as r:
        print(f"Facebook ตอบ {r.status}: {r.read().decode()}", flush=True)
        print("DONE - โพสต์วีดีโอแล้ว", flush=True)

try:
    post_video()
except Exception as e:
    print(f"วีดีโอพัง: {e} -> โพสต์แบบตัวอักษรแทน", flush=True)
    try:
        post_text()
    except Exception as e2:
        try:
            print(f"Facebook ตอบ ERROR: {e2.read().decode()}", flush=True)
        except Exception:
            print(f"ERROR: {e2}", flush=True)
        raise SystemExit(1)
