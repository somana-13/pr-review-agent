import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import requests

from pr_review_agent.config import settings

GITHUB_API = "https://api.github.com"
DATA_DIR = Path(__file__).parent
MAX_DIFF_CHARS = 20_000
DIFF_FETCH_WORKERS = 8

DIVERSE_POOL_REPOS = [
    "pallets/flask",
    "psf/requests",
    "tiangolo/fastapi",
    "django/django",
    "pytest-dev/pytest",
    "pandas-dev/pandas",
    "numpy/numpy",
    "scikit-learn/scikit-learn",
    "celery/celery",
    "sqlalchemy/sqlalchemy",
    "expressjs/express",
    "axios/axios",
    "lodash/lodash",
    "webpack/webpack",
    "nodejs/node",
    "vuejs/vue",
    "sveltejs/svelte",
    "facebook/react",
    "vercel/next.js",
    "microsoft/TypeScript",
]


def _headers() -> dict:
    return {"Authorization": f"Bearer {settings.github_token}", "Accept": "application/vnd.github+json"}


def _fetch_commit_diff(owner: str, repo: str, sha: str) -> str | None:
    url = f"{GITHUB_API}/repos/{owner}/{repo}/commits/{sha}"
    headers = {**_headers(), "Accept": "application/vnd.github.v3.diff"}
    try:
        response = requests.get(url, headers=headers, timeout=30)
    except requests.exceptions.RequestException:
        # one bad commit (huge diff, dropped connection, etc.) shouldn't
        # take down the whole concurrent batch -- just skip it
        return None
    if response.status_code != 200:
        return None
    diff = response.text
    return diff if len(diff) <= MAX_DIFF_CHARS else None


def _fetch_diffs_concurrently(commit_refs: list[tuple[str, str, str]]) -> list[dict]:
    results = []
    with ThreadPoolExecutor(max_workers=DIFF_FETCH_WORKERS) as executor:
        futures = {}
        for repo_full_name, sha, message in commit_refs:
            owner, repo = repo_full_name.split("/")
            future = executor.submit(_fetch_commit_diff, owner, repo, sha)
            futures[future] = (repo_full_name, sha, message)

        for future in as_completed(futures):
            repo_full_name, sha, message = futures[future]
            diff = future.result()
            if diff is not None:
                results.append({"repo": repo_full_name, "sha": sha, "message": message, "diff": diff})
    return results


def scrape_gold_positive(target: int, max_pages: int = 5) -> None:
    commit_refs = []
    for page in range(1, max_pages + 1):
        params = {"q": "CVE- in:message", "sort": "committer-date", "order": "desc", "per_page": 100, "page": page}
        response = requests.get(f"{GITHUB_API}/search/commits", headers=_headers(), params=params, timeout=30)
        if response.status_code != 200:
            print(f"  search page {page} returned {response.status_code}, stopping pagination early")
            break
        items = response.json()["items"]
        if not items:
            break
        for hit in items:
            commit_refs.append((hit["repository"]["full_name"], hit["sha"], hit["commit"]["message"]))
        if len(commit_refs) >= target * 2:
            break
        time.sleep(5)  # commit search has a stricter secondary rate limit than the core REST API

    examples = _fetch_diffs_concurrently(commit_refs)
    for example in examples:
        example["label"] = 1
    examples = examples[:target]

    out_path = DATA_DIR / "gold_positive.jsonl"
    out_path.write_text("\n".join(json.dumps(e) for e in examples) + "\n")
    print(f"Wrote {len(examples)} gold-positive examples to {out_path}")


def scrape_diverse_pool(per_repo: int) -> None:
    commit_refs = []
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
            commit_refs.append((repo_full_name, commit["sha"], commit["commit"]["message"]))

    examples = _fetch_diffs_concurrently(commit_refs)

    out_path = DATA_DIR / "unlabeled_pool.jsonl"
    out_path.write_text("\n".join(json.dumps(e) for e in examples) + "\n")
    print(f"Wrote {len(examples)} unlabeled diverse-pool examples to {out_path}")


if __name__ == "__main__":
    scrape_gold_positive(target=300)
    scrape_diverse_pool(per_repo=90)
