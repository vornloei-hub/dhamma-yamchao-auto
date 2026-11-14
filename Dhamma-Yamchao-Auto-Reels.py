import os, datetime, sys, subprocess, urllib.request, urllib.parse, uuid, json, time

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
if DRY_RUN:
    print("DRY_RUN=1 ไม่โพสต์จริง")
    raise SystemExit(0)
if not TOKEN:
    print("ERROR: ไม่มี FACEBOOK_PAGE_ACCESS_TOKEN")
    raise SystemExit(1)

# สร้างรูป + วีดีโอ 15 วิ 1080x1920
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
if res.returncode != 0:
    print(res.stderr[-1500:], flush=True)
    print("ERROR: ffmpeg พัง")
    raise SystemExit(1)
print("สร้างวีดีโอแล้ว", flush=True)

# --- โพสต์เป็น Reels ---
# ขั้นที่ 1: เริ่มอัปโหลด Reels
# POST /{page-id}/video_reels?access_token=...&video_state=PUBLISHED&description=...
# ใช้วิธี Resumable: สร้าง session ก่อน
def post_form(url, fields, file_field=None, file_bytes=None, filename="dhamma.mp4"):
    boundary = uuid.uuid4().hex
    body = b""
    for k, v in fields.items():
        body += f"--{boundary}\r\nContent-Disposition: form-data; name=\"{k}\"\r\n\r\n{v}\r\n".encode("utf-8")
    if file_field:
        body += f"--{boundary}\r\nContent-Disposition: form-data; name=\"{file_field}\"; filename=\"{filename}\"\r\nContent-Type: video/mp4\r\n\r\n".encode() + file_bytes + f"\r\n--{boundary}--\r\n".encode()
    else:
        body += f"--{boundary}--\r\n".encode()
    req = urllib.request.Request(url, data=body, headers={"Content-Type": f"multipart/form-data; boundary={boundary}"}, method="POST")
    with urllib.request.urlopen(req, timeout=120) as r:
        return r.status, r.read().decode()

# วิธีที่ 1: ลองโพสต์เป็น Reels ตรงๆ
try:
    print("กำลังโพสต์เป็น Reels...", flush=True)
    # Facebook Reels API: POST /{page-id}/video_reels
    url = f"https://graph.facebook.com/v21.0/{PAGE_ID}/video_reels"
    with open("dhamma.mp4", "rb") as f:
        vb = f.read()
    status, body = post_form(url, {"access_token": TOKEN, "description": caption, "video_state": "PUBLISHED"}, "file_url", vb)
    print(f"Reels ตอบ {status}: {body}", flush=True)
    print("DONE - โพสต์ Reels แล้ว", flush=True)
except Exception as e:
    try:
        err = e.read().decode()
    except Exception:
        err = str(e)
    print(f"Reels พัง: {err}", flush=True)
    print("ลองโพสต์เป็น Video ธรรมดาแทน...", flush=True)
    # Fallback: โพสต์เป็น Video ธรรมดา
    url2 = f"https://graph.facebook.com/v21.0/{PAGE_ID}/videos"
    with open("dhamma.mp4", "rb") as f:
        vb = f.read()
    status2, body2 = post_form(url2, {"access_token": TOKEN, "description": caption}, "source", vb)
    print(f"Video ตอบ {status2}: {body2}", flush=True)
    print("DONE - โพสต์ Video แล้ว (ยังไม่เป็น Reels)", flush=True)
