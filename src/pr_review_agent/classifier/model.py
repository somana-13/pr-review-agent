import json
from functools import cache
from pathlib import Path

import torch
from peft import PeftModel
from transformers import AutoModelForSequenceClassification, AutoTokenizer

from pr_review_agent.classifier.preprocess import normalize_diff
from pr_review_agent.config import settings

BASE_MODEL = "microsoft/codebert-base"


@cache
def _load_classifier():
    tokenizer = AutoTokenizer.from_pretrained(settings.classifier_adapter_path)
    base_model = AutoModelForSequenceClassification.from_pretrained(BASE_MODEL, num_labels=2)
    model = PeftModel.from_pretrained(base_model, settings.classifier_adapter_path)
    model.eval()
    return tokenizer, model


@cache
def get_threshold() -> float:
    metadata_path = Path(settings.classifier_adapter_path) / "threshold.json"
    return json.loads(metadata_path.read_text())["threshold"]


def score_diff(diff: str) -> float:
    tokenizer, model = _load_classifier()
    text = normalize_diff(diff)
    inputs = tokenizer(text, truncation=True, padding=True, max_length=512, return_tensors="pt")
    with torch.no_grad():
        logits = model(**inputs).logits
    probs = torch.softmax(logits, dim=-1)
    return probs[0, 1].item()  # probability of the "security-relevant" class
