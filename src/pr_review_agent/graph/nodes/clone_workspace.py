from pr_review_agent.config import settings
from pr_review_agent.graph.state import ReviewState
from pr_review_agent.tools.github_tools import clone_pr_workspace, get_pr_head


def clone_workspace(state: ReviewState) -> dict:
    head = get_pr_head(state["owner"], state["repo"], state["pr_number"], settings.github_token)
    workspace = clone_pr_workspace(head["clone_url"], head["ref"], head["sha"])
    return {"workspace_path": workspace}
