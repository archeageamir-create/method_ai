"""Generate a small, reproducible image set with a Hugging Face Diffusers model."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import torch
from diffusers import AutoPipelineForText2Image
from huggingface_hub import HfApi


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True)
    parser.add_argument("--prompts", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--steps", type=int, required=True)
    parser.add_argument("--guidance", type=float, required=True)
    parser.add_argument("--width", type=int, default=512)
    parser.add_argument("--height", type=int, default=512)
    parser.add_argument("--seed-base", type=int, required=True)
    parser.add_argument("--variant", default="fp16")
    args = parser.parse_args()

    if not torch.cuda.is_available():
        raise RuntimeError("CUDA is required for the approved local generation profile")

    prompts = json.loads(args.prompts.read_text(encoding="utf-8"))
    args.output.mkdir(parents=True, exist_ok=True)
    revision = HfApi().model_info(args.model).sha

    load_kwargs = {"torch_dtype": torch.float16, "revision": revision}
    if args.variant:
        load_kwargs["variant"] = args.variant
    try:
        pipe = AutoPipelineForText2Image.from_pretrained(args.model, **load_kwargs)
    except OSError:
        load_kwargs.pop("variant", None)
        pipe = AutoPipelineForText2Image.from_pretrained(args.model, **load_kwargs)

    # Keep peak VRAM below the 8 GB board limit while still doing denoising on CUDA.
    pipe.enable_model_cpu_offload()
    pipe.enable_attention_slicing()
    pipe.set_progress_bar_config(disable=False)

    manifest_path = args.output / "generation_manifest.csv"
    fieldnames = [
        "item_id", "filename", "model_id", "model_revision", "seed", "prompt",
        "steps", "guidance_scale", "width", "height", "dtype", "device",
        "generated_at_utc", "sha256",
    ]
    rows = []
    for index, item in enumerate(prompts):
        item_id = item["item_id"]
        target = args.output / f"{item_id}.png"
        seed = args.seed_base + index
        if not target.exists():
            generator = torch.Generator(device="cpu").manual_seed(seed)
            image = pipe(
                prompt=item["prompt"],
                num_inference_steps=args.steps,
                guidance_scale=args.guidance,
                width=args.width,
                height=args.height,
                generator=generator,
            ).images[0]
            image.save(target, format="PNG")
        rows.append({
            "item_id": item_id,
            "filename": target.name,
            "model_id": args.model,
            "model_revision": revision,
            "seed": seed,
            "prompt": item["prompt"],
            "steps": args.steps,
            "guidance_scale": args.guidance,
            "width": args.width,
            "height": args.height,
            "dtype": "float16",
            "device": torch.cuda.get_device_name(0),
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "sha256": sha256(target),
        })
        print(f"saved {target}", flush=True)

    with manifest_path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    main()
