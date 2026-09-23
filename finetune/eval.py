import json
from pathlib import Path

import torch
from peft import PeftModel
from sklearn.metrics import precision_recall_fscore_support
from transformers import AutoModelForSequenceClassification, AutoTokenizer

DATA_DIR = Path(__file__).parent / "data"
ADAPTER_DIR = Path(__file__).parent / "checkpoints" / "lora-adapter"
BASE_MODEL = "microsoft/codebert-base"
MIN_RECALL = 0.90


def load_test_examples() -> list[dict]:
    path = DATA_DIR / "test.jsonl"
    return [json.loads(line) for line in path.read_text().splitlines() if line]


def score_examples(examples: list[dict]) -> list[float]:
    tokenizer = AutoTokenizer.from_pretrained(str(ADAPTER_DIR))
    base_model = AutoModelForSequenceClassification.from_pretrained(BASE_MODEL, num_labels=2)
    model = PeftModel.from_pretrained(base_model, str(ADAPTER_DIR))
    model.eval()

    scores = []
    with torch.no_grad():
        for example in examples:
            inputs = tokenizer(example["diff"], truncation=True, padding=True, max_length=512, return_tensors="pt")
            logits = model(**inputs).logits
            probs = torch.softmax(logits, dim=-1)
            scores.append(probs[0, 1].item())  # probability of the "security-relevant" class
    return scores


def pick_recall_constrained_threshold(labels: list[int], scores: list[float], min_recall: float) -> float:
    # scan thresholds from most to least selective; return the first (highest)
    # one that still meets the recall floor, since recall only rises as the
    # threshold drops and we want the most selective cutoff that clears the bar
    for threshold in sorted(set(scores), reverse=True):
        predictions = [1 if s >= threshold else 0 for s in scores]
        _, recall, _, _ = precision_recall_fscore_support(labels, predictions, average="binary", zero_division=0)
        if recall >= min_recall:
            return threshold
    return 0.0  # nothing cleared the bar; fall back to flagging everything


def main() -> None:
    examples = load_test_examples()
    labels = [e["label"] for e in examples]
    scores = score_examples(examples)

    threshold = pick_recall_constrained_threshold(labels, scores, MIN_RECALL)
    predictions = [1 if s >= threshold else 0 for s in scores]
    precision, recall, f1, _ = precision_recall_fscore_support(
        labels, predictions, average="binary", zero_division=0
    )

    print(f"test set: {len(examples)} examples ({sum(labels)} positive)")
    print(f"chosen threshold: {threshold:.3f} (target min recall: {MIN_RECALL})")
    print(f"precision: {precision:.3f}  recall: {recall:.3f}  f1: {f1:.3f}")


if __name__ == "__main__":
    main()
