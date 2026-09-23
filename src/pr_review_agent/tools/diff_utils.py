import re

CHANGED_FILE_PATTERN = re.compile(r"^\+\+\+ b/(.+)$", re.MULTILINE)


def extract_changed_files(diff: str) -> list[str]:
    """Return paths of files added or modified in a unified diff (ignores deletions)."""
    return CHANGED_FILE_PATTERN.findall(diff)
