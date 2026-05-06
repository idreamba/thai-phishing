from pydantic import BaseModel, Field


class DetectRequest(BaseModel):
    text: str = Field(..., min_length=1, examples=[
        "บัญชีคุณถูกระงับ กรุณายืนยันข้อมูลที่ bit.ly/abc ภายใน 24 ชม."
    ])


class ModelScore(BaseModel):
    label: str
    confidence: float
    probabilities: dict[str, float]


class DetectResponse(BaseModel):
    label: str
    risk_score: float
    confidence: float
    action: str
    reasons: list[str]
    rule_score: float
    model_score: ModelScore | None = None
