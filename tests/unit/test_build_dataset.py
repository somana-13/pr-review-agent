from build_dataset import repo_level_split


def _make_examples():
    examples = []
    for repo in ("a/one", "b/two", "c/three", "d/four"):
        for i in range(5):
            examples.append({"repo": repo, "sha": f"{repo}-{i}", "label": i % 2})
    return examples


def test_repo_level_split_never_splits_a_repo_across_sets():
    examples = _make_examples()
    splits = repo_level_split(examples)

    repos_per_split = {name: {e["repo"] for e in split} for name, split in splits.items()}
    all_repos_seen = set()
    for repos in repos_per_split.values():
        assert repos.isdisjoint(all_repos_seen), "a repo appeared in more than one split"
        all_repos_seen |= repos


def test_repo_level_split_includes_every_example_exactly_once():
    examples = _make_examples()
    splits = repo_level_split(examples)

    all_shas = [e["sha"] for split in splits.values() for e in split]
    assert sorted(all_shas) == sorted(e["sha"] for e in examples)
