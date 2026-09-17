import typer

from pr_review_agent.baseline import baseline_review
from pr_review_agent.config import settings
from pr_review_agent.tools.github_tools import fetch_pr_diff, parse_pr_url, post_pr_comment

app = typer.Typer()


@app.command()
def hello():
    """Sanity-check command: confirms the CLI is wired up correctly."""
    typer.echo("pr-review-agent CLI is alive.")


@app.command()
def review(pr_url: str, post: bool = False):
    """Fetch a GitHub PR's diff, review it with Haiku, and print the result."""
    owner, repo, pr_number = parse_pr_url(pr_url)
    diff = fetch_pr_diff(owner, repo, pr_number, settings.github_token)
    typer.echo(diff)
    typer.echo("\n--- Review ---\n")
    review_text = baseline_review(diff)
    typer.echo(review_text)

    if post:
        comment_url = post_pr_comment(owner, repo, pr_number, review_text, settings.github_token)
        typer.echo(f"\nPosted: {comment_url}")


if __name__ == "__main__":
    app()
