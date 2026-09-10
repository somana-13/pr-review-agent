import typer

app = typer.Typer()


@app.command()
def hello():
    """Sanity-check command: confirms the CLI is wired up correctly."""
    typer.echo("pr-review-agent CLI is alive.")


if __name__ == "__main__":
    app()
