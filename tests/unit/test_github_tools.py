import pytest

from pr_review_agent.tools.github_tools import parse_pr_url


def test_parse_pr_url_extracts_owner_repo_number():
    owner, repo, number = parse_pr_url("https://github.com/octocat/Hello-World/pull/42")
    assert owner == "octocat"
    assert repo == "Hello-World"
    assert number == 42


def test_parse_pr_url_ignores_trailing_query_params():
    owner, repo, number = parse_pr_url("https://github.com/octocat/Hello-World/pull/42?some=param")
    assert (owner, repo, number) == ("octocat", "Hello-World", 42)


def test_parse_pr_url_rejects_non_pr_url():
    with pytest.raises(ValueError):
        parse_pr_url("https://github.com/octocat/Hello-World")
