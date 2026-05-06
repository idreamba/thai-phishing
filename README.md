# Thai Phishing & Scam Text Detection Prototype

Prototype สำหรับตรวจจับข้อความ Phishing / Scam ภาษาไทย

## Features

- FastAPI REST API
- Rule-based scam detection
- URL / short link detection
- WangchanBERTa inference
- กำหนด `MODEL_PATH` เองได้ผ่าน `.env`
- รองรับ local model สำหรับ production/offline deployment
- มี script สำหรับ preload model จาก Hugging Face
- มี script สำหรับ fine-tune เบื้องต้น

---

## 1. ติดตั้ง
ต้องใช้ python3.11 ไม่งั้นมัน error

```bash

brew install python@3.11
brew install cmake pkg-config sentencepiece

python3.11 -m venv .venv
source .venv/bin/activate

python --version
# -- python 3.11


#อัพเกรดก่อน ไม่งั้นอาจเจอ eror ตอนติดตั้ง
pip install --upgrade pip

python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

cp .env.example .env
```

ถ้ายังติด sentcepiece ให้ลองลงตรงๆ ก่อน
```bash
pip install sentencepiece==0.2.0
pip install -r requirements.txt
```

Windows:

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

---

## 2. โหลด WangchanBERTa มาเก็บ local

ค่า default จะโหลดจาก:

```text
airesearch/wangchanberta-base-att-spm-uncased
```

รัน:

```bash
python scripts/preload_model.py
```

ไฟล์จะถูกบันทึกไว้ที่:

```text
./models/wangchanberta-base
```

---

## 3. รัน API

```bash
uvicorn app.main:app --reload --port 8000
```

เปิด Swagger:

```text
http://localhost:8000/docs
```

---

## 4. ทดสอบ API

```bash
curl -X POST http://localhost:8000/detect \
  -H "Content-Type: application/json" \
  -d '{"text":"บัญชีคุณถูกระงับ กรุณายืนยันข้อมูลที่ bit.ly/abc ภายใน 24 ชม."}'
```

ตัวอย่าง response:

```json
{
  "label": "phishing",
  "risk_score": 0.91,
  "confidence": 0.84,
  "action": "block",
  "reasons": [
    "พบลิงก์ย่อ",
    "พบคำเร่งด่วน",
    "พบคำเกี่ยวกับการยืนยันข้อมูล"
  ]
}
```

---

## 5. ตั้งค่า MODEL_PATH เอง

แก้ไฟล์ `.env`

```env
MODEL_PATH=./models/wangchanberta-base
LOCAL_FILES_ONLY=true
```

ถ้า fine-tune แล้ว ให้ชี้ไปที่ model ใหม่:

```env
MODEL_PATH=./models/scam-detector-v1
LOCAL_FILES_ONLY=true
```

---

## 6. Fine-tune

เตรียม CSV format:

```csv
text,label
"บัญชีคุณถูกระงับ กรุณายืนยันข้อมูล",phishing
"โปรโมชันใหม่จากร้านค้า",legitimate
```

รัน:

```bash
python train.py --csv data/sample_train.csv --output_dir ./models/scam-detector-v1 --epochs 3
```

จากนั้นแก้ `.env`:

```env
MODEL_PATH=./models/scam-detector-v1
LOCAL_FILES_ONLY=true
```

---

## 7. Docker

```bash
docker build -t thai-phishing-api .
docker run --env-file .env -p 8000:8000 thai-phishing-api
```

---

## Production Note

ระบบนี้เป็น prototype สำหรับทดลองจริง ควรต่อยอดเพิ่ม:

- PostgreSQL สำหรับเก็บ logs / feedback
- Redis / Queue สำหรับ batch processing
- MLflow สำหรับ model registry
- Monitoring false positive / false negative
- URL reputation service
- Human review workflow
