import sys
from pathlib import Path

from huggingface_hub import HfApi

from pr_review_agent.config import settings

ADAPTER_DIR = Path(__file__).parent / "checkpoints" / "lora-adapter"


def export(repo_id: str) -> None:
    api = HfApi(token=settings.hf_token)
    api.create_repo(repo_id, exist_ok=True, private=False)
    api.upload_folder(folder_path=str(ADAPTER_DIR), repo_id=repo_id)
    print(f"Uploaded adapter to https://huggingface.co/{repo_id}")


if __name__ == "__main__":
    export(sys.argv[1])
