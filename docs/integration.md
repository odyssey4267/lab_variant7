# Документация по интеграции (уровень 2)

## 1. Архитектура взаимодействия

Все три модуля интегрированы в единый конвейер «ввод → обработка → вывод», которым управляет
модуль `app`. Модуль обработки можно вызывать двумя способами:

| Транспорт | Как включается | Для чего |
|-----------|----------------|----------|
| `direct` (по умолчанию) | прямой вызов функции `processing_module.process` | работа в одном процессе |
| `http` | `--transport http --url <адрес>` | модуль обработки — отдельный REST-сервис (HTTP + JSON) |

Статус: интегрированы все модули; REST-транспорт подключён.

## 2. Схема потоков данных

```mermaid
sequenceDiagram
    participant U as Пользователь
    participant A as app (управляющий)
    participant I as input_module
    participant C as http_client
    participant S as server (REST)
    participant P as processing_module
    participant O as output_module
    U-»A: python src/main.py файл --transport http
    A-»I: read_matrix(файл)
    I--»A: Matrix
    A-»C: process_remote(Matrix)
    C-»S: POST /api/v1/process (JSON: matrix)
    S-»P: process(Matrix)
    P--»S: ProcessingResult
    S--»C: 200 OK (JSON: result)
    C--»A: ProcessingResult
    A-»O: render(Report)
    O--»A: текст
    A--»U: вывод + код возврата
```

## 3. Структуры данных модулей

| Модуль | Структура | Поля |
|--------|-----------|------|
| Ввод | `Matrix` | список из n строк по m вещественных чисел |
| Обработка (вход) | `Matrix` | то же |
| Обработка (выход) | `ProcessingResult` | `zero_columns` (m значений bool), `descending_rows` (n), `symmetric_rows` (n) |
| Вывод (вход) | `Report` | `matrix`, `zero_columns`, `descending_rows`, `symmetric_rows` |
| REST-запрос | JSON | `api_version`, `matrix{rows, cols, data}` |
| REST-ответ | JSON | `api_version`, `result{zeroColumns, descendingRows, symmetricRows}` |

## 4. Таблица сопоставления данных (mapping)

| Источник | Приёмник | Правило | Подход |
|----------|----------|---------|--------|
| `Matrix` (список строк) | `matrix.data` | копия, числа приводятся к `float` | преобразование типов |
| `len(Matrix)` | `matrix.rows` | вычисляется | маппинг (производное поле) |
| `len(Matrix[0])` | `matrix.cols` | вычисляется | маппинг (производное поле) |
| `ProcessingResult.zero_columns` | `result.zeroColumns` | snake_case → camelCase | маппинг (переименование) |
| `ProcessingResult.descending_rows` | `result.descendingRows` | snake_case → camelCase | маппинг (переименование) |
| `ProcessingResult.symmetric_rows` | `result.symmetricRows` | snake_case → camelCase | маппинг (переименование) |
| JSON `true/false` (или `0/1`) | `bool` | `0/1` приводятся к `False/True`, остальное — ошибка | преобразование типов |
| JSON-числа | `float` | `nan`, `inf`, строки и `bool` отвергаются | нормализация и проверка |
| `ProcessingResult` + `Matrix` | `Report` | объединяются в управляющем модуле | прямое сопоставление |
| вектор bool (позиции с 0) | номера в тексте отчёта | `k + 1` для позиций с `True` | нормализация (нумерация с 1) |

Преобразования реализованы в `src/matrix_lab/mapping.py`.

## 5. Протокол и форматы

**Протокол:** REST поверх HTTP/1.x; формат сообщений — JSON (UTF-8). Реализация на стандартной
библиотеке (`http.server`, `urllib`).

| Метод и путь | Назначение | Успех | Ошибки |
|--------------|-----------|-------|--------|
| `GET /api/v1/health` | проверка работоспособности | 200 | — |
| `POST /api/v1/process` | обработка матрицы | 200 | 400 — некорректные данные; 404 — неверный путь |

Запуск сервиса и клиента:

```bash
# терминал 1: модуль обработки как сервис
python src/serve.py --port 8080

# терминал 2: приложение, использующее сервис
python src/main.py examples/input1.txt --transport http --url http://127.0.0.1:8080
```

## 6. Примеры запросов и ответов

**Запрос** `POST /api/v1/process` (матрица из `examples/input1.txt`):

```json
{"api_version": "1.0", "matrix": {"rows": 3, "cols": 4, "data": [[0.0, 5.0, 0.0, 1.0], [0.0, 3.0, 0.0, 2.0], [0.0, 1.0, 0.0, 1.0]]}}
```

**Ответ** `200 OK`:```json
{"api_version": "1.0", "result": {"zeroColumns": [true, false, true, false], "descendingRows": [false, false, false], "symmetricRows": [false, false, false]}}
```

**Ответ** `400 Bad Request` (в строке меньше чисел, чем указано в `cols`):

```json
{"error": "invalid_data", "message": "Строка 1: ожидалось 2 чисел."}
```

## 7. Конфликты при совместной работе

Модули разрабатывались в параллельных ветках `feature/output-module` и `feature/rest-transport`;
обе ветки изменяли строку «Статус интеграции» в `README.md`. Конфликт слияния возник при слиянии
второй ветки в `develop` и был разрешён вручную: в итоговой строке объединены оба изменения.
