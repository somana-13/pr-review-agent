MAX_DIFF_CHARS = 4_000  # roughly fits CodeBERT's 512-token limit


def normalize_diff(diff: str) -> str:
    return diff.strip()[:MAX_DIFF_CHARS]
