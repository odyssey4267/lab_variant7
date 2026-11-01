# MatrixLogicVectors

**Автор(ы):** Калинина Полина Т9-ИП-25-1, 2026
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
- для разработки: `pip install -r requirements-dev.txt` (flake8, coverage).

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
python -m unittest discover -s tests -t . -v
flake8 src tests
coverage run -m unittest discover -s tests -t . && coverage report
```

## Структура проекта

```
lab1_variant7/
├── .github/
│   ├── ISSUE_TEMPLATE/bug_report.md
│   ├── PULL_REQUEST_TEMPLATE.md
│   └── workflows/{ci.yml, integration.yml}
├── docs/
│   ├── technical_specification.md   # ТЗ (ЛР №1)
│   ├── report.*, LEVELS.md, IMPLEMENTATION.md, GIT_GUIDE.md   # материалы ЛР №1
│   ├── architecture.md, testing.md, review.md, platform_comparison.md, russian_git_analogs.md  # ЛР №2
│   ├── integration_plan.md, integration.md, integration_test.md                               # ЛР №3
│   └── error_handling.md, code_review.md, integration_strategies.md                           # ЛР №3
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
├── tests/
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
