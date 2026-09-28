from pr_review_agent.graph.nodes.planner import route_to_specialists

for security_relevant in (True, False):
    sends = route_to_specialists({"security_relevant": security_relevant})
    nodes = sorted(s.node for s in sends)
    print(f"security_relevant={security_relevant}: dispatches to {nodes}")
