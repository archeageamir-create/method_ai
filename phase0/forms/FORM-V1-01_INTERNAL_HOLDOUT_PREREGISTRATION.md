# FORM-V1-01 — preregistration internal holdout

Форма заполняется и подписывается **до** передачи закрытых файлов исполнителю inference.

## 1. Идентификация protocol

| Поле | Значение |
|---|---|
| Protocol ID | |
| Версия статистического плана | `STATISTICAL_ANALYSIS_PLAN_V0_1.md` |
| Дата и время заморозки | |
| Git commit | |
| SHA-256 export/bundle protocol | |
| Владелец protocol | |
| Независимый статистический reviewer | |

## 2. Целевая область

| Поле | Заранее зафиксированное значение |
|---|---|
| Target population | |
| Допустимые форматы | |
| Минимальные размеры | |
| Real source/camera families | |
| Generator families | |
| Исключения | |
| Заявляемые object profiles | `original` / `jpeg_q75` / `jpeg_q50` / `browser_screenshot_100` / иное: |

## 3. Данные и blind

| Поле | Значение |
|---|---|
| Split manifest | |
| SHA-256 split manifest | |
| Количество real parents | |
| Количество AI parents | |
| Проверка уникальности `family_id` между split | |
| Место хранения labels | |
| Держатель labels/ключа | |
| Исполнитель inference без labels | |
| Плановая дата раскрытия | |

## 4. Замороженные инструменты

Для каждого модуля приложить отдельную строку.

| Module ID | Repo commit | Model revision | SHA-256 weights | Runtime | Preprocessing | Operating point |
|---|---|---|---|---|---|---|
| Community Forensics 384 | | | | | | |
| SPAI | | | | | | |

## 5. Первичные критерии

Если утверждённый reviewer не изменил проект до заморозки:

- TPR: нижняя односторонняя 95% exact bound ≥ 0.80;
- FPR: верхняя односторонняя 95% exact bound ≤ 0.05;
- technical failure rate по каждому классу: верхняя граница ≤ 0.05;
- при `n=400`: минимум 334 TP и максимум 12 FP;
- групповой stop-rule при `n=100`: минимум 78 TP и максимум 4 FP.

Любое изменение записывается здесь **до** запуска с обоснованием и подписью reviewer:

>

## 6. Анализ

| Поле | Значение |
|---|---|
| Analysis script | |
| SHA-256 analysis script | |
| Версия Python/SciPy | |
| Метод доверительных границ | Clopper–Pearson exact one-sided 95% |
| Bootstrap seed | |
| Bootstrap repeats | 10 000 |
| Правило технических отказов | |
| Правило повторного запуска | |

## 7. Стоп-правила

- [ ] family leakage не обнаружена;
- [ ] labels недоступны исполнителю inference;
- [ ] hashes данных и manifests сохранены;
- [ ] код, веса, preprocessing и operating point заморожены;
- [ ] шаблон итоговой таблицы заморожен;
- [ ] порядок раскрытия labels согласован;
- [ ] отклонения от protocol отсутствуют либо перечислены ниже.

Отклонения до старта:

>

## 8. Подписи заморозки

| Роль | ФИО | Дата/время | Подпись/идентификатор |
|---|---|---|---|
| Владелец protocol | | | |
| Держатель labels | | | |
| Исполнитель inference | | | |
| Статистический reviewer | | | |
