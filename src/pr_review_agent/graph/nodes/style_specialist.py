from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langgraph.prebuilt import create_react_agent

from pr_review_agent.graph.state import ReviewState
from pr_review_agent.llm.bedrock_client import get_llm
from pr_review_agent.tools.diff_utils import extract_changed_files
from pr_review_agent.tools.lint_tools import make_run_linter_tool

SYSTEM_PROMPT = (
    "You are a style specialist reviewing a GitHub pull request. You have "
    "a run_linter tool that runs ruff on the changed files and returns "
    "objective findings. Call it, then write a concise style review, "
    "layering your own judgment on top of (not just repeating) the linter "
    "output. Ignore security and test coverage entirely. Keep feedback "
    "brief."
)


def style_specialist(state: ReviewState) -> dict:
    changed_files = extract_changed_files(state["diff"])
    tools = [make_run_linter_tool(state["workspace_path"], changed_files)]
    agent = create_react_agent(get_llm(), tools)
    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=state["diff"]),
    ]
    result = agent.invoke({"messages": messages})

    tool_calls = [
        f"style_specialist called {call['name']}"
        for message in result["messages"]
        if isinstance(message, AIMessage)
        for call in message.tool_calls
    ]

    return {
        "style_findings": [result["messages"][-1].content],
        "tool_call_log": tool_calls,
    }
