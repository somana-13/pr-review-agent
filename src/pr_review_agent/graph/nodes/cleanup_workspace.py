import shutil

from pr_review_agent.graph.state import ReviewState


def cleanup_workspace(state: ReviewState) -> dict:
    shutil.rmtree(state["workspace_path"], ignore_errors=True)
    return {}
