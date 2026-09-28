import sys
from pathlib import Path

FINETUNE_DATA_DIR = Path(__file__).parent.parent / "finetune" / "data"
sys.path.insert(0, str(FINETUNE_DATA_DIR))
