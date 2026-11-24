# План и результаты тестирования (ЛР №4)

## 1. Цель и объект

Проверить, что программа строит три логических вектора по вещественной матрице n × m и корректно
отвергает неверные данные. Объект — все модули: `logic`, `io_utils`, `mapping`, `server`,
`http_client`, `output_module`, `processing_module`, `app`, `models`, `errors`, `stubs`.

## 2. Метод и инструмент (вариант 7)

| Что | Решение |
|-----|---------|
| Метод «чёрного ящика» | анализ граничных значений + предположение об ошибке |
| Методы «белого ящика» | покрытие решений, условий, комбинаций условий (таблицы истинности D1–D8) |
| Инструмент | pytest (по варианту — Google Test для C++; для проекта на Python используется pytest — отклонение от варианта необходимо согласовать с преподавателем) |
| Покрытие | coverage.py (+ pytest-cov), учёт ветвей, цель варианта — не менее 80 % |
| Статический анализ | flake8 (`max-line-length = 100`, `max-complexity = 10`) |

## 3. Виды тестов и расположение

| Вид | Файлы | Тестов |
|-----|-------|-------:|
| «Чёрный ящик» (метка `blackbox`) | `tests/test_bva_*.py`, `test_server_guessing.py`, `test_client_guessing.py`, `test_input_guessing.py`, `test_output_bva.py` | 131 |
| «Белый ящик» (метка `whitebox`) | `tests/test_whitebox.py` | 31 |
| Интеграционные сценарии IT-01 … IT-09 (метка `integration`) | `tests/test_integration_scenarios.py` | 13 |
| Регрессионные (метка `regression`) | `tests/regression/` | по одному на дефект |
| Тесты ЛР №1–3 (unittest) | `tests/test_logic.py`, `test_io.py`, `test_app.py`, `test_pipeline*.py`, … | 80 |

Всего тестов в проекте: **196**. Таблицы тестовых случаев (`tests/cases*.py`) используются и
pytest, и скриптом `tools/protocol.py` — протокол собирается из реальных запусков.

## 4. Критерии успешности

- все тесты проходят (`pytest`);
- покрытие операторов и ветвей не ниже 80 % (`--cov-fail-under=80`);
- `flake8 src tests tools` без замечаний;
- каждый найденный дефект имеет отчёт, исправление и регрессионный тест.

## 5. Результаты

Покрытие (coverage.py, операторы + ветви): **99%** при цели не менее 80 %.

| Модуль | Операторов | Пропущено | Ветвей | Частично | Покрытие |
|---|---:|---:|---:|---:|---:|
| `main.py` | 20 | 0 | 2 | 0 | 100% |
| `__init__.py` | 0 | 0 | 0 | 0 | 100% |
| `app.py` | 22 | 0 | 2 | 0 | 100% |
| `errors.py` | 10 | 0 | 0 | 0 | 100% |
| `http_client.py` | 56 | 0 | 12 | 0 | 100% |
| `input_module.py` | 12 | 0 | 2 | 0 | 100% |
| `io_utils.py` | 62 | 1 | 22 | 1 | 98% |
| `logic.py` | 26 | 0 | 8 | 0 | 100% |
| `mapping.py` | 65 | 0 | 30 | 0 | 100% |
| `models.py` | 15 | 0 | 0 | 0 | 100% |
| `output_module.py` | 12 | 0 | 0 | 0 | 100% |
| `processing_module.py` | 9 | 0 | 0 | 0 | 100% |
| `server.py` | 62 | 0 | 8 | 0 | 100% |
| `stubs.py` | 9 | 0 | 0 | 0 | 100% |
| `serve.py` | 18 | 0 | 0 | 0 | 100% |
| `TOTAL` | 398 | 1 | 86 | 1 | 99% |

Найдено и исправлено **9 дефектов** (`docs/bug_reports.md`). Протоколы: `docs/test_protocol_run1.md`
(до исправлений, уровень 1) и `docs/test_protocol.md` (итоговый).

## 6. Запуск

```bash
pytest                                   # все тесты
pytest -m blackbox                       # только «чёрный ящик»
pytest -m regression                     # регрессионные
pytest --cov=src --cov-branch --cov-report=term-missing --cov-fail-under=80
python tools/protocol.py --out docs/test_protocol.md
flake8 src tests tools
```
