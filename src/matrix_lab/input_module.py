"""Модуль ввода: получает матрицу из файла или с клавиатуры."""

from __future__ import annotations

from typing import Optional

from .errors import InvalidDataError
from .io_utils import read_matrix_console, read_matrix_file
from .models import Matrix


def read_matrix(source: Optional[str] = None) -> Matrix:
    """Прочитать матрицу. source — путь к файлу или None (ввод с клавиатуры).

    :raises InvalidDataError: файл не найден, неверный формат, ввод прерван.
    """
    try:
        if source:
            return read_matrix_file(source)
        return read_matrix_console()
    except (ValueError, OSError, EOFError) as err:
        raise InvalidDataError(str(err) or "ввод прерван") from err
