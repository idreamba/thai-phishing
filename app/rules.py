import re
from urllib.parse import urlparse

URL_PATTERN = re.compile(
    r"(https?://[^\s]+|www\.[^\s]+|[a-zA-Z0-9.-]+\.(?:com|net|org|co|th|io|app|xyz|info|top|site|online)[^\s]*)",
    re.IGNORECASE,
)

SHORTENER_DOMAINS = {
    "bit.ly",
    "tinyurl.com",
    "t.co",
    "goo.gl",
    "ow.ly",
    "cutt.ly",
    "is.gd",
    "s.id",
    "rebrand.ly",
    "shorturl.at",
}

URGENCY_KEYWORDS = [
    "ด่วน",
    "ภายใน 24 ชม",
    "ภายใน24ชม",
    "ทันที",
    "ก่อนถูกระงับ",
    "ระงับบัญชี",
    "บัญชีถูกระงับ",
    "หมดเขต",
    "หากไม่ดำเนินการ",
]

CREDENTIAL_KEYWORDS = [
    "ยืนยันข้อมูล",
    "เข้าสู่ระบบ",
    "login",
    "password",
    "รหัสผ่าน",
    "otp",
    "pin",
    "เลขบัตร",
    "ข้อมูลส่วนตัว",
    "ยืนยันตัวตน",
]

MONEY_KEYWORDS = [
    "โอนเงิน",
    "ชำระเงิน",
    "ค่าธรรมเนียม",
    "กู้เงิน",
    "เงินด่วน",
    "รับเงิน",
    "รางวัล",
    "เครดิตฟรี",
    "ลงทุน",
    "ผลตอบแทน",
]

BRAND_IMPERSONATION_KEYWORDS = [
    "ธนาคาร",
    "kbank",
    "scb",
    "กรุงไทย",
    "ktb",
    "ออมสิน",
    "ไปรษณีย์",
    "flash",
    "kerry",
    "dhl",
    "ตำรวจ",
    "กรมสรรพากร",
    "line official",
]


def extract_urls(text: str) -> list[str]:
    return URL_PATTERN.findall(text)


def _domain_from_url(url: str) -> str:
    if not url.startswith(("http://", "https://")):
        url = "http://" + url
    parsed = urlparse(url)
    return parsed.netloc.lower().replace("www.", "")


def evaluate_rules(text: str) -> tuple[float, list[str]]:
    lower = text.lower()
    reasons: list[str] = []
    score = 0.0

    urls = extract_urls(text)
    if urls:
        score += 0.20
        reasons.append("พบ URL ในข้อความ")

        for url in urls:
            domain = _domain_from_url(url)
            if domain in SHORTENER_DOMAINS:
                score += 0.25
                reasons.append("พบลิงก์ย่อ")
                break

            if any(domain.endswith(tld) for tld in [".xyz", ".top", ".site", ".online", ".info"]):
                score += 0.15
                reasons.append("พบโดเมนที่มีความเสี่ยงสูง")

    if any(k in lower for k in URGENCY_KEYWORDS):
        score += 0.20
        reasons.append("พบคำเร่งด่วนหรือข่มขู่ให้รีบดำเนินการ")

    if any(k in lower for k in CREDENTIAL_KEYWORDS):
        score += 0.25
        reasons.append("พบคำเกี่ยวกับการยืนยันข้อมูล/รหัสผ่าน/OTP")

    if any(k in lower for k in MONEY_KEYWORDS):
        score += 0.15
        reasons.append("พบคำเกี่ยวกับเงิน การโอน หรือผลประโยชน์")

    if any(k in lower for k in BRAND_IMPERSONATION_KEYWORDS):
        score += 0.10
        reasons.append("พบการอ้างถึงองค์กร/แบรนด์ที่มักถูกปลอมแปลง")

    score = min(score, 1.0)

    if not reasons:
        reasons.append("ไม่พบ rule ที่มีความเสี่ยงชัดเจน")

    return score, reasons
