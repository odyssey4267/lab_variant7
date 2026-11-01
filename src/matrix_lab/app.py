"""Управляющий (верхний) модуль: связывает ввод, обработку и вывод.

Модули передаются как функции (внедрение зависимостей), поэтому любой из них
можно заменить заглушкой или удалённым вызовом без изменения этого кода.
"""

from __future__ import annotations

import sys
from typing import Callable, Optional

from .errors import IntegrationError
from .models import Matrix, ProcessingResult, Report

ReadInput = Callable[[], Matrix]
Process = Callable[[Matrix], ProcessingResult]
Render = Callable[[Report], str]


def _print_error(text: str) -> None:
    print(text, file=sys.stderr)


def run(
    read_input: ReadInput,
    process: Process,
    render: Render,
    write: Callable[[str], None] = print,
    write_err: Optional[Callable[[str], None]] = None,
) -> int:
    """Выполнить конвейер «ввод -> обработка -> вывод». Вернуть код возврата."""
    if write_err is None:
        write_err = _print_error
    try:
        matrix = read_input()
        result = process(matrix)
        report = Report(
            matrix=matrix,
            zero_columns=result.zero_columns,
            descending_rows=result.descending_rows,
            symmetric_rows=result.symmetric_rows,
        )
        write(render(report))
    except IntegrationError as err:
        write_err(f"Ошибка ({type(err).__name__}): {err}")
        return err.exit_code
    return 0
