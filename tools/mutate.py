"""Мутационная проверка набора тестов: «сломать» код и посмотреть, заметят ли тесты.

В копии проекта по одному вносятся простые изменения (мутанты): `<` -> `<=`, `and` -> `or`,
удаление `not`, `+` -> `-`, изменение числовой константы. Для каждого мутанта запускается pytest.
Мутант «убит», если тесты упали; «выжил» — если все тесты прошли (тесты не проверяют это место
или мутант эквивалентен исходному коду).

    python tools/mutate.py                       # все модули matrix_lab
    python tools/mutate.py --files logic.py      # выбранные модули
"""

import argparse
import ast
import os
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PKG = os.path.join("src", "matrix_lab")
SWAP_CMP = {ast.Lt: ast.LtE, ast.LtE: ast.Lt, ast.Gt: ast.GtE, ast.GtE: ast.Gt,
            ast.Eq: ast.NotEq, ast.NotEq: ast.Eq}
SWAP_BIN = {ast.Add: ast.Sub, ast.Sub: ast.Add}
SWAP_BOOL = {ast.And: ast.Or, ast.Or: ast.And}


class Mutator(ast.NodeTransformer):
    """Проходит по дереву; изменяет только узел с номером `target`."""

    def __init__(self, target):
        self.target = target
        self.count = 0
        self.info = None

    def _hit(self, node, text):
        self.count += 1
        if self.count - 1 == self.target:
            self.info = f"строка {node.lineno}: {text}"
            return True
        return False

    def visit_Compare(self, node):
        self.generic_visit(node)
        for i, op in enumerate(node.ops):
            new = SWAP_CMP.get(type(op))
            if new and self._hit(node, f"{type(op).__name__} -> {new.__name__}"):
                node.ops[i] = new()
        return node

    def visit_BinOp(self, node):
        self.generic_visit(node)
        new = SWAP_BIN.get(type(node.op))
        if new and self._hit(node, f"{type(node.op).__name__} -> {new.__name__}"):
            node.op = new()
        return node

    def visit_BoolOp(self, node):
        self.generic_visit(node)
        new = SWAP_BOOL[type(node.op)]
        if self._hit(node, f"{type(node.op).__name__} -> {new.__name__}"):
            node.op = new()
        return node

    def visit_UnaryOp(self, node):
        self.generic_visit(node)
        if isinstance(node.op, ast.Not) and self._hit(node, "удалено not"):
            return node.operand
        return node

    def visit_Constant(self, node):
        value = node.value
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return node
        if isinstance(value, int):
            new = value + 1
        else:
            new = value * 10 if value else 1.0
        if self._hit(node, f"константа {value!r} -> {new!r}"):
            return ast.copy_location(ast.Constant(new), node)
        return node


def mutants_of(source):
    """Число мутантов в исходнике."""
    counter = Mutator(-1)
    counter.visit(ast.parse(source))
    return counter.count


def make_mutant(source, index):
    mutator = Mutator(index)
    tree = mutator.visit(ast.parse(source))
    ast.fix_missing_locations(tree)
    return ast.unparse(tree) + "\n", mutator.info


def run_tests(workdir, timeout):
    try:
        command = [sys.executable, "-m", "pytest", "-x", "-q", "-p", "no:cacheprovider"]
        result = subprocess.run(command, cwd=workdir, capture_output=True, text=True,
                                timeout=timeout)
    except subprocess.TimeoutExpired:
        return True   # зависание тоже считается обнаруженным отличием
    return result.returncode != 0


def main(argv=None):
    parser = argparse.ArgumentParser(description="Мутационная проверка набора тестов.")
    parser.add_argument("--files", nargs="*", help="имена модулей из src/matrix_lab")
    parser.add_argument("--timeout", type=int, default=60)
    args = parser.parse_args(argv)

    names = args.files or sorted(f for f in os.listdir(os.path.join(ROOT, PKG))
                                 if f.endswith(".py") and f != "__init__.py")

    total = killed = 0
    survivors = []
    with tempfile.TemporaryDirectory() as tmp:
        work = os.path.join(tmp, "project")
        shutil.copytree(ROOT, work, ignore=shutil.ignore_patterns(
            ".git", ".mutants", "__pycache__", ".pytest_cache", "coverage.*", ".coverage", ".venv"))
        for name in names:
            path = os.path.join(work, PKG, name)
            with open(path, encoding="utf-8") as f:
                original = f.read()
            for index in range(mutants_of(original)):
                mutated, info = make_mutant(original, index)
                with open(path, "w", encoding="utf-8") as f:
                    f.write(mutated)
                total += 1
                if run_tests(work, args.timeout):
                    killed += 1
                else:
                    survivors.append(f"{name}, {info}")
            with open(path, "w", encoding="utf-8") as f:
                f.write(original)
    print(f"Мутантов: {total}; убито: {killed}; выжило: {total - killed}")
    print(f"Mutation score: {100.0 * killed / max(total, 1):.1f}%")
    for line in survivors:
        print("ВЫЖИЛ:", line)
    return 0


if __name__ == "__main__":
    sys.exit(main())
