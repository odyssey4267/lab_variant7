"""Тесты проекта. Каталог src/ добавляется в путь импорта, чтобы импортировать пакет matrix_lab."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
