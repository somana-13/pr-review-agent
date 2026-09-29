import json
import time
from pathlib import Path

import boto3
from botocore.config import Config
from langchain_aws import ChatBedrockConverse
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field

from pr_review_agent.config import settings

DATA_DIR = Path(__file__).parent
SONNET_MODEL_ID = "us.anthropic.claude-sonnet-4-5-20250929-v1:0"
DELAY_BETWEEN_CALLS_S = 2
_BOTO_CONFIG = Config(retries={"max_attempts": 10, "mode": "adaptive"})

SYSTEM_PROMPT = (
    "You are labeling commits for a training dataset. Decide whether a "
    "commit's diff is security-sensitive: does it fix or touch "
    "authentication, access control, injection risks, secrets, unsafe "
    "deserialization, cryptography, or a known vulnerability? Routine "
    "refactors, docs, dependency bumps, and features with no security "
    "angle are NOT security-sensitive."
)


class SecurityLabel(BaseModel):
    label: int = Field(description="1 if security-sensitive, 0 otherwise")
    confidence: float = Field(description="Confidence from 0.0 to 1.0")
    rationale: str = Field(description="One sentence explaining the label")


def _label_one(example: dict, structured_llm) -> dict:
    content = f"Commit message: {example['message']}\n\nDiff:\n{example['diff']}"
    result: SecurityLabel = structured_llm.invoke(
        [SystemMessage(content=SYSTEM_PROMPT), HumanMessage(content=content)]
    )
    return {
        **example,
        "label": result.label,
        "confidence": result.confidence,
        "rationale": result.rationale,
    }


def label_pool() -> None:
    client = boto3.client("bedrock-runtime", region_name=settings.aws_region, config=_BOTO_CONFIG)
    llm = ChatBedrockConverse(model=SONNET_MODEL_ID, client=client)
    structured_llm = llm.with_structured_output(SecurityLabel)

    pool_path = DATA_DIR / "unlabeled_pool.jsonl"
    examples = [json.loads(line) for line in pool_path.read_text().splitlines() if line]

    out_path = DATA_DIR / "labeled_pool.jsonl"
    labeled_count = 0
    errors = 0
    with out_path.open("w") as out_file:
        for i, example in enumerate(examples, 1):
            try:
                labeled = _label_one(example, structured_llm)
                out_file.write(json.dumps(labeled) + "\n")
                out_file.flush()
                labeled_count += 1
            except Exception as e:  # noqa: BLE001 -- best-effort batch job, any failure should be skipped, not fatal
                errors += 1
                print(f"  skipped one example due to error: {e}")
            if i % 25 == 0 or i == len(examples):
                print(f"  processed {i}/{len(examples)} ({labeled_count} labeled, {errors} errors)")
            time.sleep(DELAY_BETWEEN_CALLS_S)

    print(f"Wrote {labeled_count} labeled examples to {out_path}")


if __name__ == "__main__":
    label_pool()
