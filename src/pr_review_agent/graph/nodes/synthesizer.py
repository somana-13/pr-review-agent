from langchain_core.messages import HumanMessage, SystemMessage

from pr_review_agent.graph.state import ReviewState
from pr_review_agent.llm.bedrock_client import get_llm

SYSTEM_PROMPT = (
    "You are synthesizing a GitHub PR review comment from three "
    "specialists' notes (security, test coverage, style). Merge them into "
    "one well-organized comment with a short section per specialist. Drop "
    "sections where the specialist found nothing notable. Keep it concise."
)


def synthesizer(state: ReviewState) -> dict:
    llm = get_llm()
    findings = (
        "## Security specialist notes\n"
        + "\n".join(state["security_findings"])
        + "\n\n## Test coverage specialist notes\n"
        + "\n".join(state["test_coverage_findings"])
        + "\n\n## Style specialist notes\n"
        + "\n".join(state["style_findings"])
    )
    messages = [SystemMessage(content=SYSTEM_PROMPT), HumanMessage(content=findings)]
    response = llm.invoke(messages)
    return {"final_review": response.content}
