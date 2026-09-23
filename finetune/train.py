import json
from pathlib import Path

import numpy as np
import torch
from datasets import Dataset
from peft import LoraConfig, TaskType, get_peft_model
from sklearn.metrics import accuracy_score, precision_recall_fscore_support
from transformers import (
    AutoModelForSequenceClassification,
    AutoTokenizer,
    Trainer,
    TrainingArguments,
)

DATA_DIR = Path(__file__).parent / "data"
OUTPUT_DIR = Path(__file__).parent / "checkpoints"
BASE_MODEL = "microsoft/codebert-base"


def load_split(name: str) -> Dataset:
    path = DATA_DIR / f"{name}.jsonl"
    rows = [json.loads(line) for line in path.read_text().splitlines() if line]
    return Dataset.from_list(rows)


def compute_metrics(eval_pred):
    logits, labels = eval_pred
    predictions = np.argmax(logits, axis=-1)
    precision, recall, f1, _ = precision_recall_fscore_support(
        labels, predictions, average="binary", zero_division=0
    )
    return {
        "accuracy": accuracy_score(labels, predictions),
        "precision": precision,
        "recall": recall,
        "f1": f1,
    }


def main() -> None:
    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL)

    def tokenize(batch):
        return tokenizer(batch["diff"], truncation=True, padding="max_length", max_length=512)

    train_ds = load_split("train").map(tokenize, batched=True)
    val_ds = load_split("val").map(tokenize, batched=True)

    base_model = AutoModelForSequenceClassification.from_pretrained(BASE_MODEL, num_labels=2)

    lora_config = LoraConfig(
        r=8,
        lora_alpha=16,
        target_modules=["query", "value"],
        task_type=TaskType.SEQ_CLS,
    )
    model = get_peft_model(base_model, lora_config)
    model.print_trainable_parameters()

    device = "mps" if torch.backends.mps.is_available() else "cpu"
    model.to(device)

    training_args = TrainingArguments(
        output_dir=str(OUTPUT_DIR),
        num_train_epochs=3,
        per_device_train_batch_size=4,
        per_device_eval_batch_size=4,
        eval_strategy="epoch",
        save_strategy="no",
        logging_steps=5,
        learning_rate=2e-4,
        report_to=[],
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_ds,
        eval_dataset=val_ds,
        compute_metrics=compute_metrics,
    )
    trainer.train()

    adapter_dir = OUTPUT_DIR / "lora-adapter"
    model.save_pretrained(str(adapter_dir))
    tokenizer.save_pretrained(str(adapter_dir))
    print(f"Saved adapter to {adapter_dir}")


if __name__ == "__main__":
    main()
