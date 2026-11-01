"""Точка входа: сборка конвейера «ввод -> обработка -> вывод» и запуск.

Примеры:
    python src/main.py examples/input1.txt
    python src/main.py                        # ввод с клавиатуры
"""

from __future__ import annotations

import argparse
import sys

from matrix_lab import app, stubs


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Вариант 7: логические векторы по вещественной матрице n*m."
    )
    parser.add_argument("file", nargs="?", help="файл с матрицей (формат: n m, затем n строк)")
    return parser.parse_args(argv)


def main(argv=None) -> int:
    parse_args(argv)
    # Нисходящая интеграция: сначала все нижние модули — заглушки.
    read_input = stubs.read_input_stub
    process = stubs.process_stub
    render = stubs.render_stub
    return app.run(read_input, process, render)


if __name__ == "__main__":
    sys.exit(main())
