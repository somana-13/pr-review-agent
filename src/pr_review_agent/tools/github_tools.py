import re
import subprocess
import tempfile

import requests

GITHUB_API = "https://api.github.com"
PR_URL_PATTERN = re.compile(r"github\.com/([^/]+)/([^/]+)/pull/(\d+)")


def parse_pr_url(url: str) -> tuple[str, str, int]:
    match = PR_URL_PATTERN.search(url)
    if not match:
        raise ValueError(f"Not a GitHub PR URL: {url}")
    owner, repo, number = match.groups()
    return owner, repo, int(number)


def fetch_pr_diff(owner: str, repo: str, pr_number: int, token: str) -> str:
    url = f"{GITHUB_API}/repos/{owner}/{repo}/pulls/{pr_number}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3.diff",
    }
    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()
    return response.text


def get_pr_head(owner: str, repo: str, pr_number: int, token: str) -> dict:
    url = f"{GITHUB_API}/repos/{owner}/{repo}/pulls/{pr_number}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
    }
    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()
    data = response.json()
    return {"clone_url": data["head"]["repo"]["clone_url"], "ref": data["head"]["ref"]}


def clone_pr_workspace(clone_url: str, ref: str) -> str:
    workspace = tempfile.mkdtemp(prefix="pr-review-")
    subprocess.run(
        ["git", "clone", "--depth", "1", "--branch", ref, clone_url, workspace],
        check=True,
        capture_output=True,
        text=True,
    )
    return workspace


def post_pr_comment(owner: str, repo: str, pr_number: int, body: str, token: str) -> str:
    url = f"{GITHUB_API}/repos/{owner}/{repo}/issues/{pr_number}/comments"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
    }
    response = requests.post(url, headers=headers, json={"body": body}, timeout=30)
    response.raise_for_status()
    return response.json()["html_url"]
