from langchain_core.messages import HumanMessage, SystemMessage

from pr_review_agent.graph.state import ReviewState
from pr_review_agent.llm.bedrock_client import get_llm

SYSTEM_PROMPT = (
    "You are a test-coverage specialist reviewing a GitHub pull request "
    "diff. Look only at whether the changed logic has matching test "
    "changes, and whether new edge cases are covered. Ignore security and "
    "style entirely. If test coverage looks adequate or the diff doesn't "
    "need tests (e.g. docs, config), say so in one short sentence."
)


def test_coverage_specialist(state: ReviewState) -> dict:
    llm = get_llm()
    messages = [SystemMessage(content=SYSTEM_PROMPT), HumanMessage(content=state["diff"])]
    response = llm.invoke(messages)
    return {"test_coverage_findings": [response.content]}
