from app.config import settings


UNSAFE_LABELS = {"spam", "scam", "phishing", "suspicious", "unsafe"}


def combine_risk(rule_score: float, model_score: dict | None) -> tuple[str, float, float]:
    if model_score is None:
        risk = rule_score
        label = "suspicious" if risk >= settings.warn_threshold else "legitimate"
        confidence = risk
        return label, round(risk, 4), round(confidence, 4)

    model_label = model_score["label"]
    model_confidence = float(model_score["confidence"])

    model_risk = model_confidence if model_label in UNSAFE_LABELS else 1.0 - model_confidence

    # production prototype: ให้ rule มีน้ำหนักสูง เพราะ phishing มักเปลี่ยน pattern เร็ว
    risk = (0.45 * rule_score) + (0.55 * model_risk)

    final_label = model_label
    if risk >= settings.block_threshold:
        final_label = "phishing" if model_label in {"phishing", "legitimate"} else model_label
    elif risk >= settings.high_risk_threshold and model_label == "legitimate":
        final_label = "suspicious"
    elif risk < settings.warn_threshold:
        final_label = "legitimate"

    return final_label, round(risk, 4), round(model_confidence, 4)


def decide_action(risk_score: float) -> str:
    if risk_score >= settings.block_threshold:
        return "block"
    if risk_score >= settings.high_risk_threshold:
        return "high_risk_warning"
    if risk_score >= settings.warn_threshold:
        return "warning"
    return "allow"
