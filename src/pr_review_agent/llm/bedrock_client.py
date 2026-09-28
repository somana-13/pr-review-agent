import boto3
from botocore.config import Config
from langchain_aws import ChatBedrockConverse

from pr_review_agent.config import settings

# "adaptive" mode does client-side rate limiting plus exponential backoff,
# which handles bursty parallel specialist calls far better than the
# default retry mode's fixed small retry budget.
_BOTO_CONFIG = Config(retries={"max_attempts": 10, "mode": "adaptive"})


def get_llm() -> ChatBedrockConverse:
    client = boto3.client("bedrock-runtime", region_name=settings.aws_region, config=_BOTO_CONFIG)
    return ChatBedrockConverse(model=settings.bedrock_model_id, client=client)
