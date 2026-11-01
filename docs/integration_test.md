# Тестирование интеграции (уровень 2)

## Тестовые сценарии

| № | Сценарий | Ожидаемый результат | Тест |
|---|----------|--------------------|------|
| 1 | Ввод из файла передаётся в обработку (модуль ввода → модуль обработки) | векторы совпадают с эталоном | `test_processing_module.TestInputToProcessingIntegration` |
| 2 | Полный конвейер, прямые вызовы, пример 1 | `[True, False, True, False]  -> столбцы: 1, 3` | `test_pipeline.TestFullPipelineDirect.test_example_1` |
| 3 | Полный конвейер, прямые вызовы, пример 2 | три вектора по эталону | `test_pipeline.TestFullPipelineDirect.test_example_2` |
| 4 | Файл не найден | код возврата 1, сообщение `InvalidDataError` | `test_pipeline.TestFullPipelineDirect.test_missing_file` |
| 5 | Обрыв ввода с клавиатуры | код возврата 1, «ввод прерван» | `test_pipeline.TestFullPipelineDirect.test_eof_on_console` |
| 6 | Матрица 1 × 1 | все три вектора из одного `True` | `test_processing_module.test_one_by_one_matrix` |
| 7 | Непрямоугольная и пустая матрица | `InvalidDataError` | `test_processing_module` |
| 8 | Преобразование данных туда-обратно (mapping) | исходные данные восстанавливаются | `test_mapping` |
| 9 | Недопустимые структуры JSON, `nan`, `bool` вместо чисел | `InvalidDataError` | `test_mapping.test_bad_structures` |
| 10 | Клиент ↔ сервис по HTTP | результат совпадает с прямым вызовом | `test_http_integration.test_response_matches_direct_call` |
| 11 | Сервис получает некорректный JSON или матрицу | HTTP 400 | `test_http_integration.test_server_rejects_*` |
| 12 | Полный конвейер через REST | вывод идентичен прямому вызову | `test_pipeline_http` |
| 13 | Сервис недоступен | ошибка интеграции, код возврата > 0 | `test_http_integration.test_unreachable_service` |

## Результаты

Запуск: `python -m unittest discover -s tests -t . -v`

```
...................................................................
----------------------------------------------------------------------
Ran 67 tests in 0.447s

OK
```

Все сценарии выполнены успешно. Дополнительно проверена ручная демонстрация:

```
$ python src/main.py examples/input1.txt --transport http --url http://127.0.0.1:8080
Матрица:
0  5  0  1
0  3  0  2
0  1  0  1

1) Все элементы k-го столбца нулевые (k = 1..m):
    [True, False, True, False]  -> столбцы: 1, 3
2) Элементы k-й строки упорядочены по убыванию (k = 1..n):
    [False, False, False]  -> строки: нет
3) k-я строка симметрична (k = 1..n):
    [False, False, False]  -> строки: нет
(код возврата: 0)
```
