#!/usr/bin/env python3
"""Build the fixed 10-image transformation dry-run corpus.

The source and derived image corpus stays under ``work/datasets`` and is ignored
by Git.  The manifest makes every operation reproducible without publishing the
private source photographs.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from PIL import Image, ImageOps


@dataclass(frozen=True)
class Sample:
    sample_id: str
    ground_truth: str
    source_family: str
    relative_path: str


SAMPLES = (
    Sample("IMG-000021", "real", "Apple iPhone", "work/datasets/iphone-202607-real/02_development_jpeg/IMG_9505.jpg"),
    Sample("IMG-000022", "real", "Apple iPhone", "work/datasets/iphone-202607-real/02_development_jpeg/IMG_9506.jpg"),
    Sample("IMG-000023", "real", "Apple iPhone", "work/datasets/iphone-202607-real/02_development_jpeg/IMG_9507.jpg"),
    Sample("IMG-000024", "real", "Apple iPhone", "work/datasets/iphone-202607-real/02_development_jpeg/IMG_9508.jpg"),
    Sample("IMG-000025", "real", "Apple iPhone", "work/datasets/iphone-202607-real/02_development_jpeg/IMG_9509.jpg"),
    Sample("AI-001", "ai_generated", "OpenAI image generator", "work/datasets/ai-generated-202607/02_detector_input/AI-001.png"),
    Sample("AI-002", "ai_generated", "OpenAI image generator", "work/datasets/ai-generated-202607/02_detector_input/AI-002.png"),
    Sample("AI-011", "ai_generated", "SDXL Turbo", "work/datasets/ai-generated-202607/02_detector_input/AI-011.png"),
    Sample("AI-016", "ai_generated", "Stable Diffusion 1.5", "work/datasets/ai-generated-202607/02_detector_input/AI-016.png"),
    Sample("AI-017", "ai_generated", "Stable Diffusion 1.5", "work/datasets/ai-generated-202607/02_detector_input/AI-017.png"),
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def edge_path() -> Path:
    candidates = (
        Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"),
        Path(r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"),
    )
    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise FileNotFoundError("Microsoft Edge is required for the controlled browser screenshot transform")


def controlled_browser_screenshot(source: Path, target: Path, width: int, height: int, edge: Path, profile: Path) -> None:
    document = f"""<!doctype html>
<meta charset=\"utf-8\">
<style>
  html, body {{ margin: 0; padding: 0; width: {width}px; height: {height}px; overflow: hidden; background: #000; }}
  img {{ display: block; width: {width}px; height: {height}px; object-fit: fill; }}
</style>
<img src=\"{html.escape(source.resolve().as_uri(), quote=True)}\" width=\"{width}\" height=\"{height}\">
"""
    with tempfile.NamedTemporaryFile("w", suffix=".html", encoding="utf-8", delete=False) as stream:
        stream.write(document)
        page = Path(stream.name)
    try:
        command = [
            str(edge),
            "--headless=new",
            "--disable-gpu",
            "--hide-scrollbars",
            "--force-device-scale-factor=1",
            f"--user-data-dir={profile}",
            f"--window-size={width},{height}",
            f"--screenshot={target.resolve()}",
            page.resolve().as_uri(),
        ]
        result = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=90)
        if result.returncode != 0 or not target.exists():
            raise RuntimeError(f"Edge screenshot failed: {result.stderr.strip()}")
    finally:
        page.unlink(missing_ok=True)


def parse_args() -> argparse.Namespace:
    repo_root = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=repo_root)
    parser.add_argument(
        "--output",
        type=Path,
        default=repo_root / "work/datasets/transformation-dry-run-202607",
    )
    parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    output = args.output.resolve()
    allowed_root = (repo_root / "work/datasets").resolve()
    if allowed_root not in output.parents:
        raise ValueError(f"Output must stay inside {allowed_root}")
    if output.exists():
        if not args.overwrite:
            raise FileExistsError(f"Output exists; pass --overwrite: {output}")
        shutil.rmtree(output)

    originals_dir = output / "00_selected_originals"
    detector_dir = output / "02_detector_input"
    manifests_dir = output / "manifests"
    results_dir = output / "results"
    profile_dir = output / ".edge-profile"
    for directory in (originals_dir, detector_dir, manifests_dir, results_dir, profile_dir):
        directory.mkdir(parents=True, exist_ok=True)

    edge = edge_path()
    manifest_rows: list[dict[str, object]] = []
    subset_rows: list[dict[str, object]] = []

    for index, sample in enumerate(SAMPLES):
        source = (repo_root / sample.relative_path).resolve()
        if not source.exists():
            raise FileNotFoundError(source)
        selected = originals_dir / f"{sample.sample_id}{source.suffix.lower()}"
        shutil.copy2(source, selected)

        with Image.open(source) as opened:
            original = ImageOps.exif_transpose(opened).convert("RGB")
        width, height = original.size
        source_hash = sha256(source)
        subset_rows.append(
            {
                "sample_id": sample.sample_id,
                "ground_truth": sample.ground_truth,
                "source_family": sample.source_family,
                "source_filename": source.name,
                "source_sha256": source_hash,
                "width": width,
                "height": height,
                "selection_rule": "fixed_before_transformation_scoring",
            }
        )

        variants: list[tuple[str, str, Image.Image, str, dict[str, object]]] = []
        variants.append(("jpeg_q75", ".jpg", original.copy(), "Pillow 10.4.0", {"quality": 75, "subsampling": "default", "metadata": "stripped"}))
        variants.append(("jpeg_q50", ".jpg", original.copy(), "Pillow 10.4.0", {"quality": 50, "subsampling": "default", "metadata": "stripped"}))
        half = (max(1, width // 2), max(1, height // 2))
        variants.append(("resize_50", ".png", original.resize(half, Image.Resampling.LANCZOS), "Pillow 10.4.0", {"scale": 0.5, "filter": "Lanczos"}))
        crop_box = (
            (width - max(1, int(width * 0.9))) // 2,
            (height - max(1, int(height * 0.9))) // 2,
            (width + max(1, int(width * 0.9))) // 2,
            (height + max(1, int(height * 0.9))) // 2,
        )
        variants.append(("crop_center_10", ".png", original.crop(crop_box), "Pillow 10.4.0", {"center_crop_removed_each_dimension_percent": 10}))
        resized = original.resize(half, Image.Resampling.LANCZOS)
        variants.append(("resize_50_jpeg_q75", ".jpg", resized, "Pillow 10.4.0", {"scale": 0.5, "filter": "Lanczos", "quality": 75, "metadata": "stripped"}))
        rng = np.random.default_rng(2026071400 + index)
        noisy = np.clip(np.asarray(original, dtype=np.float32) + rng.normal(0.0, 4.0, (height, width, 1)), 0, 255).astype(np.uint8)
        variants.append(("gaussian_noise_sigma4", ".png", Image.fromarray(noisy, "RGB"), "Pillow 10.4.0 + NumPy 1.26.4", {"distribution": "normal", "sigma_8bit": 4, "seed": 2026071400 + index}))
        down_up = original.resize(half, Image.Resampling.NEAREST).resize((width, height), Image.Resampling.NEAREST)
        variants.append(("down50_up_nearest", ".png", down_up, "Pillow 10.4.0", {"downscale": 0.5, "upscale_to_original": True, "filter": "nearest_neighbor"}))

        for transform_id, suffix, image, tool, parameters in variants:
            target = detector_dir / f"{sample.sample_id}__{transform_id}{suffix}"
            save_args = {"quality": parameters["quality"]} if suffix == ".jpg" else {}
            image.save(target, **save_args)
            manifest_rows.append(
                make_manifest_row(sample, source.name, source_hash, transform_id, parameters, target, tool)
            )

        screenshot_target = detector_dir / f"{sample.sample_id}__browser_screenshot_100.png"
        controlled_browser_screenshot(selected, screenshot_target, width, height, edge, profile_dir)
        manifest_rows.append(
            make_manifest_row(
                sample,
                source.name,
                source_hash,
                "browser_screenshot_100",
                {"browser": "Microsoft Edge headless", "css_scale": 1.0, "device_scale_factor": 1, "viewport": f"{width}x{height}"},
                screenshot_target,
                "Microsoft Edge controlled browser screenshot",
            )
        )

    write_csv(manifests_dir / "SUBSET_MANIFEST.csv", subset_rows)
    write_csv(manifests_dir / "TRANSFORMATION_MANIFEST.csv", manifest_rows)
    print(json.dumps({"samples": len(SAMPLES), "derivatives": len(manifest_rows), "output": str(output)}, ensure_ascii=False))


def make_manifest_row(
    sample: Sample,
    source_filename: str,
    source_hash: str,
    transform_id: str,
    parameters: dict[str, object],
    target: Path,
    tool: str,
) -> dict[str, object]:
    with Image.open(target) as image:
        width, height = image.size
        file_format = image.format
    return {
        "sample_id": sample.sample_id,
        "ground_truth": sample.ground_truth,
        "source_family": sample.source_family,
        "source_filename": source_filename,
        "source_sha256": source_hash,
        "transformation": transform_id,
        "parameters_json": json.dumps(parameters, ensure_ascii=False, sort_keys=True),
        "derived_filename": target.name,
        "derived_sha256": sha256(target),
        "file_format": file_format,
        "width": width,
        "height": height,
        "tool": tool,
    }


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        raise ValueError(f"No rows for {path}")
    with path.open("w", newline="", encoding="utf-8-sig") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    main()
