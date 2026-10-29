"""Точка входа. Примеры запуска:

    python main.py                       # ввод с клавиатуры
    python main.py examples/input1.txt   # ввод из файла
"""

from __future__ import annotations

import argparse
import sys

from matrix_lab import logic
from matrix_lab.io_utils import (
    format_matrix,
    format_vector,
    read_matrix_console,
    read_matrix_file,)

def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Вариант 7: логические векторы по вещественной матрице n*m."
    )
    parser.add_argument("file", nargs="?", help="файл с матрицей (формат: n m, затем n строк)")
    args = parser.parse_args(argv)

    try:
        matrix = read_matrix_file(args.file) if args.file else read_matrix_console()
        zero_cols = logic.column_all_zero(matrix)
    except (OSError, ValueError) as err:
        print(f"Ошибка: {err}", file=sys.stderr)
        return 1

    print("\nМатрица:")
    print(format_matrix(matrix))
    print("\n1) Все элементы k-го столбца нулевые (k = 1..m):")
    print("   ", format_vector(zero_cols))
    return 0

if __name__ == "__main__":
    sys.exit(main())
