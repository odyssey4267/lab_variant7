"""Демонстрация доступа к данным: запись и чтение матриц через ORM.

Запуск: python src/db_demo.py  (таблицы должны быть созданы: python src/db_init.py)
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from matrix_lab.db import repository as repo  # noqa: E402
from matrix_lab.db.session import make_engine, make_session_factory  # noqa: E402


def main() -> None:
    session = make_session_factory(make_engine())()
    try:
        if not repo.list_matrices(session, query="demo-1")[0]:
            repo.create_matrix(session, "demo-1", [[3, 2, 0], [0, 5, 0]], ["demo"])
            repo.create_matrix(session, "demo-2", [[1, 2, 1], [4, 4, 4]], ["demo", "symmetric"])
        items, total = repo.list_matrices(session, tag="demo")
        print(f"Матриц с тегом demo: {total}")
        for record in items:
            print(f"  [{record.id}] {record.name}: {record.n_rows}x{record.n_cols}",
                  repo.matrix_data(record))
        analysis = repo.run_analysis(session, items[0].id)
        print("Анализ", analysis.id, "->", repo.analysis_vectors(analysis))
    finally:
        session.close()


if __name__ == "__main__":
    main()
