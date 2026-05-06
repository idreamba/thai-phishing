from fastapi import FastAPI

from app.model import model_service
from app.preprocess import normalize_text
from app.rules import evaluate_rules
from app.scoring import combine_risk, decide_action
from app.schemas import DetectRequest, DetectResponse, ModelScore


app = FastAPI(
    title="Thai Phishing & Scam Text Detection API",
    version="1.0.0",
)


@app.on_event("startup")
def startup_event() -> None:
    model_service.load()


@app.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "model_enabled": model_service.enabled,
        "model_path": model_service.model_path,
        "model_load_error": model_service.load_error,
    }


@app.post("/detect", response_model=DetectResponse)
def detect(payload: DetectRequest) -> DetectResponse:
    text = normalize_text(payload.text)

    rule_score, reasons = evaluate_rules(text)
    raw_model_score = model_service.predict(text)

    label, risk_score, confidence = combine_risk(rule_score, raw_model_score)
    action = decide_action(risk_score)

    model_score = None
    if raw_model_score:
        model_score = ModelScore(
            label=raw_model_score["label"],
            confidence=raw_model_score["confidence"],
            probabilities=raw_model_score["probabilities"],
        )

    if raw_model_score is None:
        reasons.append("ยังไม่ได้โหลดโมเดล หรือใช้ rule-based fallback")

    return DetectResponse(
        label=label,
        risk_score=risk_score,
        confidence=confidence,
        action=action,
        reasons=reasons,
        rule_score=rule_score,
        model_score=model_score,
    )
