# Хранилище данных и интеллектуальный интерфейс (ЛР №5)

Вариант 7: тип хранилища — реляционное (SQLite), инструмент — SQLAlchemy + FastAPI, интерфейс —
REST API + Swagger UI. Предметная область — сквозной проект (логические векторы по матрице n × m).

## 1. Проектирование

**Концептуальная модель** — сущности и связи на диаграмме `docs/er_diagram.md`.
**Логическая модель** — 7 таблиц (ниже). **Физическая модель** — SQLite, DDL в `sql/schema.sql`,
ORM-модели в `src/matrix_lab/db/models.py`, миграции в `migrations/`.

### Нормализация

* **1НФ.** Все атрибуты атомарны. Матрица не хранится строкой «1 2 3» в одном поле, а раскладывается
  по ячейкам (`matrix_cell`: строка, столбец, значение); логический вектор — по элементам
  (`vector_result`). Повторяющихся групп нет.
* **2НФ.** Во всех таблицах с составным ключом (`matrix_tag`) неключевых атрибутов нет; в остальных
  таблицах ключ простой (`id`), поэтому частичных зависимостей быть не может. Уникальность позиции
  ячейки (`matrix_id`, `row_idx`, `col_idx`) обеспечена ограничением `UNIQUE`.
* **3НФ.** Транзитивных зависимостей нет: размеры матрицы хранятся только в `matrix`, имя тега — только
  в `tag` (в `matrix_tag` лишь идентификаторы), параметр `eps` — в `analysis`, а не дублируется в
  каждом элементе результата.

### Таблицы

| Таблица | Поля | Ключи и ограничения |
|---|---|---|
| `matrix` | id, name, n_rows, n_cols, created_at, note | PK id; UNIQUE name; CHECK n_rows ≥ 1, n_cols ≥ 1 |
| `matrix_cell` | id, matrix_id, row_idx, col_idx, value | FK matrix_id → matrix (CASCADE); UNIQUE (matrix_id, row_idx, col_idx) |
| `tag` | id, name | PK id; UNIQUE name |
| `matrix_tag` | matrix_id, tag_id | составной PK; FK на matrix и tag (CASCADE) |
| `analysis` | id, matrix_id, eps, created_at | FK matrix_id → matrix (CASCADE) |
| `vector_result` | id, analysis_id, kind, position, value | FK analysis_id → analysis (CASCADE); CHECK kind IN (zero_columns, descending_rows, symmetric_rows); UNIQUE (analysis_id, kind, position) |
| `setting` | key, value | PK key |

Каскадное удаление: при удалении матрицы удаляются её ячейки, связи с тегами, анализы и результаты.
В SQLite внешние ключи по умолчанию не проверяются, поэтому при каждом подключении выполняется
`PRAGMA foreign_keys=ON` (`db/session.py`).

## 2. Доступ к данным

`src/matrix_lab/db/repository.py` — функции чтения и записи (ORM, без «сырого» SQL):
`create_matrix`, `get_matrix`, `update_matrix`, `delete_matrix`, `list_matrices` (фильтры, сортировка,
страницы), `run_analysis`, `get_analysis`, `list_analyses`, `get/set_setting`. Обработка матрицы
выполняется функциями из `logic.py` (ЛР №1–3) — хранилище встроено в тот же проект.

Защита: имена полей сортировки проверяются по белому списку; значения подставляются параметрами
(ORM), поэтому SQL-инъекция невозможна; поиск по имени экранирует `%` и `_`; размер матрицы ограничен
`MAX_CELLS = 100000` элементов.

## 3. REST API

Запуск: `python src/serve_api.py`. Swagger UI — http://127.0.0.1:8000/docs, схема — `/openapi.json`
(выгрузка в файл: `python tools/export_openapi.py` → `docs/openapi.json`, импортируется в Postman).

| Метод | Адрес | Назначение | Коды |
|---|---|---|---|
| POST | /api/v1/matrices | добавить матрицу | 201, 409 (имя занято), 422 |
| GET | /api/v1/matrices | список: `tag`, `q`, `sort_by`, `order`, `limit`, `offset` | 200, 422 |
| GET | /api/v1/matrices/{id} | получить матрицу | 200, 404 |
| PUT | /api/v1/matrices/{id} | изменить имя, данные, теги, примечание | 200, 404, 409, 422 |
| DELETE | /api/v1/matrices/{id} | удалить | 204, 404 |
| POST | /api/v1/matrices/{id}/analyses | запустить обработку (тело необязательно: `{"eps": …}`) | 201, 404, 422 |
| GET | /api/v1/matrices/{id}/analyses | история запусков | 200, 404 |
| GET | /api/v1/analyses/{id} | результат одного запуска | 200, 404 |
| GET / PUT | /api/v1/settings | настройки пользователя | 200, 422 |
| GET | /api/v1/matrices/{id}/statistics | статистика матрицы (уровень 3) | 200, 404 |
| GET | /api/v1/matrices/{id}/forecast?row=0&steps=3 | прогноз строки (уровень 3) | 200, 404, 422 |
| GET | /api/v1/analytics/summary | сводка по всем анализам (уровень 3) | 200 |
| GET | /api/v1/health | проверка работоспособности | 200 |

### Примеры

Добавить матрицу:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/matrices \
  -H "Content-Type: application/json" \
  -d '{"name": "example1", "data": [[3, 2, 0], [0, 5, 0]], "tags": ["demo"]}'
```

Ответ (201), формат:

```json
{"id": 1, "name": "example1", "rows": 2, "cols": 3, "tags": ["demo"], "note": null,
 "created_at": "2026-11-26T10:00:00", "data": [[3.0, 2.0, 0.0], [0.0, 5.0, 0.0]]}
```

Запустить обработку: `POST /api/v1/matrices/1/analyses` с телом `{}`. Ответ (201):

```json
{"id": 1, "matrix_id": 1, "eps": 1e-09, "created_at": "2026-11-26T10:00:05",
 "zero_columns": [false, false, true],
 "descending_rows": [true, false],
 "symmetric_rows": [false, true]}
```

Ошибка (например, имя занято, 409): `{"detail": "Матрица с именем «example1» уже существует."}`.

Список с фильтром и сортировкой: `GET /api/v1/matrices?tag=demo&sort_by=name&order=desc&limit=5`.

## 4. Интеллектуальный интерфейс

Главная страница `/` (один файл, `src/matrix_lab/web_page.py`) и Swagger UI `/docs`.

| Принцип | Реализация |
|---|---|
| Адаптивность и персонализация | настройки `page_size`, `sort_by`, `order`, `eps` хранятся в таблице `setting`; список матриц и анализ используют их по умолчанию; кнопка «Запомнить настройки» |
| Контекстность | интерфейс показывает только то, что относится к текущему фильтру (тег, часть имени), и общее число записей по фильтру |
| Интерактивность | формы ввода матрицы, таблица с сортировкой и фильтрами, кнопки «Обработать» и «Удалить», сообщения об ошибках |

Компоненты: сбор данных — `db/repository.py`; анализ — `logic.py`, `analytics.py`; представление —
HTML-страница и JSON; взаимодействие — маршруты FastAPI.

## 5. Интеллектуальный анализ (уровень 3)

`src/matrix_lab/analytics.py` (pandas, numpy, scikit-learn):

* `matrix_statistics` — среднее, медиана, стандартное отклонение, минимум, максимум, средние по
  столбцам, суммы по строкам;
* `forecast_row` — линейная регрессия (`LinearRegression`) по номеру столбца: прогноз продолжения
  строки на `steps` элементов;
* `vector_summary` — по всем сохранённым анализам: сколько элементов каждого вектора и доля `True`
  (`pandas.groupby`).

Маршруты — `src/matrix_lab/analytics_routes.py`.

## 6. Запуск

```bash
pip install -r requirements-dev.txt
alembic upgrade head          # создать/обновить базу (миграции, см. docs/migrations.md)
python src/serve_api.py       # сервер на порту 8000
python src/db_demo.py         # пример записи и чтения через ORM
pytest tests/storage -v       # тесты хранилища и API
```

База хранится в файле `matrix_lab.db` в каталоге запуска; другой адрес — переменная окружения
`DATABASE_URL` (например, `sqlite:///other.db`).
