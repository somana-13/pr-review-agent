from pr_review_agent.graph.nodes.planner import route_to_specialists


def test_route_to_specialists_includes_security_when_relevant():
    sends = route_to_specialists({"security_relevant": True})
    nodes = {s.node for s in sends}
    assert nodes == {"security_specialist", "test_coverage_specialist", "style_specialist"}


def test_route_to_specialists_skips_security_when_not_relevant():
    sends = route_to_specialists({"security_relevant": False})
    nodes = {s.node for s in sends}
    assert nodes == {"test_coverage_specialist", "style_specialist"}
