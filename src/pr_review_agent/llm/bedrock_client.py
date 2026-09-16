from langchain_aws import ChatBedrockConverse

from pr_review_agent.config import settings


def get_llm() -> ChatBedrockConverse:
    return ChatBedrockConverse(
        model=settings.bedrock_model_id,
        region_name=settings.aws_region,
    )
