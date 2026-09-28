from pr_review_agent.classifier.model import score_diff
from pr_review_agent.graph.state import ReviewState


def classifier_gate(state: ReviewState) -> dict:
    return {"security_score": score_diff(state["diff"])}
