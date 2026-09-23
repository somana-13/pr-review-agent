import shutil

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langgraph.prebuilt import create_react_agent

from pr_review_agent.config import settings
from pr_review_agent.graph.state import ReviewState
from pr_review_agent.llm.bedrock_client import get_llm
from pr_review_agent.tools.github_tools import clone_pr_workspace, get_pr_head
from pr_review_agent.tools.static_analysis import make_run_semgrep_tool

SYSTEM_PROMPT = (
    "You are a security specialist reviewing a GitHub pull request. You "
    "have a run_semgrep tool that statically scans the full checked-out "
    "repository (not just the diff) for security issues. Call it, then "
    "write a concise security review of the diff below, cross-referencing "
    "any relevant Semgrep findings. Ignore style and test coverage "
    "entirely. If nothing is security-relevant, say so in one sentence."
)


def security_specialist(state: ReviewState) -> dict:
    head = get_pr_head(state["owner"], state["repo"], state["pr_number"], settings.github_token)
    workspace = clone_pr_workspace(head["clone_url"], head["ref"])

    try:
        tools = [make_run_semgrep_tool(workspace)]
        agent = create_react_agent(get_llm(), tools)
        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=state["diff"]),
        ]
        result = agent.invoke({"messages": messages})
    finally:
        shutil.rmtree(workspace, ignore_errors=True)

    tool_calls = [
        f"security_specialist called {call['name']}"
        for message in result["messages"]
        if isinstance(message, AIMessage)
        for call in message.tool_calls
    ]

    return {
        "security_findings": [result["messages"][-1].content],
        "tool_call_log": tool_calls,
    }
