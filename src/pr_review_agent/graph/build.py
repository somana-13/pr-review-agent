from langgraph.graph import END, START, StateGraph

from pr_review_agent.graph.nodes.planner import planner_router
from pr_review_agent.graph.nodes.security_specialist import security_specialist
from pr_review_agent.graph.nodes.style_specialist import style_specialist
from pr_review_agent.graph.nodes.synthesizer import synthesizer
from pr_review_agent.graph.nodes.test_coverage_specialist import test_coverage_specialist
from pr_review_agent.graph.state import ReviewState


def build_graph():
    graph = StateGraph(ReviewState)

    graph.add_node("planner_router", planner_router)
    graph.add_node("security_specialist", security_specialist)
    graph.add_node("test_coverage_specialist", test_coverage_specialist)
    graph.add_node("style_specialist", style_specialist)
    graph.add_node("synthesizer", synthesizer)

    graph.add_edge(START, "planner_router")
    graph.add_edge("planner_router", "security_specialist")
    graph.add_edge("planner_router", "test_coverage_specialist")
    graph.add_edge("planner_router", "style_specialist")
    graph.add_edge("security_specialist", "synthesizer")
    graph.add_edge("test_coverage_specialist", "synthesizer")
    graph.add_edge("style_specialist", "synthesizer")
    graph.add_edge("synthesizer", END)

    return graph.compile()
