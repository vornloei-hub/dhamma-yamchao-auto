"""
Dhamma Yamchao - Auto Daily 06:00
For new GitHub account with new email (Dhamma only)
"""
import os, json, datetime, urllib.request

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
MAKE_WEBHOOK_URL = os.environ.get("MAKE_WEBHOOK_URL", "")

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

script = f"""{title} | ธรรมะยามเช้า - สติ [AI]

{message}

เช้านี้ ขอให้ใจสงบ มีสติ และมีความสุข
ธรรมะสั้นๆ เพื่อเริ่มวันใหม่ด้วยใจที่เบา

#ธรรมะยามเช้า #สติ #ธรรมะ #AI
"""

os.makedirs("output", exist_ok=True)
with open(f"output/{TODAY}-dhamma.txt", "w", encoding="utf-8") as f:
    f.write(script)

payload = {
    "date": TODAY,
    "topic": title,
    "title": f"{title} | ธรรมะยามเช้า - สติ [AI]",
    "caption": script,
    "ai_label": True,
    "page": "ธรรมะยามเช้า - สติ",
    "time": "06:00",
}
print(json.dumps(payload, ensure_ascii=False, indent=2))
if MAKE_WEBHOOK_URL:
    try:
        req = urllib.request.Request(MAKE_WEBHOOK_URL, data=json.dumps(payload, ensure_ascii=False).encode("utf-8"), headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req, timeout=20) as r:
            print("Webhook:", r.status)
    except Exception as e:
        print("Webhook failed:", e)
print("DONE Dhamma")
