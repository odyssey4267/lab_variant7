"""Тесты вспомогательных скриптов: db_init, db_demo, serve_api, export_openapi."""

import json
import runpy
import sys
from pathlib import Path

import db_demo
import db_init
import serve_api

ROOT = Path(__file__).resolve().parents[2]


def use_file_db(monkeypatch, tmp_path):
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'scripts.db'}")


def test_db_init_creates_tables(monkeypatch, tmp_path, capsys):
    use_file_db(monkeypatch, tmp_path)
    db_init.main()
    assert "Таблицы созданы" in capsys.readouterr().out
    assert (tmp_path / "scripts.db").exists()


def test_db_demo_writes_and_reads(monkeypatch, tmp_path, capsys):
    use_file_db(monkeypatch, tmp_path)
    db_init.main()
    db_demo.main()
    first = capsys.readouterr().out
    assert "Матриц с тегом demo: 2" in first and "Анализ 1" in first
    db_demo.main()  # повторный запуск не создаёт дубликатов
    assert "Матриц с тегом demo: 2" in capsys.readouterr().out


def test_serve_api_starts_uvicorn(monkeypatch):
    calls = {}
    monkeypatch.setattr(serve_api.uvicorn, "run", lambda app, **kw: calls.update(kw=kw))
    monkeypatch.setattr(sys, "argv", ["serve_api.py", "9001"])
    monkeypatch.setenv("DATABASE_URL", "sqlite://")
    serve_api.main()
    assert calls["kw"] == {"host": "127.0.0.1", "port": 9001}


def test_serve_api_default_port(monkeypatch):
    calls = {}
    monkeypatch.setattr(serve_api.uvicorn, "run", lambda app, **kw: calls.update(kw=kw))
    monkeypatch.setattr(sys, "argv", ["serve_api.py"])
    monkeypatch.setenv("DATABASE_URL", "sqlite://")
    serve_api.main()
    assert calls["kw"]["port"] == 8000


def test_export_openapi_writes_file(monkeypatch, tmp_path):
    target = ROOT / "docs" / "openapi.json"
    before = target.read_bytes() if target.exists() else None
    try:
        runpy.run_path(str(ROOT / "tools" / "export_openapi.py"), run_name="__main__")
        spec = json.loads(target.read_text(encoding="utf-8"))
        assert "/api/v1/matrices" in spec["paths"]
    finally:
        if before is None:
            target.unlink()
        else:
            target.write_bytes(before)
