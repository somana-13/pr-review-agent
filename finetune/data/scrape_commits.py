import json
import time
from pathlib import Path

import requests

from pr_review_agent.config import settings

GITHUB_API = "https://api.github.com"
DATA_DIR = Path(__file__).parent
MAX_DIFF_CHARS = 20_000

DIVERSE_POOL_REPOS = [
    "pallets/flask",
    "psf/requests",
    "tiangolo/fastapi",
    "django/django",
    "pytest-dev/pytest",
]


def _headers() -> dict:
    return {"Authorization": f"Bearer {settings.github_token}", "Accept": "application/vnd.github+json"}


def _fetch_commit_diff(owner: str, repo: str, sha: str) -> str | None:
    url = f"{GITHUB_API}/repos/{owner}/{repo}/commits/{sha}"
    headers = {**_headers(), "Accept": "application/vnd.github.v3.diff"}
    response = requests.get(url, headers=headers, timeout=30)
    if response.status_code != 200:
        return None
    diff = response.text
    return diff if len(diff) <= MAX_DIFF_CHARS else None


def scrape_gold_positive(count: int) -> None:
    params = {"q": "CVE- in:message", "sort": "committer-date", "order": "desc", "per_page": count}
    response = requests.get(f"{GITHUB_API}/search/commits", headers=_headers(), params=params, timeout=30)
    response.raise_for_status()

    examples = []
    for hit in response.json()["items"]:
        repo_full_name = hit["repository"]["full_name"]
        owner, repo = repo_full_name.split("/")
        diff = _fetch_commit_diff(owner, repo, hit["sha"])
        if diff is None:
            continue
        examples.append(
            {
                "repo": repo_full_name,
                "sha": hit["sha"],
                "message": hit["commit"]["message"],
                "diff": diff,
                "label": 1,
            }
        )
        time.sleep(0.5)

    out_path = DATA_DIR / "gold_positive.jsonl"
    out_path.write_text("\n".join(json.dumps(e) for e in examples) + "\n")
    print(f"Wrote {len(examples)} gold-positive examples to {out_path}")


def scrape_diverse_pool(per_repo: int) -> None:
    examples = []
    for repo_full_name in DIVERSE_POOL_REPOS:
        owner, repo = repo_full_name.split("/")
        response = requests.get(
            f"{GITHUB_API}/repos/{owner}/{repo}/commits",
            headers=_headers(),
            params={"per_page": per_repo},
            timeout=30,
        )
        response.raise_for_status()
        for commit in response.json():
            diff = _fetch_commit_diff(owner, repo, commit["sha"])
            if diff is None:
                continue
            examples.append(
                {
                    "repo": repo_full_name,
                    "sha": commit["sha"],
                    "message": commit["commit"]["message"],
                    "diff": diff,
                }
            )
            time.sleep(0.5)

    out_path = DATA_DIR / "unlabeled_pool.jsonl"
    out_path.write_text("\n".join(json.dumps(e) for e in examples) + "\n")
    print(f"Wrote {len(examples)} unlabeled diverse-pool examples to {out_path}")


if __name__ == "__main__":
    scrape_gold_positive(count=10)
    scrape_diverse_pool(per_repo=5)
