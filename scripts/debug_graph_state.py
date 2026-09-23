from pr_review_agent.graph.build import build_graph

fake_diff = """diff --git a/hello.py b/hello.py
new file mode 100644
+print('hello world')
"""

result = build_graph().invoke({"diff": fake_diff})

print("security:", result["security_findings"])
print("test_coverage:", result["test_coverage_findings"])
print("style:", result["style_findings"])
