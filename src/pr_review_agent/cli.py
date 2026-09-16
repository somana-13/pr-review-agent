import typer

from pr_review_agent.config import settings
from pr_review_agent.tools.github_tools import fetch_pr_diff, parse_pr_url

app = typer.Typer()


@app.command()
def hello():
    """Sanity-check command: confirms the CLI is wired up correctly."""
    typer.echo("pr-review-agent CLI is alive.")


@app.command()
def review(pr_url: str):
    """Fetch a GitHub PR's diff and print it (review logic comes later)."""
    owner, repo, pr_number = parse_pr_url(pr_url)
    diff = fetch_pr_diff(owner, repo, pr_number, settings.github_token)
    typer.echo(diff)


if __name__ == "__main__":
    app()
