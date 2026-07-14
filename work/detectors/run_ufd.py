"""Single-image UniversalFakeDetect inference for local research use."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import torch
from PIL import Image


ROOT = Path(__file__).resolve().parent
REPO = ROOT / "universal-fake-detect"
WEIGHTS = REPO / "pretrained_weights" / "fc_weights.pth"
sys.path.insert(0, str(REPO))

from models import get_model  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("images", type=Path, nargs="+")
    args = parser.parse_args()

    if not torch.cuda.is_available():
        raise RuntimeError("CUDA GPU is required for the approved local profile")

    model = get_model("CLIP:ViT-L/14")
    state_dict = torch.load(WEIGHTS, map_location="cpu", weights_only=True)
    model.fc.load_state_dict(state_dict)
    model = model.eval().to("cuda")

    tensors = [model.preprocess(Image.open(path).convert("RGB")) for path in args.images]
    tensor = torch.stack(tensors).to("cuda")
    with torch.inference_mode():
        scores = torch.sigmoid(model(tensor)).flatten().tolist()

    print(json.dumps({
        "detector": "UniversalFakeDetect CLIP ViT-L/14",
        "results": [
            {"image": str(path.resolve()), "score_fake": score}
            for path, score in zip(args.images, scores)
        ],
        "device": torch.cuda.get_device_name(0),
        "warning": "Research signal only; not an expert conclusion.",
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
