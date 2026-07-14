#!/usr/bin/env python3
"""Create public tables for the fixed transformation dry run."""

from __future__ import annotations

import csv
import json
import statistics
from collections import defaultdict
from pathlib import Path


THRESHOLD = 0.5
TRANSFORM_ORDER = (
    "jpeg_q75",
    "jpeg_q50",
    "resize_50",
    "crop_center_10",
    "browser_screenshot_100",
    "gaussian_noise_sigma4",
    "down50_up_nearest",
    "resize_50_jpeg_q75",
)
TRANSFORM_LABELS = {
    "jpeg_q75": "JPEG Q75",
    "jpeg_q50": "JPEG Q50",
    "resize_50": "Resize 50% (Lanczos)",
    "crop_center_10": "Center crop 10%",
    "browser_screenshot_100": "Browser screenshot 100%",
    "gaussian_noise_sigma4": "Gaussian noise sigma=4",
    "down50_up_nearest": "Down 50% -> up (nearest)",
    "resize_50_jpeg_q75": "Resize 50% + JPEG Q75",
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as stream:
        return list(csv.DictReader(stream))


def fmt(value: float) -> str:
    return f"{value:.10g}"


def yes(value: bool) -> str:
    return "true" if value else "false"


def main() -> None:
    repo = Path(__file__).resolve().parents[2]
    local = repo / "work/datasets/transformation-dry-run-202607"
    manifest = read_csv(local / "manifests/TRANSFORMATION_MANIFEST.csv")
    real_baseline = {row["sample_id"]: row for row in read_csv(repo / "phase0/REAL_DRY_RUN_RESULTS_2026-07-14.csv")}
    ai_baseline = {row["sample_id"]: row for row in read_csv(repo / "phase0/AI_DRY_RUN_RESULTS_2026-07-14.csv")}
    baselines = real_baseline | ai_baseline
    with (local / "results/community-forensics-384/results.json").open(encoding="utf-8") as stream:
        community = {row["image"]: float(row["score_fake"]) for row in json.load(stream)["results"]}
    spai = {
        row["image"]: float(row["spai"])
        for row in read_csv(local / "results/spai-resize1024/02_detector_input.csv")
    }

    rows: list[dict[str, str]] = []
    for item in manifest:
        baseline = baselines[item["sample_id"]]
        c0 = float(baseline["community_score_fake"])
        s0 = float(baseline["spai_score_fake"])
        c1 = community[item["derived_filename"]]
        s1 = spai[item["derived_filename"]]
        truth_ai = item["ground_truth"] == "ai_generated"
        c0p, c1p = c0 >= THRESHOLD, c1 >= THRESHOLD
        s0p, s1p = s0 >= THRESHOLD, s1 >= THRESHOLD
        rows.append(
            {
                "sample_id": item["sample_id"],
                "ground_truth": item["ground_truth"],
                "source_family": item["source_family"],
                "transformation": item["transformation"],
                "parameters_json": item["parameters_json"],
                "file_format": item["file_format"],
                "width": item["width"],
                "height": item["height"],
                "derived_sha256": item["derived_sha256"],
                "community_baseline": fmt(c0),
                "community_transformed": fmt(c1),
                "community_delta": fmt(c1 - c0),
                "community_baseline_ge_0_5": yes(c0p),
                "community_transformed_ge_0_5": yes(c1p),
                "community_decision_flip": yes(c0p != c1p),
                "community_correct_after": yes(c1p == truth_ai),
                "spai_baseline": fmt(s0),
                "spai_transformed": fmt(s1),
                "spai_delta": fmt(s1 - s0),
                "spai_baseline_ge_0_5": yes(s0p),
                "spai_transformed_ge_0_5": yes(s1p),
                "spai_decision_flip": yes(s0p != s1p),
                "spai_correct_after": yes(s1p == truth_ai),
                "interpretation": "research_signal_only",
            }
        )

    csv_path = repo / "phase0/TRANSFORMATION_DRY_RUN_RESULTS_2026-07-14.csv"
    with csv_path.open("w", newline="", encoding="utf-8-sig") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    report = build_report(rows)
    report_path = repo / "phase0/PILOT_TRANSFORMATION_DRY_RUN_2026-07-14.md"
    report_path.write_text(report, encoding="utf-8")
    print(f"Wrote {len(rows)} rows to {csv_path}")
    print(f"Wrote report to {report_path}")


def build_report(rows: list[dict[str, str]]) -> str:
    by_transform: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        by_transform[row["transformation"]].append(row)

    lines = [
        "# Пилот устойчивости к преобразованиям — 2026-07-14",
        "",
        "Статус: открытый **development/dry run**, не валидация методики и не экспертный вывод.",
        "",
        "## Короткий результат",
        "",
        "- Самое заметное ухудшение дал **JPEG Q50**: Community Forensics сохранил сигнал `AI` на 3 из 5 ИИ-изображений, SPAI — только на 2 из 5.",
        "- При JPEG Q75 результат мягче: Community Forensics — 4/5, SPAI — 4/5.",
        "- Контролируемый browser screenshot сохранил обнаружение ИИ на 4/5 у Community Forensics и 5/5 у SPAI; на этой малой выборке SPAI перестал ошибочно помечать один реальный оригинал как `AI`.",
        "- Детекторы реагируют на преобразования по-разному. Поэтому один балл нельзя использовать как самостоятельное доказательство происхождения изображения.",
        "",
        "## Что проверено",
        "",
        "До получения результатов зафиксированы 10 оригиналов:",
        "",
        "- 5 реальных JPEG с Apple iPhone: `IMG-000021`–`IMG-000025`;",
        "- 5 ИИ-изображений: 2 OpenAI image generator, 1 SDXL-Turbo, 2 Stable Diffusion 1.5.",
        "",
        "Для каждого оригинала создано 8 производных вариантов, всего **80 файлов**:",
        "",
        "1. JPEG Q75;",
        "2. JPEG Q50;",
        "3. уменьшение до 50% (Lanczos);",
        "4. центральное кадрирование 10%;",
        "5. контролируемый browser screenshot при масштабе 100%;",
        "6. Gaussian noise, `sigma=4` в шкале 8 bit;",
        "7. уменьшение до 50% и возврат к исходному размеру nearest-neighbor;",
        "8. уменьшение до 50% + JPEG Q75.",
        "",
        "Browser screenshot выполнен Microsoft Edge в headless-режиме: CSS scale 100%, device scale factor 1, viewport равен размеру исходного изображения. Это воспроизводимый захват браузерной отрисовки, **не фотографирование физического экрана**.",
        "",
        "Порог `score_fake >= 0.5` заранее сохранён как временный исследовательский порог. Community Forensics использовал вход 384 px; SPAI — фиксированный препроцессинг `SmallestMaxSize(1024)`.",
        "",
        "## Решения после преобразования",
        "",
        "В ячейках `AI` — сколько из 5 ИИ-изображений осталось выше порога; `Real FP` — сколько из 5 реальных изображений ошибочно оказалось выше порога.",
        "",
        "| Преобразование | Community AI | Community Real FP | SPAI AI | SPAI Real FP |",
        "|---|---:|---:|---:|---:|",
    ]
    for transform in TRANSFORM_ORDER:
        group = by_transform[transform]
        c_ai = positive_count(group, "community", "ai_generated")
        c_real = positive_count(group, "community", "real")
        s_ai = positive_count(group, "spai", "ai_generated")
        s_real = positive_count(group, "spai", "real")
        lines.append(f"| {TRANSFORM_LABELS[transform]} | {c_ai}/5 | {c_real}/5 | {s_ai}/5 | {s_real}/5 |")

    lines += [
        "",
        "Для выбранных оригиналов baseline был: Community Forensics — `AI 4/5`, `Real FP 0/5`; SPAI — `AI 5/5`, `Real FP 1/5`.",
        "",
        "## Смена решения относительно оригинала",
        "",
        "| Преобразование | Community flips | SPAI flips | Медиана abs(delta), Community | Медиана abs(delta), SPAI |",
        "|---|---:|---:|---:|---:|",
    ]
    for transform in TRANSFORM_ORDER:
        group = by_transform[transform]
        c_flips = sum(row["community_decision_flip"] == "true" for row in group)
        s_flips = sum(row["spai_decision_flip"] == "true" for row in group)
        c_delta = statistics.median(abs(float(row["community_delta"])) for row in group)
        s_delta = statistics.median(abs(float(row["spai_delta"])) for row in group)
        lines.append(f"| {TRANSFORM_LABELS[transform]} | {c_flips}/10 | {s_flips}/10 | {c_delta:.4f} | {s_delta:.4f} |")

    flips = []
    for row in rows:
        for detector in ("community", "spai"):
            if row[f"{detector}_decision_flip"] == "true":
                before = "AI" if row[f"{detector}_baseline_ge_0_5"] == "true" else "real"
                after = "AI" if row[f"{detector}_transformed_ge_0_5"] == "true" else "real"
                flips.append((row["sample_id"], TRANSFORM_LABELS[row["transformation"]], detector, before, after))
    lines += [
        "",
        "Всего зафиксировано **{} смен порогового решения** в 160 парных оценках (80 файлов x 2 детектора).".format(len(flips)),
        "",
        "| Образец | Преобразование | Детектор | Было -> стало |",
        "|---|---|---|---|",
    ]
    for sample_id, transform, detector, before, after in flips:
        detector_label = "Community Forensics" if detector == "community" else "SPAI"
        lines.append(f"| {sample_id} | {transform} | {detector_label} | {before} -> {after} |")

    lines += [
        "",
        "## Ограничения",
        "",
        "- Выборка мала и открыта для разработки; она не даёт оценку чувствительности/специфичности генеральной совокупности.",
        "- Изображения OpenAI созданы через интерфейс, который не раскрывает точный seed и revision модели.",
        "- Browser screenshot моделирует браузерную перерисовку, но не физическую съёмку монитора камерой.",
        "- Временный порог 0.5 не калиброван на независимой закрытой выборке.",
        "- Все преобразованные изображения и локальные манифесты оставлены вне публичного Git-репозитория; в репозиторий включены только таблица сигналов и описание процедуры.",
        "",
        "## Практический вывод для методики",
        "",
        "1. Отчёт должен сохранять исходный файл и отдельно фиксировать каждую исследованную копию.",
        "2. JPEG-компрессию и иные преобразования необходимо учитывать как фактор, способный скрыть или изменить модельный сигнал.",
        "3. Несовпадение детекторов и смена решения после преобразования являются основанием для осторожности, а не для выбора «удобного» результата.",
        "4. Следующий этап — увеличить выборку, заранее заморозить holdout и считать ROC-AUC, PR-AUC, EER, Brier score и TPR при фиксированных FPR.",
        "",
        "Полные построчные значения: [`TRANSFORMATION_DRY_RUN_RESULTS_2026-07-14.csv`](TRANSFORMATION_DRY_RUN_RESULTS_2026-07-14.csv).",
        "",
    ]
    return "\n".join(lines)


def positive_count(group: list[dict[str, str]], detector: str, truth: str) -> int:
    return sum(
        row["ground_truth"] == truth and row[f"{detector}_transformed_ge_0_5"] == "true"
        for row in group
    )


if __name__ == "__main__":
    main()
