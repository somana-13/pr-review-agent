from langchain_core.messages import HumanMessage, SystemMessage

from pr_review_agent.graph.state import ReviewState
from pr_review_agent.llm.bedrock_client import get_llm

SYSTEM_PROMPT = (
    "You are a security specialist reviewing a GitHub pull request diff. "
    "Look only for security issues: injection risks, hardcoded secrets, "
    "unsafe deserialization, auth/access-control bugs, unsafe dependency "
    "changes. Ignore style and test coverage entirely. If you find nothing "
    "security-relevant, say so in one short sentence."
)


def security_specialist(state: ReviewState) -> dict:
    llm = get_llm()
    messages = [SystemMessage(content=SYSTEM_PROMPT), HumanMessage(content=state["diff"])]
    response = llm.invoke(messages)
    return {"security_findings": [response.content]}
