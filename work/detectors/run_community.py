"""Single-image Community Forensics inference for local research use."""

from __future__ import annotations

import argparse
import contextlib
import json
import sys
from pathlib import Path

import torch
from PIL import Image
from torchvision import transforms


ROOT = Path(__file__).resolve().parent
REPO = ROOT / "community-forensics"
MODEL_DIR = ROOT / "models" / "commfor-model-384"
sys.path.insert(0, str(REPO))

import models  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("images", type=Path, nargs="+")
    args = parser.parse_args()

    if not torch.cuda.is_available():
        raise RuntimeError("CUDA GPU is required for the approved local profile")

    processor = transforms.Compose([
        transforms.Resize(440),
        transforms.CenterCrop(384),
        transforms.ToTensor(),
        transforms.Normalize(
            mean=[0.485, 0.456, 0.406],
            std=[0.229, 0.224, 0.225],
        ),
    ])
    # The upstream loader prints a status line to stdout. Keep stdout as clean
    # machine-readable JSON and route that diagnostic line to stderr instead.
    with contextlib.redirect_stdout(sys.stderr):
        model = models.ViTClassifier.from_pretrained(MODEL_DIR).eval().to("cuda")
    tensors = [processor(Image.open(path).convert("RGB")) for path in args.images]
    tensor = torch.stack(tensors).to("cuda")
    with torch.inference_mode():
        scores = torch.sigmoid(model(tensor)).flatten().tolist()

    print(json.dumps({
        "detector": "Community Forensics 384",
        "results": [
            {"image": path.name, "score_fake": score}
            for path, score in zip(args.images, scores)
        ],
        "device": torch.cuda.get_device_name(0),
        "warning": "Research signal only; not an expert conclusion.",
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
