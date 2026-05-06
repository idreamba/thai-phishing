from pathlib import Path
from dotenv import load_dotenv
import os

from transformers import AutoModelForSequenceClassification, AutoTokenizer


load_dotenv()

hf_model_name = os.getenv(
    "HF_MODEL_NAME",
    "airesearch/wangchanberta-base-att-spm-uncased",
)
model_path = os.getenv("MODEL_PATH", "./models/wangchanberta-base")

Path(model_path).mkdir(parents=True, exist_ok=True)

print(f"Downloading model from: {hf_model_name}")
print(f"Saving to: {model_path}")

try:
    tokenizer = AutoTokenizer.from_pretrained(hf_model_name)
except ImportError:
    # Fallback for environments missing protobuf-backed fast tokenizer deps.
    tokenizer = AutoTokenizer.from_pretrained(hf_model_name, use_fast=False)
model = AutoModelForSequenceClassification.from_pretrained(
    hf_model_name,
    num_labels=len(os.getenv("LABELS", "legitimate,spam,scam,phishing,suspicious").split(",")),
    ignore_mismatched_sizes=True,
)

tokenizer.save_pretrained(model_path)
model.save_pretrained(model_path)

print("Done.")
