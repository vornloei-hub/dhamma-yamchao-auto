import os, json, datetime, urllib.request, urllib.parse, sys

# GitHub -> Facebook ตรง ไม่ใช้ Make แล้ว
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
print(f"Page ID: {PAGE_ID}")
print(f"DRY_RUN: {DRY_RUN}")

if DRY_RUN:
    print("DRY_RUN=1 ไม่โพสต์จริง")
    print("DONE")
    raise SystemExit(0)

if not TOKEN:
    print("ERROR: ไม่มี FACEBOOK_PAGE_ACCESS_TOKEN ใน Secrets")
    raise SystemExit(1)

if not PAGE_ID or PAGE_ID == "61596776541126":
    print("ERROR: PAGE_ID ยังเป็นตัวเก่า ต้องเป็น 1338551616018917")
    raise SystemExit(1)

url = f"https://graph.facebook.com/v21.0/{PAGE_ID}/feed"
data = urllib.parse.urlencode({"message": caption, "access_token": TOKEN}).encode()
req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/x-www-form-urlencoded"}, method="POST")
try:
    with urllib.request.urlopen(req, timeout=30) as r:
        body = r.read().decode()
        print(f"Facebook ตอบ {r.status}: {body}")
        print("DONE - โพสต์ลงเพจแล้ว")
except Exception as e:
    try:
        body = e.read().decode()
    except Exception:
        body = str(e)
    print(f"Facebook ตอบ ERROR: {body}")
    raise SystemExit(1)
