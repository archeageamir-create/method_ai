# План использования публичных датасетов V0.1

**Статус:** рабочий shortlist; данные ещё не включены в замороженный protocol

## Короткий ответ

Большую часть требуемых 2000 независимых parents можно взять из существующих публичных датасетов. Снимать 1000 real и вручную генерировать 1000 AI не требуется.

Однако публичная доступность сама по себе не делает набор пригодным для закрытой валидации. До включения проверяются:

1. происхождение и основание ground truth;
2. лицензия именно на изображения, а не только на код репозитория;
3. отсутствие тех же файлов и источников в обучении проверяемого детектора;
4. независимость parents и отсутствие производных между split;
5. соответствие target population проекта;
6. возможность заранее сформировать blind manifest и сохранить SHA-256.

## Предварительная архитектура 2000 parents

| Этап | Real | AI | Предварительные источники |
|---|---:|---:|---|
| Development | 200 | 200 | GenImage и наборы с известным overlap допустимы, так как этап открытый |
| Internal holdout | 400 | 400 | RAISE/Warwick + четыре recent-generator subsets AIGIBench после проверки лицензий и overlap |
| External holdout | 400 | 400 | FloreView/HDR или независимые Warwick devices + четыре Synthbuster families |

Это схема источников, а не готовый split. Конкретные `sample_id` выбираются детерминированно до запуска детекторов и фиксируются отдельным manifest.

## Рекомендуемые наборы

### 1. Synthbuster — сильный кандидат для AI external holdout

- 9000 AI-изображений, по 1000 от девяти моделей: DALL·E 2, DALL·E 3, Adobe Firefly, Midjourney v5, SD 1.3, SD 1.4, SD 2, SDXL и GLIDE;
- опубликованы prompts и параметры;
- 12.4 GB, сохранён MD5 архива;
- лицензия: CC BY-NC-SA 4.0;
- изображения сопоставимы с RAISE-1k по содержанию и не имеют заранее внесённых JPEG/resampling degradations.

Источник: [официальная запись Zenodo, DOI 10.5281/zenodo.10066460](https://zenodo.org/records/10066460).

Предлагаемый отбор: 4 семейства × 100 parents. Точный набор моделей определяется после сопоставления с training/evaluation списками Community Forensics и SPAI.

### 2. AIGIBench — кандидат для recent-generator internal holdout

- 25 test subsets;
- среди заявленных источников есть FLUX.1-dev, Midjourney V6, Stable Diffusion 3, Imagen, DALL·E 3 и другие современные методы;
- содержит отдельные robustness и real-world subsets.

Источник: [официальный репозиторий AIGIBench](https://github.com/HorizonTEL/AIGIBench).

В репозитории зафиксирована custom license: CC BY-NC-SA 4.0 с дополнительным запретом коммерческого использования, commit `e9b95f80eb5340309876232c0361806ff8c765e4`. Перед загрузкой всё ещё нужно проверить source-specific terms вложенных subsets, состав файлов и hashes. Если права конкретного subset не определены, он остаётся сравнительным benchmark, но не входит в основной validation corpus.

### 3. RAISE — сильный источник camera-native real

- 8156 high-resolution RAW;
- изображения заявлены авторами как camera-native и не подвергавшиеся обработке;
- три камеры, четыре фотографа, более 80 мест;
- ресурс создан для digital image forensics; требуется цитирование работы авторов.

Источник: [официальный сайт RAISE](https://loki.disi.unitn.it/RAISE/).

Ограничение: только три камеры, поэтому RAISE один не закрывает требование четырёх real source/camera families. RAW преобразуется в JPEG/PNG только по отдельному заранее замороженному profile; RAW и производный файл остаются одной family.

### 4. Warwick Image Forensics Dataset — сильный источник real

- более 58 600 изображений;
- 14 цифровых камер;
- разные exposure settings;
- авторами заявлен как open-source и free for use for the digital forensic community.

Источник: [публикация и описание Warwick Dataset](https://wrap.warwick.ac.uk/id/eprint/136576/).

Перед включением архивируется точный текст условий скачивания и проверяется, что выбранные камеры отсутствуют в других split.

### 5. FloreView/HDR — резерв для external real

- FloreView: 6637 изображений и 1831 видео, 46 смартфонов, 11 брендов;
- HDR: более 5000 SDR/HDR-изображений, 23 мобильных устройства, 7 брендов.

Источник: [официальный каталог LESC](https://lesc.dinfo.unifi.it/materials/datasets/).

Статус условный до проверки точной лицензии, способа доступа и отсутствия overlap с обучением детекторов.

## Что нельзя использовать как честный primary holdout

### Community Forensics Dataset

Нельзя тестировать Community Forensics на его собственном training corpus. Набор содержит 2.7 млн AI-изображений от 4803 моделей. Авторы также указывают реальные training sources: LAION, ImageNet, COCO, FFHQ, CelebA, MetFaces, AFHQ-v2, Forchheim, IMD2020, LandscapesHQ и VISION.

Источник: [официальная карточка OwensLab/CommunityForensics](https://huggingface.co/datasets/OwensLab/CommunityForensics).

Допустимо: технический smoke test или отдельная development-проверка SPAI с явной маркировкой источника. Недопустимо: считать результат независимой валидацией Community Forensics.

### VISION и Forchheim

Оба набора прямо перечислены среди real sources, использованных при обучении Community Forensics. Для общего primary holdout двух детекторов они исключаются. Их можно использовать только в development или в исследовании, где overlap явно является частью дизайна.

### GenImage

GenImage содержит более миллиона пар и восемь семейств генераторов, но real-часть взята из ImageNet, который использовался при обучении Community Forensics. Многие генераторы GenImage также могут пересекаться с training distribution обоих детекторов.

Источник: [официальный репозиторий GenImage](https://github.com/GenImage-Dataset/GenImage).

Решение: использовать для development, проверки pipeline и сравнительного benchmark, но не как основной blind holdout общего модуля.

### COCO, LSUN и latent-diffusion training set SPAI

SPAI обучался с real COCO/LSUN и latent-diffusion training/validation data. Эти источники нельзя выдавать за независимый holdout SPAI.

## Лицензии и публикация

- Исходные изображения публичных датасетов не добавляются в публичный GitHub проекта.
- В Git хранятся dataset card, URL/DOI, зафиксированные terms, версия/дата доступа, manifest, SHA-256 и обезличенные результаты.
- Если лицензия запрещает перераспространение, Git содержит только идентификаторы и hashes.
- CC BY-NC-SA Synthbuster допускает исследовательское некоммерческое использование с атрибуцией и share-alike условиями; применение за пределами этих условий требует отдельной проверки.
- Неясная лицензия означает статус `conditional`, а не молчаливое разрешение.

## Правило отбора

1. Скачать и проверить только metadata/terms, не весь корпус.
2. Составить список допустимых source groups и проверить overlap с training sources обоих детекторов.
3. До inference детерминированно выбрать parents по сохранённому seed.
4. Сохранить оригинальные архивные checksums и SHA-256 каждого выбранного файла.
5. Отделить label manifest от файлов inference, переименованных случайными `sample_id`.
6. Не заменять пропавшие или битые файлы после просмотра scores; replacement rule фиксируется заранее.

## Ближайший практический шаг

Metadata и первичное license evidence Synthbuster, RAISE, Warwick, AIGIBench и GenImage сохранены в `dataset/evidence`. Следующий шаг — проверить source-specific terms выбранных AIGIBench subsets и условия фактической загрузки RAISE/Warwick, затем утвердить два набора для первого публичного импорта.
