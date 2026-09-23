from pr_review_agent.guardrails.checks import check_output

result = check_output("Contact the maintainer at real.person@example.com for questions.")
print("text:", result.text)
print("intervened:", result.intervened)
