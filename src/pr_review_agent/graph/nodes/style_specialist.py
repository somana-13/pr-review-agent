from langchain_core.messages import HumanMessage, SystemMessage

from pr_review_agent.graph.state import ReviewState
from pr_review_agent.llm.bedrock_client import get_llm

SYSTEM_PROMPT = (
    "You are a style specialist reviewing a GitHub pull request diff. "
    "Look only at naming, readability, formatting consistency, and "
    "obvious redundancy. Ignore security and test coverage entirely. Keep "
    "feedback brief."
)


def style_specialist(state: ReviewState) -> dict:
    llm = get_llm()
    messages = [SystemMessage(content=SYSTEM_PROMPT), HumanMessage(content=state["diff"])]
    response = llm.invoke(messages)
    return {"style_findings": [response.content]}
