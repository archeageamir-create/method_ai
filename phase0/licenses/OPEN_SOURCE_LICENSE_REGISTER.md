# Реестр лицензий open-source инструментов

**Версия:** 0.2
**Дата фиксации:** 14 июля 2026 года
**Проект:** методика судебно-экспертного фототехнического исследования ИИ-изображений, специальность 4.1

## Назначение

Документ фиксирует лицензии кода и весов двух AI-детекторов, а также двух локальных генераторов, использованных для development dry run. Оригинальные тексты лицензий приложены отдельными файлами без изменений.

## Зафиксированные компоненты

| Компонент | Зафиксированная версия | Артефакт | Лицензия | Основание |
|---|---|---|---|---|
| Community Forensics — код | commit `ee5b71d43db0f3779e1edd64ee927b13f2dd6ad4` | `JeongsooP/Community-Forensics` | MIT | файл `LICENSE` в репозитории |
| Community Forensics 384 — веса | revision `6076002bf0d9dd37537f965ee2f06f826c333b61` | `OwensLab/commfor-model-384` | MIT | поле `license: mit` в карточке модели Hugging Face |
| SPAI — код | commit `8ff7b3b6779b4fcb43cf313471d9cb1c62d129a4` | `mever-team/spai` | Apache License 2.0 | файл `LICENSE` в репозитории |
| SPAI — веса | официальный `spai.pth` | ссылка авторов в README | Apache License 2.0 | README прямо относит лицензию Apache 2.0 к исходному коду и весам модели |
| SDXL-Turbo — веса | commit `71153311d3dbb46851df1931d3ca6e939de83304` | `stabilityai/sdxl-turbo` | Stability AI Community License (`sai-nc-community`) | оригинальный `LICENSE.md` в зафиксированной revision Hugging Face |
| Stable Diffusion 1.5 — веса | commit `451f4fe16113bff5a5d2269ed5ad43b0592e9a14` | `stable-diffusion-v1-5/stable-diffusion-v1-5` | CreativeML Open RAIL-M | metadata карточки модели; полный текст приложен из исходного `CompVis/stable-diffusion` commit `21f890f9da3cfbeaba8e2ac3c425ee9e998d5229` |

## Контрольные суммы

| Файл | SHA-256 |
|---|---|
| Оригинальный `LICENSE` Community Forensics | `29A48B1748653514622E3D768797C1D9DD2B4092BFA252DC2BC9168C8C5F2BFA` |
| `model.safetensors` Community Forensics 384 | `B89F36275F3BF5E2B040EEE36597A8F19DB051BFF9A473A9CF7B2466284FB387` |
| Оригинальный `LICENSE` SPAI | `3DDF9BE5C28FE27DAD143A5DC76EEA25222AD1DD68934A047064E56ED2FA40C5` |
| Официальный `spai.pth` | `24159F27D7C8C2CD0CB6C4019189EB89AD0874A0D9D15F8DC9AFD39CA9648A55` |
| `SDXL_TURBO_LICENSE.md` | `D6F6B1A4DCE5C852BD6D7D9482D002BAF0CCDB71E662250B73BE9EEC8764EE8D` |
| `STABLE_DIFFUSION_1_5_CREATIVEML_OPENRAIL_M.txt` | `BE351EBE7AC01BCDBB018639AADCFD38F136B7DC3F2A3D4D3A24DB51D1B210EF` |

## Первоисточники

- Community Forensics: https://github.com/JeongsooP/Community-Forensics
- Community Forensics 384: https://huggingface.co/OwensLab/commfor-model-384
- SPAI: https://github.com/mever-team/spai
- SDXL-Turbo: https://huggingface.co/stabilityai/sdxl-turbo
- Stable Diffusion 1.5: https://huggingface.co/stable-diffusion-v1-5/stable-diffusion-v1-5
- Полный текст CreativeML Open RAIL-M: https://github.com/CompVis/stable-diffusion/blob/21f890f9da3cfbeaba8e2ac3c425ee9e998d5229/LICENSE

## Границы этой фиксации

- Реестр подтверждает условия использования выбранного кода и официальных весов на дату фиксации.
- Лицензии не подтверждают научную пригодность инструмента: она проверяется отдельно валидацией.
- Зависимости Python, библиотеки, обучающие и тестовые датасеты могут иметь собственные лицензии.
- Для распространения копий необходимо сохранять оригинальные лицензионные уведомления.
- Лицензии генераторов содержат собственные условия и ограничения использования; их нельзя называть эквивалентом MIT или Apache 2.0.
- Любая из приложенных лицензий не предоставляет гарантий точности или пригодности для судебно-экспертного применения.
