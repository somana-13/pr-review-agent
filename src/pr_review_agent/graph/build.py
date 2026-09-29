from langgraph.graph import END, START, StateGraph

from pr_review_agent.graph.nodes.classifier_gate import classifier_gate
from pr_review_agent.graph.nodes.cleanup_workspace import cleanup_workspace
from pr_review_agent.graph.nodes.clone_workspace import clone_workspace
from pr_review_agent.graph.nodes.guardrail_input_check import guardrail_input_check
from pr_review_agent.graph.nodes.guardrail_output_check import guardrail_output_check
from pr_review_agent.graph.nodes.planner import planner_router, route_to_specialists
from pr_review_agent.graph.nodes.security_specialist import security_specialist
from pr_review_agent.graph.nodes.style_specialist import style_specialist
from pr_review_agent.graph.nodes.synthesizer import synthesizer
from pr_review_agent.graph.nodes.test_coverage_specialist import (
    test_coverage_specialist,
)
from pr_review_agent.graph.state import ReviewState


def build_graph():
    graph = StateGraph(ReviewState)

    graph.add_node("guardrail_input_check", guardrail_input_check)
    graph.add_node("classifier_gate", classifier_gate)
    graph.add_node("planner_router", planner_router)
    graph.add_node("clone_workspace", clone_workspace)
    graph.add_node("security_specialist", security_specialist)
    graph.add_node("test_coverage_specialist", test_coverage_specialist)
    graph.add_node("style_specialist", style_specialist)
    graph.add_node("cleanup_workspace", cleanup_workspace)
    graph.add_node("synthesizer", synthesizer)
    graph.add_node("guardrail_output_check", guardrail_output_check)

    graph.add_edge(START, "guardrail_input_check")
    graph.add_edge("guardrail_input_check", "classifier_gate")
    graph.add_edge("classifier_gate", "planner_router")
    graph.add_edge("planner_router", "clone_workspace")
    graph.add_conditional_edges("clone_workspace", route_to_specialists)
    graph.add_edge("security_specialist", "cleanup_workspace")
    graph.add_edge("test_coverage_specialist", "cleanup_workspace")
    graph.add_edge("style_specialist", "cleanup_workspace")
    graph.add_edge("cleanup_workspace", "synthesizer")
    graph.add_edge("synthesizer", "guardrail_output_check")
    graph.add_edge("guardrail_output_check", END)

    return graph.compile()
