from pathlib import Path

from safetensors import safe_open

adapter_path = Path(__file__).parent / "checkpoints" / "lora-adapter" / "adapter_model.safetensors"

with safe_open(str(adapter_path), framework="pt") as f:
    keys = list(f.keys())

classifier_keys = [k for k in keys if "classifier" in k or "modules_to_save" in k]
lora_keys = [k for k in keys if "lora" in k]

print(f"Total keys: {len(keys)}")
print(f"Classifier/modules_to_save keys: {len(classifier_keys)}")
for k in classifier_keys:
    print(" ", k)
print(f"LoRA keys: {len(lora_keys)}")
