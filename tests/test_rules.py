from app.rules import evaluate_rules


def test_high_risk_text():
    text = "บัญชีคุณถูกระงับ กรุณายืนยันข้อมูลที่ bit.ly/abc ภายใน 24 ชม."
    score, reasons = evaluate_rules(text)
    assert score >= 0.5
    assert len(reasons) > 0


def test_low_risk_text():
    text = "ประชุมทีมวันนี้เวลา 10 โมง"
    score, reasons = evaluate_rules(text)
    assert score < 0.4
