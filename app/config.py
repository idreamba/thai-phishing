import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


def _bool_env(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def _float_env(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, default))
    except ValueError:
        return default


@dataclass(frozen=True)
class Settings:
    model_path: str = os.getenv("MODEL_PATH", "./models/wangchanberta-base")
    hf_model_name: str = os.getenv(
        "HF_MODEL_NAME",
        "airesearch/wangchanberta-base-att-spm-uncased",
    )
    local_files_only: bool = _bool_env("LOCAL_FILES_ONLY", False)
    labels: tuple[str, ...] = tuple(
        item.strip()
        for item in os.getenv(
            "LABELS",
            "legitimate,spam,scam,phishing,suspicious",
        ).split(",")
        if item.strip()
    )
    warn_threshold: float = _float_env("WARN_THRESHOLD", 0.40)
    high_risk_threshold: float = _float_env("HIGH_RISK_THRESHOLD", 0.70)
    block_threshold: float = _float_env("BLOCK_THRESHOLD", 0.90)


settings = Settings()
