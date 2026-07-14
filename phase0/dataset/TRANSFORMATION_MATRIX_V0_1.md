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

## Сопоставимость с внешними benchmark

- JPEG quality 50 и Gaussian noise σ=4 добавлены для сопоставления с robustness-профилями AIGIBench;
- downsample 50% → upsample до исходного размера проверяется отдельно от обычного resize;
- crop и resize не считаются взаимозаменяемым preprocessing: они могут по-разному изменять real и fake accuracy;
- каждый detector получает один заранее зафиксированный preprocessing profile; подбор crop/resize после просмотра labels запрещён.
