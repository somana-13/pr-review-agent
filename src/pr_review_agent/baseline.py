from langchain_core.messages import HumanMessage, SystemMessage

from pr_review_agent.llm.bedrock_client import get_llm

REVIEW_SYSTEM_PROMPT = (
    "You are a senior software engineer reviewing a GitHub pull request. "
    "Read the unified diff and write a concise code review: call out bugs, "
    "security issues, missing tests, and style problems. If the diff looks "
    "fine, say so briefly."
)


def baseline_review(diff: str) -> str:
    llm = get_llm()
    messages = [
        SystemMessage(content=REVIEW_SYSTEM_PROMPT),
        HumanMessage(content=diff),
    ]
    response = llm.invoke(messages)
    return response.content
