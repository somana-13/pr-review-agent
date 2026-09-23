import json
from pathlib import Path

from langchain_core.tools import tool

from pr_review_agent.tools.diff_utils import extract_changed_files


def make_compute_test_coverage_delta_tool(diff: str):
    @tool
    def compute_test_coverage_delta() -> str:
        """Compare changed source files against changed test files in this
        PR's diff and report which source files were modified without any
        matching test file change, as JSON."""
        changed_files = extract_changed_files(diff)
        test_files = [f for f in changed_files if _looks_like_test(f)]
        source_files = [f for f in changed_files if f.endswith(".py") and not _looks_like_test(f)]
        untested = [f for f in source_files if not _has_matching_test(f, test_files)]

        return json.dumps(
            {
                "changed_source_files": source_files,
                "changed_test_files": test_files,
                "source_files_without_test_changes": untested,
            }
        )

    return compute_test_coverage_delta


def _looks_like_test(path: str) -> bool:
    name = Path(path).name
    return name.startswith("test_") or name.endswith("_test.py") or "/tests/" in path or path.startswith("tests/")


def _has_matching_test(source_path: str, test_files: list[str]) -> bool:
    stem = Path(source_path).stem
    return any(stem in test_path for test_path in test_files)
