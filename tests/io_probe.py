"""Вспомогательные функции для проверки чтения файлов в разных кодировках."""

import os
import tempfile

from matrix_lab.io_utils import read_matrix_file

def read_file_with_bom():
    """Файл «2 1 / 5 / 6», сохранённый как UTF-8 с BOM (так сохраняет Блокнот Windows)."""
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "bom.txt")
        with open(path, "wb") as f:
            f.write("\ufeff2 1\n5\n6\n".encode("utf-8"))
        return read_matrix_file(path)
