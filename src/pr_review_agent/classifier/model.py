import json
from functools import cache
from pathlib import Path

import torch
from huggingface_hub import hf_hub_download
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
    adapter_path = Path(settings.classifier_adapter_path)
    if adapter_path.exists():
        metadata_path = adapter_path / "threshold.json"
    else:
        # not a local path -- treat it as a Hugging Face Hub repo id, same
        # as from_pretrained does implicitly for the model/tokenizer below
        metadata_path = Path(hf_hub_download(repo_id=settings.classifier_adapter_path, filename="threshold.json"))
    return json.loads(metadata_path.read_text())["threshold"]


def score_diff(diff: str) -> float:
    tokenizer, model = _load_classifier()
    text = normalize_diff(diff)
    inputs = tokenizer(text, truncation=True, padding=True, max_length=512, return_tensors="pt")
    with torch.no_grad():
        logits = model(**inputs).logits
    probs = torch.softmax(logits, dim=-1)
    return probs[0, 1].item()  # probability of the "security-relevant" class
