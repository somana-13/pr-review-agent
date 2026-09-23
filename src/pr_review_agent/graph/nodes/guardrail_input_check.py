from pr_review_agent.graph.state import ReviewState
from pr_review_agent.guardrails.checks import check_input


def guardrail_input_check(state: ReviewState) -> dict:
    result = check_input(state["diff"])
    flags = ["guardrail intervened on input (diff sanitized)"] if result.intervened else []
    return {"diff": result.text, "guardrail_flags": flags}
