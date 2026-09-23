import operator
from typing import Annotated, TypedDict


class ReviewState(TypedDict):
    diff: str
    owner: str
    repo: str
    pr_number: int
    workspace_path: str
    security_findings: Annotated[list[str], operator.add]
    test_coverage_findings: Annotated[list[str], operator.add]
    style_findings: Annotated[list[str], operator.add]
    tool_call_log: Annotated[list[str], operator.add]
    guardrail_flags: Annotated[list[str], operator.add]
    final_review: str
