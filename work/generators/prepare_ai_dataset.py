"""Assemble generated originals into a numbered detector input and provenance manifests."""

from __future__ import annotations

import csv
import hashlib
import shutil
from datetime import date
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[2]
DATASET = ROOT / "work" / "datasets" / "ai-generated-202607"

OPENAI_OUTPUT = Path.home() / ".codex" / "generated_images" / "019f5b5d-d5fe-7d73-b1b5-7aa11784a418"
OPENAI_ITEMS = [
    ("AI-001", OPENAI_OUTPUT / "exec-4230a36f-a105-42c7-9da5-00ffb87f3bd7.png", "office desk near a window in daylight, laptop, mug, notebook, pen and plant"),
    ("AI-002", OPENAI_OUTPUT / "exec-6aae7396-36a7-4ba3-b34b-322cdeab4482.png", "residential intersection after rain at blue hour"),
    ("AI-003", OPENAI_OUTPUT / "exec-0b0050dc-fe35-42b2-b085-9cf65f521552.png", "fictional adult man by a concrete wall"),
    ("AI-004", OPENAI_OUTPUT / "exec-6cbc43fb-ca7d-4023-aa6b-fb9154409833.png", "simple breakfast on a wooden kitchen table"),
    ("AI-005", OPENAI_OUTPUT / "exec-46d55a8b-5839-45a8-b076-28a74d28842e.png", "small lake, reeds and low hills on a cloudy day"),
    ("AI-006", OPENAI_OUTPUT / "exec-90fe905c-6e4a-4361-972c-1ecd32d1336d.png", "shared office desk in late afternoon with laptop and bottle"),
    ("AI-007", OPENAI_OUTPUT / "exec-e7048799-c744-42ac-9747-529760229bec.png", "city bus stop on a gray winter morning"),
    ("AI-008", OPENAI_OUTPUT / "exec-44ba395d-49c1-4733-9ad8-2de179f85368.png", "fictional adult woman by a brick wall"),
    ("AI-009", OPENAI_OUTPUT / "exec-099312f5-8784-409f-a8fa-bc3db0901e35.png", "groceries on a kitchen counter"),
    ("AI-010", OPENAI_OUTPUT / "exec-5dd65487-4fe7-4760-b996-d2c1ca9b8483.png", "flat steppe road under a pale evening sky"),
]


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest().upper()


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    originals = DATASET / "01_originals" / "openai-codex"
    detector_input = DATASET / "02_detector_input"
    originals.mkdir(parents=True, exist_ok=True)
    detector_input.mkdir(parents=True, exist_ok=True)
    for old in detector_input.glob("AI-*.png"):
        old.unlink()

    generation_rows: list[dict] = []
    dataset_rows: list[dict] = []

    items: list[dict] = []
    for item_id, source, prompt_summary in OPENAI_ITEMS:
        if not source.exists():
            raise FileNotFoundError(source)
        original = originals / f"{item_id}.png"
        shutil.copy2(source, original)
        items.append({
            "item_id": item_id,
            "source": original,
            "generator_family": "OpenAI image generator",
            "model_id": "OpenAI image generator via Codex",
            "model_revision": "not_exposed_by_interface",
            "seed": "not_exposed_by_interface",
            "prompt": prompt_summary,
            "steps": "not_exposed_by_interface",
            "guidance_scale": "not_exposed_by_interface",
            "dtype": "service_managed",
            "device": "service_managed",
        })

    local_specs = [
        ("sdxl-turbo", 11, "SDXL Turbo"),
        ("sd15", 16, "Stable Diffusion 1.5"),
    ]
    for folder, first_number, family in local_specs:
        source_dir = DATASET / "01_originals" / folder
        with (source_dir / "generation_manifest.csv").open(encoding="utf-8-sig", newline="") as stream:
            for offset, row in enumerate(csv.DictReader(stream)):
                item_id = f"AI-{first_number + offset:03d}"
                items.append({
                    "item_id": item_id,
                    "source": source_dir / row["filename"],
                    "generator_family": family,
                    "model_id": row["model_id"],
                    "model_revision": row["model_revision"],
                    "seed": row["seed"],
                    "prompt": row["prompt"],
                    "steps": row["steps"],
                    "guidance_scale": row["guidance_scale"],
                    "dtype": row["dtype"],
                    "device": row["device"],
                })

    for item in items:
        target = detector_input / f"{item['item_id']}.png"
        shutil.copy2(item["source"], target)
        with Image.open(target) as image:
            width, height = image.size
        file_hash = digest(target)
        generation_rows.append({
            "item_id": item["item_id"],
            "filename": target.name,
            "generator_family": item["generator_family"],
            "model_id": item["model_id"],
            "model_revision": item["model_revision"],
            "seed": item["seed"],
            "prompt": item["prompt"],
            "steps": item["steps"],
            "guidance_scale": item["guidance_scale"],
            "width": width,
            "height": height,
            "dtype": item["dtype"],
            "device": item["device"],
            "generated_at": date.today().isoformat(),
            "sha256": file_hash,
        })
        dataset_rows.append({
            "sample_id": item["item_id"],
            "family_id": item["item_id"],
            "split": "development",
            "ground_truth": "ai_generated",
            "truth_basis": "controlled_generation",
            "source_type": "generator",
            "source_name": item["model_id"],
            "source_version": item["model_revision"],
            "stored_filename": target.name,
            "file_format": "PNG",
            "width": width,
            "height": height,
            "sha256": file_hash,
            "acquired_at": date.today().isoformat(),
            "acquired_by": "Смагулов Амирхан Каиржанович",
            "license_or_permission": "project_research_use",
            "transformation": "none",
            "notes": "controlled AI generation; detector signal is not an expert conclusion",
        })

    generation_fields = [
        "item_id", "filename", "generator_family", "model_id", "model_revision", "seed",
        "prompt", "steps", "guidance_scale", "width", "height", "dtype", "device",
        "generated_at", "sha256",
    ]
    dataset_fields = [
        "sample_id", "family_id", "split", "ground_truth", "truth_basis", "source_type",
        "source_name", "source_version", "stored_filename", "file_format", "width", "height",
        "sha256", "acquired_at", "acquired_by", "license_or_permission", "transformation", "notes",
    ]
    write_csv(DATASET / "manifests" / "GENERATION_MANIFEST.csv", generation_rows, generation_fields)
    write_csv(DATASET / "manifests" / "DATASET_REGISTER.csv", dataset_rows, dataset_fields)
    print(f"prepared {len(items)} images in {detector_input}")


if __name__ == "__main__":
    main()
