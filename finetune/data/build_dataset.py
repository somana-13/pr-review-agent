import json
import random
from pathlib import Path

from pr_review_agent.classifier.preprocess import normalize_diff

DATA_DIR = Path(__file__).parent
SPLIT_RATIOS = {"train": 0.7, "val": 0.15, "test": 0.15}


def load_examples() -> list[dict]:
    examples = []
    for filename in ("gold_positive.jsonl", "labeled_pool.jsonl"):
        path = DATA_DIR / filename
        for line in path.read_text().splitlines():
            if line:
                examples.append(json.loads(line))
    return examples


def repo_level_split(examples: list[dict], seed: int = 42) -> dict[str, list[dict]]:
    by_repo: dict[str, list[dict]] = {}
    for example in examples:
        by_repo.setdefault(example["repo"], []).append(example)

    repos = list(by_repo.keys())
    random.Random(seed).shuffle(repos)

    total = len(examples)
    targets = {name: ratio * total for name, ratio in SPLIT_RATIOS.items()}
    splits: dict[str, list[dict]] = {"train": [], "val": [], "test": []}

    for repo in repos:
        # assign each repo's examples wholesale to whichever split is furthest below its target
        deficits = {name: targets[name] - len(splits[name]) for name in splits}
        target_split = max(deficits, key=deficits.get)
        splits[target_split].extend(by_repo[repo])

    return splits


def build_dataset() -> None:
    examples = load_examples()
    for example in examples:
        example["diff"] = normalize_diff(example["diff"])

    splits = repo_level_split(examples)
    for name, split_examples in splits.items():
        out_path = DATA_DIR / f"{name}.jsonl"
        out_path.write_text("\n".join(json.dumps(e) for e in split_examples) + "\n")
        positive = sum(e["label"] for e in split_examples)
        print(f"{name}: {len(split_examples)} examples ({positive} positive)")


if __name__ == "__main__":
    build_dataset()
