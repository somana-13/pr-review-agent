from unittest.mock import patch

from pr_review_agent.config import settings
from pr_review_agent.graph.build import build_graph
from pr_review_agent.tools.github_tools import fetch_pr_diff

owner, repo, pr_number = "somana-13", "pr-review-agent-testbed", 1
diff = fetch_pr_diff(owner, repo, pr_number, settings.github_token)

with patch("pr_review_agent.graph.nodes.classifier_gate.score_diff", return_value=0.0):
    result = build_graph().invoke(
        {"diff": diff, "owner": owner, "repo": repo, "pr_number": pr_number, "security_findings": []}
    )

print("security_relevant:", result["security_relevant"])
print("security_findings:", result["security_findings"])
print("tool_call_log:", result["tool_call_log"])
print("final_review:\n", result["final_review"])
