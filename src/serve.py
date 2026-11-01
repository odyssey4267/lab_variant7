"""Запуск модуля обработки как REST-сервиса.

    python src/serve.py --port 8080
"""

from __future__ import annotations

import argparse
import sys

from matrix_lab.server import make_server


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="REST-сервис модуля обработки матриц.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument("--delay", type=float, default=0.0,
                        help="искусственная задержка ответа, с (для проверки таймаута)")
    args = parser.parse_args(argv)

    server = make_server(args.host, args.port, delay=args.delay)
    print(f"Сервис запущен: http://{args.host}:{args.port}/api/v1/ (Ctrl+C для остановки)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nОстановлено.")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
