# Автоматическая регистрация изображений

Скрипт `register-images.ps1` находит JPEG/PNG, считает SHA-256, читает размеры, назначает `sample_id` и добавляет строки в реестр.

Пример для собственных фотографий:

```powershell
& .\register-images.ps1 `
  -InputDirectory "C:\путь\real" `
  -OutputCsv "C:\путь\DATASET_REGISTER.csv" `
  -GroundTruth real `
  -TruthBasis controlled_capture `
  -SourceType camera `
  -SourceName "название телефона или камеры"
```

Пример для контролируемой генерации:

```powershell
& .\register-images.ps1 `
  -InputDirectory "C:\путь\ai" `
  -OutputCsv "C:\путь\DATASET_REGISTER.csv" `
  -GroundTruth ai_generated `
  -TruthBasis controlled_generation `
  -SourceType generator `
  -SourceName "название генератора" `
  -SourceVersion "версия, если известна"
```

Повторный запуск безопасен: файл с уже известным SHA-256 будет пропущен.

## Импорт собственных фотографий с iPhone

`import-iphone-real.ps1` сохраняет все HEIC без изменений, проверяет SHA-256 после копирования, выбирает заданное количество development-оригиналов, создаёт контролируемые JPEG и формирует parent-child реестр.

```powershell
& .\import-iphone-real.ps1 `
  -SourceDirectory "C:\путь\к\HEIC" `
  -OutputRoot "C:\путь\к\локальному-набору" `
  -DevelopmentCount 20 `
  -SourceName "Apple iPhone 15" `
  -SourceVersion "iOS 26.3.1"
```

Папка локального набора должна быть исключена из Git. Скрипт отказывается перезаписывать сохранённый оригинал, если его SHA-256 отличается от нового источника.

## Контролируемые преобразования

`create-test-transformations.ps1` создаёт для каждого оригинала четыре проверочные копии:

- JPEG quality 75;
- resize 50%;
- центральный crop 10%;
- resize 50% + JPEG quality 75.

Пример:

```powershell
& .\create-test-transformations.ps1 `
  -InputDirectory "C:\путь\originals" `
  -OutputDirectory "C:\путь\derived"
```

Скрипт создаёт `TRANSFORM_MANIFEST.csv` с параметрами, размерами и SHA-256 каждого производного файла. Скриншоты создаются отдельно вручную, потому что автоматическая перекодировка не имитирует настоящий скриншот.
