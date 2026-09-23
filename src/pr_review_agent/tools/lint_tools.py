import subprocess

from langchain_core.tools import tool


def make_run_linter_tool(workspace_path: str, changed_files: list[str]):
    @tool
    def run_linter() -> str:
        """Run the ruff linter on this PR's changed Python files (within
        the checked-out workspace) and return findings as JSON."""
        python_files = [f for f in changed_files if f.endswith(".py")]
        if not python_files:
            return "[]"

        result = subprocess.run(
            ["ruff", "check", "--output-format=json", *python_files],
            cwd=workspace_path,
            capture_output=True,
            text=True,
            timeout=60,
        )
        return result.stdout or "[]"

    return run_linter
