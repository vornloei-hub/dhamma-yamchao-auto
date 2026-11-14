import os, datetime, sys, subprocess, urllib.request, urllib.parse, json

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

#ธรรมะยามเช้า #สติ #เล่าสู่กัน #AI #Reels
"""
print(caption, flush=True)
print(f"Page ID: {PAGE_ID} DRY_RUN: {DRY_RUN}", flush=True)
if DRY_RUN:
    print("DRY_RUN=1 ไม่โพสต์จริง")
    raise SystemExit(0)
if not TOKEN:
    print("ERROR: ไม่มี FACEBOOK_PAGE_ACCESS_TOKEN")
    raise SystemExit(1)

# สร้างรูป + วีดีโอ 1080x1920 15 วิ
from PIL import Image, ImageDraw, ImageFont
W, H = 1080, 1920
img = Image.new("RGB", (W, H), (255, 243, 210))
draw = ImageDraw.Draw(img)
for y in range(H):
    r = int(255 - (y/H)*40); g = int(243 - (y/H)*80); b = int(210 - (y/H)*60)
    draw.line([(0, y), (W, y)], fill=(r, g, b))
draw.ellipse([(W//2-180, 180, W//2+180, 540)], fill=(255, 200, 80), outline=(255, 180, 0), width=6)
def font(size):
    try:
        return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", size)
    except Exception:
        return ImageFont.load_default()
draw.text((W//2, 700), "Dhamma Yamchao - Sati", font=font(60), fill=(80, 40, 0), anchor="mm")
draw.text((W//2, 820), "Lao Su Kan...", font=font(52), fill=(120, 60, 0), anchor="mm")
draw.text((W//2, 1000), "Dhamma for Today", font=font(64), fill=(60, 30, 0), anchor="mm")
draw.text((W//2, 1250), "Mindfulness for a new day", font=font(38), fill=(80, 50, 10), anchor="mm")
draw.text((W//2, 1750), "[AI] Dhamma for new day", font=font(34), fill=(120, 80, 0), anchor="mm")
img.save("dhamma.jpg", quality=92)
print("สร้างรูปแล้ว", flush=True)
res = subprocess.run(["ffmpeg", "-y", "-loop", "1", "-i", "dhamma.jpg", "-t", "15", "-vf", "scale=1080:1920,format=yuv420p", "-c:v", "libx264", "-r", "25", "-movflags", "+faststart", "dhamma.mp4"], capture_output=True, text=True)
if res.returncode != 0:
    print(res.stderr[-2000:], flush=True)
    raise SystemExit(1)
print("สร้างวีดีโอแล้ว", flush=True)
file_size = os.path.getsize("dhamma.mp4")
print(f"ขนาดวีดีโอ: {file_size}", flush=True)

# Reels 3 ขั้น - start / upload / finish
def fb_post(url, data_dict):
    data = urllib.parse.urlencode(data_dict).encode()
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/x-www-form-urlencoded"}, method="POST")
    with urllib.request.urlopen(req, timeout=60) as r:
        body = r.read().decode()
        print(f"FB {r.status}: {body[:800]}", flush=True)
        return json.loads(body)

start_url = f"https://graph.facebook.com/v21.0/{PAGE_ID}/video_reels"
start = fb_post(start_url, {"access_token": TOKEN, "video_state": "PUBLISHED", "upload_phase": "start", "file_size": str(file_size), "description": caption})
video_id = start.get("video_id")
upload_url = start.get("upload_url")
if not video_id or not upload_url:
    print(f"ERROR start ไม่ได้ video_id/upload_url: {start}", flush=True)
    raise SystemExit(1)

with open("dhamma.mp4", "rb") as f:
    vb = f.read()
# อัปโหลดไฟล์ - Facebook Reels ใช้ POST ไปที่ upload_url
up_req = urllib.request.Request(upload_url, data=vb, headers={"Content-Type": "application/octet-stream", "Content-Length": str(len(vb))}, method="POST")
try:
    with urllib.request.urlopen(up_req, timeout=120) as r:
        print(f"Upload {r.status}: {r.read().decode()[:500]}", flush=True)
except Exception as e:
    print(f"Upload POST พัง ลอง PUT: {e}", flush=True)
    up_req2 = urllib.request.Request(upload_url, data=vb, headers={"Content-Type": "application/octet-stream", "Content-Length": str(len(vb))}, method="PUT")
    with urllib.request.urlopen(up_req2, timeout=120) as r:
        print(f"Upload PUT {r.status}: {r.read().decode()[:500]}", flush=True)

finish = fb_post(start_url, {"access_token": TOKEN, "video_state": "PUBLISHED", "upload_phase": "finish", "video_id": video_id, "description": caption})
print("DONE - โพสต์ Reels แล้ว", flush=True)
