# Metrics Guide for Thai Phishing Model

เอกสารนี้สรุป metric ที่เห็นจากการ train ใน `train.py` และแนวทางดูผลว่าโมเดล "ดีพอใช้หรือยัง"

underfit คือโมเดล “เรียนรู้ไม่พอ” จับแพทเทิร์นไม่ได้ทั้ง train และ eval
อาการที่เห็น: train_loss สูง, eval_loss สูง และผลไม่ค่อยดีทั้งคู่

overfit คือโมเดล “จำชุด train มากเกินไป” แต่ใช้กับข้อมูลใหม่ไม่ดี
อาการที่เห็น: train_loss ต่ำลงเรื่อยๆ แต่ eval_loss ไม่ลงหรือแย่ลง

สั้นๆ:

underfit = ยังไม่เก่งพอ
overfit = เก่งเฉพาะข้อสอบเก่า


## 1) Metrics ที่มีอยู่ตอนนี้ (จาก Hugging Face Trainer)

- `train_loss`
ความผิดพลาดเฉลี่ยบนชุด train ช่วงท้ายการฝึก ยิ่งต่ำยิ่งดี แต่ไม่พอใช้ตัดสินคุณภาพจริงลำพัง

- `eval_loss`
ความผิดพลาดบนชุด eval (ข้อมูลที่ไม่ใช้ฝึก) ตัวนี้สำคัญที่สุดในสคริปต์ปัจจุบันสำหรับเช็กว่าโมเดล generalize ได้หรือไม่

- `train_runtime`
เวลาฝึกทั้งหมด (วินาที) ใช้ดูต้นทุนเวลา ไม่ได้บอกความแม่นยำ

- `train_samples_per_second`
จำนวนตัวอย่างที่ฝึกได้ต่อวินาที ใช้ดูความเร็ว pipeline

- `train_steps_per_second`
จำนวน training steps ต่อวินาที ใช้ดูประสิทธิภาพระบบ

- `epoch`
รอบการฝึกที่ metric นั้นถูกบันทึก

- `eval_runtime`
เวลา evaluate

- `eval_samples_per_second`
ความเร็วตอน evaluate

- `eval_steps_per_second`
จำนวน eval steps ต่อวินาที

### เริ่มที่ 3-5 epochs ก่อนครับสำหรับชุด 20,000 แถวนี้

แนวทางใช้งานจริง:

- เริ่ม 3 epochs แล้วดู eval_loss
- ถ้า eval_loss ยังลงต่อชัดเจน ค่อยเพิ่มเป็น 5
- ถ้า eval_loss แย่ลงหรือแกว่ง แปลว่าเริ่ม overfit ให้หยุด

สำหรับโปรเจกต์นี้ แนะนำค่าตั้งต้น:

- รอบแรก: --epochs 3
- รอบสอง (ลองเพิ่ม): --epochs 5 แล้วเทียบผล
- เกิน 8-10 มักไม่คุ้ม เว้นแต่จูน hyperparameter เพิ่ม

## 2) ควรสนใจตัวไหนก่อน

ลำดับแนะนำ:

1. `eval_loss` (สำคัญสุดตอนนี้)
2. แนวโน้ม `eval_loss` เทียบแต่ละ epoch (ลดลงต่อเนื่อง = ดี)
3. ช่องว่าง `train_loss` กับ `eval_loss` (ถ้า train ต่ำมากแต่ eval ไม่ลง = เสี่ยง overfit)
4. `train_runtime` และ throughput metrics (ใช้ optimize เวลา/ทรัพยากร)

## 3) วิธีอ่านผลเร็วๆ หลัง train

- กรณีดี:
`eval_loss` ลดลงทุก epoch หรือใกล้คงที่ที่ค่าต่ำ

- เริ่ม overfit:
`train_loss` ลดลงเรื่อยๆ แต่ `eval_loss` แย่ลง

- ยัง underfit:
ทั้ง `train_loss` และ `eval_loss` ยังสูง และแทบไม่ลด

## 4) สำหรับงาน Phishing/Scam ควรเพิ่ม metric อะไร

ตอนนี้สคริปต์ยังไม่มี metric แบบจำแนกคลาสโดยตรง ควรเพิ่มอย่างน้อย:

1. `macro_f1` (สำคัญมาก)
เหมาะกับงานหลายคลาสและข้อมูลอาจไม่สมดุลในอนาคต

2. `recall_phishing` และ `recall_scam`
งานปลอดภัยควรพลาดเคสอันตรายให้น้อยที่สุด (ลด false negative)

3. `precision_phishing` และ `precision_scam`
ควบคุม false positive ไม่ให้เตือนพร่ำเพรื่อเกินไป

4. `confusion_matrix`
ดูว่าคลาสไหนสับสนกับคลาสไหน เช่น `phishing` ถูกทายเป็น `legitimate`

## 5) KPI ที่แนะนำสำหรับใช้งานจริง (ตั้งต้น)

- โฟกัสหลัก:
`macro_f1`, `recall_phishing`, `recall_scam`

- เกณฑ์ตั้งต้น (ปรับตามความเสี่ยงธุรกิจ):
1. `recall_phishing >= 0.90`
2. `recall_scam >= 0.85`
3. `macro_f1 >= 0.80`

ถ้า trade-off ต้องเลือกระหว่าง recall กับ precision สำหรับระบบกันโกง: ให้รักษา recall ของคลาสอันตรายก่อน แล้วค่อยปรับ threshold เพื่อลด false positive

## เกณฑ์ตัดสินใจ
0.00 - 0.39 = Safe

0.40 - 0.69 = Warning

0.70 - 0.89 = High Risk

0.90 - 1.00 = Block