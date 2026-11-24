"""Метрики тестирования: покрытие, плотность дефектов, среднее время обнаружения дефекта.

Исходные данные:
    docs/bug_reports.md  — заголовки «## BUG-n …» (число дефектов);
    git                  — метка testing-start и коммиты «Тест BUG-n …» (время обнаружения);
    coverage.json        — результат `coverage json` (покрытие).

    python tools/metrics.py
"""

import json
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def git(*args):
    result = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True,
                            encoding="utf-8", check=True)
    return result.stdout.strip()


def count_sloc():
    """Строки кода в src/: без пустых и без строк-комментариев."""
    total = 0
    for folder, _, files in os.walk(os.path.join(ROOT, "src")):
        for name in files:
            if name.endswith(".py"):
                with open(os.path.join(folder, name), encoding="utf-8") as f:
                    total += sum(1 for ln in f if ln.strip() and not ln.strip().startswith("#"))
    return total


def defects():
    path = os.path.join(ROOT, "docs", "bug_reports.md")
    with open(path, encoding="utf-8") as f:
        return sorted(set(re.findall(r"^## (BUG-\d+)", f.read(), flags=re.M)))


def detection_times():
    """Минуты от метки testing-start до первого коммита «Тест BUG-n …» для каждого дефекта."""
    start = int(git("log", "-1", "--format=%ct", "testing-start"))
    found = {}
    for line in git("log", "--reverse", "--format=%ct|%s", "testing-start..HEAD").splitlines():
        stamp, subject = line.split("|", 1)
        if subject.startswith("Тест "):
            for bug in re.findall(r"BUG-\d+", subject):
                found.setdefault(bug, (int(stamp) - start) / 60.0)
    return found


def coverage_summary():
    path = os.path.join(ROOT, "coverage.json")
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    files = {name: info["summary"]["percent_covered"] for name, info in data["files"].items()}
    return data["totals"]["percent_covered"], files


def main():
    bugs = defects()
    sloc = count_sloc()
    print(f"Дефектов: {len(bugs)}; строк кода (SLOC): {sloc}")
    print(f"Плотность дефектов: {len(bugs) / (sloc / 1000.0):.1f} на 1000 строк")
    times = detection_times()
    print("\nВремя обнаружения дефектов (мин от testing-start):")
    for bug in bugs:
        if bug in times:
            print(f"  {bug}: {times[bug]:.2f}")
    if times:
        print(f"Среднее время обнаружения: {sum(times.values()) / len(times):.2f} мин")
    cov = coverage_summary()
    if cov:
        print(f"\nПокрытие (операторы + ветви): {cov[0]:.1f}%")
        for name in sorted(cov[1]):
            print(f"  {name}: {cov[1][name]:.1f}%")
    return 0


if __name__ == "__main__":
    sys.exit(main())
