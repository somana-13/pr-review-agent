import json
from pathlib import Path

from langchain_aws import ChatBedrockConverse
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field

from pr_review_agent.config import settings

DATA_DIR = Path(__file__).parent
SONNET_MODEL_ID = "us.anthropic.claude-sonnet-4-5-20250929-v1:0"

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


def label_pool() -> None:
    llm = ChatBedrockConverse(model=SONNET_MODEL_ID, region_name=settings.aws_region)
    structured_llm = llm.with_structured_output(SecurityLabel)

    pool_path = DATA_DIR / "unlabeled_pool.jsonl"
    examples = [json.loads(line) for line in pool_path.read_text().splitlines() if line]

    labeled = []
    for example in examples:
        content = f"Commit message: {example['message']}\n\nDiff:\n{example['diff']}"
        result: SecurityLabel = structured_llm.invoke(
            [SystemMessage(content=SYSTEM_PROMPT), HumanMessage(content=content)]
        )
        labeled.append(
            {
                **example,
                "label": result.label,
                "confidence": result.confidence,
                "rationale": result.rationale,
            }
        )
        print(f"{example['repo']}@{example['sha'][:7]}: label={result.label} confidence={result.confidence:.2f}")

    out_path = DATA_DIR / "labeled_pool.jsonl"
    out_path.write_text("\n".join(json.dumps(e) for e in labeled) + "\n")
    print(f"Wrote {len(labeled)} labeled examples to {out_path}")


if __name__ == "__main__":
    label_pool()
