import json
import subprocess

from langchain_core.tools import tool


def make_run_semgrep_tool(workspace_path: str):
    @tool
    def run_semgrep() -> str:
        """Run Semgrep static analysis (security-audit + secrets rulesets) on
        the checked-out PR workspace and return findings as a JSON list of
        {path, check_id, message, severity}."""
        result = subprocess.run(
            ["semgrep", "--config", "p/security-audit", "--config", "p/secrets", "--json", workspace_path],
            capture_output=True,
            text=True,
            timeout=180,
        )
        try:
            data = json.loads(result.stdout)
        except json.JSONDecodeError:
            return f"Semgrep failed to run: {result.stderr[:500]}"

        findings = [
            {
                "path": r["path"],
                "check_id": r["check_id"],
                "message": r["extra"]["message"],
                "severity": r["extra"]["severity"],
            }
            for r in data.get("results", [])
        ]
        return json.dumps(findings)

    return run_semgrep
