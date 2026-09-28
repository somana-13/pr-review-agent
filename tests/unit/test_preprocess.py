from pr_review_agent.classifier.preprocess import MAX_DIFF_CHARS, normalize_diff


def test_normalize_diff_strips_whitespace():
    assert normalize_diff("  some diff text  ") == "some diff text"


def test_normalize_diff_truncates_long_input():
    long_diff = "x" * (MAX_DIFF_CHARS + 500)
    result = normalize_diff(long_diff)
    assert len(result) == MAX_DIFF_CHARS
