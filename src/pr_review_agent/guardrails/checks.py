from typing import NamedTuple

from pr_review_agent.config import settings
from pr_review_agent.guardrails.client import get_guardrail_client


class GuardrailResult(NamedTuple):
    text: str
    intervened: bool


def _apply_guardrail(text: str, source: str) -> GuardrailResult:
    client = get_guardrail_client()
    response = client.apply_guardrail(
        guardrailIdentifier=settings.guardrail_id,
        guardrailVersion=settings.guardrail_version,
        source=source,
        content=[{"text": {"text": text}}],
    )
    intervened = response["action"] == "GUARDRAIL_INTERVENED"
    outputs = response.get("outputs", [])
    result_text = outputs[0]["text"] if outputs else text
    return GuardrailResult(text=result_text, intervened=intervened)


def check_input(text: str) -> GuardrailResult:
    return _apply_guardrail(text, "INPUT")


def check_output(text: str) -> GuardrailResult:
    return _apply_guardrail(text, "OUTPUT")
