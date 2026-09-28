import shutil
import time

from pr_review_agent.config import settings
from pr_review_agent.graph.build import build_graph
from pr_review_agent.graph.nodes.security_specialist import security_specialist
from pr_review_agent.tools.github_tools import clone_pr_workspace, fetch_pr_diff, get_pr_head, parse_pr_url

TEST_PRS = [
    "https://github.com/somana-13/pr-review-agent-testbed/pull/1",  # benign
    "https://github.com/somana-13/pr-review-agent-testbed/pull/2",  # real leaked secret
    "https://github.com/github/gitignore/pull/4898",  # benign
    "https://github.com/jlcatonjr/agentteams/pull/60",  # real CVE dependency fix
]


def run_one(pr_url: str) -> dict:
    owner, repo, pr_number = parse_pr_url(pr_url)
    diff = fetch_pr_diff(owner, repo, pr_number, settings.github_token)

    start = time.time()
    result = build_graph().invoke(
        {"diff": diff, "owner": owner, "repo": repo, "pr_number": pr_number, "security_findings": []}
    )
    total_time = time.time() - start

    ran_security = any("security_specialist called" in entry for entry in result["tool_call_log"])

    counterfactual_time = None
    if not ran_security:
        # gate skipped it -- measure what running it anyway would have cost,
        # so "savings" is a real measurement, not an assumption
        head = get_pr_head(owner, repo, pr_number, settings.github_token)
        workspace = clone_pr_workspace(head["clone_url"], head["ref"], head["sha"])
        try:
            cf_start = time.time()
            security_specialist({**result, "workspace_path": workspace})
            counterfactual_time = time.time() - cf_start
        finally:
            shutil.rmtree(workspace, ignore_errors=True)

    return {
        "pr_url": pr_url,
        "security_score": result["security_score"],
        "ran_security": ran_security,
        "total_time_s": total_time,
        "counterfactual_security_time_s": counterfactual_time,
    }


def main() -> None:
    results = []
    for i, url in enumerate(TEST_PRS):
        if i > 0:
            time.sleep(15)  # avoid bursting Bedrock across back-to-back PR runs
        results.append(run_one(url))

    for r in results:
        status = "RAN" if r["ran_security"] else "SKIPPED"
        print(f"{r['pr_url']}")
        print(f"  score={r['security_score']:.3f}  [{status}]  total={r['total_time_s']:.1f}s")
        if r["counterfactual_security_time_s"] is not None:
            print(f"  (would have cost {r['counterfactual_security_time_s']:.1f}s if not skipped)")

    skipped = [r for r in results if not r["ran_security"]]
    print(f"\nSkip rate: {len(skipped)}/{len(results)} ({len(skipped) / len(results):.0%})")
    if skipped:
        avg_saved = sum(r["counterfactual_security_time_s"] for r in skipped) / len(skipped)
        print(f"Average measured time saved per skip: {avg_saved:.1f}s")


if __name__ == "__main__":
    main()
