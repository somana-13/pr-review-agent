from functools import cache

import boto3

from pr_review_agent.config import settings


@cache
def get_guardrail_client():
    return boto3.client("bedrock-runtime", region_name=settings.aws_region)
