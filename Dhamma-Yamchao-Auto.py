"""
Dhamma Yamchao - Auto Post to Facebook Page DIRECTLY (No Make needed)
Runs 06:00 Bangkok daily, posts to Facebook Page via Graph API
Needs secrets: GEMINI_API_KEY, FACEBOOK_PAGE_ID, FACEBOOK_PAGE_ACCESS_TOKEN
"""
import os, json, datetime, urllib.request, urllib.parse

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
PAGE_ID = os.environ.get("FACEBOOK_PAGE_ID", "")
PAGE_TOKEN = os.environ.get("FACEBOOK_PAGE_ACCESS_TOKEN", "")

TODAY = datetime.date.today().isoformat()
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

caption = f"""{title} | ธรรมะยามเช้า - สติ [AI]

{message}

เช้านี้ ขอให้ใจสงบ มีสติ และมีความสุข
ธรรมะสั้นๆ เพื่อเริ่มวันใหม่ด้วยใจที่เบา

#ธรรมะยามเช้า #สติ #ธรรมะ #AI
"""

print(caption)
if not PAGE_ID or not PAGE_TOKEN:
    print("No Facebook Page Token yet - skipping post, but script OK")
    print("Add FACEBOOK_PAGE_ID + FACEBOOK_PAGE_ACCESS_TOKEN in Secrets to enable auto post")
else:
    try:
        url = f"https://graph.facebook.com/v21.0/{PAGE_ID}/feed"
        data = urllib.parse.urlencode({"message": caption, "access_token": PAGE_TOKEN}).encode()
        req = urllib.request.Request(url, data=data, method="POST")
        with urllib.request.urlopen(req, timeout=30) as r:
            print("Facebook post result:", r.read().decode())
    except Exception as e:
        print("Facebook post failed:", e)
print("DONE")
