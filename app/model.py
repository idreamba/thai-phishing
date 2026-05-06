from __future__ import annotations

from pathlib import Path
import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer

from app.config import settings


class ScamTextModel:
    def __init__(self) -> None:
        self.model_path = settings.model_path
        self.labels = list(settings.labels)
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.tokenizer = None
        self.model = None
        self.enabled = False
        self.load_error: str | None = None

    def load(self) -> None:
        try:
            path = self.model_path

            try:
                self.tokenizer = AutoTokenizer.from_pretrained(
                    path,
                    local_files_only=settings.local_files_only,
                )
            except ImportError:
                # Fallback to slow tokenizer when fast tokenizer backend is unavailable.
                self.tokenizer = AutoTokenizer.from_pretrained(
                    path,
                    local_files_only=settings.local_files_only,
                    use_fast=False,
                )

            self.model = AutoModelForSequenceClassification.from_pretrained(
                path,
                local_files_only=settings.local_files_only,
            )

            self.model.to(self.device)
            self.model.eval()
            self.enabled = True

        except Exception as exc:
            self.enabled = False
            self.load_error = str(exc)

    def predict(self, text: str) -> dict | None:
        if not self.enabled or self.tokenizer is None or self.model is None:
            return None

        inputs = self.tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            padding=True,
            max_length=256,
        )

        inputs = {key: value.to(self.device) for key, value in inputs.items()}

        with torch.no_grad():
            outputs = self.model(**inputs)
            probs = torch.softmax(outputs.logits, dim=-1)[0].detach().cpu().tolist()

        # ถ้า label count จาก config ไม่ตรงกับจำนวน logits ให้สร้าง fallback labels
        if len(self.labels) != len(probs):
            labels = [f"class_{i}" for i in range(len(probs))]
        else:
            labels = self.labels

        probabilities = {
            label: round(float(prob), 6)
            for label, prob in zip(labels, probs)
        }

        best_label = max(probabilities, key=probabilities.get)
        confidence = probabilities[best_label]

        return {
            "label": best_label,
            "confidence": confidence,
            "probabilities": probabilities,
        }


model_service = ScamTextModel()
