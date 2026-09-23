from pr_review_agent.graph.state import ReviewState
from pr_review_agent.guardrails.checks import check_output


def guardrail_output_check(state: ReviewState) -> dict:
    result = check_output(state["final_review"])
    flags = ["guardrail intervened on output (review sanitized)"] if result.intervened else []
    return {"final_review": result.text, "guardrail_flags": flags}
