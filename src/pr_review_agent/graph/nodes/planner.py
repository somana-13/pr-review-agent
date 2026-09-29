from langgraph.types import Send

from pr_review_agent.classifier.model import get_threshold
from pr_review_agent.graph.state import ReviewState


def planner_router(state: ReviewState) -> dict:
    score = state["security_score"]
    threshold = get_threshold()
    security_relevant = score >= threshold

    if security_relevant:
        log = [f"planner_router: score={score:.3f} >= threshold={threshold:.3f} -> running security_specialist"]
        return {"security_relevant": True, "tool_call_log": log}

    log = [f"planner_router: score={score:.3f} < threshold={threshold:.3f} -> skipping security_specialist"]
    skip_note = [
        (
            f"Security specialist skipped: classifier scored this diff as not "
            f"security-relevant (score={score:.3f}, threshold={threshold:.3f})."
        )
    ]
    return {"security_relevant": False, "tool_call_log": log, "security_findings": skip_note}


def route_to_specialists(state: ReviewState) -> list[Send]:
    sends = [Send("test_coverage_specialist", state), Send("style_specialist", state)]
    if state["security_relevant"]:
        sends.append(Send("security_specialist", state))
    return sends
