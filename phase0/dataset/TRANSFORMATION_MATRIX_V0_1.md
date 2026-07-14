# Матрица контролируемых преобразований V0.1

Преобразования создаются только из заранее зарегистрированных оригиналов. Каждый производный файл получает новый `sample_id`, тот же `family_id` и ссылку на `parent_sample_id`.

| Группа | Варианты первого цикла |
|---|---|
| JPEG | quality 95, 75, 50 |
| Resize | 75%, 50%, 25% от исходного размера |
| Crop | центральная обрезка 10% и 25% |
| WebP | quality 90 и 60 |
| Blur | Gaussian radius 1 и 2 |
| Noise | Gaussian noise σ=4 и σ=8 |
| Resampling | downsample 50% → upsample до исходного размера |
| Screenshot | один контролируемый скриншот при 100% масштабе |
| Комбинация | resize 50% + JPEG 75 |

## Первый dry run

Чтобы не раздувать работу, для первого dry run используется только по одному варианту:

- JPEG 75;
- resize 50%;
- crop 10%;
- screenshot;
- resize 50% + JPEG 75.

После проверки автоматизации матрица расширяется до полного набора.

## Исполнение первого цикла — 2026-07-14

Первый цикл выполнен на заранее выбранных 5 real и 5 AI-оригиналах. Для каждого создано восемь вариантов: JPEG Q75, JPEG Q50, resize 50%, crop 10%, browser screenshot 100%, Gaussian noise sigma=4, downsample 50% → upsample nearest-neighbor и resize 50% + JPEG Q75. Оба детектора обработали все 80 производных файлов.

Самым проблемным профилем стал JPEG Q50: Community Forensics сохранил условный сигнал `AI` на 3/5 AI, SPAI — на 2/5. Полный отчёт: [`../PILOT_TRANSFORMATION_DRY_RUN_2026-07-14.md`](../PILOT_TRANSFORMATION_DRY_RUN_2026-07-14.md).

## Сопоставимость с внешними benchmark

- JPEG quality 50 и Gaussian noise σ=4 добавлены для сопоставления с robustness-профилями AIGIBench;
- downsample 50% → upsample до исходного размера проверяется отдельно от обычного resize;
- crop и resize не считаются взаимозаменяемым preprocessing: они могут по-разному изменять real и fake accuracy;
- каждый detector получает один заранее зафиксированный preprocessing profile; подбор crop/resize после просмотра labels запрещён.
