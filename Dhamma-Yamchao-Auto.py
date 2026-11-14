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
    import json as _json
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
    # ใช้ภาษาอังกฤษบนรูปกันฟอนต์ไทยเพี้ยน ส่วนตัวอักษรไทยอยู่ใต้โพสต์แล้ว
    draw.text((W//2, 700), "Dhamma Yamchao - Sati", font=font(60), fill=(80, 40, 0), anchor="mm")
    draw.text((W//2, 820), "Lao Su Kan...", font=font(52), fill=(120, 60, 0), anchor="mm")
    draw.text((W//2, 1000), "Dhamma for Today", font=font(64), fill=(60, 30, 0), anchor="mm")
    draw.text((W//2, 1250), "Mindfulness for a new day", font=font(38), fill=(80, 50, 10), anchor="mm")
    draw.text((W//2, 1750), "[AI] Dhamma for new day", font=font(34), fill=(120, 80, 0), anchor="mm")
    img.save("dhamma.jpg", quality=92)
    print("สร้างรูปแล้ว", flush=True)
    cmd = ["ffmpeg", "-y", "-loop", "1", "-i", "dhamma.jpg", "-t", "15", "-vf", "scale=1080:1920,format=yuv420p", "-c:v", "libx264", "-r", "25", "-movflags", "+faststart", "dhamma.mp4"]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print(res.stderr[-1500:], flush=True)
        raise RuntimeError("ffmpeg พัง")
    print("สร้างวีดีโอแล้ว", flush=True)
    import os as _os
    file_size = _os.path.getsize("dhamma.mp4")
    print(f"ขนาดวีดีโอ: {file_size} bytes", flush=True)
    # ขั้นที่ 1: เริ่มอัปโหลด Reels - ขอ upload_url
    start_url = f"https://graph.facebook.com/v21.0/{PAGE_ID}/video_reels"
    start_data = urllib.parse.urlencode({"access_token": TOKEN, "video_state": "PUBLISHED", "upload_phase": "start", "file_size": str(file_size), "description": caption}).encode()
    start_req = urllib.request.Request(start_url, data=start_data, headers={"Content-Type": "application/x-www-form-urlencoded"}, method="POST")
    with urllib.request.urlopen(start_req, timeout=60) as r:
        start_body = r.read().decode()
        print(f"Reels start {r.status}: {start_body}", flush=True)
        start_json = _json.loads(start_body)
    video_id = start_json.get("video_id")
    upload_url = start_json.get("upload_url")
    if not video_id or not upload_url:
        raise RuntimeError(f"เริ่มอัปโหลด Reels ไม่ได้: {start_body}")
    # ขั้นที่ 2: อัปโหลดไฟล์วีดีโอไปที่ upload_url
    with open("dhamma.mp4", "rb") as f:
        vb = f.read()
    up_req = urllib.request.Request(upload_url, data=vb, headers={"Content-Type": "application/octet-stream", "Content-Length": str(len(vb))}, method="POST")
    # Facebook Reels upload ใช้ PUT บางครั้ง ใช้ POST ก็ได้ ลอง POST ก่อน
    try:
        with urllib.request.urlopen(up_req, timeout=120) as r:
            print(f"Reels upload {r.status}: {r.read().decode()[:500]}", flush=True)
    except Exception as e:
        # ลอง PUT
        print(f"Upload POST พัง ลอง PUT: {e}", flush=True)
        up_req2 = urllib.request.Request(upload_url, data=vb, headers={"Content-Type": "application/octet-stream", "Content-Length": str(len(vb))}, method="PUT")
        with urllib.request.urlopen(up_req2, timeout=120) as r:
            print(f"Reels upload PUT {r.status}: {r.read().decode()[:500]}", flush=True)
    # ขั้นที่ 3: จบการอัปโหลด - publish
    finish_url = f"https://graph.facebook.com/v21.0/{PAGE_ID}/video_reels"
    finish_data = urllib.parse.urlencode({"access_token": TOKEN, "video_state": "PUBLISHED", "upload_phase": "finish", "video_id": video_id, "description": caption}).encode()
    finish_req = urllib.request.Request(finish_url, data=finish_data, headers={"Content-Type": "application/x-www-form-urlencoded"}, method="POST")
    with urllib.request.urlopen(finish_req, timeout=60) as r:
        print(f"Reels finish {r.status}: {r.read().decode()}", flush=True)
        print("DONE - โพสต์ Reels แล้ว", flush=True)

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
