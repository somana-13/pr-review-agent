from pr_review_agent.tools.test_coverage import _has_matching_test, _looks_like_test


def test_looks_like_test_matches_common_conventions():
    assert _looks_like_test("tests/test_foo.py")
    assert _looks_like_test("src/foo_test.py")
    assert _looks_like_test("test_bar.py")
    assert not _looks_like_test("src/foo.py")


def test_has_matching_test_finds_test_by_stem():
    assert _has_matching_test("src/foo.py", ["tests/test_foo.py"])
    assert not _has_matching_test("src/foo.py", ["tests/test_bar.py"])
