import argparse
from pathlib import Path
from datetime import datetime, timezone

import pandas as pd
from datasets import Dataset
from dotenv import load_dotenv
import os

from sklearn.model_selection import train_test_split
from transformers import (
    AutoModelForSequenceClassification,
    AutoTokenizer,
    DataCollatorWithPadding,
    Trainer,
    TrainingArguments,
)


load_dotenv()


def _write_report(
    output_dir: Path,
    args: argparse.Namespace,
    train_df: pd.DataFrame,
    eval_df: pd.DataFrame,
    labels: list[str],
    train_metrics: dict,
    eval_metrics: dict,
) -> None:
    label_counts = train_df["label"].value_counts().sort_index()
    eval_label_counts = eval_df["label"].value_counts().sort_index()
    utc_now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    lines = [
        "# Training Report",
        "",
        f"- Generated at: {utc_now}",
        f"- Base model: `{args.base_model}`",
        f"- Input CSV: `{args.csv}`",
        f"- Output dir: `{args.output_dir}`",
        f"- Epochs: {args.epochs}",
        "",
        "## Dataset",
        "",
        f"- Total rows: {len(train_df) + len(eval_df)}",
        f"- Train rows: {len(train_df)}",
        f"- Eval rows: {len(eval_df)}",
        f"- Labels: {', '.join(labels)}",
        "",
        "### Train Label Distribution",
        "",
    ]

    for label in labels:
        lines.append(f"- {label}: {int(label_counts.get(label, 0))}")

    lines.extend(["", "### Eval Label Distribution", ""])
    for label in labels:
        lines.append(f"- {label}: {int(eval_label_counts.get(label, 0))}")

    lines.extend(["", "## Metrics", ""])
    for key in sorted(train_metrics.keys()):
        lines.append(f"- {key}: {train_metrics[key]}")
    for key in sorted(eval_metrics.keys()):
        lines.append(f"- {key}: {eval_metrics[key]}")

    report_path = output_dir / "report.md"
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", required=True, help="CSV file with text,label columns")
    parser.add_argument("--output_dir", default="./models/scam-detector-v1")
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--base_model", default=os.getenv("HF_MODEL_NAME", "airesearch/wangchanberta-base-att-spm-uncased"))
    args = parser.parse_args()

    df = pd.read_csv(args.csv)
    if "text" not in df.columns or "label" not in df.columns:
        raise ValueError("CSV must contain text,label columns")
    if len(df) < 2:
        raise ValueError("Need at least 2 rows to split train/eval datasets")

    labels = sorted(df["label"].unique().tolist())
    label2id = {label: idx for idx, label in enumerate(labels)}
    id2label = {idx: label for label, idx in label2id.items()}

    df["label_id"] = df["label"].map(label2id)

    n_samples = len(df)
    n_classes = df["label_id"].nunique()
    min_class_count = int(df["label_id"].value_counts().min())

    # sklearn stratified split requires enough rows in each class and eval set size
    # at least equal to the number of classes.
    can_stratify = n_classes > 1 and min_class_count >= 2 and n_samples >= (2 * n_classes)
    test_count = max(1, int(round(n_samples * 0.2)))
    if can_stratify:
        test_count = max(test_count, n_classes)

    train_df, eval_df = train_test_split(
        df,
        test_size=test_count,
        stratify=df["label_id"] if can_stratify else None,
        random_state=42,
    )

    tokenizer = AutoTokenizer.from_pretrained(args.base_model)

    def tokenize(batch):
        return tokenizer(
            batch["text"],
            truncation=True,
            max_length=256,
        )

    train_ds = Dataset.from_pandas(train_df[["text", "label_id"]]).rename_column("label_id", "labels")
    eval_ds = Dataset.from_pandas(eval_df[["text", "label_id"]]).rename_column("label_id", "labels")

    train_ds = train_ds.map(tokenize, batched=True)
    eval_ds = eval_ds.map(tokenize, batched=True)

    model = AutoModelForSequenceClassification.from_pretrained(
        args.base_model,
        num_labels=len(labels),
        id2label=id2label,
        label2id=label2id,
        ignore_mismatched_sizes=True,
    )

    training_args = TrainingArguments(
        output_dir=args.output_dir,
        learning_rate=2e-5,
        per_device_train_batch_size=8,
        per_device_eval_batch_size=8,
        num_train_epochs=args.epochs,
        weight_decay=0.01,
        evaluation_strategy="epoch",
        save_strategy="epoch",
        load_best_model_at_end=True,
        logging_steps=10,
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_ds,
        eval_dataset=eval_ds,
        tokenizer=tokenizer,
        data_collator=DataCollatorWithPadding(tokenizer=tokenizer),
    )

    train_result = trainer.train()
    eval_metrics = trainer.evaluate()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    trainer.save_model(output_dir)
    tokenizer.save_pretrained(output_dir)

    labels_path = output_dir / "labels.txt"
    labels_path.write_text("\n".join(labels), encoding="utf-8")
    _write_report(
        output_dir=output_dir,
        args=args,
        train_df=train_df,
        eval_df=eval_df,
        labels=labels,
        train_metrics=train_result.metrics,
        eval_metrics=eval_metrics,
    )

    print(f"Saved fine-tuned model to: {args.output_dir}")
    print(f"Labels: {labels}")
    print(f"Training report saved to: {output_dir / 'REPORTS.md'}")


if __name__ == "__main__":
    main()
