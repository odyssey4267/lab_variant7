"""Точка входа: сборка конвейера «ввод -> обработка -> вывод» и запуск.

Примеры:
    python src/main.py examples/input1.txt
    python src/main.py                                  # ввод с клавиатуры
    python src/main.py examples/input1.txt --transport http --url http://127.0.0.1:8080
"""

from __future__ import annotations

import argparse
import sys
from functools import partial

from matrix_lab import app, http_client, input_module, output_module, processing_module


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Вариант 7: логические векторы по вещественной матрице n*m."
    )
    parser.add_argument("file", nargs="?", help="файл с матрицей (формат: n m, затем n строк)")
    parser.add_argument("--transport", choices=("direct", "http"), default="direct",
                        help="способ вызова модуля обработки: прямой вызов или REST")
    parser.add_argument("--url", default=http_client.DEFAULT_URL, help="адрес REST-сервиса")
    parser.add_argument("--timeout", type=float, default=http_client.DEFAULT_TIMEOUT,
                        help="таймаут запроса к сервису, с")
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    read_input = partial(input_module.read_matrix, args.file)
    if args.transport == "http":
        process = partial(http_client.process_remote, base_url=args.url, timeout=args.timeout)
    else:
        process = processing_module.process
    render = output_module.render
    return app.run(read_input, process, render)


if __name__ == "__main__":
    sys.exit(main())
