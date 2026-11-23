"""Формирует протокол тестирования (Markdown) по табличным тестовым случаям.

Для каждого случая из tests/cases*.py выполняется вызов и записывается фактический результат.

    python tools/protocol.py --out docs/test_protocol.md --title "Протокол тестирования"
"""

import argparse
import datetime
import importlib
import importlib.util
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:0] = [ROOT, os.path.join(ROOT, "src")]

MODULES = ["tests.cases", "tests.cases_mapping", "tests.cases_server", "tests.cases_client",
           "tests.cases_io_guess", "tests.cases_output"]
LIMIT = 70
HEADER = ("| ID | Описание | Входные данные | Ожидаемый результат | Фактический результат "
          "| Вердикт |\n|---|---|---|---|---|---|\n")

def load_groups():
    groups = []
    for name in MODULES:
        if importlib.util.find_spec(name) is not None:
            groups.extend(importlib.import_module(name).GROUPS)
    return groups

def cell(text):
    text = str(text).replace("|", "\\|").replace("\n", " ")
    return text if len(text) <= LIMIT else text[:LIMIT - 1] + "…"

def build(title):
    from tests.cases import expected_text, input_text, run_case

    lines = [f"# {title}", "", f"Дата: {datetime.date.today().isoformat()}", ""]
    total = passed = 0
    failed = []
    for name, cases in load_groups():
        lines += [f"## {name}", "", HEADER.rstrip("\n")]
        for case in cases:
            outcome = run_case(case)
            total += 1
            passed += outcome.passed
            if not outcome.passed:
                failed.append(case.id)
            verdict = "пройден" if outcome.passed else "**не пройден**"
            lines.append("| " + " | ".join(cell(x) for x in (
                case.id, case.desc, input_text(case), expected_text(case), outcome.actual,
                verdict)) + " |")
        lines.append("")
    lines += ["## Итог", "", f"Выполнено случаев: {total}; пройдено: {passed}; "
              f"не пройдено: {total - passed}."]
    if failed:
        lines.append("Не пройдены: " + ", ".join(failed) + ".")
    return "\n".join(lines) + "\n", total, passed

def main(argv=None):
    parser = argparse.ArgumentParser(description="Протокол тестирования по таблицам случаев.")
    parser.add_argument("--out", required=True)
    parser.add_argument("--title", default="Протокол тестирования")
    args = parser.parse_args(argv)
    text, total, passed = build(args.title)
    with open(args.out, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    print(f"Записано {args.out}: случаев {total}, пройдено {passed}, не пройдено {total - passed}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
