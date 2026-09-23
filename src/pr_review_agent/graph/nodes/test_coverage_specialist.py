from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langgraph.prebuilt import create_react_agent

from pr_review_agent.graph.state import ReviewState
from pr_review_agent.llm.bedrock_client import get_llm
from pr_review_agent.tools.test_coverage import make_compute_test_coverage_delta_tool

SYSTEM_PROMPT = (
    "You are a test-coverage specialist reviewing a GitHub pull request "
    "diff. You have a compute_test_coverage_delta tool that reports which "
    "changed source files lack a matching changed test file. Call it, "
    "then write a concise assessment. Ignore security and style entirely. "
    "If test coverage looks adequate or the diff doesn't need tests (e.g. "
    "docs, config), say so in one short sentence."
)


def test_coverage_specialist(state: ReviewState) -> dict:
    tools = [make_compute_test_coverage_delta_tool(state["diff"])]
    agent = create_react_agent(get_llm(), tools)
    messages = [SystemMessage(content=SYSTEM_PROMPT), HumanMessage(content=state["diff"])]
    result = agent.invoke({"messages": messages})

    tool_calls = [
        f"test_coverage_specialist called {call['name']}"
        for message in result["messages"]
        if isinstance(message, AIMessage)
        for call in message.tool_calls
    ]

    return {
        "test_coverage_findings": [result["messages"][-1].content],
        "tool_call_log": tool_calls,
    }
