from pr_review_agent.config import settings
from pr_review_agent.graph.build import build_graph
from pr_review_agent.tools.github_tools import fetch_pr_diff

owner, repo, pr_number = "somana-13", "pr-review-agent-testbed", 1
diff = fetch_pr_diff(owner, repo, pr_number, settings.github_token)

result = build_graph().invoke({"diff": diff, "owner": owner, "repo": repo, "pr_number": pr_number})

print("security:", result["security_findings"])
print("test_coverage:", result["test_coverage_findings"])
print("style:", result["style_findings"])
print("tool_call_log:", result["tool_call_log"])
