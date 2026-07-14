"""Merge AI generation provenance with detector outputs and write pilot reports."""

from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DATASET = ROOT / "work" / "datasets" / "ai-generated-202607"
PHASE0 = ROOT / "phase0"
THRESHOLD = 0.5


def read_csv(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def write_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def count(rows: list[dict], field: str) -> int:
    return sum(row[field] == "true" for row in rows)


def main() -> None:
    manifest = {row["item_id"]: row for row in read_csv(DATASET / "manifests" / "GENERATION_MANIFEST.csv")}
    with (DATASET / "results" / "community-forensics-384" / "results.json").open(encoding="utf-8") as stream:
        community = {Path(row["image"]).stem: float(row["score_fake"]) for row in json.load(stream)["results"]}
    spai_rows = read_csv(DATASET / "results" / "spai-resize1024" / "02_detector_input.csv")
    spai = {Path(row["image"]).stem: float(row["spai"]) for row in spai_rows}

    rows = []
    for item_id in sorted(manifest):
        item = manifest[item_id]
        c_score = community[item_id]
        s_score = spai[item_id]
        c_signal = c_score >= THRESHOLD
        s_signal = s_score >= THRESHOLD
        rows.append({
            "sample_id": item_id,
            "filename": item["filename"],
            "ground_truth": "ai_generated",
            "generator_family": item["generator_family"],
            "model_id": item["model_id"],
            "model_revision": item["model_revision"],
            "seed": item["seed"],
            "sha256": item["sha256"],
            "community_score_fake": f"{c_score:.12g}",
            "spai_score_fake": f"{s_score:.12g}",
            "community_ge_0_5": str(c_signal).lower(),
            "spai_ge_0_5": str(s_signal).lower(),
            "signals_disagree": str(c_signal != s_signal).lower(),
            "interpretation": "research_signal_only",
        })
    write_csv(PHASE0 / "AI_DRY_RUN_RESULTS_2026-07-14.csv", rows)

    by_family: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        by_family[row["generator_family"]].append(row)

    family_lines = []
    for family, family_rows in by_family.items():
        family_lines.append(
            f"| {family} | {len(family_rows)} | {count(family_rows, 'community_ge_0_5')} | "
            f"{count(family_rows, 'spai_ge_0_5')} | {count(family_rows, 'signals_disagree')} |"
        )

    ai_report = f"""# Dry run на контролируемо сгенерированных изображениях — 14 июля 2026 года

**Статус:** технический открытый dry run; не валидация точности и не основание экспертного вывода.
**Оператор:** Смагулов Амирхан Каиржанович.
**Рабочая пара детекторов:** Community Forensics 384 и SPAI.
**Ground truth:** `ai_generated`, основание — контролируемая генерация с сохранённым происхождением.

## 1. Состав набора

- 20 PNG-оригиналов без последующего JPEG-сжатия;
- 10 изображений: OpenAI image generator via Codex;
- 5 изображений: `stabilityai/sdxl-turbo`, commit `71153311d3dbb46851df1931d3ca6e939de83304`;
- 5 изображений: `stable-diffusion-v1-5/stable-diffusion-v1-5`, commit `451f4fe16113bff5a5d2269ed5ad43b0592e9a14`;
- для локальных моделей сохранены точные seed, prompt, число шагов, guidance scale и SHA-256;
- интерфейс OpenAI не раскрывает точное имя версии модели, seed и параметры семплирования; в журнале это прямо обозначено как `not_exposed_by_interface`;
- пять основных типов сцен повторены в обеих локальных моделях: офис, улица, портрет, еда, пейзаж;
- изображения и полный локальный реестр исключены из Git; в репозиторий включаются только обезличенные результаты и описание процедуры.

Локальный набор: `work/datasets/ai-generated-202607/`.
Объединённые результаты: `AI_DRY_RUN_RESULTS_2026-07-14.csv`.

## 2. Генерация и вычислительная среда

- GPU: NVIDIA GeForce RTX 5050, 8 GB VRAM;
- PyTorch: 2.12.1+cu132; CUDA внутри PyTorch подтверждена;
- Diffusers: 0.36.0; Transformers: 4.57.6; Accelerate: 1.14.0;
- SDXL-Turbo: FP16, 512×512, 1 шаг, guidance scale 0, CPU offload с вычислением денойзинга на CUDA;
- Stable Diffusion 1.5: FP16, 512×512, 25 шагов, guidance scale 7.5, CPU offload с вычислением денойзинга на CUDA;
- Community Forensics: профиль 384;
- SPAI: официальный вес `spai.pth`, resize длинной стороны до 1024 px, batch size 1, два workers.

## 3. Наблюдаемые результаты

Порог 0.5 используется только для описания поведения программ. Он не является утверждённым экспертным порогом и не превращает score в вероятность версии.

| Семейство генератора | n | Community ≥ 0.5 | SPAI ≥ 0.5 | Расхождение сигналов |
|---|---:|---:|---:|---:|
{chr(10).join(family_lines)}
| **Всего** | **20** | **{count(rows, 'community_ge_0_5')}** | **{count(rows, 'spai_ge_0_5')}** | **{count(rows, 'signals_disagree')}** |

Наблюдаемая доля AI-файлов со score не ниже 0.5 составила {count(rows, 'community_ge_0_5')}/20 ({count(rows, 'community_ge_0_5') * 5}%) у Community Forensics и {count(rows, 'spai_ge_0_5')}/20 ({count(rows, 'spai_ge_0_5') * 5}%) у SPAI. Оба локальных семейства получили сигнал не ниже 0.5 на всех десяти файлах. На OpenAI-изображениях Community дал 5/10, SPAI — 8/10; три условных бинарных сигнала разошлись.

## 4. Что это означает

1. Оба детектора технически реагируют на несколько разных семейств генераторов.
2. Результат сильно зависит от семейства: OpenAI-изображения оказались заметно сложнее для Community Forensics, чем SDXL-Turbo и SD 1.5.
3. Даже очень высокий score не идентифицирует конкретный генератор и не доказывает обстоятельства происхождения без других данных.
4. Нулевой или низкий score не исключает AI-генерацию: на пяти OpenAI-файлах Community и на двух OpenAI-файлах SPAI условный сигнал отсутствовал.
5. Набор открыт, мал и использован для настройки процесса, поэтому наблюдаемые доли нельзя выдавать за валидированные чувствительность или точность.

## 5. Следующий шаг

1. Добавить независимое четвёртое семейство после получения законного доступа к подходящей модели; FLUX.1-schnell пока не использован из-за gated-доступа официального репозитория и ограничений 8 GB VRAM.
2. Применить заранее заданную матрицу преобразований: JPEG 75, resize, crop, screenshot и повторное сохранение.
3. Заморозить версии, decision policy и статистический план до просмотра internal holdout.
4. Сформировать закрытый и внешний наборы независимо от этих 40 development-файлов.
"""
    (PHASE0 / "PILOT_AI_DRY_RUN_2026-07-14.md").write_text(ai_report, encoding="utf-8")

    real_rows = read_csv(PHASE0 / "REAL_DRY_RUN_RESULTS_2026-07-14.csv")
    real_community = count(real_rows, "community_ge_0_5")
    real_spai = count(real_rows, "spai_ge_0_5")
    real_disagree = count(real_rows, "signals_disagree")
    real_both = sum(
        row["community_ge_0_5"] == "true" and row["spai_ge_0_5"] == "true" for row in real_rows
    )
    ai_both = sum(
        row["community_ge_0_5"] == "true" and row["spai_ge_0_5"] == "true" for row in rows
    )
    summary = f"""# Сводка открытого dry run на 40 изображениях — 14 июля 2026 года

**Статус:** development-проверка процесса, не валидация метода. Порог 0.5 — только условный способ описать сигналы двух программ.

| Ground truth | n | Community ≥ 0.5 | SPAI ≥ 0.5 | Оба ≥ 0.5 | Расхождение |
|---|---:|---:|---:|---:|---:|
| Реальные контролируемые фото | 20 | {real_community} | {real_spai} | {real_both} | {real_disagree} |
| Контролируемая AI-генерация | 20 | {count(rows, 'community_ge_0_5')} | {count(rows, 'spai_ge_0_5')} | {ai_both} | {count(rows, 'signals_disagree')} |
| **Всего** | **40** | **{real_community + count(rows, 'community_ge_0_5')}** | **{real_spai + count(rows, 'spai_ge_0_5')}** | **{real_both + ai_both}** | **{real_disagree + count(rows, 'signals_disagree')}** |

## Наблюдения

- Community Forensics: условный сигнал на 15/20 AI и на 1/20 реальных файлов.
- SPAI: условный сигнал на 18/20 AI и на 6/20 реальных файлов.
- правило «хотя бы один детектор» обнаружило бы 18/20 AI, но одновременно пометило бы 7/20 реальных файлов;
- правило «оба детектора» пометило бы 15/20 AI и 0/20 реальных файлов в этой конкретной открытой выборке;
- эти значения нельзя переносить на практику: изображения известны разработчику, выборка мала, неслучайна и не закрыта.

## Процессуальный вывод

Dry run выполнил свою задачу: подтвердил работоспособность цепочки, выявил расхождения моделей и показал, почему методике нужны `Hu`, анализ метаданных/происхождения и закрытая валидация. Порог или правило объединения по этим 40 файлам не утверждаются.
"""
    (PHASE0 / "PILOT_DRY_RUN_40_SUMMARY_2026-07-14.md").write_text(summary, encoding="utf-8")


if __name__ == "__main__":
    main()
