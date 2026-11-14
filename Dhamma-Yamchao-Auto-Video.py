import os, datetime, urllib.request, urllib.parse, json, sys, subprocess, textwrap

# GitHub -> Video -> Facebook ตรง ไม่ใช้ Make
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
print(caption)
print(f"Page ID: {PAGE_ID} DRY_RUN: {DRY_RUN}")

if DRY_RUN:
    print("DRY_RUN=1 ไม่โพสต์จริง")
    raise SystemExit(0)
if not TOKEN:
    print("ERROR: ไม่มี FACEBOOK_PAGE_ACCESS_TOKEN")
    raise SystemExit(1)

# --- สร้างรูปพื้นหลังธรรมะ + ข้อความ ---
from PIL import Image, ImageDraw, ImageFont
W, H = 1080, 1920
# พื้นหลังไล่สีส้มทองเช้า
img = Image.new("RGB", (W, H), (255, 243, 210))
draw = ImageDraw.Draw(img)
for y in range(H):
    r = int(255 - (y/H)*40)
    g = int(243 - (y/H)*80)
    b = int(210 - (y/H)*60)
    draw.line([(0, y), (W, y)], fill=(r, g, b))
# วงกลมพระอาทิตย์
draw.ellipse([(W//2-180, 180, W//2+180, 540)], fill=(255, 200, 80), outline=(255, 180, 0), width=6)
# ข้อความ
def get_font(size, bold=True):
    for p in ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]:
        try:
            return ImageFont.truetype(p, size)
        except: pass
    return ImageFont.load_default()

# ชื่อเพจ
draw.text((W//2, 700), "ธรรมะยามเช้า - สติ", font=get_font(78), fill=(80, 40, 0), anchor="mm")
draw.text((W//2, 820), "เล่าสู่กัน...", font=get_font(62), fill=(120, 60, 0), anchor="mm")
# หัวข้อ
wrapped = "\n".join(textwrap.wrap(title, width=14))
draw.text((W//2, 1000), wrapped, font=get_font(88), fill=(60, 30, 0), anchor="mm", align="center", spacing=18)
# เนื้อหา
wrapped2 = "\n".join(textwrap.wrap(message, width=22))
draw.text((W//2, 1350), wrapped2, font=get_font(52), fill=(80, 50, 10), anchor="mm", align="center", spacing=16)
draw.text((W//2, 1750), "[AI] ธรรมะสั้นๆ เพื่อเริ่มวันใหม่", font=get_font(38), fill=(120, 80, 0), anchor="mm")
img.save("dhamma.jpg", quality=92)
print("สร้างรูป dhamma.jpg แล้ว")

# --- แปลงรูปเป็นวีดีโอ 15 วิ ด้วย ffmpeg ---
# ซูมช้าๆ + ค้างไว้
cmd = ["ffmpeg", "-y", "-loop", "1", "-i", "dhamma.jpg", "-filter_complex", "[0:v]scale=1080:1920,zoompan=z='min(zoom+0.0008,1.15)':d=375:s=1080x1920:fps=25", "-t", "15", "-pix_fmt", "yuv420p", "-c:v", "libx264", "dhamma.mp4"]
subprocess.run(cmd, check=True)
print("สร้างวีดีโอ dhamma.mp4 แล้ว")

# --- อัพโหลดวีดีโอไป Facebook ---
# ใช้ /videos ไม่ใช่ /feed
url = f"https://graph.facebook.com/v21.0/{PAGE_ID}/videos"
boundary = "----DhammaBoundary123"
with open("dhamma.mp4", "rb") as f:
    video_bytes = f.read()
body = b""
body += f"--{boundary}\r\nContent-Disposition: form-data; name=\"description\"\r\n\r\n{caption}\r\n".encode()
body += f"--{boundary}\r\nContent-Disposition: form-data; name=\"access_token\"\r\n\r\n{TOKEN}\r\n".encode()
body += f"--{boundary}\r\nContent-Disposition: form-data; name=\"file_url\"; filename=\"dhamma.mp4\"\r\nContent-Type: video/mp4\r\n\r\n".encode() + video_bytes + f"\r\n--{boundary}--\r\n".encode()
# ใช้ source แบบ multipart
# Facebook ต้องการ field ชื่อ source
body2 = b""
body2 += f"--{boundary}\r\nContent-Disposition: form-data; name=\"description\"\r\n\r\n{caption}\r\n".encode()
body2 += f"--{boundary}\r\nContent-Disposition: form-data; name=\"access_token\"\r\n\r\n{TOKEN}\r\n".encode()
body2 += f"--{boundary}\r\nContent-Disposition: form-data; name=\"source\"; filename=\"dhamma.mp4\"\r\nContent-Type: video/mp4\r\n\r\n".encode() + video_bytes + f"\r\n--{boundary}--\r\n".encode()

req = urllib.request.Request(url, data=body2, headers={"Content-Type": f"multipart/form-data; boundary={boundary}"}, method="POST")
try:
    with urllib.request.urlopen(req, timeout=120) as r:
        print(f"Facebook ตอบ {r.status}: {r.read().decode()}")
        print("DONE - โพสต์วีดีโอแล้ว")
except Exception as e:
    try:
        print(f"Facebook ตอบ ERROR: {e.read().decode()}")
    except Exception:
        print(f"ERROR: {e}")
    raise SystemExit(1)
