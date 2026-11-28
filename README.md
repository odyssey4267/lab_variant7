# MatrixLogicVectors

**Автор(ы):** Фамилия Имя, группа XXX-11, 2026

**Версия:** 1.2.0 (хранилище данных и интеллектуальный интерфейс, ЛР №5)

**Статус интеграции:** все модули интегрированы (ввод → обработка → вывод), REST-транспорт, обработка исключений

Учебный проект (дисциплина «Инструментальные средства разработки программного обеспечения»,
вариант 7): по вещественной матрице n × m строятся логические векторы.

## Назначение

Для матрицы A размерности n × m программа формирует векторы, k-й элемент которых равен `True`,
если выполнено условие, и `False` иначе:

1. все элементы k-го столбца нулевые;
2. элементы k-й строки упорядочены по убыванию;
3. k-я строка симметрична.

Подробности — в техническом задании: `docs/technical_specification.md`.
Система состоит из трёх интегрированных модулей (ввод, обработка, вывод) и управляющего модуля,
стратегия интеграции — нисходящая: `docs/integration_plan.md`.

## Требования к окружению

- Python 3.9 или новее (для запуска сторонние библиотеки не нужны);
- Git;
- для разработки: `pip install -r requirements-dev.txt` (pytest, pytest-cov, flake8, coverage).

## Запуск

```bash
python src/main.py                        # ввод матрицы с клавиатуры
python src/main.py examples/input1.txt   # ввод из файла, прямые вызовы модулей

# модуль обработки как REST-сервис
python src/serve.py --port 8080                                              # терминал 1
python src/main.py examples/input1.txt --transport http --url http://127.0.0.1:8080   # терминал 2
```

Формат файла: первая строка `n m`, далее `n` строк по `m` чисел через пробел
(десятичная запятая допускается). Примеры — в каталоге `examples/`.

Коды возврата: 0 — успех; 1 — некорректные данные; 2 — модуль недоступен; 3 — таймаут;
4 — конфликт версий API.

## Тесты и проверки

```bash
pytest                                   # все тесты
pytest -m regression                     # регрессионные
pytest --cov=src --cov-branch --cov-report=term-missing --cov-fail-under=80
flake8 src tests tools
python tools/protocol.py --out docs/test_protocol.md   # протокол тестирования
python tools/metrics.py                  # метрики
python tools/mutate.py                   # мутационная проверка
```

## Структура проекта

```
matrix-vectors/
├── .github/
│   ├── ISSUE_TEMPLATE/bug_report.md
│   ├── PULL_REQUEST_TEMPLATE.md
│   └── workflows/{ci.yml, integration.yml, testing.yml}
├── docs/
│   ├── technical_specification.md   # ТЗ (ЛР №1)
│   ├── architecture.md, testing.md, review.md, platform_comparison.md, russian_git_analogs.md  # ЛР №2
│   ├── integration_plan.md, integration.md, integration_test.md                               # ЛР №3
│   ├── error_handling.md, code_review.md, integration_strategies.md                           # ЛР №3
│   └── testing.md, bug_reports.md, test_protocol*.md, testing_methods.md,
│       testing_metrics.md, test_review.md, code_review_lr4.md                          # ЛР №4
├── examples/                        # примеры входных файлов
├── src/
│   ├── main.py                      # точка входа (сборка конвейера)
│   ├── serve.py                     # запуск REST-сервиса обработки
│   └── matrix_lab/
│       ├── logic.py, io_utils.py    # логика (ЛР №1) и ввод/вывод
│       ├── models.py, errors.py     # контракты между модулями
│       ├── app.py                   # управляющий модуль
│       ├── input_module.py, processing_module.py, output_module.py
│       ├── mapping.py               # сопоставление данных (JSON)
│       ├── server.py, http_client.py   # REST-сервис и клиент
│       └── stubs.py                 # заглушки (нисходящая интеграция)
├── tests/                           # unit, «чёрный/белый ящик», интеграция, регрессия
├── tools/                           # protocol.py, metrics.py, mutate.py (ЛР №4)
├── requirements-dev.txt, setup.cfg, .coveragerc
└── README.md
```

## Стратегия ветвления

Используется упрощённый **Git Flow**:

| Ветка | Назначение |
|-------|-----------|
| `main` | стабильная версия; каждое состояние можно выпускать, релизы помечаются тегами (`v0.1.0`, `v1.0.0`) |
| `develop` | интеграционная ветка; сюда сливаются завершённые функции |
| `feature/*` | короткоживущие ветки под одну задачу; создаются от `develop`, сливаются обратно в `develop` |

Порядок работы: `feature/*` → `develop` → `main` (слияния через `git merge --no-ff`, чтобы в истории
оставались видны ветки).

**Почему не GitHub Flow.** В GitHub Flow есть только `main` и короткие ветки, а выпуск происходит после
каждого слияния. В учебном проекте нужна отдельная «буферная» ветка `develop`, где можно накапливать и
проверять изменения (в том числе при интеграции модулей в ЛР №3), не нарушая стабильности `main`.
Полноценный Git Flow с ветками `release/*` и `hotfix/*` для проекта такого размера избыточен.


## Хранилище данных и REST API (ЛР №5)

Матрицы и результаты обработки хранятся в SQLite (SQLAlchemy), доступ — через REST API (FastAPI) с
Swagger UI. Подробности: `docs/database.md`, схема: `docs/er_diagram.md`, миграции: `docs/migrations.md`.

```bash
pip install -r requirements-dev.txt
alembic upgrade head          # создать базу (миграции)
python src/serve_api.py       # http://127.0.0.1:8000  (страница)  и  /docs  (Swagger UI)
python src/db_demo.py         # пример записи и чтения через ORM
pytest tests/storage -v       # тесты хранилища и API
python tools/db_check.py      # проверка SQL-скриптов sql/schema.sql и sql/seed.sql
```
