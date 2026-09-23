import operator
from typing import Annotated, TypedDict


class ReviewState(TypedDict):
    diff: str
    security_findings: Annotated[list[str], operator.add]
    test_coverage_findings: Annotated[list[str], operator.add]
    style_findings: Annotated[list[str], operator.add]
    final_review: str
